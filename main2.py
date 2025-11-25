import cv2
import time
import firebase_admin
from firebase_admin import credentials, db
from deepface import DeepFace
from datetime import datetime
import os

# Firebase Initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://faceattendancerealtime-2c129-default-rtdb.firebaseio.com/",
    'storageBucket': "faceattendancerealtime-2c129.appspot.com"
})
ref = db.reference('attendance')

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Optional: map ID to real names
id_to_name = {
    "U03EV22S0053": "vishwanath",
    "U03EV22S0057": "mahesh",
    "ganesh": "ganesh"
}

logged_in_users = {}
logout_timestamps = {}
movement_tracker = {}

def get_motivational_quote(emotion):
    quotes = {
        "happy": "Keep smiling, the world is brighter with you!",
        "sad": "Every day may not be good, but there's something good in every day.",
        "angry": "Stay calm. You’ve got this.",
        "surprise": "Expect the unexpected and enjoy the ride!",
        "fear": "Courage is not the absence of fear, but the triumph over it.",
        "neutral": "Another day to be awesome!"
    }
    return quotes.get(emotion, "Keep pushing forward!")

def is_head_moved(name, current_position):
    if name not in movement_tracker:
        movement_tracker[name] = {
            "positions": [current_position],
            "timestamp": time.time()
        }
        return False

    tracker = movement_tracker[name]
    tracker["positions"].append(current_position)

    if time.time() - tracker["timestamp"] > 3:
        tracker["positions"] = [current_position]
        tracker["timestamp"] = time.time()
        return False

    xs = [pos[0] for pos in tracker["positions"]]
    ys = [pos[1] for pos in tracker["positions"]]

    if max(xs) - min(xs) > 30 or max(ys) - min(ys) > 30:
        del movement_tracker[name]
        return True

    return False

def record_attendance(name, emotion=None, logout=False):
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    user_ref = ref.child(name).child(today)

    if logout:
        if name in logged_in_users:
            logout_time = time.time()
            duration = round((logout_time - logged_in_users[name]) / 3600, 2)
            user_ref.update({
                'logout_time': current_time,
                'duration_hours': duration
            })
            print(f"{name} logged out at {current_time} | Duration: {duration} hrs")
            logout_timestamps[name] = logout_time

            # Weekly and Monthly Summary
            week_number = datetime.now().isocalendar()[1]
            month = datetime.now().strftime('%Y-%m')
            user_summary_ref = ref.child(name)

            # ---------- Weekly ----------
            weekly_ref = user_summary_ref.child('weekly_summary').child(str(week_number))
            existing_week = weekly_ref.get() or {}
            weekly_total = existing_week.get('total_hours', 0) + duration
            weekly_dates = existing_week.get('dates', [])
            if today not in weekly_dates:
                weekly_dates.append(today)
            weekly_days = len(weekly_dates)
            weekly_avg = round(weekly_total / weekly_days, 2)
            weekly_ref.update({
                'total_hours': weekly_total,
                'days': weekly_days,
                'average_hours': weekly_avg,
                'dates': weekly_dates
            })

            # ---------- Monthly ----------
            monthly_ref = user_summary_ref.child('monthly_summary').child(month)
            existing_month = monthly_ref.get() or {}
            monthly_total = existing_month.get('total_hours', 0) + duration
            monthly_dates = existing_month.get('dates', [])
            if today not in monthly_dates:
                monthly_dates.append(today)
            monthly_days = len(monthly_dates)
            monthly_avg = round(monthly_total / monthly_days, 2)
            monthly_ref.update({
                'total_hours': monthly_total,
                'days': monthly_days,
                'average_hours': monthly_avg,
                'dates': monthly_dates
            })

            del logged_in_users[name]

    else:
        if name not in logged_in_users:
            now = time.time()
            last_logout = logout_timestamps.get(name, 0)
            if now - last_logout < 30:
                print(f"{name} tried to login again too soon.")
                return
            logged_in_users[name] = now
            user_ref.update({
                'login_time': current_time,
                'emotion': emotion,
                'quote': get_motivational_quote(emotion)
            })
            print(f"{name} logged in at {current_time}")

# Start webcam
cap = cv2.VideoCapture(0)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)

        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]

            if face_roi.shape[0] < 50 or face_roi.shape[1] < 50:
                continue

            try:
                result = DeepFace.find(face_roi, db_path="face_db", model_name="Facenet", enforce_detection=False)

                if len(result[0]) > 0:
                    df = result[0]
                    best_match = df.iloc[0]
                    distance = best_match['distance']

                    if distance < 10:
                        identity = best_match['identity']

                        # ✅ Ignore results not from face_db
                        if "face_db" not in identity:
                            continue

                        raw_id = os.path.splitext(os.path.basename(identity))[0]
                        name = id_to_name.get(raw_id, raw_id)
                        current_time = time.time()

                        center_x = x + w // 2
                        center_y = y + h // 2

                        if not is_head_moved(name, (center_x, center_y)):
                            cv2.putText(frame, "Move Head", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            continue

                        if name in logged_in_users:
                            login_time = logged_in_users[name]
                            if current_time - login_time >= 60:
                                print(f"{name} re-detected after 1 minute. Logging out...")
                                record_attendance(name, logout=True)
                                cv2.putText(frame, f"Logged Out", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                            else:
                                cv2.putText(frame, f"Already Logged In", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 0), 1)
                        else:
                            emotion_analysis = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
                            emotion = emotion_analysis[0]['dominant_emotion']
                            record_attendance(name, emotion)
                            quote = get_motivational_quote(emotion)
                            cv2.putText(frame, f"Marked", (x, y - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, f"Name: {name}", (x, y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                    else:
                        cv2.putText(frame, "Unknown Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                else:
                    cv2.putText(frame, "Unknown Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            except Exception as e:
                print("Recognition error:", e)

        cv2.imshow('Face Recognition Attendance System', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    for name in list(logged_in_users):
        record_attendance(name, logout=True)
    cap.release()
    cv2.destroyAllWindows()
