import os
import subprocess
import time
import psutil

def count_explorer():
    return len([p for p in psutil.process_iter(['name']) if p.info['name'] and 'explorer' in p.info['name'].lower()])

print("Initial explorer count:", count_explorer())

# Test 1: os.startfile(os.environ['USERPROFILE'])
user_dir = os.environ.get('USERPROFILE', 'C:\\')
print(f"Testing os.startfile('{user_dir}')...")
try:
    os.startfile(user_dir)
    print("Success with user_dir!")
except Exception as e:
    print("Failed with user_dir:", e)

time.sleep(2)
print("After user_dir count:", count_explorer())

# Test 2: subprocess.Popen(["explorer.exe", "shell:MyComputerFolder"])
print("Testing subprocess.Popen(['explorer.exe', 'shell:MyComputerFolder'])...")
try:
    p = subprocess.Popen(["explorer.exe", "shell:MyComputerFolder"])
    print("Success with shell:MyComputerFolder, PID:", p.pid)
except Exception as e:
    print("Failed:", e)

time.sleep(2)
print("After shell:MyComputerFolder count:", count_explorer())
