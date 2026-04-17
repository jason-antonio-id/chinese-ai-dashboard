import tensorflow as tf
import numpy as np
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from PIL import Image

model = MobileNetV2(weights='imagenet')

img = Image.open('image.png').resize((224, 224))
img_array = np.array(img)
img_array = np.expand_dims(img_array, axis=0)
img_array = preprocess_input(img_array.astype(np.float32))

predictions = model.predict(img_array)
results = decode_predictions(predictions, top=3)[0]

print("===== Product Image Classifier =====")
for i, (id, label, score) in enumerate(results):
    print(f"{i+1}. {label} — {round(score * 100, 1)}% confident")
print("====================================")
