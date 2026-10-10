"""
VIKRAM AI - Main Application Server & WebSocket Bridge
Serves the Futuristic HUD interface, REST APIs, real-time WebSocket telemetry,
and coordinates the background service and system tray.
"""

import asyncio
import json
import logging
import os
import platform
import sys
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.app.tray import SystemTrayManager
from backend.assistant.speaker_verification import speaker_verifier
from backend.assistant.text_to_speech import tts
from backend.assistant.wakeword import wakeword_listener
from backend.database.sqlite import db
from backend.monitoring.system_monitor import SystemMonitor
from backend.security.authentication import DeviceAuthenticator
from backend.security.permissions import PermissionManager
from backend.service.background_service import background_service
from backend.service.lifecycle import lifecycle, AssistantState
from backend.service.startup import StartupManager

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Configure root logger
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(LOGS_DIR, "assistant.log"), encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("vikram.main")

# Connected WebSocket clients manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.active_connections.discard(connection)


ws_manager = ConnectionManager()
tray_manager = None
event_loop = None


def sync_broadcast(event_type: str, data: Any):
    """Bridge for background threads to broadcast to WebSocket clients."""
    if event_loop and event_loop.is_running():
        payload = {"type": event_type, "data": data}
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(payload), event_loop)


# Connect broadcast callback
background_service.set_broadcast_callback(sync_broadcast)


async def periodic_telemetry_loop():
    """Broadcasts telemetry every 2 seconds to connected HUD clients."""
    while True:
        try:
            if ws_manager.active_connections:
                telemetry = SystemMonitor.get_telemetry()
                await ws_manager.broadcast({
                    "type": "telemetry",
                    "data": telemetry,
                })
        except Exception as e:
            logger.debug(f"Telemetry loop notice: {e}")
        await asyncio.sleep(2.0)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    global event_loop, tray_manager
    event_loop = asyncio.get_running_loop()

    # Silence Windows proactor loop WinError 10054 on disconnects
    def silence_proactor_error(loop, context):
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError) or "10054" in str(context):
            return
        loop.default_exception_handler(context)

    event_loop.set_exception_handler(silence_proactor_error)

    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_c_lost = getattr(_ProactorBasePipeTransport, "_call_connection_lost", None)
        if callable(_orig_c_lost):
            def _safe_c_lost(transport_self: Any, exc: Any) -> None:
                try:
                    _orig_c_lost(transport_self, exc)
                except (ConnectionResetError, OSError):
                    pass
            setattr(_ProactorBasePipeTransport, "_call_connection_lost", _safe_c_lost)
    except Exception:
        pass

    # Start background service
    background_service.start()

    # Automatically ensure DOOM AI is permanently registered in Windows Startup
    try:
        from backend.service.startup import StartupManager
        StartupManager.set_startup(True)
    except Exception as ex:
        logger.debug(f"Windows startup registration notice: {ex}")

    # Start Windows System Tray
    try:
        tray_manager = SystemTrayManager(
            on_open_gui=lambda: None,
            on_pause_listening=lambda: background_service.pause_listening(),
            on_resume_listening=lambda: background_service.resume_listening(),
            on_stop_assistant=lambda: background_service.stop(),
            on_restart_assistant=lambda: background_service.start(),
            on_exit_app=lambda: os._exit(0),
        )
        tray_manager.start()
    except (RuntimeError, OSError) as e:
        logger.warning(f"System tray initialization warning: {e}")

    # Start physical shortcut controller (Alt+Up to activate, Alt+Down to deactivate)
    try:
        from backend.assistant.shortcut_controller import shortcut_controller
        shortcut_controller.start(blocking=False)
    except Exception as e:
        logger.warning(f"Physical shortcut controller initialization warning: {e}")

    # Launch telemetry periodic task
    telemetry_task = asyncio.create_task(periodic_telemetry_loop())

    logger.info("DOOM AI server initialized.")
    try:
        yield
    finally:
        telemetry_task.cancel()
        try:
            from backend.assistant.shortcut_controller import shortcut_controller
            shortcut_controller.stop()
        except Exception:
            pass
        if tray_manager:
            tray_manager.stop()
        background_service.stop()


app = FastAPI(title="DOOM AI Assistant", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST API Endpoints
@app.get("/api/status")
async def get_status():
    pairing = DeviceAuthenticator.get_pairing_info()
    return {
        "state": lifecycle.state,
        "is_paired": bool(pairing and pairing.get("is_paired")),
        "pairing": pairing,
        "voice_enrolled": speaker_verifier.is_enrolled(),
        "network_online": SystemMonitor.is_network_online(),
        "command_count": db.get_command_count(),
    }


@app.get("/api/setup/detect")
async def setup_detect():
    hw = DeviceAuthenticator.get_system_hardware_info()
    telemetry = SystemMonitor.get_telemetry()
    cores = telemetry["cpu"]["cores"]
    proc = platform.processor() or "x86_64"
    disk_total = telemetry["storage"]["total_gb"]
    disk_free = telemetry["storage"]["free_gb"]
    return {
        "computer_name": hw["computer_name"],
        "os": hw["os"],
        "cpu": f"{cores} Cores ({proc})",
        "ram": f"{telemetry['ram']['total_gb']} GB Total",
        "gpu": telemetry["gpu"]["name"],
        "storage": f"{disk_total} GB Total ({disk_free} GB Free)",
        "microphone": "Default Windows Audio Input (Active)",
        "speakers": "Default Windows Audio Output (Active)",
        "network": telemetry["network"]["status"],
    }


@app.post("/api/setup/pair")
async def setup_pair(request: Request):
    body = await request.json() if request.headers.get("content-length") else {}
    custom_name = body.get("device_name")
    result = DeviceAuthenticator.pair_current_device(custom_name)
    return result


@app.get("/api/setup/permissions")
async def get_permissions():
    return PermissionManager.list_permissions()


@app.post("/api/setup/permissions")
async def update_permission(request: Request):
    body = await request.json()
    name = body.get("name")
    granted = body.get("granted", True)
    success = PermissionManager.set_permission(name, granted)
    return {"success": success}


@app.post("/api/setup/permissions/grant-all")
async def grant_all_permissions():
    PermissionManager.grant_all()
    return {"success": True}


@app.post("/api/setup/voice-sample")
async def submit_voice_sample(request: Request):
    body = await request.json()
    audio_data = body.get("audio_data")
    result = speaker_verifier.add_enrollment_sample(
        audio_data or [0.2, 0.4, 0.6, 0.3]
    )
    return result


@app.post("/api/setup/complete")
async def complete_setup():
    tts.speak("At your service, Master.")
    return {"success": True, "message": "VIKRAM IS READY"}


@app.get("/api/command")
@app.post("/api/command")
async def execute_command_api(request: Request):
    if request.method == "GET":
        text = request.query_params.get("cmd") or request.query_params.get("command") or ""
        is_voice = request.query_params.get("is_voice", "false").lower() == "true"
    else:
        body = await request.json() if request.headers.get("content-length") else {}
        text = body.get("command", "")
        is_voice = body.get("is_voice", False)
    result = background_service.handle_command(text, is_voice=is_voice)
    return result


@app.get("/api/assistant/activate")
@app.post("/api/assistant/activate")
async def activate_assistant_api():
    """Activates DOOM AI: resumes listening, sets state ONLINE, announces readiness, and focuses window."""
    background_service.resume_listening()
    lifecycle.set_state(AssistantState.ONLINE)
    background_service.broadcast("state_change", {"state": AssistantState.ONLINE.value})
    tts.resume()
    tts.speak("DOOM AI is active, Master.", priority=True)

    # Bring existing GUI / HUD window to foreground asynchronously in background
    def _focus_hud():
        try:
            from backend.automation.action_engine import action_engine
            hwnds = action_engine.find_windows_by_title_or_process(
                "DOOM", ["msedge.exe", "chrome.exe", "firefox.exe", "opera.exe", "brave.exe"]
            )
            if hwnds:
                action_engine.set_foreground(hwnds[0])
            else:
                import webbrowser
                webbrowser.open("http://127.0.0.1:8765")
        except Exception as ex:
            logger.debug(f"Window focus notice on activation: {ex}")
            try:
                import webbrowser
                webbrowser.open("http://127.0.0.1:8765")
            except Exception:
                pass

    threading.Thread(target=_focus_hud, daemon=True, name="DoomActivateHudFocus").start()

    return {"status": "ACTIVE", "state": lifecycle.state, "message": "DOOM AI is active and listening"}


@app.get("/api/assistant/deactivate")
@app.post("/api/assistant/deactivate")
async def deactivate_assistant_api():
    """Deactivates DOOM AI: pauses listening, halts active TTS and automation, sets state PAUSED."""
    background_service.pause_listening()
    tts.interrupt()
    try:
        from backend.security.confirmation import confirmation_gate
        confirmation_gate.resolve("no")
    except Exception:
        pass
    lifecycle.set_state(AssistantState.PAUSED)
    background_service.broadcast("state_change", {"state": "PAUSED"})
    tts.speak("DOOM AI deactivated, Master.", priority=True)
    return {"status": "DEACTIVATED", "state": lifecycle.state, "message": "DOOM AI is deactivated"}


@app.get("/api/service/restart")
@app.post("/api/service/restart")
async def restart_service_api():
    background_service.stop()
    await asyncio.sleep(0.5)
    background_service.start()
    return {"success": True, "message": "DOOM AI Background Service restarted"}


@app.get("/api/system/restart")
@app.post("/api/system/restart")
async def restart_system_server():
    """Restarts the DOOM AI uvicorn server with the latest code."""
    import sys, subprocess, threading
    logger.info("Restarting DOOM AI server with updated codebase...")
    py_exe = sys.executable
    cmd = [py_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8765"]
    flags = 0x00000008 if os.name == "nt" else 0
    subprocess.Popen(cmd, cwd=PROJECT_ROOT, creationflags=flags)
    threading.Timer(0.6, lambda: os._exit(0)).start()
    return {"status": "RESTARTING", "message": "DOOM AI server restarting with latest code..."}


@app.get("/api/chat/mute")
@app.post("/api/chat/mute")
async def handle_chat_mute_api(request: Request):
    from backend.ai.chat_engine import chat_engine
    if request.method == "POST":
        body = await request.json() if request.headers.get("content-length") else {}
        muted = body.get("muted", not chat_engine.is_chat_muted)
        chat_engine.is_chat_muted = bool(muted)
        if chat_engine.is_chat_muted:
            tts.interrupt()
    return {"success": True, "chat_muted": chat_engine.is_chat_muted}


@app.get("/api/history")
async def get_history(limit: int | None = None):
    return db.get_command_history(limit=limit)


@app.get("/api/history/count")
async def get_history_count():
    return {"count": db.get_command_count()}


@app.delete("/api/history")
async def clear_history():
    db.clear_command_history()
    await ws_manager.broadcast({
        "type": "command_count",
        "data": {"count": 0}
    })
    return {"success": True}


@app.get("/api/settings")
async def get_settings():
    return db.get_all_settings()


@app.post("/api/settings")
async def update_settings(request: Request):
    body = await request.json()
    for k, v in body.items():
        db.set_setting(k, str(v))
        if k == "start_with_windows":
            StartupManager.set_startup_enabled(str(v) == "1")
    return {"success": True}


@app.get("/api/telemetry")
async def get_telemetry():
    return SystemMonitor.get_telemetry()


# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Send initial state immediately
    await websocket.send_json({
        "type": "init",
        "data": {
            "state": lifecycle.state,
            "pairing": DeviceAuthenticator.get_pairing_info(),
            "telemetry": SystemMonitor.get_telemetry(),
            "command_count": db.get_command_count(),
        },
    })
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                mtype = msg.get("type")
                mdata = msg.get("data", {})

                if mtype == "ping":
                    await websocket.send_json({"type": "pong"})

                elif mtype == "speech_input":
                    text = mdata.get("text", "")
                    audio_features = mdata.get("audio_features")
                    wakeword_listener.process_speech_input(text, audio_features, allow_direct=True)

                elif mtype == "command":
                    cmd_text = mdata.get("command", "")
                    background_service.handle_command(cmd_text, is_voice=False)

                elif mtype == "audio_level":
                    await ws_manager.broadcast({
                        "type": "audio_level",
                        "data": mdata.get("level", 0.0),
                    })

                elif mtype == "set_chat_mute":
                    muted = bool(mdata.get("muted", False))
                    from backend.ai.chat_engine import chat_engine
                    chat_engine.is_chat_muted = muted
                    if muted:
                        tts.interrupt()
                    logger.info(f"AI Chat mute set to: {muted}")

                elif mtype == "stop_tts":
                    tts.interrupt()
                    logger.info("TTS interrupted by client request.")

            except (json.JSONDecodeError, KeyError, ValueError, RuntimeError) as e:
                logger.error(f"WebSocket message handling error: {e}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# Mount Frontend static files
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    app.mount("/css", StaticFiles(directory=css_dir), name="css")
    app.mount("/js", StaticFiles(directory=js_dir), name="js")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return HTMLResponse("<h1>VIKRAM AI - Interface initializing...</h1>")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8765, log_level="info")

