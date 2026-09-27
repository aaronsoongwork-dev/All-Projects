"""
Sanity check you can run before touching the API at all:
    python test_model_loads.py path/to/some_test_clip.wav

Confirms:
  1. Your checkpoint loads into FusionEmotionModel without shape errors
  2. Whisper transcribes the clip
  3. The fusion model produces a prediction

If this script works, the API will work — the API layer is just HTTP/
WebSocket plumbing around these same three calls.
"""
import sys

from config import FUSION_MODEL_CHECKPOINT, DEVICE
from models import stt, audio_utils, emotion_model


def main(wav_path: str):
    print(f"Loading Whisper...")
    stt.load_model()

    print(f"Loading fusion model from {FUSION_MODEL_CHECKPOINT} on {DEVICE}...")
    emotion_model.load_model(FUSION_MODEL_CHECKPOINT, device=DEVICE)

    with open(wav_path, "rb") as f:
        raw_bytes = f.read()

    print("Converting audio format...")
    wav_bytes = audio_utils.to_wav_pcm16(raw_bytes, source_format=wav_path.split(".")[-1])
    waveform = audio_utils.bytes_to_model_waveform(wav_bytes)

    print("Transcribing...")
    transcript = stt.transcribe(wav_bytes)
    print(f"  transcript: {transcript!r}")

    print("Running fusion model...")
    result = emotion_model.predict(waveform, transcript)
    print(f"  result: {result}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_model_loads.py path/to/clip.wav")
        sys.exit(1)
    main(sys.argv[1])
