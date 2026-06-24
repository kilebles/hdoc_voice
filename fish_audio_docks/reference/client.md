> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fish.audio/llms.txt
> Use this file to discover all available pages before exploring further.

# Client

<a id="fishaudio.client" />

# fishaudio.client

Main Fish Audio client classes.

<a id="fishaudio.client.FishAudio" />

## FishAudio Objects

```python theme={null}
class FishAudio()
```

Synchronous Fish Audio API client.

**Example**:

```python theme={null}
from fishaudio import FishAudio

client = FishAudio(api_key="your_api_key")

# Generate speech
audio = client.tts.convert(text="Hello world")
with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

# List voices
voices = client.voices.list(page_size=20)
print(f"Found {voices.total} voices")
```

<a id="fishaudio.client.FishAudio.__init__" />

#### \_\_init\_\_

```python theme={null}
def __init__(*,
             api_key: Optional[str] = None,
             base_url: str = "https://api.fish.audio",
             timeout: float = 240.0,
             httpx_client: Optional[httpx.Client] = None)
```

Initialize Fish Audio client.

**Arguments**:

* `api_key` - API key (can also use FISH\_API\_KEY env var)
* `base_url` - API base URL
* `timeout` - Request timeout in seconds
* `httpx_client` - Optional custom HTTP client

<a id="fishaudio.client.FishAudio.tts" />

#### tts

```python theme={null}
@property
def tts() -> TTSClient
```

Access TTS (text-to-speech) operations.

<a id="fishaudio.client.FishAudio.asr" />

#### asr

```python theme={null}
@property
def asr() -> ASRClient
```

Access ASR (speech-to-text) operations.

<a id="fishaudio.client.FishAudio.voices" />

#### voices

```python theme={null}
@property
def voices() -> VoicesClient
```

Access voice management operations.

<a id="fishaudio.client.FishAudio.account" />

#### account

```python theme={null}
@property
def account() -> AccountClient
```

Access account/billing operations.

<a id="fishaudio.client.FishAudio.close" />

#### close

```python theme={null}
def close() -> None
```

Close the HTTP client.

<a id="fishaudio.client.AsyncFishAudio" />

## AsyncFishAudio Objects

```python theme={null}
class AsyncFishAudio()
```

Asynchronous Fish Audio API client.

**Example**:

```python theme={null}
from fishaudio import AsyncFishAudio

async def main():
    client = AsyncFishAudio(api_key="your_api_key")

    # Generate speech
    audio = client.tts.convert(text="Hello world")
    async with aiofiles.open("output.mp3", "wb") as f:
        async for chunk in audio:
            await f.write(chunk)

    # List voices
    voices = await client.voices.list(page_size=20)
    print(f"Found {voices.total} voices")

asyncio.run(main())
```

<a id="fishaudio.client.AsyncFishAudio.__init__" />

#### \_\_init\_\_

```python theme={null}
def __init__(*,
             api_key: Optional[str] = None,
             base_url: str = "https://api.fish.audio",
             timeout: float = 240.0,
             httpx_client: Optional[httpx.AsyncClient] = None)
```

Initialize async Fish Audio client.

**Arguments**:

* `api_key` - API key (can also use FISH\_API\_KEY env var)
* `base_url` - API base URL
* `timeout` - Request timeout in seconds
* `httpx_client` - Optional custom async HTTP client

<a id="fishaudio.client.AsyncFishAudio.tts" />

#### tts

```python theme={null}
@property
def tts() -> AsyncTTSClient
```

Access TTS (text-to-speech) operations.

<a id="fishaudio.client.AsyncFishAudio.asr" />

#### asr

```python theme={null}
@property
def asr() -> AsyncASRClient
```

Access ASR (speech-to-text) operations.

<a id="fishaudio.client.AsyncFishAudio.voices" />

#### voices

```python theme={null}
@property
def voices() -> AsyncVoicesClient
```

Access voice management operations.

<a id="fishaudio.client.AsyncFishAudio.account" />

#### account

```python theme={null}
@property
def account() -> AsyncAccountClient
```

Access account/billing operations.

<a id="fishaudio.client.AsyncFishAudio.close" />

#### close

```python theme={null}
async def close() -> None
```

Close the HTTP client.
