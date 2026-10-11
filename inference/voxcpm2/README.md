# Standalone NaijaVoice VoxCPM2 inference service

An isolated CUDA-host service. It does not import or modify the main backend,
frontend, F5 adapter, translation, or diacritization. It is not automatically
started or selected by NaijaVoice. No model weights are included.

## Model and license

Uses **LyngualLabs/YorubaEnglish-CodeSwitching-TTS**, a VoxCPM2 fine-tune.
The current checkpoint is **CC-BY-NC-4.0**, for research/non-commercial use.
**Do not treat it as commercially licensed**, even though the upstream VoxCPM2
base/code has a different license. Obtain appropriate permission from the
checkpoint owner before commercial deployment.
[Checkpoint card](https://huggingface.co/LyngualLabs/YorubaEnglish-CodeSwitching-TTS)

Generation uses `cfg_value=2.0`, `inference_timesteps=22`, and
`retry_badcase=False`. Denoising and compile optimization are disabled
(`load_denoiser=False`, `optimize=False`) to avoid an extra denoiser download and
CUDA compilation overhead. Device is explicitly `cuda`.

## Architecture and contract

- `voxcpm_service/main.py`: app factory, validation, `/health` and `/tts`.
- `config.py`: checkpoint ID and paths to the existing default voice assets.
- `engine.py`: lazy model import/load, one cached model, serialized generation.
- `audio.py`: backward RMS trimming and in-memory PCM-16 WAV encoding.

`GET /health` returns `{"status":"ok","model_loaded":false}` before the first
request. This is liveness, not GPU readiness. `POST /tts` accepts only the existing
remote contract `{"text":"Ẹ káàbọ̀. Welcome!"}` and returns `audio/wav`.
Nonblank strings of 1–5000 characters are accepted; invalid input returns `422`.
Failures return a sanitized `503`; exception details are logged on the GPU host.
The service preserves supplied text, adding no translation or diacritization.

Reference voice: the repository's existing
`backend/assets/voices/naijavoice_default_voice.wav`, with its exact UTF-8
transcript read from `backend/assets/voices/naijavoice_default_voice.txt`.
Paths are anchored to the repository, not the working directory. To deploy the
service without the whole repository, set absolute
`VOXCPM_REFERENCE_AUDIO_PATH` and `VOXCPM_REFERENCE_TRANSCRIPT_PATH` overrides.
Verify that the transcript actually matches the spoken clip.

Trimming scans backwards in **0.1-second windows**, skipping windows with
**RMS <= 0.01**, then retains up to **0.4 seconds** after the last active window.
It preserves leading silence and internal pauses, does not pad short tails,
and has at most one window of boundary uncertainty. Empty/all-silent results
are rejected rather than returned as successful speech.

## CUDA host startup (Linux, Python 3.11 recommended)

Copy the repository including its two voice assets to `/opt/naijavoice-ai`.
Use a CUDA-capable NVIDIA host with a matching PyTorch/torchaudio installation.
A Colab T4 may take over 120 seconds for some requests. Use one worker to avoid
loading a separate 2B model per worker.

```bash
cd /opt/naijavoice-ai/inference/voxcpm2
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
# Install the matching CUDA PyTorch/torchaudio build for your host first,
# following https://pytorch.org/get-started/locally/ (Colab already provides it).
python -m pip install -r requirements-gpu.txt
export HF_HOME=/var/tmp/naijavoice-hf-cache
python -c "import torch; assert torch.cuda.is_available(), 'CUDA GPU required'"
python -m uvicorn voxcpm_service.main:app --host 0.0.0.0 --port 8000 --workers 1
```

In another terminal:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail --max-time 900 http://127.0.0.1:8000/tts \
  -H 'Content-Type: application/json; charset=utf-8' \
  -d '{"text":"Ẹ káàbọ̀ sí NaijaVoice AI. Welcome!"}' -o /tmp/naijavoice.wav
```

The first `/tts` request downloads the checkpoint into the external Hugging Face
cache and loads it on the GPU; `/health` does neither. Warm up directly before
routing traffic through the main backend, whose TTS read timeout is 300 seconds.
GPU dependency installation also installs substantial Torch/ML dependencies.
These commands are for the GPU host; do not install them on the Windows API host.
The GPU requirements use upstream Git source, as recommended by the checkpoint
card. Record/pin the tested VoxCPM commit in your GPU deployment for repeatability.

## Exact Colab startup

1. Select **Runtime → Change runtime type → T4 GPU** (or a larger CUDA GPU).
2. Copy this repository folder, including voice assets, to
   **My Drive/naijavoice-ai** in Google Drive. Run these notebook cells:

```python
from google.colab import drive
drive.mount('/content/drive')
```

```python
%pip install -r /content/drive/MyDrive/naijavoice-ai/inference/voxcpm2/requirements-gpu.txt
```

If pip reports already-imported packages were upgraded, restart the Colab
session, remount Drive, and continue below. Do not rerun installation unnecessarily.

```python
import os, subprocess, sys, torch
assert torch.cuda.is_available(), "Select a CUDA GPU runtime"
os.environ["HF_HOME"] = "/content/naijavoice-hf-cache"  # outside the repository
service_dir = "/content/drive/MyDrive/naijavoice-ai/inference/voxcpm2"
log = open("/content/naijavoice-inference.log", "a")
server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "voxcpm_service.main:app",
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1"],
    cwd=service_dir, stdout=log, stderr=subprocess.STDOUT,
)
print("Server PID:", server.pid)
```

Once the log reports startup complete, check and warm up in a new cell:

```python
import requests
print(requests.get("http://127.0.0.1:8000/health", timeout=10).json())
response = requests.post("http://127.0.0.1:8000/tts",
                         json={"text": "Ẹ káàbọ̀ sí NaijaVoice AI. Welcome!"}, timeout=900)
response.raise_for_status()
assert response.headers["content-type"].startswith("audio/wav")
from IPython.display import Audio, display
display(Audio(response.content))
```

Optional standalone tunnel, after warmup:

```python
%pip install pyngrok
```

```python
from getpass import getpass
from pyngrok import ngrok
ngrok.set_auth_token(getpass("ngrok token: "))
tunnel = ngrok.connect(8000, "http")
print(tunnel.public_url)
```

**Integration boundary:** this standalone app intentionally serves `/health`
and `/tts` only. The main backend currently shares `TTS_INFERENCE_URL` across
`/tts`, `/translate`, and `/diacritize`. Do not simply replace that working base
URL with this standalone tunnel: route `/tts` to this service through the
existing inference gateway while retaining `/translate` and `/diacritize`, or
plan a separate configuration change later. No such change is made here.
No F5 fallback is added. Colab shutdown or tunnel expiry makes the service unavailable.

## Lightweight local tests (no VoxCPM, Torch, GPU or weights)

Create a separate environment, install `requirements-test.txt`, then run from
`inference/voxcpm2`:

```bash
python -m pytest -q --basetemp=.test-tmp
```

Tests mock the VoxCPM module/model but use real NumPy trimming and SoundFile WAV
encoding. Runtime requirements are FastAPI, Uvicorn, NumPy and SoundFile; tests
add pytest and HTTPX. Only `requirements-gpu.txt` adds VoxCPM and its ML dependency
tree. Optional tunnel setup adds pyngrok on Colab, not to the API backend.
