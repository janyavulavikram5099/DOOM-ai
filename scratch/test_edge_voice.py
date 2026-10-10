import asyncio
import inspect
import struct
import uuid
import websockets

async def test_edge():
    voice = "en-US-ChristopherNeural"
    text = "Hello Master. All systems are operational."
    conn_id = uuid.uuid4().hex
    url = (
        "wss://speech.platform.bing.com/consumer/speech/synthesize/readahead/edge/v1"
        "?TrustedClientToken=6A5AA1D4EAFF4E9FB37E23D68491D6F4"
        f"&ConnectionId={conn_id}"
    )
    headers = {
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
        "Origin": "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
    }

    # Inspect websockets.connect parameter name
    sig = inspect.signature(websockets.connect)
    param_name = "additional_headers" if "additional_headers" in sig.parameters else "extra_headers"
    kwargs = {param_name: headers}

    print(f"Connecting to Edge Neural TTS using {param_name}...")
    async with websockets.connect(url, **kwargs) as ws:
        cfg = (
            "Content-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n"
            '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"true"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}'
        )
        await ws.send(cfg)

        req_id = uuid.uuid4().hex
        ssml = (
            f"X-RequestId:{req_id}\r\nContent-Type:application/ssml+xml\r\nPath:ssml\r\n\r\n"
            f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>"
            f"<voice name='{voice}'>"
            f"<prosody pitch='-5Hz' rate='0%'>"
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

        print(f"Successfully received {len(audio_data)} bytes of deep male neural audio!")
        with open("scratch/test_deep_male.mp3", "wb") as f:
            f.write(audio_data)

if __name__ == "__main__":
    asyncio.run(test_edge())
