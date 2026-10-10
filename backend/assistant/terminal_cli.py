"""
DOOM AI - Interactive Master CMD Terminal Interface
Allows direct terminal control, conversational queries, and system automation.
Communicates with running server via HTTP /api/command or falls back to in-process execution.
"""

import os
import sys
import time
import requests

# Terminal visual enhancements
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

API_BASE = "http://127.0.0.1:8765"


def init_windows_vt_console():
    """Enables VT100 ANSI escape sequences on Windows console."""
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h_out = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(h_out, mode.value | 0x0004)


def print_banner():
    banner = f"""{CYAN}{BOLD}
=====================================================================
                      D O O M   A I   T E R M I N A L
               Autonomous Windows Desktop System Intelligence
====================================================================={RESET}
{DIM}Mode: Master Interactive Console | Voice & Action Engine Active{RESET}
{DIM}Type your commands (e.g. 'open whatsapp', 'volume up', 'battery status') or 'exit'.{RESET}
"""
    print(banner)


def check_server_online() -> bool:
    try:
        r = requests.get(f"{API_BASE}/api/status", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def execute_via_api(command: str) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}/api/command", json={"command": command, "is_voice": False}, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def execute_in_process(command: str) -> dict:
    try:
        from backend.service.background_service import background_service
        return background_service.handle_command(command, is_voice=False)
    except Exception as ex:
        return {"status": "error", "message": f"Execution error: {ex}"}


def main():
    init_windows_vt_console()
    print_banner()

    is_online = check_server_online()
    if is_online:
        print(f"[{GREEN}ONLINE{RESET}] Connected to DOOM AI background daemon at {API_BASE}\n")
    else:
        print(f"[{YELLOW}LOCAL{RESET}] Background server not detected; using direct in-process engine.\n")

    while True:
        try:
            prompt = f"{GREEN}{BOLD}[DOOM AI]{RESET} {CYAN}Master{RESET} > "
            user_input = input(prompt).strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print(f"\n{YELLOW}Terminating terminal session. DOOM AI remains standing by, Master.{RESET}")
                time.sleep(0.5)
                break

            if user_input.lower() in ("clear", "cls"):
                # pyrefly: ignore [deprecated]
                os.system("cls" if os.name == "nt" else "clear")
                print_banner()
                continue

            print(f"{DIM}Processing: '{user_input}'...{RESET}")

            # Try API first
            res = execute_via_api(user_input)
            if not res:
                # Direct in-process fallback
                res = execute_in_process(user_input)

            if res:
                status = res.get("status", "success")
                speech = res.get("speech") or res.get("message") or ""
                intent = res.get("intent", "COMMAND")

                if status == "error":
                    print(f"{RED}[ERROR]{RESET} {speech or 'Execution failed.'}")
                else:
                    print(f"{GREEN}[OK]{RESET} {BOLD}{speech}{RESET} {DIM}(Intent: {intent}){RESET}")
            else:
                print(f"{YELLOW}[NOTICE]{RESET} Command completed.")

            print()

        except (KeyboardInterrupt, EOFError):
            print(f"\n{YELLOW}Session ended.{RESET}")
            break
        except Exception as e:
            print(f"{RED}[ERROR]{RESET} {e}")


if __name__ == "__main__":
    main()
