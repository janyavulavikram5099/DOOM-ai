"""
VIKRAM AI - Central Action Dispatcher
Enforces policy check, routes to appropriate executor, records command history,
and plays audible TTS response.
"""

import logging
from typing import Any

from ..ai.gemini_qa import answer as ai_answer
from ..ai.language_detector import detect_language, get_language_name, is_english
from ..assistant.conversation import conversation_context
from ..assistant.text_to_speech import tts
from ..database.sqlite import db
from ..security.confirmation import confirmation_gate
from ..security.policy_engine import PolicyEngine
from ..automation.registry import app_registry
from .application_executor import ApplicationExecutor
from .browser_executor import BrowserExecutor
from .code_executor import CodeExecutor
from .file_executor import FileExecutor
from ..ai.telugu_engine import telugu_engine, is_telugu
from .system_executor import SystemExecutor

logger = logging.getLogger("vikram.execution.dispatcher")


class ActionDispatcher:
    @classmethod
    def _derive_search_query(cls, raw_text: str, intent: str, params: dict[str, Any]) -> str:
        """Derives a clean, useful Google search query from the user's original request."""
        import re
        text = raw_text.strip()
        # Strip wake words
        text = re.sub(
            r"^(?:hey\s+doom|hi\s+doom|hello\s+doom|ok\s+doom|okay\s+doom|doom\s+ai|doom|hey\s+vikram|vikram)\s*[,:\-]?\s*",
            "",
            text,
            flags=re.I
        ).strip()

        # 1. Explicit SEARCH command: "search Unstop site" -> "Unstop site"
        m_explicit = re.match(r"^(?:please\s+)?(?:can\s+you\s+)?search\b\s*(.*)", text, re.I)
        if m_explicit:
            q = m_explicit.group(1).strip()
            if q.lower().startswith("for ") and not q.lower().startswith("for loop"):
                q = q[4:].strip()
            elif q.lower().startswith("about "):
                q = q[6:].strip()
            return q.strip("?. ") or text

        # 2. Official website patterns: "find the official website of Microsoft" -> "Microsoft official website"
        m_web = re.search(r"(?:find|search|open|show|get)?\s*(?:the\s+)?(?:official\s+)?website\s+of\s+(.+)", text, re.I)
        if m_web:
            entity = m_web.group(1).strip("?. ")
            return f"{entity} official website"

        m_web2 = re.search(r"official\s+website\s+(?:for|of)\s+(.+)", text, re.I)
        if m_web2:
            entity = m_web2.group(1).strip("?. ")
            return f"{entity} official website"

        # 3. Information patterns: "find information about Java inheritance" -> "Java inheritance"
        m_info = re.search(r"(?:find|search|get|show)?\s*(?:information|info|details|data)\s+(?:about|on|regarding)\s+(.+)", text, re.I)
        if m_info:
            return m_info.group(1).strip("?. ")

        # 4. App download: if intent is OPEN_APPLICATION and params has app_name
        if intent == "OPEN_APPLICATION":
            app = params.get("app_name", "").strip()
            if app:
                if not any(w in app.lower() for w in ["download", "app", "installer", "software"]):
                    return f"{app} download"
                return app

        # 5. General question or command: strip leading command verbs
        clean = re.sub(r"^(?:can you|please|tell me|search for|search about|search|google)\s+", "", text, flags=re.I).strip("?. ")
        return clean or text

    @classmethod
    def execute(cls, parsed_intent: dict[str, Any]) -> dict[str, Any]:
        """
        Main execution flow:
        Intent -> Policy Engine -> Confirmation Check -> Executor -> History Log -> TTS.
        """
        intent = parsed_intent.get("intent", "UNKNOWN")
        params = parsed_intent.get("params", {})
        raw_text = parsed_intent.get("raw_text", "")
        language = parsed_intent.get("language") or ("te" if is_telugu(raw_text) else "en")

        logger.info(f"Executing intent: {intent} (language: {language}) with params: {params}")

        # Handle Confirmation Responses (e.g. user said "yes" or "no" after confirmation prompt)
        if intent == "CONFIRM_ACTION":
            pending = confirmation_gate.resolve("yes")
            if pending:
                return cls.execute(pending)
            else:
                resp = "ఆదేశం ఏదీ పెండింగ్‌లో లేదు, మాస్టర్." if language == "te" else "No action was pending confirmation."
                tts.speak(resp, lang=language)
                return {"status": "NOOP", "message": resp}

        if intent == "CANCEL_ACTION":
            confirmation_gate.resolve("no")
            resp = "చర్య రద్దు చేయబడింది, మాస్టర్." if language == "te" else "Action cancelled."
            tts.speak(resp, lang=language)
            return {"status": "CANCELLED", "message": resp}

        if intent == "GREETING":
            voice_response = telugu_engine.get_response("GREETING", params) if language == "te" else "Hello Master."
            tts.speak(voice_response, lang=language)
            db.add_command_history("Master", raw_text, intent, "SUCCESS", voice_response)
            return {"status": "SUCCESS", "intent": intent, "voice_response": voice_response, "details": {}}


        # 1. Policy & Permission Validation
        is_allowed, reason, requires_confirm = PolicyEngine.validate_action(intent, params)
        if not is_allowed:
            tts.speak(reason)
            db.add_command_history("Master", raw_text, intent, "BLOCKED", reason)
            return {"status": "BLOCKED", "message": reason}

        # 2. Confirmation Gate if high impact
        if requires_confirm:
            confirmation_gate.set_pending(intent, params, reason)
            tts.speak(reason)
            db.add_command_history("Master", raw_text, intent, "PENDING_CONFIRMATION", reason)
            return {"status": "PENDING_CONFIRMATION", "message": reason}

        # 3. Dispatch to Executor
        success = False
        voice_response = "Okay, Master."
        details: dict[str, Any] = {}

        if intent == "OPEN_APPLICATION":
            app = params.get("app_name", "")
            success, voice_response = ApplicationExecutor.launch(app)
            if success:
                app_registry.set_active_app(app)
                conversation_context.update(current_app=app, last_intent=intent)
            else:
                voice_response = f"{app.strip().title() if app.strip() else 'Application'} is not installed, Master."

        elif intent == "CLOSE_APPLICATION":
            app = params.get("app_name", "")
            success, voice_response = ApplicationExecutor.close(app)
            if success:
                if app_registry.last_active_app and app.lower() in app_registry.last_active_app.lower():
                    app_registry.clear_active_app()
                conversation_context.update(current_app=None, last_intent=intent)

        elif intent == "EXECUTE_TASK_PLAN":
            plan = params.get("plan")
            if not plan:
                success = False
                voice_response = "Invalid task plan, Master."
            else:
                logger.info(f"Executing task plan {plan.plan_id} for app '{plan.target_app}' with {len(plan.steps)} steps.")
                all_succeeded = True
                last_step_result = None
                executed_steps = []

                last_step_data = {}
                last_step_msg = ""
                for step in plan.steps:
                    logger.info(f"Executing plan step {step.step_id}: {step.description} [{step.app_id} -> {step.action}]")
                    try:
                        ctrl = app_registry.get_controller(step.app_id)
                        res = ctrl.execute_action(step.action, step.params)
                        if isinstance(res, tuple):
                            step_success = res[0]
                            step_msg = res[1]
                            step_data = res[2] if len(res) > 2 else {}
                        else:
                            step_success = getattr(res, "success", True)
                            step_msg = getattr(res, "message", "") or getattr(res, "error", "")
                            step_data = getattr(res, "data", {})

                        executed_steps.append({
                            "step_id": step.step_id,
                            "action": step.action,
                            "success": step_success,
                            "message": step_msg,
                            "data": step_data
                        })

                        if not step_success:
                            logger.error(f"Step {step.step_id} failed: {step_msg}")
                            if step.critical:
                                all_succeeded = False
                                voice_response = f"Failed to complete task: {step_msg or 'unknown error'}."
                                break
                        else:
                            last_step_data = step_data
                            last_step_msg = step_msg

                    except Exception as e:
                        logger.error(f"Exception during step {step.step_id} execution: {e}")
                        all_succeeded = False
                        voice_response = f"An error occurred while executing {step.description}: {str(e)}."
                        break

                if all_succeeded:
                    success = True
                    if last_step_data and "spoken_response" in last_step_data:
                        voice_response = last_step_data["spoken_response"]
                    elif last_step_data and "formatted_result" in last_step_data:
                        expr = last_step_data.get("expression", "")
                        res_val = last_step_data.get("formatted_result", "")
                        voice_response = f"Calculated: {expr} is {res_val}, Master."
                    else:
                        voice_response = plan.success_response

                    app_registry.set_active_app(plan.target_app)
                    conversation_context.update(current_app=plan.target_app, last_intent=intent)

                details["plan_id"] = plan.plan_id
                details["steps_executed"] = executed_steps

        elif intent == "OPEN_WEBSITE":
            from ..monitoring.system_monitor import SystemMonitor
            site = params.get("website", "")
            browser = params.get("browser", "chrome")
            if not SystemMonitor.is_network_online():
                voice_response = "Internet connection is required for that action, Master."
                tts.speak(voice_response, lang=language)
                return {"status": "OFFLINE", "voice_response": voice_response, "details": {"website": site}}
            success, voice_response = BrowserExecutor.open_website(site, browser)

        elif intent == "OPEN_FILE":
            path = params.get("file_path") or params.get("file_name", "")
            is_folder = params.get("is_folder", False)
            success, voice_response = FileExecutor.open_file(path, is_folder)

        elif intent == "CREATE_FILE":
            name = params.get("file_name", "")
            success, voice_response = FileExecutor.create_file(name)

        elif intent == "DELETE_FILE":
            name = params.get("file_name", "")
            success, voice_response = FileExecutor.delete_file(name)

        elif intent == "SEARCH_FILES":
            pat = params.get("pattern", "")
            success, voice_response, results = FileExecutor.search_files(pat)
            details["results"] = results

        elif intent == "COMPILE_CODE":
            name = params.get("file_name", "")
            success, voice_response, details = CodeExecutor.compile_code(name)

        elif intent == "RUN_CODE":
            name = params.get("file_name", "")
            success, voice_response, details = CodeExecutor.run_code(name)

        elif intent == "COMPILE_AND_RUN_CODE":
            name = params.get("file_name", "")
            success, voice_response, details = CodeExecutor.compile_and_run(name)

        elif intent == "EXPLAIN_ERROR":
            success, voice_response, diag = CodeExecutor.explain_last_error()
            details = diag or {}

        elif intent == "LOCK_DEVICE":
            success, voice_response = SystemExecutor.lock_workstation(lang=language)

        elif intent == "UNLOCK_DEVICE":
            success, voice_response = SystemExecutor.unlock_request()

        elif intent == "SLEEP_DEVICE":
            success, voice_response = SystemExecutor.sleep_device()

        elif intent == "SHUTDOWN_DEVICE":
            success, voice_response = SystemExecutor.shutdown_device()

        elif intent == "RESTART_DEVICE":
            success, voice_response = SystemExecutor.restart_device()

        elif intent == "VOLUME_CONTROL":
            action = params.get("action", "up")
            level = params.get("level", 50)
            success, voice_response = SystemExecutor.volume_control(action, level, lang=language)
            details["volume_action"] = action
            details["volume_level"] = level

        elif intent == "BRIGHTNESS_CONTROL":
            action = params.get("action", "up")
            level = params.get("level", 15)
            success, voice_response = SystemExecutor.brightness_control(action, level, lang=language)
            details["brightness_action"] = action
            details["brightness_level"] = level

        elif intent == "AIRPLANE_MODE_CONTROL":
            action = params.get("action", "on")
            success, voice_response = SystemExecutor.set_airplane_mode(action, lang=language)
            details["airplane_mode_action"] = action

        elif intent == "ACCESSIBILITY_CONTROL":
            action = params.get("action", "open")
            feature = params.get("feature", "general")
            success, voice_response = SystemExecutor.accessibility_control(action, feature, lang=language)
            details["accessibility_feature"] = feature
            details["accessibility_action"] = action

        elif intent == "OPEN_SETTINGS":
            setting = params.get("setting", "general")
            success, voice_response = SystemExecutor.open_settings_page(setting, lang=language)
            details["setting_page"] = setting

        elif intent == "SCREENSHOT":
            success, voice_response, path = SystemExecutor.take_screenshot()
            details["screenshot_path"] = path

        elif intent == "GET_DATE_TIME":
            query_type = params.get("type", "both")
            success, voice_response, dt_details = SystemExecutor.get_date_time(query_type)
            details.update(dt_details)

        elif intent == "WIFI_CONTROL":
            action = params.get("action", "on")
            success, voice_response = SystemExecutor.set_wifi_state(action, lang=language)
            details["wifi_action"] = action

        elif intent == "BLUETOOTH_CONTROL":
            action = params.get("action", "on")
            success, voice_response = SystemExecutor.set_bluetooth_state(action, lang=language)
            details["bluetooth_action"] = action

        elif intent == "SYSTEM_INFO":
            success = True
            metric = params.get("metric", "all")
            if metric == "battery":
                import psutil
                bat = psutil.sensors_battery()
                if bat:
                    pct = int(bat.percent)
                    is_plugged = bool(bat.power_plugged) if bat.power_plugged is not None else False
                    charging_str = "and currently charging" if is_plugged else "on battery"
                    voice_response = f"Battery is at {pct} percent, {charging_str}, Master."
                    details["battery_percent"] = pct
                    details["is_charging"] = is_plugged
                else:
                    voice_response = "Battery sensor information is unavailable, Master."
            elif metric == "cpu":
                import psutil
                voice_response = f"CPU usage is currently at {int(psutil.cpu_percent(interval=None))}%."
            elif metric == "ram":
                import psutil
                voice_response = f"Memory usage is at {int(psutil.virtual_memory().percent)}%."
            else:
                voice_response = "Displaying system diagnostics."

        elif intent == "ASK_AI":
            from ..monitoring.system_monitor import SystemMonitor
            query = params.get("query", raw_text)
            if not SystemMonitor.is_network_online():
                offline_msg = "Internet connection is required for that action, Master."
                tts.speak(offline_msg, lang=language)
                return {
                    "status": "OFFLINE",
                    "intent": "ASK_AI",
                    "voice_response": offline_msg,
                    "details": {
                        "query": query,
                        "answer": "Internet connection is required for that action, Master.",
                        "lang": language or "en"
                    }
                }
            from ..ai.chat_engine import chat_engine
            res = chat_engine.process_prompt(query)
            return {
                "status": "SUCCESS",
                "intent": "ASK_AI",
                "voice_response": res.get("tts_answer", "Completed, Master."),
                "details": {
                    "query": query,
                    "answer": res.get("answer", ""),
                    "source_url": res.get("source_url", ""),
                    "source_title": res.get("source_title", ""),
                    "lang": res.get("lang", language or "en")
                }
            }

        else:
            # Unknown or unmatched command — do NOT auto-search Google.
            # Only two triggers for web search:
            #   A) Missing application (handled in OPEN_APPLICATION above)
            #   B) Explicit "search <query>" command (handled in SEARCH_WEB above)
            clean_raw = raw_text.strip()
            if not clean_raw:
                return {"status": "NOOP", "intent": "UNKNOWN", "voice_response": "", "details": {}}

            success = False
            voice_response = "I'm not sure how to help with that, Master. Try saying 'search' followed by what you're looking for."
            if language == "te":
                voice_response = "మాస్టర్, నాకు అది అర్థం కాలేదు. 'search' అని చెప్పి మీరు వెతుకుతున్నది చెప్పండి."

        # Generate natural Telugu response if user query was in Telugu
        if language == "te":
            if success:
                if is_telugu(voice_response):
                    pass  # Retain tailored Telugu response from executor
                elif "isn't installed" in voice_response:
                    voice_response = "అప్లికేషన్ ఇన్‌స్టాల్ చేయబడలేదు మాస్టర్, నేను క్రోమ్‌లో సెర్చ్ చేశాను."
                elif "isn't available locally" in voice_response or "not available locally" in voice_response:
                    voice_response = "ఇది లోకల్‌గా అందుబాటులో లేదు మాస్టర్, నేను క్రోమ్‌లో సెర్చ్ చేశాను."
                else:
                    voice_response = telugu_engine.get_response(intent, params, details)
            else:
                if "Internet connection is required" in voice_response:
                    voice_response = "ఆ శోధన కోసం ఇంటర్నెట్ కనెక్షన్ అవసరం, మాస్టర్."
                else:
                    voice_response = "క్షమించండి మాస్టర్, ఈ పనిని పూర్తి చేయడంలో సమస్య ఎదురైంది."

        # Audible neural response in user's spoken language (LOCK_DEVICE speaks pre-lock)
        if intent != "LOCK_DEVICE":
            tts.speak(voice_response, lang=language)


        # Record in persistent history
        status_label = "SUCCESS" if success else "FAILED"
        import json
        details_str = json.dumps(details) if details else None
        db.add_command_history("Master", raw_text, intent, status_label, voice_response, details_str)

        return {
            "status": status_label,
            "intent": intent,
            "voice_response": voice_response,
            "details": details
        }
