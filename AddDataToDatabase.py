import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    'databaseURL': "#your fiebase URL"
})
ref = db.reference('Students')

data = {
    "963852":
        {
            "name" : "Elon Musk",
            "major" : "Robotics",
            "starting_year" : 2021,
            "total_attendance" : 6,
            "standing" : "good",
            "year" : 4,
            "last_attendance_time" : "2025-04-16 00:54:34"
        },
    "U03EV22S0053":
        {
           "name" : "xyz",
            "major" : "BCA",
            "starting_year" : 2021,
            "total_attendance" : 6,
            "standing" : "good",
            "year" : 4,
            "last_attendance_time" : "2025-04-16 00:54:34"
        },
    "U03EV22S0057":
        {
            "name" : "abc",
            "major" : "BCA",
            "starting_year" : 2021,
            "total_attendance" : 6,
            "standing" : "good",
            "year" : 4,
            "last_attendance_time" : "2025-04-16 00:54:34"
        }
}

for key,value in data.items():

    ref.child(key).set(value)
