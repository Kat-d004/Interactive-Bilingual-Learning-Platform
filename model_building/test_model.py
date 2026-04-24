import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras import models

# ---------------- Settings ----------------
MODEL_PATH = "models/sesotho_numbers_model.h5"
TEST_DIR = "/home/kopano/Documents/School_Stuff/final_yr_project/Spoken_Number_Recognition-master/codes/spoken_numbers_wav/sesotho_spectrogram_image_ts/linomoro"
IMG_SIZE = (200, 200)

# ---------------- Load Model ----------------
model = models.load_model(MODEL_PATH)
print("Model loaded successfully!\n")

correct = 0
total = 0
all_losses = []

# ---------------- Loop Through Folders ----------------
folders = sorted(os.listdir(TEST_DIR))

for folder in folders:
    folder_path = os.path.join(TEST_DIR, folder)

    if not os.path.isdir(folder_path):
        continue

    print(f"\n===== Testing Folder {folder} =====")

    files = sorted(os.listdir(folder_path))

    for file in files[:15]:
        img_path = os.path.join(folder_path, file)

        # Load image
        img = image.load_img(img_path, target_size=IMG_SIZE)
        x = image.img_to_array(img) / 255.0
        x = np.expand_dims(x, axis=0)

        # Prediction
        preds = model.predict(x, verbose=0)

        predicted_class = np.argmax(preds)
        confidence = np.max(preds) * 100

        '''if f"{predicted_class+1:02d}" == "01":
            predicted_label = "01"
        elif f"{predicted_class+1:02d}" == "02":
            predicted_label = "10"
        else:
            predicted_label = f"{predicted_class:02d}"'''

        # Convert prediction to folder label (01–10)
        predicted_label = f"{predicted_class+1:02d}"

        # True label
        true_label = folder

        # Compute loss
        true_index = int(folder) - 1
        loss = tf.keras.losses.sparse_categorical_crossentropy(
            np.array([true_index]), preds
        ).numpy()[0]
        all_losses.append(loss)

        # Accuracy count
        if predicted_label == true_label:
            correct += 1

        total += 1

        print(f"{file} -> Predicted: {predicted_label} | Confidence: {confidence:.2f}%")

# ---------------- Overall Metrics ----------------
accuracy = (correct / total) * 100
avg_loss = np.mean(all_losses)

print("\n======================================")
print("OVERALL MODEL PERFORMANCE")
print("======================================")
print(f"Total Files Tested : {total}")
print(f"Correct Predictions: {correct}")
print(f"Accuracy           : {accuracy:.2f}%")
print(f"Average Loss       : {avg_loss:.4f}")