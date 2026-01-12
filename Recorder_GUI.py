"""
Modern Spoken Number Recognition GUI
Compatible with Python 3.12, TensorFlow 2.x, librosa 0.10+, Tkinter, and PyAudio.
"""

import os
import struct
import wave
import numpy as np
import tkinter as tk
from tkinter import messagebox

import librosa
import librosa.display
import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras import models, backend as K
from tensorflow.keras.preprocessing import image

import pyaudio

# ------------------- Settings -------------------
RATE = 22050
CHANNELS = 1
WIDTH = 2
BLOCKSIZE = 256
RECORD_SECONDS = 2
THRESHOLD = 3000
MFCC_N_MELS = 256
MFCC_FMAX = 8000
IMG_SIZE = (200, 200)
MODEL_PATH = "sesotho_mfcc_cnn_model_mark_2.h5"
TMP_DIR = "tmp"

os.makedirs(TMP_DIR, exist_ok=True)

# ------------------- Initialize -------------------
top = tk.Tk()
top.title("Spoken Number Recognition")

s1 = tk.StringVar()
s1.set("You said: ")

# Load model
K.clear_session()
model = models.load_model(MODEL_PATH)

# ------------------- Audio Functions -------------------
def is_silent(data, threshold=THRESHOLD):
    return max(np.abs(data)) < threshold

def record_audio(filename="myNumber.wav"):
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(WIDTH),
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    output=False)

    print("Waiting for sound...")
    while True:
        input_bytes = stream.read(BLOCKSIZE, exception_on_overflow=False)
        input_vals = np.array(struct.unpack('h' * BLOCKSIZE, input_bytes))
        if not is_silent(input_vals):
            break

    print("Recording...")
    output_wf = wave.open(filename, 'wb')
    output_wf.setnchannels(CHANNELS)
    output_wf.setsampwidth(WIDTH)
    output_wf.setframerate(RATE)

    num_blocks = int(RATE / BLOCKSIZE * RECORD_SECONDS)
    silence_count = 0

    for _ in range(num_blocks):
        input_bytes = stream.read(BLOCKSIZE, exception_on_overflow=False)
        input_vals = np.array(struct.unpack('h' * BLOCKSIZE, input_bytes))
        
        if is_silent(input_vals):
            silence_count += 1
        else:
            silence_count = 0

        if silence_count > 20:
            break

        input_vals = np.clip(input_vals, -2**15, 2**15 - 1)
        output_bytes = struct.pack('h' * len(input_vals), *input_vals)
        output_wf.writeframes(output_bytes)

    print("Done recording.")
    output_wf.close()
    stream.stop_stream()
    stream.close()
    p.terminate()

# ------------------- MFCC Functions -------------------
def save_mfcc_image(audio_file, img_file, n_mels=MFCC_N_MELS, fmax=MFCC_FMAX):
    y, sr = librosa.load(audio_file)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, fmax=fmax)
    S_db = librosa.power_to_db(S, ref=np.max)

    plt.figure(figsize=(3, 3), dpi=100)
    librosa.display.specshow(librosa.power_to_db(S, ref=np.max), fmax=fmax)
    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    plt.savefig(img_file, bbox_inches='tight', pad_inches=0)
    plt.close()

# ------------------- Prediction -------------------
def predict_audio(audio_file="myNumber.wav"):
    img_file = os.path.join(TMP_DIR, "myImgg.jpg")
    save_mfcc_image(audio_file, img_file)

    # Load the image and preprocess
    img = image.load_img(img_file, target_size=IMG_SIZE)
    x = image.img_to_array(img) / 255.0
    x = np.expand_dims(x, axis=0)

    preds = model.predict(x)
    print (preds * 100)
    max_prob = np.max(preds)

    if max_prob < 0.1:
        s1.set("Cannot Recognize!")
    else:
        res = np.argmax(preds)
        prob = f"{max_prob*100:.2f}"
        #s1.set(f"You said: {res} with {prob}")    #for english
        s1.set(f"You said: {res+1} with {prob}") #for sesotho 

    top.update()
    print(s1.get())

# ------------------- Button Callbacks -------------------
def start_recording():
    try:
        record_audio()
        predict_audio()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        print("Error:", e)

def quit_app():
    top.destroy()

# ------------------- GUI Layout -------------------
label_title = tk.Label(top, text="Spoken Number Recognition", font=(None, 30))
button_start = tk.Button(top, text="Start", command=start_recording, font=(None, 20))
button_quit = tk.Button(top, text="Quit", command=quit_app, font=(None, 20))
label_result = tk.Label(top, textvariable=s1, font=(None, 25))

label_title.pack(pady=10)
button_start.pack(pady=10)
button_quit.pack(pady=10)
label_result.pack(pady=10, fill=tk.X)

top.mainloop()
