import cv2
import numpy as np
from PIL import Image
import os

# Load the face cascade
cascade_path = "haarcascade_frontalface_default.xml"
if not os.path.exists(cascade_path):
    raise FileNotFoundError("haarcascade_frontalface_default.xml not found!")

detector = cv2.CascadeClassifier(cascade_path)
recognizer = cv2.face.LBPHFaceRecognizer_create()

dataset_path = "face_db"
image_paths = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path) if f.endswith('.jpg')]

faces = []
ids = []
str_to_int = {}
current_id = 0

print("[INFO] Training faces. Please wait...")

for imagePath in image_paths:
    filename = os.path.basename(imagePath)
    parts = filename.split(".")

    if len(parts) < 3:
        print(f"Filename format error in: {filename}")
        continue

    user_id_str = parts[1]

    if user_id_str not in str_to_int:
        str_to_int[user_id_str] = current_id
        current_id += 1

    try:
        img = Image.open(imagePath).convert("L")  # grayscale
        img_np = np.array(img, 'uint8')
        faces_detected = detector.detectMultiScale(img_np)

        for (x, y, w, h) in faces_detected:
            faces.append(img_np[y:y+h, x:x+w])
            ids.append(str_to_int[user_id_str])

    except Exception as e:
        print(f"Error processing image {imagePath}: {e}")

if len(faces) == 0:
    print("[ERROR] No faces found in face_db!")
else:
    recognizer.train(faces, np.array(ids))
    recognizer.save('trainer.yml')
    print(f"[INFO] {len(set(ids))} users trained. Total faces: {len(faces)}")