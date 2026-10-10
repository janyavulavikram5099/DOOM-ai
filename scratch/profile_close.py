import subprocess, time, cProfile
from backend.execution.application_executor import ApplicationExecutor

subprocess.Popen(['notepad.exe'])
time.sleep(0.5)

pr = cProfile.Profile()
pr.enable()
ok, msg = ApplicationExecutor.close('notepad')
pr.disable()
print(f"Result: {ok}, {msg}")
pr.print_stats(sort='tottime')
