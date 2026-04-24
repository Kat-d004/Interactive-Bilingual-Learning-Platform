#!/usr/bin/env python3
"""
asr_predict.py
Headless ASR predictor — no GUI, no pyaudio, no tkinter.
Called by recognize.php with a single argument: path to the WAV file.
Outputs a single line of JSON to stdout.

Usage:
    python3 asr_predict.py /path/to/recording.wav
"""

import sys
import json
import os
import numpy as np
import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')          # non-interactive backend — required for server use
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import models, backend as K
from tensorflow.keras.preprocessing import image as keras_image
import warnings
import os
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# ── Settings (keep in sync with your training script) ────────────────────────
MFCC_N_MELS = 256
MFCC_FMAX   = 8000
IMG_SIZE    = (200, 200)
MODEL_PATH  = os.path.join(os.path.dirname(__file__), 'models', 'sesotho_numbers_model.h5')
TMP_DIR     = os.path.join(os.path.dirname(__file__), 'tmp')
MIN_PROB    = 0.10   # confidence threshold

# Sesotho number labels (index 0 → "Ngoe" / 1, etc.)
SESOTHO_LABELS = [
    "Ngoe",    # 1
    "Peli",     # 2
    "Tharo",    # 3
    "Nne",      # 4
    "Hlano",    # 5
    "Tšelela",  # 6
    "Supa",     # 7
    "Robeli",   # 8
    "Robong",   # 9
    "Leshome",  # 10
]

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(1)

def save_melspectrogram(audio_file, img_file):
    y, sr = librosa.load(audio_file)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=MFCC_N_MELS, fmax=MFCC_FMAX)
    S_db = librosa.power_to_db(S, ref=np.max)
    plt.figure(figsize=(3, 3), dpi=100)
    librosa.display.specshow(S_db, fmax=MFCC_FMAX)
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(img_file, bbox_inches='tight', pad_inches=0)
    plt.close()

def predict(wav_path):
    os.makedirs(TMP_DIR, exist_ok=True)
    img_path = os.path.join(TMP_DIR, 'pred_' + os.path.basename(wav_path) + '.jpg')

    try:
        save_melspectrogram(wav_path, img_path)
    except Exception as e:
        err(f"Spectrogram error: {e}")

    try:
        img = keras_image.load_img(img_path, target_size=IMG_SIZE)
        x   = keras_image.img_to_array(img) / 255.0
        x   = np.expand_dims(x, axis=0)
    except Exception as e:
        err(f"Image load error: {e}")
    finally:
        try:
            os.unlink(img_path)
        except Exception:
            pass

    try:
        K.clear_session()
        mdl   = models.load_model(MODEL_PATH)
        preds = mdl.predict(x, verbose=0)
    except Exception as e:
        err(f"Model error: {e}")

    max_prob = float(np.max(preds))
    if max_prob < MIN_PROB:
        print(json.dumps({
            "recognized": False,
            "message":    "Cannot recognize"
        }))
        return

    idx     = int(np.argmax(preds))
    number  = idx + 1                            # 1-based
    sesotho = SESOTHO_LABELS[idx] if idx < len(SESOTHO_LABELS) else str(number)
    prob    = round(max_prob * 100, 2)

    print(json.dumps({
        "recognized": True,
        "number":     number,       # integer 1-10
        "sesotho":    sesotho,      # e.g. "Hlano"
        "confidence": prob,         # e.g. 94.27
        "all_probs":  [round(float(p)*100, 2) for p in preds[0]]
    }))

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        err("Usage: asr_predict.py <wav_file>")

    wav = sys.argv[1]
    if not os.path.isfile(wav):
        err(f"File not found: {wav}")

    predict(wav)
