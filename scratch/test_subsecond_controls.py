import time
from backend.ai.intent_parser import IntentParser
from backend.execution.action_executor import ActionDispatcher

test_commands = [
    'percentage of chraging',
    'percentage of charging',
    'charging percentage',
    'how much charging',
    'volume up',
    'volume down',
    'mute',
    'what is the time',
    'what is today date',
]

print("=" * 60)
print("VIKRAM / DOOM AI - LATENCY & COMMAND BENCHMARK")
print("=" * 60)

for cmd in test_commands:
    t0 = time.time()
    parsed = IntentParser.parse(cmd)
    t_parsed = time.time()
    res = ActionDispatcher.execute(parsed)
    t_executed = time.time()
    
    parse_ms = (t_parsed - t0) * 1000
    exec_ms = (t_executed - t_parsed) * 1000
    total_ms = (t_executed - t0) * 1000
    
    status = res.get("status")
    voice = res.get("voice_response")
    intent = parsed.get("intent")
    
    print(f"[{cmd}]")
    print(f"  Intent: {intent} | Status: {status}")
    print(f"  Parse: {parse_ms:.2f}ms | Exec: {exec_ms:.2f}ms | Total: {total_ms:.2f}ms")
import subprocess
subprocess.Popen(['notepad.exe'])
time.sleep(0.5)

from backend.execution.application_executor import ApplicationExecutor

t0 = time.time()
ok, msg = ApplicationExecutor.close('notepad')
t1 = time.time()
print(f"[close notepad]")
print(f"  Result: ok={ok}, \"{msg}\" | Exec: {(t1-t0)*1000:.2f}ms")
print("=" * 60)
