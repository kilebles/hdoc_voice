> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fish.audio/llms.txt
> Use this file to discover all available pages before exploring further.

# Text to Speech Stream with Timestamps

> Stream generated speech with timestamp alignment snapshots

<Warning>
  This endpoint returns `text/event-stream`. Each SSE `message` event contains
  one JSON payload with a base64-encoded audio chunk.
</Warning>

<Note>
  Use this endpoint when you need both progressive audio delivery and
  text-to-audio alignment data, such as karaoke-style highlighting, word or
  phrase progress indicators, captions synchronized to generated speech, or
  timeline editing.
</Note>

## How the Stream Works

The response is a Server-Sent Events stream. Every event includes:

| Field                    | Type             | Description                                                                                                                                               |
| ------------------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `audio_base64`           | `string`         | One base64-encoded audio chunk. Concatenate all chunks in arrival order to reconstruct the complete audio.                                                |
| `content`                | `string`         | Text content described by this event's latest alignment snapshot. Long input can be split into multiple content chunks.                                   |
| `alignment`              | `object \| null` | Latest cumulative timestamp snapshot for `chunk_seq`. When present, replace the previous snapshot for that `chunk_seq`; do not append segments.           |
| `chunk_seq`              | `integer`        | Sequence number of the text chunk described by `alignment`. Bucket alignment snapshots by this value.                                                     |
| `chunk_audio_offset_sec` | `number`         | Absolute start time of this text chunk within the full audio, in seconds. Add this to segment-local `start` and `end` values for a global audio timeline. |

`audio_base64` is the transport stream. `alignment` is a metadata snapshot for
`chunk_seq`. They are delivered together in the same SSE event, but the
alignment is not a per-audio-packet delta.

When `latency` is set to `balanced`, long input can be split into several text
chunks. A chunk may produce multiple non-null alignment snapshots as more audio
is rendered. Each newer snapshot supersedes the previous snapshot for the same
`chunk_seq`.

<Tip>
  Store alignments in a map keyed by `chunk_seq`. On every non-null `alignment`,
  replace the stored value for that key. Do not collect every non-null alignment
  as a separate final result.
</Tip>

## Alignment Shape

Each non-null `alignment` contains the current cumulative timing segments for a
single text chunk:

```json theme={null}
{
  "audio_base64": "SUQzBAAAAAAA...",
  "content": "Hello world",
  "chunk_seq": 0,
  "chunk_audio_offset_sec": 0.0,
  "alignment": {
    "audio_duration": 0.86,
    "segments": [
      {
        "text": "Hello",
        "start": 0,
        "end": 0.42
      },
      {
        "text": "world",
        "start": 0.42,
        "end": 0.86
      }
    ]
  }
}
```

`start` and `end` are measured in seconds from the start of that text chunk's
generated audio. Add `chunk_audio_offset_sec` to get timestamps on the complete
audio timeline.

`alignment` can be `null` before the first snapshot is available or when
alignment is unavailable. After a snapshot exists, later audio events may repeat
the latest snapshot so clients can continue using a simple latest-wins update
model.

## Minimal Request

```bash theme={null}
curl --no-buffer --request POST \
  --url https://api.fish.audio/v1/tts/stream/with-timestamp \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --header 'model: s2-pro' \
  --data '{
    "text": "Hello! Welcome to Fish Audio.",
    "reference_id": "model-id",
    "format": "opus",
    "latency": "balanced"
  }'
```

## Parsing the Stream

The stream payload uses standard SSE framing. Parse each `data:` line as JSON,
append every decoded `audio_base64` chunk to your audio buffer, and replace the
latest alignment snapshot for `chunk_seq` whenever `alignment` is non-null.

<Tabs>
  <Tab title="Python">
    ```python theme={null}
    import base64
    import json
    import requests

    response = requests.post(
        "https://api.fish.audio/v1/tts/stream/with-timestamp",
        headers={
            "Authorization": "Bearer <token>",
            "Content-Type": "application/json",
            "model": "s2-pro",
        },
        json={
            "text": "Hello! Welcome to Fish Audio.",
            "reference_id": "model-id",
            "format": "opus",
            "latency": "balanced",
        },
        stream=True,
    )

    audio_chunks = []
    alignment_by_chunk = {}

    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue

        event = json.loads(line.removeprefix("data: "))
        audio_chunks.append(base64.b64decode(event["audio_base64"]))

        if event["alignment"] is not None:
            alignment_by_chunk[event["chunk_seq"]] = {
                "content": event["content"],
                "offset": event["chunk_audio_offset_sec"],
                "alignment": event["alignment"],
            }

    audio = b"".join(audio_chunks)
    ```
  </Tab>

  <Tab title="Node.js">
    ```javascript theme={null}
    const response = await fetch(
      "https://api.fish.audio/v1/tts/stream/with-timestamp",
      {
        method: "POST",
        headers: {
          Authorization: "Bearer <token>",
          "Content-Type": "application/json",
          model: "s2-pro",
        },
        body: JSON.stringify({
          text: "Hello! Welcome to Fish Audio.",
          reference_id: "model-id",
          format: "opus",
          latency: "balanced",
        }),
      }
    );

    const audioChunks = [];
    const alignmentByChunk = new Map();
    const decoder = new TextDecoder();
    let buffer = "";

    for await (const chunk of response.body) {
      buffer += decoder.decode(chunk, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const eventText of events) {
        const dataLine = eventText
          .split("\n")
          .find((line) => line.startsWith("data: "));

        if (!dataLine) continue;

        const event = JSON.parse(dataLine.slice(6));
        audioChunks.push(Buffer.from(event.audio_base64, "base64"));

        if (event.alignment !== null) {
          alignmentByChunk.set(event.chunk_seq, {
            content: event.content,
            offset: event.chunk_audio_offset_sec,
            alignment: event.alignment,
          });
        }
      }
    }

    const audio = Buffer.concat(audioChunks);
    ```
  </Tab>
</Tabs>

## Handling Split Content Chunks

Long input can produce multiple text chunks. Treat audio and alignment as two
related streams:

1. Append every decoded `audio_base64` chunk in event order. Do this even when `alignment` is `null`.
2. For non-null `alignment`, replace the stored snapshot for `chunk_seq`.
3. Convert each snapshot's local segment times into global times by adding `chunk_audio_offset_sec`.

<Note>
  `audio_base64` chunks are transport chunks, not sentence or word boundaries.
  Do not try to align each audio chunk individually. Use `alignment.segments`
  plus `chunk_audio_offset_sec` for text timing.
</Note>

For example, if an event has `chunk_audio_offset_sec: 16.24`, add `16.24`
seconds to every segment in that event's `alignment` before rendering it on the
complete audio timeline.

<Tabs>
  <Tab title="Python">
    ```python theme={null}
    def build_global_timeline(alignment_by_chunk):
        timeline = []

        for chunk_seq, item in sorted(alignment_by_chunk.items()):
            offset_seconds = item["offset"]
            alignment = item["alignment"]

            for segment in alignment["segments"]:
                timeline.append({
                    "text": segment["text"],
                    "start": segment["start"] + offset_seconds,
                    "end": segment["end"] + offset_seconds,
                    "chunk_seq": chunk_seq,
                })

        return timeline
    ```
  </Tab>

  <Tab title="Node.js">
    ```javascript theme={null}
    function buildGlobalTimeline(alignmentByChunk) {
      const timeline = [];

      for (const [chunkSeq, item] of [...alignmentByChunk.entries()].sort(
        ([a], [b]) => a - b
      )) {
        for (const segment of item.alignment.segments) {
          timeline.push({
            text: segment.text,
            start: segment.start + item.offset,
            end: segment.end + item.offset,
            chunk_seq: chunkSeq,
          });
        }
      }

      return timeline;
    }
    ```
  </Tab>
</Tabs>

## Format Guidance

For timestamped streaming, we recommend `opus` with the default 48 kHz sample
rate when your client supports it. Opus is designed for streaming and gives the
best balance of quality, latency, and bandwidth for this endpoint.

`wav` and `pcm` avoid lossy codec artifacts and are straightforward to align,
but they produce much larger payloads. Use them when you need uncompressed
audio, direct sample-level processing, or a playback pipeline that already
expects raw audio.

<Warning>
  Use `mp3` only when broad playback compatibility is more important than the
  cleanest streaming boundaries. MP3 encoding uses overlapping audio windows, so
  its encoded chunks may not line up as neatly with timestamp snapshot updates
  as Opus.
</Warning>

This endpoint accepts the same TTS request fields as the [Text to Speech API](/api-reference/endpoint/openapi-v1/text-to-speech), including `reference_id`, `references`, `prosody`, `temperature`, `top_p`, `chunk_length`, `format`, and `latency`.


## OpenAPI

````yaml post /v1/tts/stream/with-timestamp
openapi: 3.1.0
info:
  title: FishAudio OpenAPI
  version: '1'
servers:
  - description: Fish Audio API
    url: https://api.fish.audio
security: []
tags: []
paths:
  /v1/tts/stream/with-timestamp:
    post:
      tags:
        - OpenAPI v1
      summary: Text to Speech Stream with Timestamps
      parameters:
        - in: header
          name: model
          description: Specify which TTS model to use. We recommend `s2-pro`.
          required: true
          schema:
            default: s2-pro
            enum:
              - s1
              - s2-pro
            title: Model
            type: string
          deprecated: false
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TTSStreamWithTimestampRequest'
          application/msgpack:
            schema:
              $ref: '#/components/schemas/TTSStreamWithTimestampRequest'
      responses:
        '200':
          description: >-
            Server-Sent Events stream. Each `message` event contains a JSON
            payload with one base64 audio chunk. Concatenate every
            `audio_base64` chunk in arrival order to reconstruct the complete
            audio. `alignment` is the latest cumulative timestamp snapshot for
            `chunk_seq`; clients should replace the previous snapshot for that
            chunk instead of appending segments. `chunk_audio_offset_sec` can be
            added to segment times to derive absolute timestamps in the full
            audio.
          headers:
            Transfer-Encoding:
              schema:
                type: string
              description: chunked
          content:
            text/event-stream:
              schema:
                description: >-
                  One Server-Sent Events message payload for streaming TTS with
                  timestamps. Each event contains one audio chunk. Concatenate
                  all `audio_base64` chunks in arrival order to reconstruct the
                  complete audio. `alignment` is the latest cumulative timestamp
                  snapshot for the reported `chunk_seq`; clients should replace
                  the previous snapshot for that chunk instead of appending
                  segments.
                examples:
                  - alignment:
                      audio_duration: 16.24
                      segments:
                        - end: 0.16
                          start: 0
                          text: I
                        - end: 0.48
                          start: 0.16
                          text: can't
                        - end: 0.8
                          start: 0.48
                          text: believe
                        - end: 1.12
                          start: 0.8
                          text: its
                        - end: 1.44
                          start: 1.2
                          text: been
                        - end: 1.76
                          start: 1.44
                          text: this
                        - end: 2.48
                          start: 1.76
                          text: long
                        - end: 2.64
                          start: 2.56
                          text: It
                        - end: 3.04
                          start: 2.72
                          text: feels
                        - end: 3.28
                          start: 3.12
                          text: like
                        - end: 4
                          start: 3.36
                          text: forever
                        - end: 4.32
                          start: 4
                          text: since
                        - end: 4.48
                          start: 4.32
                          text: we
                        - end: 4.96
                          start: 4.48
                          text: last
                        - end: 5.28
                          start: 4.96
                          text: really
                        - end: 5.84
                          start: 5.28
                          text: talked
                        - end: 6.24
                          start: 6
                          text: Ive
                        - end: 6.64
                          start: 6.24
                          text: missed
                        - end: 6.96
                          start: 6.64
                          text: hearing
                        - end: 7.2
                          start: 6.96
                          text: your
                        - end: 7.76
                          start: 7.2
                          text: voice
                        - end: 7.92
                          start: 7.76
                          text: your
                        - end: 8.48
                          start: 7.92
                          text: stories
                        - end: 8.72
                          start: 8.48
                          text: even
                        - end: 8.8
                          start: 8.72
                          text: the
                        - end: 9.2
                          start: 8.8
                          text: little
                        - end: 9.52
                          start: 9.2
                          text: things
                        - end: 9.68
                          start: 9.52
                          text: you
                        - end: 10
                          start: 9.68
                          text: used
                        - end: 10.08
                          start: 10
                          text: to
                        - end: 10.64
                          start: 10.08
                          text: say
                        - end: 10.96
                          start: 10.64
                          text: How
                        - end: 11.12
                          start: 10.96
                          text: have
                        - end: 11.36
                          start: 11.12
                          text: you
                        - end: 11.92
                          start: 11.36
                          text: been
                        - end: 12.24
                          start: 12
                          text: Ive
                        - end: 12.48
                          start: 12.24
                          text: thought
                        - end: 12.8
                          start: 12.48
                          text: about
                        - end: 13.2
                          start: 12.8
                          text: calling
                        - end: 13.36
                          start: 13.2
                          text: you
                        - end: 13.68
                          start: 13.36
                          text: so
                        - end: 13.92
                          start: 13.68
                          text: many
                        - end: 14.56
                          start: 13.92
                          text: times
                        - end: 14.72
                          start: 14.56
                          text: but
                        - end: 14.88
                          start: 14.72
                          text: I
                        - end: 15.2
                          start: 14.88
                          text: never
                        - end: 15.36
                          start: 15.2
                          text: knew
                        - end: 15.6
                          start: 15.36
                          text: where
                        - end: 15.6
                          start: 15.6
                          text: to
                        - end: 16.24
                          start: 15.68
                          text: start
                    audio_base64: SUQzBAAAAAAA...
                    chunk_audio_offset_sec: 0
                    chunk_seq: 0
                    content: >-
                      I can’t believe it’s been this long. It feels like forever
                      since we last really talked. I’ve missed hearing your
                      voice, your stories, even the little things you used to
                      say. How have you been? I’ve thought about calling you so
                      many times, but I never knew where to start.
                  - alignment:
                      audio_duration: 16.24
                      segments:
                        - end: 0.16
                          start: 0
                          text: I
                        - end: 0.48
                          start: 0.16
                          text: can't
                        - end: 0.8
                          start: 0.48
                          text: believe
                        - end: 1.12
                          start: 0.8
                          text: its
                        - end: 1.44
                          start: 1.2
                          text: been
                        - end: 1.76
                          start: 1.44
                          text: this
                        - end: 2.48
                          start: 1.76
                          text: long
                        - end: 2.64
                          start: 2.56
                          text: It
                        - end: 3.04
                          start: 2.72
                          text: feels
                        - end: 3.28
                          start: 3.12
                          text: like
                        - end: 4
                          start: 3.36
                          text: forever
                        - end: 4.32
                          start: 4
                          text: since
                        - end: 4.48
                          start: 4.32
                          text: we
                        - end: 4.96
                          start: 4.48
                          text: last
                        - end: 5.28
                          start: 4.96
                          text: really
                        - end: 5.84
                          start: 5.28
                          text: talked
                        - end: 6.24
                          start: 6
                          text: Ive
                        - end: 6.64
                          start: 6.24
                          text: missed
                        - end: 6.96
                          start: 6.64
                          text: hearing
                        - end: 7.2
                          start: 6.96
                          text: your
                        - end: 7.76
                          start: 7.2
                          text: voice
                        - end: 7.92
                          start: 7.76
                          text: your
                        - end: 8.48
                          start: 7.92
                          text: stories
                        - end: 8.72
                          start: 8.48
                          text: even
                        - end: 8.8
                          start: 8.72
                          text: the
                        - end: 9.2
                          start: 8.8
                          text: little
                        - end: 9.52
                          start: 9.2
                          text: things
                        - end: 9.68
                          start: 9.52
                          text: you
                        - end: 10
                          start: 9.68
                          text: used
                        - end: 10.08
                          start: 10
                          text: to
                        - end: 10.64
                          start: 10.08
                          text: say
                        - end: 10.96
                          start: 10.64
                          text: How
                        - end: 11.12
                          start: 10.96
                          text: have
                        - end: 11.36
                          start: 11.12
                          text: you
                        - end: 11.92
                          start: 11.36
                          text: been
                        - end: 12.24
                          start: 12
                          text: Ive
                        - end: 12.48
                          start: 12.24
                          text: thought
                        - end: 12.8
                          start: 12.48
                          text: about
                        - end: 13.2
                          start: 12.8
                          text: calling
                        - end: 13.36
                          start: 13.2
                          text: you
                        - end: 13.68
                          start: 13.36
                          text: so
                        - end: 13.92
                          start: 13.68
                          text: many
                        - end: 14.56
                          start: 13.92
                          text: times
                        - end: 14.72
                          start: 14.56
                          text: but
                        - end: 14.88
                          start: 14.72
                          text: I
                        - end: 15.2
                          start: 14.88
                          text: never
                        - end: 15.36
                          start: 15.2
                          text: knew
                        - end: 15.6
                          start: 15.36
                          text: where
                        - end: 15.6
                          start: 15.6
                          text: to
                        - end: 16.24
                          start: 15.68
                          text: start
                    audio_base64: //uSxOAAF...
                    chunk_audio_offset_sec: 0
                    chunk_seq: 0
                    content: >-
                      I can’t believe it’s been this long. It feels like forever
                      since we last really talked. I’ve missed hearing your
                      voice, your stories, even the little things you used to
                      say. How have you been? I’ve thought about calling you so
                      many times, but I never knew where to start.
                  - alignment:
                      audio_duration: 10.48
                      segments:
                        - end: 0.8
                          start: 0.4
                          text: Seeing
                        - end: 0.96
                          start: 0.8
                          text: you
                        - end: 1.44
                          start: 0.96
                          text: again
                        - end: 1.68
                          start: 1.44
                          text: now
                        - end: 2.08
                          start: 1.68
                          text: makes
                        - end: 2.24
                          start: 2.08
                          text: me
                        - end: 2.8
                          start: 2.24
                          text: realize
                        - end: 3.12
                          start: 2.8
                          text: just
                        - end: 3.28
                          start: 3.12
                          text: how
                        - end: 3.6
                          start: 3.28
                          text: much
                        - end: 3.76
                          start: 3.6
                          text: Ive
                        - end: 4.24
                          start: 3.84
                          text: missed
                        - end: 4.56
                          start: 4.24
                          text: you
                        - end: 4.8
                          start: 4.64
                          text: We
                        - end: 5.04
                          start: 4.8
                          text: have
                        - end: 5.36
                          start: 5.04
                          text: so
                        - end: 5.76
                          start: 5.36
                          text: much
                        - end: 5.76
                          start: 5.76
                          text: to
                        - end: 6.16
                          start: 5.76
                          text: catch
                        - end: 6.4
                          start: 6.16
                          text: up
                        - end: 6.72
                          start: 6.4
                          text: 'on'
                        - end: 6.96
                          start: 6.8
                          text: and
                        - end: 7.04
                          start: 6.96
                          text: I
                        - end: 7.36
                          start: 7.04
                          text: dont
                        - end: 7.6
                          start: 7.36
                          text: even
                        - end: 7.84
                          start: 7.6
                          text: know
                        - end: 8.08
                          start: 7.84
                          text: which
                        - end: 8.4
                          start: 8.08
                          text: part
                        - end: 8.48
                          start: 8.4
                          text: of
                        - end: 8.72
                          start: 8.56
                          text: my
                        - end: 8.96
                          start: 8.72
                          text: life
                        - end: 9.12
                          start: 9.12
                          text: to
                        - end: 9.44
                          start: 9.12
                          text: tell
                        - end: 9.6
                          start: 9.44
                          text: you
                        - end: 10
                          start: 9.6
                          text: about
                        - end: 10.48
                          start: 10.08
                          text: first
                    audio_base64: //uSxImAl...
                    chunk_audio_offset_sec: 16.24
                    chunk_seq: 1
                    content: >-
                      Seeing you again now makes me realize just how much I’ve
                      missed you. We have so much to catch up on, and I don’t
                      even know which part of my life to tell you about first.
                properties:
                  audio_base64:
                    description: >-
                      Base64 encoded audio chunk. Concatenate every chunk in
                      event order to reconstruct the full audio.
                    title: Audio Base64
                    type: string
                  content:
                    description: >-
                      Text content described by this event's latest alignment
                      snapshot. Long input may be split into multiple content
                      chunks in one stream.
                    title: Content
                    type: string
                  alignment:
                    anyOf:
                      - $ref: '#/components/schemas/TTSTimestampAlignment'
                      - type: 'null'
                    description: >-
                      Latest cumulative timestamp snapshot for `chunk_seq`. When
                      present, replace the previous alignment for the same
                      `chunk_seq`; do not append segments. Null means no
                      alignment snapshot has been produced yet or alignment is
                      unavailable.
                  chunk_seq:
                    description: >-
                      Sequence number of the text chunk described by
                      `alignment`. Clients should bucket alignment snapshots by
                      this value.
                    minimum: 0
                    title: Chunk Seq
                    type: integer
                  chunk_audio_offset_sec:
                    description: >-
                      Absolute start time of this text chunk within the full
                      audio, in seconds.
                    minimum: 0
                    title: Chunk Audio Offset Sec
                    type: number
                required:
                  - audio_base64
                  - content
                  - alignment
                  - chunk_seq
                  - chunk_audio_offset_sec
                title: TTSTimestampStreamEvent
                type: object
              examples:
                first_event:
                  summary: First text chunk event with alignment
                  value: >+
                    data: {"audio_base64": "SUQzBAAAAAAA...", "content": "I
                    can’t believe it’s been this long. It feels like forever
                    since we last really talked. I’ve missed hearing your voice,
                    your stories, even the little things you used to say. How
                    have you been? I’ve thought about calling you so many times,
                    but I never knew where to start.", "alignment": {"segments":
                    [{"text": "I", "start": 0.0, "end": 0.16}, {"text": "can't",
                    "start": 0.16, "end": 0.48}, {"text": "believe", "start":
                    0.48, "end": 0.8}, {"text": "its", "start": 0.8, "end":
                    1.12}, {"text": "been", "start": 1.2, "end": 1.44}, {"text":
                    "this", "start": 1.44, "end": 1.76}, {"text": "long",
                    "start": 1.76, "end": 2.48}, {"text": "It", "start": 2.56,
                    "end": 2.64}, {"text": "feels", "start": 2.72, "end": 3.04},
                    {"text": "like", "start": 3.12, "end": 3.28}, {"text":
                    "forever", "start": 3.36, "end": 4.0}, {"text": "since",
                    "start": 4.0, "end": 4.32}, {"text": "we", "start": 4.32,
                    "end": 4.48}, {"text": "last", "start": 4.48, "end": 4.96},
                    {"text": "really", "start": 4.96, "end": 5.28}, {"text":
                    "talked", "start": 5.28, "end": 5.84}, {"text": "Ive",
                    "start": 6.0, "end": 6.24}, {"text": "missed", "start":
                    6.24, "end": 6.64}, {"text": "hearing", "start": 6.64,
                    "end": 6.96}, {"text": "your", "start": 6.96, "end": 7.2},
                    {"text": "voice", "start": 7.2, "end": 7.76}, {"text":
                    "your", "start": 7.76, "end": 7.92}, {"text": "stories",
                    "start": 7.92, "end": 8.48}, {"text": "even", "start": 8.48,
                    "end": 8.72}, {"text": "the", "start": 8.72, "end": 8.8},
                    {"text": "little", "start": 8.8, "end": 9.2}, {"text":
                    "things", "start": 9.2, "end": 9.52}, {"text": "you",
                    "start": 9.52, "end": 9.68}, {"text": "used", "start": 9.68,
                    "end": 10.0}, {"text": "to", "start": 10.0, "end": 10.08},
                    {"text": "say", "start": 10.08, "end": 10.64}, {"text":
                    "How", "start": 10.64, "end": 10.96}, {"text": "have",
                    "start": 10.96, "end": 11.12}, {"text": "you", "start":
                    11.12, "end": 11.36}, {"text": "been", "start": 11.36,
                    "end": 11.92}, {"text": "Ive", "start": 12.0, "end": 12.24},
                    {"text": "thought", "start": 12.24, "end": 12.48}, {"text":
                    "about", "start": 12.48, "end": 12.8}, {"text": "calling",
                    "start": 12.8, "end": 13.2}, {"text": "you", "start": 13.2,
                    "end": 13.36}, {"text": "so", "start": 13.36, "end": 13.68},
                    {"text": "many", "start": 13.68, "end": 13.92}, {"text":
                    "times", "start": 13.92, "end": 14.56}, {"text": "but",
                    "start": 14.56, "end": 14.72}, {"text": "I", "start": 14.72,
                    "end": 14.88}, {"text": "never", "start": 14.88, "end":
                    15.2}, {"text": "knew", "start": 15.2, "end": 15.36},
                    {"text": "where", "start": 15.36, "end": 15.6}, {"text":
                    "to", "start": 15.6, "end": 15.6}, {"text": "start",
                    "start": 15.68, "end": 16.24}], "audio_duration": 16.24},
                    "chunk_seq": 0, "chunk_audio_offset_sec": 0.0}

                following_event:
                  summary: Following audio event with latest alignment snapshot
                  value: >+
                    data: {"audio_base64": "//uSxOAAF...", "content": "I can’t
                    believe it’s been this long. It feels like forever since we
                    last really talked. I’ve missed hearing your voice, your
                    stories, even the little things you used to say. How have
                    you been? I’ve thought about calling you so many times, but
                    I never knew where to start.", "alignment": {"segments":
                    [{"text": "I", "start": 0.0, "end": 0.16}, {"text": "can't",
                    "start": 0.16, "end": 0.48}, {"text": "believe", "start":
                    0.48, "end": 0.8}, {"text": "its", "start": 0.8, "end":
                    1.12}, {"text": "been", "start": 1.2, "end": 1.44}, {"text":
                    "this", "start": 1.44, "end": 1.76}, {"text": "long",
                    "start": 1.76, "end": 2.48}, {"text": "It", "start": 2.56,
                    "end": 2.64}, {"text": "feels", "start": 2.72, "end": 3.04},
                    {"text": "like", "start": 3.12, "end": 3.28}, {"text":
                    "forever", "start": 3.36, "end": 4.0}, {"text": "since",
                    "start": 4.0, "end": 4.32}, {"text": "we", "start": 4.32,
                    "end": 4.48}, {"text": "last", "start": 4.48, "end": 4.96},
                    {"text": "really", "start": 4.96, "end": 5.28}, {"text":
                    "talked", "start": 5.28, "end": 5.84}, {"text": "Ive",
                    "start": 6.0, "end": 6.24}, {"text": "missed", "start":
                    6.24, "end": 6.64}, {"text": "hearing", "start": 6.64,
                    "end": 6.96}, {"text": "your", "start": 6.96, "end": 7.2},
                    {"text": "voice", "start": 7.2, "end": 7.76}, {"text":
                    "your", "start": 7.76, "end": 7.92}, {"text": "stories",
                    "start": 7.92, "end": 8.48}, {"text": "even", "start": 8.48,
                    "end": 8.72}, {"text": "the", "start": 8.72, "end": 8.8},
                    {"text": "little", "start": 8.8, "end": 9.2}, {"text":
                    "things", "start": 9.2, "end": 9.52}, {"text": "you",
                    "start": 9.52, "end": 9.68}, {"text": "used", "start": 9.68,
                    "end": 10.0}, {"text": "to", "start": 10.0, "end": 10.08},
                    {"text": "say", "start": 10.08, "end": 10.64}, {"text":
                    "How", "start": 10.64, "end": 10.96}, {"text": "have",
                    "start": 10.96, "end": 11.12}, {"text": "you", "start":
                    11.12, "end": 11.36}, {"text": "been", "start": 11.36,
                    "end": 11.92}, {"text": "Ive", "start": 12.0, "end": 12.24},
                    {"text": "thought", "start": 12.24, "end": 12.48}, {"text":
                    "about", "start": 12.48, "end": 12.8}, {"text": "calling",
                    "start": 12.8, "end": 13.2}, {"text": "you", "start": 13.2,
                    "end": 13.36}, {"text": "so", "start": 13.36, "end": 13.68},
                    {"text": "many", "start": 13.68, "end": 13.92}, {"text":
                    "times", "start": 13.92, "end": 14.56}, {"text": "but",
                    "start": 14.56, "end": 14.72}, {"text": "I", "start": 14.72,
                    "end": 14.88}, {"text": "never", "start": 14.88, "end":
                    15.2}, {"text": "knew", "start": 15.2, "end": 15.36},
                    {"text": "where", "start": 15.36, "end": 15.6}, {"text":
                    "to", "start": 15.6, "end": 15.6}, {"text": "start",
                    "start": 15.68, "end": 16.24}], "audio_duration": 16.24},
                    "chunk_seq": 0, "chunk_audio_offset_sec": 0.0}

                later_text_chunk_event:
                  summary: Later text chunk event with another alignment
                  value: >+
                    data: {"audio_base64": "//uSxImAl...", "content": "Seeing
                    you again now makes me realize just how much I’ve missed
                    you. We have so much to catch up on, and I don’t even know
                    which part of my life to tell you about first.",
                    "alignment": {"segments": [{"text": "Seeing", "start": 0.4,
                    "end": 0.8}, {"text": "you", "start": 0.8, "end": 0.96},
                    {"text": "again", "start": 0.96, "end": 1.44}, {"text":
                    "now", "start": 1.44, "end": 1.68}, {"text": "makes",
                    "start": 1.68, "end": 2.08}, {"text": "me", "start": 2.08,
                    "end": 2.24}, {"text": "realize", "start": 2.24, "end":
                    2.8}, {"text": "just", "start": 2.8, "end": 3.12}, {"text":
                    "how", "start": 3.12, "end": 3.28}, {"text": "much",
                    "start": 3.28, "end": 3.6}, {"text": "Ive", "start": 3.6,
                    "end": 3.76}, {"text": "missed", "start": 3.84, "end":
                    4.24}, {"text": "you", "start": 4.24, "end": 4.56}, {"text":
                    "We", "start": 4.64, "end": 4.8}, {"text": "have", "start":
                    4.8, "end": 5.04}, {"text": "so", "start": 5.04, "end":
                    5.36}, {"text": "much", "start": 5.36, "end": 5.76},
                    {"text": "to", "start": 5.76, "end": 5.76}, {"text":
                    "catch", "start": 5.76, "end": 6.16}, {"text": "up",
                    "start": 6.16, "end": 6.4}, {"text": "on", "start": 6.4,
                    "end": 6.72}, {"text": "and", "start": 6.8, "end": 6.96},
                    {"text": "I", "start": 6.96, "end": 7.04}, {"text": "dont",
                    "start": 7.04, "end": 7.36}, {"text": "even", "start": 7.36,
                    "end": 7.6}, {"text": "know", "start": 7.6, "end": 7.84},
                    {"text": "which", "start": 7.84, "end": 8.08}, {"text":
                    "part", "start": 8.08, "end": 8.4}, {"text": "of", "start":
                    8.4, "end": 8.48}, {"text": "my", "start": 8.56, "end":
                    8.72}, {"text": "life", "start": 8.72, "end": 8.96},
                    {"text": "to", "start": 9.12, "end": 9.12}, {"text": "tell",
                    "start": 9.12, "end": 9.44}, {"text": "you", "start": 9.44,
                    "end": 9.6}, {"text": "about", "start": 9.6, "end": 10.0},
                    {"text": "first", "start": 10.08, "end": 10.48}],
                    "audio_duration": 10.48}, "chunk_seq": 1,
                    "chunk_audio_offset_sec": 16.24}

        '401':
          description: No permission -- see authorization schemes
          headers: {}
          content:
            application/json:
              schema:
                properties:
                  status:
                    title: Status
                    type: integer
                  message:
                    title: Message
                    type: string
                required:
                  - status
                  - message
                type: object
        '402':
          description: No payment -- see charging schemes
          headers: {}
          content:
            application/json:
              schema:
                properties:
                  status:
                    title: Status
                    type: integer
                  message:
                    title: Message
                    type: string
                required:
                  - status
                  - message
                type: object
        '422':
          description: ''
          headers: {}
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    loc:
                      title: Location
                      description: error field
                      type: array
                      items:
                        type: string
                    type:
                      title: Type
                      description: error type
                      type: string
                    msg:
                      title: Message
                      description: error message
                      type: string
                    ctx:
                      title: Context
                      description: error context
                      type: string
                    in:
                      title: In
                      type: string
                      enum:
                        - path
                        - query
                        - header
                        - cookie
                        - body
                  required:
                    - loc
                    - type
                    - msg
      security:
        - BearerAuth: []
      x-codeSamples:
        - lang: bash
          label: Stream With Timestamps
          source: |-
            curl --no-buffer --request POST \
              --url https://api.fish.audio/v1/tts/stream/with-timestamp \
              --header 'Authorization: Bearer <token>' \
              --header 'Content-Type: application/json' \
              --header 'model: s2-pro' \
              --data '{
                "text": "[happy] I can’t believe it’s been this long. It feels like forever since we last really talked. I’ve missed hearing your voice, your stories, even the little things you used to say. How have you been? I’ve thought about calling you so many times, but I never knew where to start. Seeing you again now makes me realize just how much I’ve missed you. We have so much to catch up on, and I don’t even know which part of my life to tell you about first.",
                "format": "opus",
                "normalize": true,
                "temperature": 0.9,
                "chunk_length": 100,
                "top_p": 0.9,
                "latency": "balanced",
                "sample_rate": 48000,
                "reference_id": "fbe02f8306fc4d3d915e9871722a39d5"
              }'
components:
  schemas:
    TTSStreamWithTimestampRequest:
      description: >-
        Request body for streaming text-to-speech synthesis with timestamp
        alignment. The request fields match the standard TTS endpoint, but the
        response is delivered as a Server-Sent Events stream. Each SSE payload
        includes an audio chunk and, when available, the latest cumulative
        alignment snapshot for a `chunk_seq`. Clients should concatenate
        `audio_base64` chunks in arrival order and replace the stored alignment
        for each `chunk_seq` whenever a newer snapshot is received.
      properties:
        text:
          description: Text to convert to speech.
          title: Text
          type: string
        temperature:
          default: 0.7
          description: >-
            Controls expressiveness. Higher is more varied, lower is more
            consistent.
          maximum: 1
          minimum: 0
          title: Temperature
          type: number
        top_p:
          default: 0.7
          description: Controls diversity via nucleus sampling.
          maximum: 1
          minimum: 0
          title: Top P
          type: number
        references:
          anyOf:
            - description: 'Single speaker: array of reference audio samples'
              items:
                $ref: '#/components/schemas/ReferenceAudio'
              type: array
            - description: >-
                Multiple speakers: array of arrays, where each inner array
                contains reference samples for one speaker
              items:
                items:
                  $ref: '#/components/schemas/ReferenceAudio'
                type: array
              type: array
            - type: 'null'
          description: >-
            Inline voice references for zero-shot cloning. Requires MessagePack
            (not JSON). For single speaker, provide an array of ReferenceAudio
            objects. For multiple speakers, provide an array of arrays where
            each inner array contains references for one speaker.
            **Multi-speaker is only available with the S2-Pro model.** The
            speaker index corresponds to the index in reference_id array.
            Example for multi-speaker: [[{audio, text}], [{audio, text}, {audio,
            text}]] for 2 speakers where speaker 1 has 2 reference samples.
          title: References
        reference_id:
          anyOf:
            - description: 'Single speaker: voice model ID string'
              type: string
            - description: 'Multiple speakers: array of voice model IDs, one per speaker'
              items:
                type: string
              type: array
            - type: 'null'
          default: null
          description: >-
            Voice model ID(s) from Fish Audio library or your custom models. For
            single-speaker synthesis, provide a string. For multi-speaker
            synthesis (dialogue), provide an array of model IDs. **Multi-speaker
            is only available with the S2-Pro model.** When using multiple
            speakers, use speaker tags in your text like `<|speaker:0|>` and
            `<|speaker:1|>` to indicate speaker changes. Example:
            `<|speaker:0|>Hello!<|speaker:1|>Hi there!<|speaker:0|>How are you?`
            with `reference_id: ["speaker-a-id", "speaker-b-id"]`.
          title: Reference Id
        prosody:
          anyOf:
            - $ref: '#/components/schemas/ProsodyControl'
            - type: 'null'
          default: null
          description: Speed and volume adjustments for the output.
        chunk_length:
          default: 300
          description: Text segment size for processing.
          maximum: 300
          minimum: 100
          title: Chunk Length
          type: integer
        normalize:
          default: true
          description: >-
            Normalizes text for English and Chinese, improving stability for
            numbers.
          title: Normalize
          type: boolean
        format:
          default: mp3
          description: Output audio format.
          enum:
            - wav
            - pcm
            - mp3
            - opus
          title: Format
          type: string
        sample_rate:
          anyOf:
            - type: integer
            - type: 'null'
          default: null
          description: >-
            Audio sample rate in Hz. When null, uses the format's default (44100
            Hz for most formats, 48000 Hz for opus).
          title: Sample Rate
        mp3_bitrate:
          default: 128
          description: MP3 bitrate in kbps. Only applies when format is mp3.
          enum:
            - 64
            - 128
            - 192
          title: Mp3 Bitrate
          type: integer
        opus_bitrate:
          default: -1000
          description: >-
            Opus bitrate in bps. -1000 for automatic. Only applies when format
            is opus.
          enum:
            - -1000
            - 24000
            - 32000
            - 48000
            - 64000
          title: Opus Bitrate
          type: integer
        latency:
          default: normal
          description: >-
            Latency-quality trade-off. normal: best quality, balanced: reduced
            latency, low: lowest latency.
          enum:
            - low
            - normal
            - balanced
          title: Latency
          type: string
        max_new_tokens:
          default: 1024
          description: Maximum audio tokens to generate per text chunk.
          title: Max New Tokens
          type: integer
        repetition_penalty:
          default: 1.2
          description: >-
            Penalty for repeating audio patterns. Values above 1.0 reduce
            repetition.
          title: Repetition Penalty
          type: number
        min_chunk_length:
          default: 50
          description: Minimum characters before splitting into a new chunk.
          maximum: 100
          minimum: 0
          title: Min Chunk Length
          type: integer
        condition_on_previous_chunks:
          default: true
          description: Use previous audio as context for voice consistency.
          title: Condition On Previous Chunks
          type: boolean
        early_stop_threshold:
          default: 1
          description: Early stopping threshold for batch processing.
          maximum: 1
          minimum: 0
          title: Early Stop Threshold
          type: number
      required:
        - text
      title: TTSStreamWithTimestampRequest
      type: object
    TTSTimestampAlignment:
      properties:
        segments:
          description: Ordered text timing segments for the generated audio.
          items:
            $ref: '#/components/schemas/TTSTimestampSegment'
          title: Segments
          type: array
        audio_duration:
          description: Audio duration in seconds for this alignment's content chunk.
          title: Audio Duration
          type: number
      required:
        - segments
        - audio_duration
      title: TTSTimestampAlignment
      type: object
    ReferenceAudio:
      description: >-
        A voice sample with its transcript, used for zero-shot voice cloning.
        The model will attempt to match the voice characteristics from the audio
        sample.
      properties:
        audio:
          description: >-
            Raw audio bytes of the voice sample. Supported formats: WAV, MP3,
            FLAC. For best results, use 10-30 seconds of clear speech with
            minimal background noise.
          format: binary
          title: Audio
          type: string
        text:
          description: >-
            The exact transcript of what is spoken in the audio sample. Accuracy
            is important for voice cloning quality.
          title: Text
          type: string
      required:
        - audio
        - text
      title: ReferenceAudio
      type: object
    ProsodyControl:
      description: >-
        Controls for adjusting the prosody (rhythm and intonation) of generated
        speech.
      properties:
        speed:
          default: 1
          description: >-
            Speaking rate multiplier. Valid range: 0.5 to 2.0. 1.0 = normal
            speed, 0.5 = half speed, 2.0 = double speed. Useful for adjusting
            pacing without regenerating audio.
          title: Speed
          type: number
        volume:
          default: 0
          description: >-
            Volume adjustment in decibels (dB). 0 = no change, positive values =
            louder, negative values = quieter.
          title: Volume
          type: number
        normalize_loudness:
          default: true
          description: >-
            Normalize output loudness for more consistent perceived volume.
            **S2-Pro only.**
          title: Normalize Loudness
          type: boolean
      title: ProsodyControl
      type: object
    TTSTimestampSegment:
      properties:
        text:
          description: Text segment covered by this timing entry.
          title: Text
          type: string
        start:
          description: Segment start time in seconds.
          title: Start
          type: number
        end:
          description: Segment end time in seconds.
          title: End
          type: number
      required:
        - text
        - start
        - end
      title: TTSTimestampSegment
      type: object
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer

````