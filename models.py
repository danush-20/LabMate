import firebase_admin
from firebase_admin import credentials, db
import time
import random

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")  # Update with your Firebase key
firebase_admin.initialize_app(cred, {'databaseURL': os.getenv('databaseURL')})  # Update with your DB URL


num_systems = 70
systems_per_row = 10  # Each L1R row has 10 systems

sample_apps = ['Google Chrome', 'Microsoft Edge', 'Mozilla Firefox', 'Notepad', 'File Explorer', 'VS Code', 
               'PyCharm', 'Microsoft Word', 'Microsoft Excel', 'Microsoft PowerPoint', 'VLC Media Player', 
               'Discord', 'Steam', 'qBittorrent', 'uTorrent']

lab_computers = {
    "L9R1-01": {}, "L9R1-04": {}, "L9R1-05": {}, "L9R1-09": {}, "L9R2-03": {}, "L9R2-05": {},
    "L9R2-09": {}, "L9R3-01": {}, "L9R3-05": {}, "L9R3-09": {}, "L9R4-02": {}, "L9R4-05": {},
    "L9R5-01": {}, "L9R5-02": {}
}


# Loop through systems with L1R row updates
def update_systems():
    ref = db.reference("system/Lab-1")  # Reference for Lab-1 only
    for sys_id in range(1, num_systems + 1):
        row_number = ((sys_id - 1) // systems_per_row) + 1  # Calculate L1R row
        system_number = f"{sys_id:02d}"  # Formats numbers like 01, 02, ..., 10, 11, etc.
        system_name = f"L1R{row_number}-{system_number}"  # Generate system name

        system_data = {
            "active window": "Unknown",
            "internet app": "System",
            "internet speed": "0.00 MB/s | 0.00 MB/s",
            "last_active": "Unknown"	
        }
        
        ref.child(system_name).set(system_data)

    print("Firebase data updated for Lab-1 successfully!")

def add_sleep():
    lab_ref = db.reference("/Active")  # Reference to "sleep" node
    labs = ["lab9", "lab10", "lab11"]  # Add more labs as needed
    for lab in labs:
        lab_ref.child(lab).set({})  # Use lab_ref instead of ref
    print("Sleep data added successfully!")


def update_window():
    ref = db.reference("system/Lab-1")  # Reference for Lab-1 only
    for sys_id in range(1, num_systems + 1):
        row_number = ((sys_id - 1) // systems_per_row) + 1  # Calculate L1R row
        system_number = f"{sys_id:02d}"  # Formats numbers like 01, 02, ..., 10, 11, etc.
        system_name = f"L1R{row_number}-{system_number}"  # Generate system name
        active_window = random.choice(sample_apps)
        system_data = {
            "active window": active_window,
            "internet app": "System",
            "internet speed": "0.00 MB/s | 0.00 MB/s",
            "last_active": "Unknown"	
        }
        
        ref.child(system_name).set(system_data)
    
    print("Firebase data updated for Lab-1 successfully!")

def add_sleep_labs():
    sleep_ref = db.reference("/Active")
    labs = [f"Lab-{i}" for i in range(1, 11)]  # Generates Lab-1 to Lab-10
    for lab in labs:
        sleep_ref.child(lab).set({"status": "inactive"})  # Default status
    print("Labs with status added under 'sleep'!")

add_sleep_labs()