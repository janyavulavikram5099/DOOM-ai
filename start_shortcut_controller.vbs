Set fso = CreateObject("Scripting.FileSystemObject")
strScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strScriptDir

REM Check virtual environment
strPyExe = "python.exe"
If fso.FileExists(strScriptDir & "\.venv\Scripts\python.exe") Then
    strPyExe = strScriptDir & "\.venv\Scripts\python.exe"
End If

strCmd = chr(34) & strPyExe & chr(34) & " -m backend.assistant.shortcut_controller"
WshShell.Run strCmd, 0, False

Set WshShell = Nothing
Set fso = Nothing
