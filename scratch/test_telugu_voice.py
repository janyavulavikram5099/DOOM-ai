import asyncio
import inspect
import struct
import uuid
import websockets

async def test_voices():
    voices_to_test = [
        ("en-US-ChristopherNeural", "Hello Master. Deep male voice test.", "en-US", "-4Hz"),
        ("en-US-GuyNeural", "Hello Master. Guy neural male voice test.", "en-US", "-3Hz"),
        ("en-IN-PrabhatNeural", "Hello Master. Prabhat Indian male voice test.", "en-IN", "-3Hz"),
        ("te-IN-MohanNeural", "నమస్కారం మాస్టర్. డూమ్ ఏఐ మీ సేవలో ఉంది.", "te-IN", "-2Hz"),
    ]

    url = (
        "wss://speech.platform.bing.com/consumer/speech/synthesize/readahead/edge/v1"
        "?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
        f"&ConnectionId={uuid.uuid4().hex}"
    )
    headers = {
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "Origin": "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
    }

    sig = inspect.signature(websockets.connect)
    param_name = "additional_headers" if "additional_headers" in sig.parameters else "extra_headers"
    kwargs = {param_name: headers}

    for voice, text, lang, pitch in voices_to_test:
        try:
            print(f"Testing voice: {voice} ({lang})...")
            async with websockets.connect(url, **kwargs) as ws:
                cfg = (
                    "Content-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n"
                    '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"true"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}'
                )
                await ws.send(cfg)

                req_id = uuid.uuid4().hex
                ssml = (
                    f"X-RequestId:{req_id}\r\nContent-Type:application/ssml+xml\r\nPath:ssml\r\n\r\n"
                    f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'>"
                    f"<voice name='{voice}'>"
                    f"<prosody pitch='{pitch}' rate='0%'>"
                    f"{text}"
                    f"</prosody>"
                    f"</voice>"
                    f"</speak>"
                )
                await ws.send(ssml)

                audio_data = bytearray()
                async for msg in ws:
                    if isinstance(msg, bytes):
                        if len(msg) > 2:
                            header_len = struct.unpack(">H", msg[:2])[0]
                            audio_data.extend(msg[2 + header_len:])
                    elif isinstance(msg, str) and "Path:turn.end" in msg:
                        break

                print(f"  Result for {voice}: {len(audio_data)} bytes received!")
                if len(audio_data) > 500:
                    with open(f"logs/tts_cache/test_{voice}.mp3", "wb") as f:
                        f.write(audio_data)
        except Exception as e:
            print(f"  Error testing {voice}: {e}")

if __name__ == "__main__":
    asyncio.run(test_voices())
