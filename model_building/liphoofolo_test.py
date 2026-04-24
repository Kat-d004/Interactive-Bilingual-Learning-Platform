import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras import models

# ---------------- Settings ----------------
MODEL_PATH = "models/sesotho_animals_model.h5"
TEST_DIR = "/home/kopano/Documents/School_Stuff/final_yr_project/Spoken_Number_Recognition-master/codes/spoken_numbers_wav/sesotho_spectrogram_image_ts/liphoofolo"
IMG_SIZE = (200, 200)

# ---------------- Class Mapping ----------------
class_names = {
    0: "tau",   # 1
    1: "tlou",      # 2
    2: "noha",    # 3
    3: "phokojoe",     # 4
    4: "nonyana",   # 5
    5: "katse",     # 6
    6: "ntja",   # 7
    7: "nku",    # 8
    8: "khomo",
    9: "khoho"
}

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

    print(f"\n===== Testing Folder {folder} ({class_names[int(folder)-1]}) =====")

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

        predicted_label_name = class_names[predicted_class]

        # True label
        true_index = int(folder) - 1
        true_label_name = class_names[true_index]

        # Compute loss
        loss = tf.keras.losses.sparse_categorical_crossentropy(
            np.array([true_index]), preds
        ).numpy()[0]
        all_losses.append(loss)

        # Accuracy count
        if predicted_class == true_index:
            correct += 1

        total += 1

        print(f"{file} -> Predicted: {predicted_label_name} | Confidence: {confidence:.2f}%")

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