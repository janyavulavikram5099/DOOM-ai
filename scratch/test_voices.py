import win32com.client

def list_sapi_voices():
    try:
        sp = win32com.client.Dispatch("SAPI.SpVoice")
        print("Installed SAPI Voices:")
        for idx, v in enumerate(sp.GetVoices()):
            desc = v.GetDescription()
            print(f"  [{idx}] {desc}")
    except Exception as e:
        print(f"Error listing SAPI voices: {e}")

if __name__ == "__main__":
    list_sapi_voices()
