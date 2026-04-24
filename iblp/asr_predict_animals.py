#!/usr/bin/env python3
"""
asr_predict_animals.py
Headless ASR predictor for Sesotho animals model.
Called by recognize_animals.php with a single argument: path to the WAV file.
Outputs a single line of JSON to stdout.

Usage:
    python3 asr_predict_animals.py /path/to/recording.wav
"""

import sys
import json
import os
import warnings
import numpy as np

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import models, backend as K
from tensorflow.keras.preprocessing import image as keras_image

# ── Settings ──────────────────────────────────────────────────────────────────
MFCC_N_MELS = 256
MFCC_FMAX   = 8000
IMG_SIZE    = (200, 200)
MODEL_PATH  = os.path.join(os.path.dirname(__file__), 'models', 'sesotho_animals_model.h5')
TMP_DIR     = os.path.join(os.path.dirname(__file__), 'tmp')
MIN_PROB    = 0.10

# Index → Sesotho label + English + animal ID (matches animalsData in HTML)
LABELS = [
    { "sesotho": "Tau",         "english": "Lion",     "id": "lion"     },  # 0
    { "sesotho": "Tlou",        "english": "Elephant", "id": "elephant" },  # 1
    { "sesotho": "Noha",        "english": "Snake",      "id": "snake"      },  # 2
    { "sesotho": "Phokojoe",    "english": "Fox",      "id": "fox"      },  # 3
    { "sesotho": "Nonyana",     "english": "Bird",     "id": "bird"     },  # 4
    { "sesotho": "Katse",       "english": "Cat",      "id": "cat"      },  # 5
    { "sesotho": "Ntja",        "english": "dog",    "id": "dog"    },  # 6
    { "sesotho": "Nku",         "english": "Sheep",    "id": "sheep"    },  # 7
    { "sesotho": "Khomo",       "english": "Cow",  "id": "cow"  },  # 8
    { "sesotho": "Khoho",       "english": "Chicken",     "id": "chiken"     },  # 9
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
    img_path = os.path.join(TMP_DIR, 'pred_ani_' + os.path.basename(wav_path) + '.jpg')

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
        print(json.dumps({"recognized": False, "message": "Cannot recognize"}))
        return

    idx    = int(np.argmax(preds))
    label  = LABELS[idx] if idx < len(LABELS) else {"sesotho": str(idx), "english": str(idx), "id": str(idx)}
    prob   = round(max_prob * 100, 2)

    print(json.dumps({
        "recognized": True,
        "id":         label["id"],       # matches animalsData id in HTML
        "sesotho":    label["sesotho"],  # e.g. "Tau"
        "english":    label["english"],  # e.g. "Lion"
        "confidence": prob,
        "all_probs":  [round(float(p)*100, 2) for p in preds[0]]
    }))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        err("Usage: asr_predict_animals.py <wav_file>")
    wav = sys.argv[1]
    if not os.path.isfile(wav):
        err(f"File not found: {wav}")
    predict(wav)
