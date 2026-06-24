> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fish.audio/llms.txt
> Use this file to discover all available pages before exploring further.

# Utils

<a id="fishaudio.utils.play" />

# fishaudio.utils.play

Audio playback utility.

<a id="fishaudio.utils.play.play" />

#### play

```python theme={null}
def play(audio: Union[bytes, Iterable[bytes]],
         *,
         notebook: bool = False,
         use_ffmpeg: bool = True) -> None
```

Play audio using various playback methods.

**Arguments**:

* `audio` - Audio bytes or iterable of bytes
* `notebook` - Use Jupyter notebook playback (IPython.display.Audio)
* `use_ffmpeg` - Use ffplay for playback (default, falls back to sounddevice)

**Raises**:

* `DependencyError` - If required playback tool is not installed

**Examples**:

```python theme={null}
from fishaudio import FishAudio, play

client = FishAudio(api_key="...")
audio = client.tts.convert(text="Hello world")

# Play directly
play(audio)

# In Jupyter notebook
play(audio, notebook=True)

# Force sounddevice fallback
play(audio, use_ffmpeg=False)
```

<a id="fishaudio.utils.save" />

# fishaudio.utils.save

Audio saving utility.

<a id="fishaudio.utils.save.save" />

#### save

```python theme={null}
def save(audio: Union[bytes, Iterable[bytes]], filename: str) -> None
```

Save audio to a file.

**Arguments**:

* `audio` - Audio bytes or iterable of bytes
* `filename` - Path to save the audio file

**Examples**:

```python theme={null}
from fishaudio import FishAudio, save

client = FishAudio(api_key="...")
audio = client.tts.convert(text="Hello world")

# Save to file
save(audio, "output.mp3")

# Works with iterators too
audio_stream = client.tts.convert(text="Another example")
save(audio_stream, "another.mp3")
```

<a id="fishaudio.utils.stream" />

# fishaudio.utils.stream

Audio streaming utility.

<a id="fishaudio.utils.stream.stream" />

#### stream

```python theme={null}
def stream(audio_stream: Iterator[bytes]) -> bytes
```

Stream audio in real-time while playing it with mpv.

This function plays the audio as it's being generated and
simultaneously captures it to return the complete audio buffer.

**Arguments**:

* `audio_stream` - Iterator of audio byte chunks

**Returns**:

Complete audio bytes after streaming finishes

**Raises**:

* `DependencyError` - If mpv is not installed

**Examples**:

```python theme={null}
from fishaudio import FishAudio, stream

client = FishAudio(api_key="...")
audio_stream = client.tts.convert(text="Hello world")

# Stream and play in real-time, get complete audio
complete_audio = stream(audio_stream)

# Save the captured audio
with open("output.mp3", "wb") as f:
    f.write(complete_audio)
```
