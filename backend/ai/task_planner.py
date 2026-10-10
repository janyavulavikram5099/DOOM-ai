"""
Multi-Step Task Planner for DOOM AI.
Deconstructs complex, compound natural voice instructions into structured, sequential action steps.
Handles context tracking across conversational turns and generates structured execution plans.
"""

import logging
import re
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from ..automation.registry import app_registry

logger = logging.getLogger("vikram.ai.task_planner")


@dataclass
class TaskStep:
    """Represents an atomic action step within a multi-step task plan."""
    step_id: int
    app_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    critical: bool = True


@dataclass
class ActionPlan:
    """Represents an end-to-end multi-step plan decomposed from a user's instruction."""
    plan_id: str
    raw_query: str
    target_app: str
    steps: List[TaskStep] = field(default_factory=list)
    success_response: str = "Task executed successfully, Master."
    requires_confirmation: bool = False
    confirmation_prompt: str = ""


class TaskPlanner:
    """
    Analyzes complex user voice queries and plans sequential operations
    across Windows applications.
    """

    def __init__(self):
        pass

    def plan(self, query: str) -> Optional[ActionPlan]:
        """
        Main entry point to plan a compound or single task.
        Returns an ActionPlan if the query represents a multi-step or in-app action,
        or None if it should fall back to general intent routing.
        """
        if not query or not query.strip():
            return None

        clean_query = query.strip()
        logger.info(f"Analyzing query for task planning: '{clean_query}'")

        # 1. WhatsApp messaging pattern
        whatsapp_plan = self._plan_whatsapp(clean_query)
        if whatsapp_plan:
            return whatsapp_plan

        # 2. Calculator arithmetic evaluation pattern
        calc_plan = self._plan_calculator(clean_query)
        if calc_plan:
            return calc_plan

        # 3. Browser search & top result pattern
        browser_plan = self._plan_browser(clean_query)
        if browser_plan:
            return browser_plan

        # 4. Spotify playback pattern
        spotify_plan = self._plan_spotify(clean_query)
        if spotify_plan:
            return spotify_plan

        # 5. File Explorer navigation pattern
        explorer_plan = self._plan_explorer(clean_query)
        if explorer_plan:
            return explorer_plan

        # 6. Editor / Code / Note pattern
        editor_plan = self._plan_editor(clean_query)
        if editor_plan:
            return editor_plan

        # 7. Generic compound "open X and ..." pattern
        compound_plan = self._plan_generic_compound(clean_query)
        if compound_plan:
            return compound_plan

        return None

    def _plan_whatsapp(self, query: str) -> Optional[ActionPlan]:
        """
        Ultra-flexible extraction for any natural WhatsApp voice instruction:
        - "open whatsapp and send a message to Amma saying hi"
        - "open whatsapp and send message to Amma saying hi"
        - "open whatsapp and send a message to Amma hi"
        - "open whatsapp send message to Amma hi"
        - "open whatsapp and send hi to Amma"
        - "open whatsapp and message Amma saying hi"
        - "open whatsapp and text Amma hi"
        - "send a message to Amma saying hi"
        - "message Amma saying hi"
        - "tell Amma on whatsapp hi"
        """
        raw = query.strip()
        lower = raw.lower()

        # Check if WhatsApp or messaging is involved
        has_wa = "whatsapp" in lower or "whatsup" in lower or "whats up" in lower
        has_msg = any(w in lower for w in ["message", "send", "text", "tell", "saying", "msg"])
        
        if not (has_wa or (app_registry.last_active_app == "whatsapp" and has_msg)):
            if not ("send" in lower and any(w in lower for w in ["to", "saying", "that"])):
                return None

        # Clean noise prefixes
        clean = re.sub(r"^(?:hey\s+(?:doom|vikram)[,\s]*)?", "", raw, flags=re.I).strip()
        clean = re.sub(r"^(?:please\s+)?(?:can you\s+)?", "", clean, flags=re.I).strip()
        clean = re.sub(r"^open\s+whatsapp\s+(?:and\s+|,\s*)?", "", clean, flags=re.I).strip()

        contact = None
        msg = None

        # Form 1: send <msg> to <contact> (e.g. "send hi to Amma", "send hello to Rahul on whatsapp")
        m1 = re.search(r'^(?:send|text|message)\s+(?P<msg>.+?)\s+to\s+(?P<contact>[a-zA-Z0-9\s]+?)(?:\s+on\s+whatsapp)?$', clean, re.I)
        if m1 and m1.group("msg").strip().lower() not in ["a message", "message", "the message", "text"]:
            contact = m1.group("contact").strip()
            msg = m1.group("msg").strip().strip('"\'')

        # Form 2: [send [a] message to | message [to] | text [to] | tell] <contact> [saying | that | with message | :] <msg>
        if not contact or not msg:
            m2 = re.search(
                r'^(?:send\s+(?:a\s+)?message\s+(?:to\s+)?|message\s+(?:to\s+)?|text\s+(?:to\s+)?|tell\s+(?:to\s+)?|send\s+to\s+)'
                r'(?P<contact>[a-zA-Z0-9\s]+?)'
                r'(?:\s+(?:saying|that|with\s+message|with\s+the\s+message|msg)\s+|[:,\s]+saying\s+|[:,-]\s*)'
                r'(?P<msg>.+)$',
                clean,
                re.I
            )
            if m2:
                contact = m2.group("contact").strip()
                contact = re.sub(r'^(to\s+|on\s+whatsapp\s+)', '', contact, flags=re.I).strip()
                contact = re.sub(r'\s+on\s+whatsapp$', '', contact, flags=re.I).strip()
                msg = m2.group("msg").strip().strip('"\'')

        # Form 3: [send [a] message to | send to | message | text | tell] <contact> <msg> (without "saying")
        # e.g. "send a message to Amma hi", "message Amma hi", "send message to Amma are you free"
        if not contact or not msg:
            m3 = re.search(
                r'^(?:send\s+(?:a\s+)?message\s+to\s+|send\s+to\s+|message\s+(?:to\s+)?|text\s+(?:to\s+)?|tell\s+)'
                r'(?P<contact>[a-zA-Z0-9]+)\s+'
                r'(?P<msg>.+)$',
                clean,
                re.I
            )
            if m3:
                contact = m3.group("contact").strip()
                contact = re.sub(r'\s+on\s+whatsapp$', '', contact, flags=re.I).strip()
                raw_m = m3.group("msg").strip().strip('"\'')
                msg = re.sub(r'^(?:saying|that|with\s+message)\s+', '', raw_m, flags=re.I).strip()

        # Form 4: General WhatsApp with "saying" anywhere
        if not contact or not msg:
            m4 = re.search(r'(?:to|message)\s+(?P<contact>[a-zA-Z0-9\s]+?)\s+saying\s+(?P<msg>.+)', clean, re.I)
            if m4:
                contact = m4.group("contact").strip()
                msg = m4.group("msg").strip().strip('"\'')

        if contact and msg:
            # Clean punctuation from end of msg
            msg = msg.rstrip(".!?")
            return self._build_whatsapp_plan(query, contact, msg)

        return None

    def _build_whatsapp_plan(self, query: str, contact: str, msg: str) -> ActionPlan:
        plan_id = str(uuid.uuid4())[:8]
        steps = [
            TaskStep(
                step_id=1,
                app_id="whatsapp",
                action="open",
                params={},
                description="Open WhatsApp and bring to foreground"
            ),
            TaskStep(
                step_id=2,
                app_id="whatsapp",
                action="send_message",
                params={"contact": contact, "message": msg},
                description=f"Find '{contact}', open conversation, type and send: '{msg}'"
            )
        ]
        return ActionPlan(
            plan_id=plan_id,
            raw_query=query,
            target_app="whatsapp",
            steps=steps,
            success_response=f"Message sent to {contact}, Master."
        )

    def _plan_calculator(self, query: str) -> Optional[ActionPlan]:
        """
        Matches:
        - "open calculator and calculate 250 multiplied by 45"
        - "calculate 500 divided by 4"
        - "what is 25 plus 40 in calculator"
        """
        lower = query.lower()
        if not ("calculator" in lower or "calculate" in lower or "math" in lower):
            return None

        # Extract expression
        expr_match = re.search(
            r'(?:calculate|what is|compute|solve)\s+(?P<expr>[0-9\s\+\-\*\/\.\(\)xX\^]|plus|minus|times|multiplied by|divided by|into|by)+',
            query,
            re.IGNORECASE
        )
        if expr_match:
            expr = expr_match.group("expr").strip()
            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id="calculator",
                    action="open",
                    params={},
                    description="Launch Windows Calculator"
                ),
                TaskStep(
                    step_id=2,
                    app_id="calculator",
                    action="calculate",
                    params={"expression": expr},
                    description=f"Evaluate expression: {expr}"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app="calculator",
                steps=steps,
                success_response=f"Calculated {expr}, Master."
            )

        return None

    def _plan_browser(self, query: str) -> Optional[ActionPlan]:
        """
        Matches:
        - "open chrome, search for java inheritance and open the first result"
        - "search google for latest ai news and open top result"
        - "open youtube and search lofi beats"
        - "open gmail and draft an email to <recipient>"
        """
        lower = query.lower()
        browser_app = "edge" if "edge" in lower else "chrome"

        # Check Gmail draft
        if "gmail" in lower and ("draft" in lower or "email" in lower or "write" in lower or "compose" in lower):
            to_match = re.search(r'(?:to|recipient)\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', query)
            to_addr = to_match.group(1) if to_match else ""
            subj_match = re.search(r'subject\s+([a-zA-Z0-9\s]+?)(?:body|content|$)', query, re.I)
            subj = subj_match.group(1).strip() if subj_match else ""
            body_match = re.search(r'(?:body|saying|content)\s+(.+)$', query, re.I)
            body = body_match.group(1).strip() if body_match else ""

            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id=browser_app,
                    action="open",
                    params={},
                    description="Open web browser"
                ),
                TaskStep(
                    step_id=2,
                    app_id=browser_app,
                    action="draft_email",
                    params={"to": to_addr, "subject": subj, "body": body},
                    description="Open Gmail composer and fill draft"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app=browser_app,
                steps=steps,
                success_response="Gmail draft prepared in browser, Master."
            )

        # Check search with top result
        search_top_match = re.search(
            r'(?:open\s+(?:chrome|edge|browser|google)\s+(?:and|,)?\s*)?'
            r'(?:search(?:\s+for)?|google)\s+(?P<q>.+?)\s+'
            r'(?:and\s+open\s+(?:the\s+)?(?:first|top)\s+result)',
            query,
            re.IGNORECASE
        )
        if search_top_match:
            search_query = search_top_match.group("q").strip()
            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id=browser_app,
                    action="open",
                    params={},
                    description=f"Launch {browser_app.capitalize()}"
                ),
                TaskStep(
                    step_id=2,
                    app_id=browser_app,
                    action="search_and_open_top_result",
                    params={"query": search_query},
                    description=f"Search for '{search_query}' and open top result"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app=browser_app,
                steps=steps,
                success_response=f"Searched for '{search_query}' and opened the top result, Master."
            )

        # Simple browser search
        simple_search = re.search(
            r'open\s+(?:chrome|edge|browser)\s+and\s+search(?:\s+for)?\s+(?P<q>.+)',
            query,
            re.IGNORECASE
        )
        if simple_search:
            search_query = simple_search.group("q").strip()
            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id=browser_app,
                    action="open",
                    params={},
                    description=f"Launch {browser_app.capitalize()}"
                ),
                TaskStep(
                    step_id=2,
                    app_id=browser_app,
                    action="search",
                    params={"query": search_query},
                    description=f"Search for '{search_query}'"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app=browser_app,
                steps=steps,
                success_response=f"Searched for '{search_query}' in {browser_app.capitalize()}, Master."
            )

        return None

    def _plan_spotify(self, query: str) -> Optional[ActionPlan]:
        """
        Matches:
        - "open spotify and play bohemian rhapsody"
        - "play bohemian rhapsody on spotify"
        - "pause spotify" / "next song on spotify"
        """
        lower = query.lower()
        if "spotify" not in lower and app_registry.last_active_app != "spotify":
            return None

        # Play/pause/next/prev controls
        if re.search(r'\b(pause|stop)\b', lower):
            return ActionPlan(
                plan_id=str(uuid.uuid4())[:8],
                raw_query=query,
                target_app="spotify",
                steps=[TaskStep(step_id=1, app_id="spotify", action="pause", description="Pause Spotify playback")],
                success_response="Spotify playback paused, Master."
            )

        if re.search(r'\b(next\s+song|next\s+track|skip)\b', lower):
            return ActionPlan(
                plan_id=str(uuid.uuid4())[:8],
                raw_query=query,
                target_app="spotify",
                steps=[TaskStep(step_id=1, app_id="spotify", action="next_track", description="Skip to next track")],
                success_response="Skipped to next song, Master."
            )

        # Search and play
        m = re.search(
            r'(?:open\s+spotify\s+and\s+)?play\s+(?P<song>.+?)(?:\s+on\s+spotify)?$',
            query,
            re.IGNORECASE
        )
        if m:
            song = m.group("song").strip()
            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id="spotify",
                    action="open",
                    params={},
                    description="Launch Spotify"
                ),
                TaskStep(
                    step_id=2,
                    app_id="spotify",
                    action="search_and_play",
                    params={"query": song},
                    description=f"Search and play '{song}'"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app="spotify",
                steps=steps,
                success_response=f"Now playing '{song}' on Spotify, Master."
            )

        return None

    def _plan_explorer(self, query: str) -> Optional[ActionPlan]:
        """
        Matches:
        - "open file explorer and go to downloads"
        - "open downloads folder"
        - "search for report in file explorer"
        """
        lower = query.lower()
        folder_match = re.search(
            r'open\s+(?P<folder>downloads|documents|desktop|pictures|music|videos|c\s+drive)\s+(?:folder|directory)?',
            query,
            re.IGNORECASE
        )
        if folder_match:
            folder = folder_match.group("folder").strip()
            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id="explorer",
                    action="open_folder",
                    params={"folder": folder},
                    description=f"Open '{folder}' in File Explorer"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app="explorer",
                steps=steps,
                success_response=f"Opened {folder} folder, Master."
            )

        return None

    def _plan_editor(self, query: str) -> Optional[ActionPlan]:
        """
        Matches:
        - "open vs code and run the project"
        - "open notepad and write <notes>"
        """
        lower = query.lower()
        if "vs code" in lower or "vscode" in lower or "code" in lower:
            if "run" in lower or "compile" in lower:
                plan_id = str(uuid.uuid4())[:8]
                steps = [
                    TaskStep(step_id=1, app_id="vscode", action="open", description="Open VS Code"),
                    TaskStep(step_id=2, app_id="vscode", action="run_code", description="Run active project (F5)")
                ]
                return ActionPlan(
                    plan_id=plan_id,
                    raw_query=query,
                    target_app="vscode",
                    steps=steps,
                    success_response="Triggered project execution in VS Code, Master."
                )

        if "notepad" in lower and ("write" in lower or "type" in lower):
            m = re.search(r'(?:write|type)\s+(?P<text>.+)', query, re.I)
            text = m.group("text").strip() if m else ""
            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(step_id=1, app_id="notepad", action="open", description="Open Notepad"),
                TaskStep(step_id=2, app_id="notepad", action="new_file", description="New note"),
                TaskStep(step_id=3, app_id="notepad", action="type_text", params={"content": text}, description="Type content")
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app="notepad",
                steps=steps,
                success_response="Notepad opened and content written, Master."
            )

        return None

    def _plan_generic_compound(self, query: str) -> Optional[ActionPlan]:
        """
        Matches general compound commands: "open <app> and <action>"
        """
        m = re.search(r'open\s+(?P<app>[a-zA-Z0-9\s]+?)\s+and\s+(?P<rest>.+)', query, re.I)
        if m:
            app_name = m.group("app").strip().lower()
            rest = m.group("rest").strip()

            # Ignore if app is too generic or a verb
            if app_name in ["the", "a", "this", "my"]:
                return None

            plan_id = str(uuid.uuid4())[:8]
            steps = [
                TaskStep(
                    step_id=1,
                    app_id=app_name,
                    action="open",
                    description=f"Open {app_name}"
                ),
                TaskStep(
                    step_id=2,
                    app_id=app_name,
                    action="generic_action",
                    params={"sub_command": rest},
                    description=f"Perform '{rest}' in {app_name}"
                )
            ]
            return ActionPlan(
                plan_id=plan_id,
                raw_query=query,
                target_app=app_name,
                steps=steps,
                success_response=f"Executed actions in {app_name}, Master."
            )

        return None


# Global singleton task planner
task_planner = TaskPlanner()
