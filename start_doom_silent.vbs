Set fso = CreateObject("Scripting.FileSystemObject")
strScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strScriptDir

strPyExe = "python.exe"
If fso.FileExists(strScriptDir & "\.venv\Scripts\python.exe") Then
    strPyExe = strScriptDir & "\.venv\Scripts\python.exe"
End If

REM Check if DOOM AI server is already alive on port 8765
bRunning = False
Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
On Error Resume Next
http.Open "GET", "http://127.0.0.1:8765/api/status", False
http.setTimeouts 500, 500, 500, 500
http.Send
If Err.Number = 0 Then
    If http.Status = 200 Then
        bRunning = True
    End If
End If
On Error GoTo 0
Set http = Nothing

If Not bRunning Then
    REM Start DOOM AI Server directly in the background (silent window style 0)
    strCmd = chr(34) & strPyExe & chr(34) & " -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"
    WshShell.Run strCmd, 0, False
End If

Set WshShell = Nothing
Set fso = Nothing
