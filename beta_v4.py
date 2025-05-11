import psutil
import time
import pygetwindow as gw
import win32process
import firebase_admin
from firebase_admin import credentials, db
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import json
import io
import threading
import ctypes


with open("firebase_connector.json") as f:
    config = json.load(f)

cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)

# App Name Mapping
APP_NAME_MAPPING = {
    "chrome.exe": "Google Chrome", "msedge.exe": "Microsoft Edge", "firefox.exe": "Mozilla Firefox",
    "notepad.exe": "Notepad", "explorer.exe": "File Explorer", "code.exe": "VS Code",
    "pycharm64.exe": "PyCharm", "word.exe": "Microsoft Word", "excel.exe": "Microsoft Excel",
    "powerpnt.exe": "Microsoft PowerPoint", "vlc.exe": "VLC Media Player",
    "discord.exe": "Discord", "steam.exe": "Steam", "qbittorrent.exe": "qBittorrent",
    "utorrent.exe": "uTorrent", "msedgewebview2.exe": "Microsoft Edge WebView"
}

WINDOWS_SYSTEM_PROCESSES = {
    "svchost.exe", "wininit.exe", "services.exe", "winlogon.exe",
    "lsass.exe", "csrss.exe", "taskhost.exe", "dwm.exe", "msmpeng.exe"
}

controller_active = False

def put_system_to_sleep():
    """ Puts the system into sleep mode based on the OS """
    try:
        ctypes.windll.powrprof.SetSuspendState(False, True, True)
        print("System is now in sleep mode.")
    except Exception as e:
        print("Failed to put system to sleep:", e)


def update_system_options(event=None):
    """Update system dropdown based on selected lab."""
    selected_lab = lab_var.get()
    lab_number = int(selected_lab.split('-')[1])  # Extract lab number from "Lab-X"

    num_systems = 70  # Total systems in the lab
    systems_per_row = 10  # Number of systems per row

    system_options = []
    for sys_id in range(1, num_systems + 1):
        row_number = ((sys_id - 1) // systems_per_row) + 1  # Calculate L1R row
        system_number = f"{sys_id:02d}"  # Formats numbers like 01, 02, ..., 10, 11, etc.
        system_name = f"L{lab_number}R{row_number}-{system_number}"  # Generate system name
        system_options.append(system_name)

    system_var.set(system_options[0])  # Set default value
    system_dropdown["values"] = system_options  # Update dropdown options

def get_lab_info():
    """Create a GUI window to select lab and system."""
    global lab_var, system_var, system_dropdown

    root = tk.Tk()
    root.title("Lab & System Selection")

    tk.Label(root, text="Select Lab:").grid(row=0, column=0, padx=10, pady=5)
    lab_var = tk.StringVar()
    lab_options = [f"Lab-{i}" for i in range(1, 11)]  # Lab-1 to Lab-10
    lab_dropdown = ttk.Combobox(root, textvariable=lab_var, values=lab_options, state="readonly")
    lab_dropdown.grid(row=0, column=1, padx=10, pady=5)
    lab_dropdown.current(0)  # Default to first option
    lab_dropdown.bind("<<ComboboxSelected>>", update_system_options)  # Bind event

    tk.Label(root, text="Select System:").grid(row=1, column=0, padx=10, pady=5)
    system_var = tk.StringVar()
    system_dropdown = ttk.Combobox(root, textvariable=system_var, state="readonly")
    system_dropdown.grid(row=1, column=1, padx=10, pady=5)

    update_system_options()  # Initialize system dropdown with first lab's values

    def submit():
        root.quit()  # Close the window
        root.destroy()

    tk.Button(root, text="Submit", command=submit).grid(row=2, column=0, columnspan=2, pady=10)

    root.mainloop()

    return lab_var.get(), system_var.get()




LAB_NO, SYSTEM_NO = get_lab_info()

# Firebase Reference
firebase_ref = db.reference(f"system/{LAB_NO}/{SYSTEM_NO}")
firebase_db = db.reference(f"system/{LAB_NO}")

def get_active_window():
    """Returns the title and process name of the active window."""
    active_window = gw.getActiveWindow()
    if active_window and active_window.title:
        hwnd = active_window._hWnd
        title = active_window.title.strip()

        if title == "" or title == "Program Manager":
            return "Desktop", "explorer.exe"
        
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()

            if process_name in WINDOWS_SYSTEM_PROCESSES:
                return "System Process", process_name

            return APP_NAME_MAPPING.get(process_name, active_window.title), process_name
        except Exception:
            return "Unknown", "Unknown"
    return "Unknown", "Unknown"

def get_top_network_process():
    """Finds the process consuming the highest network data."""
    max_usage = 0
    top_process = "No Active Network Process"

    for proc in psutil.process_iter(attrs=['pid', 'name']):
        try:
            connections = proc.connections(kind='inet')
            if connections:
                net_io = proc.io_counters()
                data_used = net_io.read_bytes + net_io.write_bytes

                if data_used > max_usage and proc.info['name'].lower() not in WINDOWS_SYSTEM_PROCESSES:
                    max_usage = data_used
                    top_process = APP_NAME_MAPPING.get(proc.info['name'].lower(), proc.info['name'])

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return top_process

controller_active = False
threads = []  # Track threads for manual control

def update_active_window():
    """Updates active window and last active timestamp every 2 seconds."""
    while controller_active:
        active_window_title, _ = get_active_window()  # Replace with actual function
        firebase_ref.update({
            "active window": active_window_title,
            "last_active": int(time.time())
        })
        time.sleep(2)

def update_network_data():
    """Updates internet speed and top network app every 10 seconds."""
    while controller_active:
        old_io = psutil.net_io_counters()
        time.sleep(10)
        new_io = psutil.net_io_counters()

        recv_speed = (new_io.bytes_recv - old_io.bytes_recv) / (1024 * 1024)  # MB/s
        sent_speed = (new_io.bytes_sent - old_io.bytes_sent) / (1024 * 1024)  # MB/s
        top_network_app = get_top_network_process()  # Replace with actual function

        firebase_ref.update({
            "internet speed": f"{recv_speed:.2f} MB/s | {sent_speed:.2f} MB/s",
            "internet app": top_network_app
        })

def make_me_sleep():
    """Checks sleep status and puts the system to sleep based on the status every 10 seconds."""
    while controller_active:
        time.sleep(10)  # Check every 10 seconds
        status_ref = db.reference(f"sleep/{LAB_NO}")
        sleep_status = status_ref.get()

        if sleep_status and 'status' in sleep_status:
            if sleep_status['status'] == "Slept":
                put_system_to_sleep()  # Replace with actual function
            elif sleep_status['status'] == "Sleep":
                pass  # Do nothing, just wait
            else:
                print("Unknown status:", sleep_status)

def start_threads():
    """Starts all the threads when the controller is active."""
    global threads
    if not threads:  # Only start threads if they are not already running
        # Create and start threads
        t1 = threading.Thread(target=update_active_window, daemon=True)
        t2 = threading.Thread(target=update_network_data, daemon=True)
        t3 = threading.Thread(target=make_me_sleep, daemon=True)

        threads = [t1, t2, t3]
        
        t1.start()
        t2.start()
        t3.start()

def stop_threads():
    """Stops all running threads by clearing the controller_active flag."""
    global threads
    controller_active = False  # Stop the threads by clearing the flag
    for thread in threads:
        thread.join()  # Ensure each thread finishes properly
    threads = []  # Reset threads list

def controller():
    global controller_active
    while True:
        time.sleep(10)
        status_ref = db.reference(f"Active/{LAB_NO}")
        active_status = status_ref.get()

        if active_status['status'] == 'active':
            if not controller_active:
                controller_active = True  # Set the status to active
                start_threads()  # Start threads when active
        else:
            if controller_active:
                controller_active = False  # Set the status to inactive
                stop_threads()  # Stop threads when inactive

# Start the controller thread that monitors the status
threading.Thread(target=controller, daemon=True).start()

# Keep the main thread alive
while True:
    time.sleep(1)
