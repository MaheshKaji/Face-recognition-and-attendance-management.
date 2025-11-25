import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import numpy as np

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "#you firebase URL",
        'storageBucket': "#firebase key"
    })

# Importing student images
folderPath = 'Images'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
studentsId = []

for path in pathList:
    filename = f'Images/{path}'  # Ensure this matches the folder in Firebase
    bucket = storage.bucket()
    blob = bucket.blob(filename)

    # Check if the file exists in Firebase Storage
    if blob.exists():
        print(f"Downloading {filename}...")
        try:
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            img = cv2.imdecode(array, cv2.IMREAD_COLOR)
            imgList.append(img)
            studentsId.append(os.path.splitext(path)[0])
        except Exception as e:
            print(f"Error processing file {filename}: {e}")
    else:
        print(f"File {filename} does not exist in the Firebase bucket.")
        continue

print(studentsId)

# Function to find face encodings
def findEncoding(imagesList):
    encodeList = []
    for img in imagesList:
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encodeList.append(encodings[0])  # Append the first encoding
        else:
            print("No face found in image.")
            encodeList.append(None)  # Handle missing faces, could skip or set as None
    return encodeList

print("Encoding started....")
encodeListKnown = findEncoding(imgList)
encodeListKnownWithIds = [encodeListKnown, studentsId]
print("Encoding Complete")

# Save the encodings to a file
with open("EncodeFile.p", "wb") as file:
    pickle.dump(encodeListKnownWithIds, file)

print("Encodings saved successfully!")

