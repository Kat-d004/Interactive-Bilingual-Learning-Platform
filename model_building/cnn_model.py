import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Set image dimensions
nrow = 200
ncol = 200
input_shape = (nrow, ncol, 3)

# Create a new model
model = keras.Sequential()

model.add(layers.Conv2D(16, (7, 7), activation='relu', padding='same', input_shape=input_shape))
model.add(layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
model.add(layers.BatchNormalization())

model.add(layers.Conv2D(32, (5, 5), activation='relu', padding='same'))
model.add(layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
model.add(layers.BatchNormalization())

model.add(layers.Conv2D(64, (3, 3), activation='relu', padding='same'))
model.add(layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
model.add(layers.BatchNormalization())

model.add(layers.Conv2D(128, (3, 3), activation='relu', padding='same'))
model.add(layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
model.add(layers.BatchNormalization())

model.add(layers.Conv2D(128, (3, 3), activation='relu', padding='same'))
model.add(layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
model.add(layers.BatchNormalization())

model.add(layers.Conv2D(256, (3, 3), activation='relu', padding='same'))
model.add(layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
model.add(layers.BatchNormalization())

model.add(layers.Flatten())
model.add(layers.Dense(1024, activation='relu'))
model.add(layers.BatchNormalization())
model.add(layers.Dropout(0.5))

model.add(layers.Dense(8, activation='softmax'))

model.summary()

# Data generators
train_data_dir = '/home/kopano/Documents/School_Stuff/final_yr_project/Spoken_Number_Recognition-master/codes/spoken_numbers_wav/sesotho_spectrogram_image_tr/mebala'
batch_size_tr = 64

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=10,      # Added
    width_shift_range=0.1,  # Added
    height_shift_range=0.1, # Added
    shear_range=0.2,        # Added
    zoom_range=0.2,         # Added
    horizontal_flip=False,
    validation_split=0.1
)

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(nrow, ncol),
    batch_size=batch_size_tr,
    class_mode='sparse',
    subset='training'  # Remove if not using validation_split
)

test_data_dir = '/home/kopano/Documents/School_Stuff/final_yr_project/Spoken_Number_Recognition-master/codes/spoken_numbers_wav/sesotho_spectrogram_image_ts/mebala'
batch_size_ts = 5

test_datagen = ImageDataGenerator(rescale=1./255)

test_generator = test_datagen.flow_from_directory(
    test_data_dir,
    target_size=(nrow, ncol),
    batch_size=batch_size_ts,
    class_mode='sparse',
    shuffle=False  # Usually False for test/validation data
)

# Compile the model
model.compile(
    optimizer=optimizers.Adam(learning_rate=0.0001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Calculate steps (with error handling)
steps_per_epoch = max(1, train_generator.samples // batch_size_tr)
validation_steps = max(1, test_generator.samples // batch_size_ts)

nepochs = 70

# Train the model
history = model.fit(
    train_generator,
    epochs=nepochs,
    validation_data=test_generator,
    verbose=1
)

# Save the model
model.save('experiments/sesotho_simple_colours_model.h5')

# Optional: Save the training history
import pickle
with open('training_history_display.pkl', 'wb') as f:
    pickle.dump(history.history, f)

print("Model training completed and saved!")
