#!/usr/bin/env python3
"""
asr_predict_english.py
Whisper-based ASR for English colour/number/animal recognition.
Called by recognize_english.php with: python3 asr_predict_english.py <wav> <topic>
topic = colours | numbers | animals

Outputs one line of JSON to stdout.
"""

import sys, json, os, warnings
warnings.filterwarnings('ignore')
import os
os.environ['XDG_CACHE_HOME'] = os.path.join(os.path.dirname(__file__), 'whisper_cache')

import whisper

# ── Vocabulary per topic ──────────────────────────────────────────────────────
VOCAB = {
    "colours": {
        "red":    {"id": "red",    "english": "Red",    "sesotho": "Khubelu"},
        "green":  {"id": "green",  "english": "Green",  "sesotho": "Tala"},
        "blue":   {"id": "blue",   "english": "Blue",   "sesotho": "Putsoa"},
        "black":  {"id": "black",  "english": "Black",  "sesotho": "Nts'o"},
        "white":  {"id": "white",  "english": "White",  "sesotho": "Nts'eou"},
        "pink":   {"id": "pink",   "english": "Pink",   "sesotho": "Pinki"},
        "purple": {"id": "purple", "english": "Purple", "sesotho": "Pherese"},
        "yellow": {"id": "yellow", "english": "Yellow", "sesotho": "Ts'ehla"},
    },
    "numbers": {
    "one":   {"id": "1",  "english": "One",   "sesotho": "Ngoe"},
    "two":   {"id": "2",  "english": "Two",   "sesotho": "Peli"},
    "three": {"id": "3",  "english": "Three", "sesotho": "Tharo"},
    "four":  {"id": "4",  "english": "Four",  "sesotho": "Nne"},
    "five":  {"id": "5",  "english": "Five",  "sesotho": "Hlano"},
    "six":   {"id": "6",  "english": "Six",   "sesotho": "Ts'elela"},
    "seven": {"id": "7",  "english": "Seven", "sesotho": "Supa"},
    "eight": {"id": "8",  "english": "Eight", "sesotho": "Robeli"},
    "nine":  {"id": "9",  "english": "Nine",  "sesotho": "Robong"},
    "ten":   {"id": "10", "english": "Ten",   "sesotho": "Leshome"},
    "1":     {"id": "1",  "english": "One",   "sesotho": "Ngoe"},
    "2":     {"id": "2",  "english": "Two",   "sesotho": "Peli"},
    "3":     {"id": "3",  "english": "Three", "sesotho": "Tharo"},
    "4":     {"id": "4",  "english": "Four",  "sesotho": "Nne"},
    "5":     {"id": "5",  "english": "Five",  "sesotho": "Hlano"},
    "6":     {"id": "6",  "english": "Six",   "sesotho": "Ts'elela"},
    "7":     {"id": "7",  "english": "Seven", "sesotho": "Supa"},
    "8":     {"id": "8",  "english": "Eight", "sesotho": "Robeli"},
    "9":     {"id": "9",  "english": "Nine",  "sesotho": "Robong"},
    "10":    {"id": "10", "english": "Ten",   "sesotho": "Leshome"},
},
    "animals": {
        "cat":      {"id": "cat",      "english": "Cat",      "sesotho": "Katse"},
        "dog":      {"id": "dog",      "english": "Dog",      "sesotho": "Ntja"},
        "bird":     {"id": "bird",     "english": "Bird",     "sesotho": "Nonyana"},
        "cow":      {"id": "cow",      "english": "Cow",      "sesotho": "Khoho"},
        "chicken":  {"id": "chicken",  "english": "Chicken",  "sesotho": "Khoho"},
        "sheep":    {"id": "sheep",    "english": "Sheep",    "sesotho": "Nku"},
        "lion":     {"id": "lion",     "english": "Lion",     "sesotho": "Tau"},
        "elephant": {"id": "elephant", "english": "Elephant", "sesotho": "Tlou"},
        "snake":    {"id": "snake",    "english": "Snake",    "sesotho": "Noha"},
        "fox":      {"id": "fox",      "english": "Fox",      "sesotho": "Phokojoe"},
    },
}

def err(msg):
    print(json.dumps({"error": msg}))
    sys.exit(1)

def predict(wav_path, topic):
    vocab = VOCAB.get(topic)
    if not vocab:
        err(f"Unknown topic: {topic}")

    try:
        model = whisper.load_model("base")
        result = model.transcribe(wav_path, language="en", fp16=False)
    except Exception as e:
        err(f"Whisper error: {e}")

    raw   = result.get("text", "").strip().lower()
    clean = "".join(c for c in raw if c.isalpha() or c.isspace()).strip()

    words = clean.split()

    matched = None
    for word in words:
        # exact match (handles "sheep" after stripping "sheep.")
        if word in vocab:
            matched = vocab[word]
            break
        # digit match — convert spoken digit to string e.g. "6" won't reach here
        # so also check raw words before stripping for digits
    
    # second pass on raw words to catch digits like "6", "10"
    if not matched:
        for word in raw.split():
            word = word.strip('.,!?')
            if word in vocab:
                matched = vocab[word]
                break

    if not matched:
        print(json.dumps({
            "recognized": False,
            "message": "Cannot recognize",
            "transcript": raw
        }))
        return

    print(json.dumps({
        "recognized": True,
        "id":         matched["id"],
        "english":    matched["english"],
        "sesotho":    matched["sesotho"],
        "confidence": 95.0,
        "transcript": raw
}))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        err("Usage: asr_predict_english.py <wav_file> <topic>")
    wav = sys.argv[1]
    topic = sys.argv[2]
    if not os.path.isfile(wav):
        err(f"File not found: {wav}")
    predict(wav, topic)
