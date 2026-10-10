import subprocess

ps = """
Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Speech_OneCore\\Voices\\Tokens\\*' | Select-Object -Property PSChildName, @{n='Name';e={$_.Name}}, @{n='Gender';e={$_.Gender}} | Format-Table -AutoSize
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
print(res.stdout)
