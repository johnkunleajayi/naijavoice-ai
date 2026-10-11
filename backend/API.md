# Yoruba TTS API foundation

`POST /api/tts` accepts JSON:

```json
{"text": "ẹ káàárọ̀", "language": "yo"}
```

Only `yo` is accepted. Text must be a nonblank string of 1–5000 characters.
Invalid requests return FastAPI validation errors with status `422`.

The service preprocesses Yoruba before either speech engine is called:

- Trim surrounding whitespace and replace uppercase `Ẹ` with `ẹ`, `Ọ` with `ọ`.
- Preserve internal spacing, existing tone marks, and supplied punctuation.
- Append a period unless the final character is `.`, `!`, or `?`.
- Detect Yoruba diacritics using Unicode decomposition for inspection only.
  Acute/grave tones, explicit mid tone, and underdots count as marked input.
- Marked input bypasses diacritization. Detection indicates presence of marks,
  not whether a sentence is fully or correctly diacritized; partially marked
  input is also preserved.
- Unmarked input passes through the injectable `YorubaDiacritizer` interface.
  When `TTS_INFERENCE_URL` is configured, `RemoteYorubaDiacritizer` sends UTF-8
  JSON to `/diacritize` and validates the returned nonblank `text` string.
  Without a remote URL, the local-only fallback remains pass-through.
  There are no word replacements or dictionaries.

`YorubaPreprocessor` applies final normalization after diacritization, so future
service output follows the same character and sentence rules. For example,
`Mo fe ko ede Yoruba daadaa` is restored remotely before punctuation is added;
properly marked `Mo fẹ́ kọ́ èdè Yorùbá dáadáa.` stays unchanged.

Remote diacritization uses the same base URL as TTS, a 5-second connection
timeout and 60-second read inactivity timeout. Network errors, non-200 statuses,
invalid UTF-8/JSON, missing or non-string text, and blank restored text return the
existing clean `503`. TTS is not called after diacritization failure. Redirects
are not followed and requests are not retried. Marked input bypasses this request.

The engine contract returns WAV bytes. With a configured engine, the route
returns `200` with `Content-Type: audio/wav`. Unavailable inference returns `503` with:

```json
{"detail": "Speech generation is not available yet."}
```

## Remote Yoruba inference

`TTS_INFERENCE_URL` selects the remote adapter, taking precedence over local
model settings. The configured `backend/.env` points to:
`https://trustless-episode-blank.ngrok-free.dev`.
The application loads that file at startup; process environment variables take
precedence. Restart the backend after changing the URL (the engine is cached).

The public endpoint stays `POST /api/tts` with `text` and `language: "yo"`.
Normalization happens in the existing service before the remote adapter sends
UTF-8 JSON `{"text": "..."}` to `{TTS_INFERENCE_URL}/tts`. Successful WAV bytes
are returned unchanged with `Content-Type: audio/wav`. No local GPU or F5-TTS
installation is needed for remote mode.

Connection timeout: 5 seconds. Read inactivity timeout: 120 seconds for speech
generation. Write timeout: 10 seconds. Redirects are not followed; requests are
not retried. Timeout, connection errors, non-200 responses, and responses without
a RIFF/WAVE header return the existing sanitized `503` without upstream details.
The adapter includes the ngrok browser-warning bypass header.

If `TTS_INFERENCE_URL` is empty, the existing lazy local F5-TTS adapter remains
available; without configured local files it continues to return `503`.
Tests isolate environment configuration and mock all remote HTTP requests.

## F5-TTS Yoruba adapter

`F5TTSYorubaEngine` implements the engine contract for
[naijaml/f5-tts-yoruba](https://huggingface.co/naijaml/f5-tts-yoruba).
No model, vocoder, inference package, or GPU is needed to start the API or run tests.
No real inference has been attempted or verified on this local computer.

Set these process environment variables on the future inference host:

- `TTS_CHECKPOINT_PATH`: local Yoruba checkpoint (for example `model_150000.pt`).
- `TTS_VOCAB_PATH`: matching local Yoruba vocabulary file.
- `TTS_REFERENCE_AUDIO_PATH`: local reference audio containing exactly the transcript below.
- `TTS_DEVICE`: defaults to `cuda`; explicitly configurable (for example `cpu`).

Reference transcript: `ẹ kú àárọ̀, báwo ni àwọn ọmọ yín ṣe wà?`

`backend/.env.example` documents the variables. The application loads
`backend/.env` without overriding existing process environment variables. Restart the server after changing configuration. Missing or nonexistent
files are rejected before importing F5-TTS and return the existing clean `503`.

Optional runtime dependencies are declared in `requirements-tts.txt` for future
installation on the inference host; they have not been installed here. Provision
the Yoruba model and matching vocabulary separately. F5-TTS's default constructor
also resolves a Vocos vocoder through Hugging Face on first load if not cached;
provision/cache that dependency before running on an offline host.

The adapter patches `f5_tts.model.utils.convert_char_to_pinyin` to return its input
unchanged **before** importing `F5TTS`. Do not import `f5_tts.api` elsewhere before
this initialization. The adapter uses `F5TTS_v1_Base`, `speed=1.0`, and `nfe_step=16`,
and encodes the returned samples as in-memory PCM-16 WAV.

Model imports/loading happen only on the first synthesis request with configured
local files. One engine is cached per process; a lock serializes loading and
inference because F5-TTS holds mutable state. The synchronous API route runs work
in FastAPI's thread pool. Optional-package, device, model-loading, inference, and
encoding failures map to the same sanitized `503`. Tests use fake F5-TTS and
SoundFile modules and never load model weights or invoke GPU code.

Run tests from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## English-to-Yoruba translation

`POST /api/translate` accepts `{"text":"I want to write in Yoruba very well."}`
and returns `{"text":"Mo fẹ́ kọ̀wé lédè Yorùbá dáadáa."}`. Input must be a nonblank
string of 1–5000 characters; invalid input returns `422`.

The separate translation module exposes a `TranslationEngine` protocol and
`TranslationService`. Its remote adapter reuses `TTS_INFERENCE_URL` and posts
UTF-8 JSON to `/translate`. Returned Yoruba is passed through unchanged: it is
not sent to diacritization, punctuation normalization, or TTS. The frontend is
unchanged.

Missing configuration, timeout, connection errors, non-200 status, invalid
UTF-8/JSON, or missing/non-string/blank translated text returns `503`:
`{"detail":"Translation is not available right now. Please try again later."}`.
The adapter uses a 5-second connection timeout and 60-second read inactivity
timeout, does not follow redirects, and does not retry requests. Tests mock the
remote service and verify UTF-8 and translation-only behavior.
