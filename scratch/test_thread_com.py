import threading
import time
import pythoncom
import win32com.client

def worker():
    pythoncom.CoInitialize()
    sp = win32com.client.Dispatch("SAPI.SpVoice")
    sp.Rate = -1
    sp.Volume = 100
    t0 = time.time()
    # Flag 0 is synchronous, flag 1 is SVSFlagsAsync
    sp.Speak("Instant voice ready.", 0)
    print("SPOKEN IN:", round(time.time() - t0, 3), "s")
    pythoncom.CoUninitialize()

t = threading.Thread(target=worker)
t.start()
t.join()
print("THREAD COM TEST COMPLETE")
