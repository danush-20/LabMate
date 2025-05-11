from flask import Flask, render_template,request, redirect, url_for, session, flash
import firebase_admin   
from StaffPack import app
from firebase_admin import credentials, db, auth
import time
import requests
import os
from dotenv import load_dotenv

cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred, {databaseURL: os.getenv("databaseURL")})
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
@app.route('/')
def homepage():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['username']
    password = request.form['password']
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    response = requests.post(url, json=payload)
    data = response.json()

    if "idToken" in data:
        session['user'] = data['localId']  # Firebase UID
        return redirect(url_for('labnames'))
    else:
        flash("Invalid credentials. Please try again.","danger")
        return redirect(url_for('homepage'))

@app.route('/labname')
def labnames():
    if 'user' in session:
        ref = db.reference('system/')  
        system_data = ref.get() or {}
        status_ref = db.reference(f"Active/")
        active_status = status_ref.get()
        combined_data = {lab: active_status[lab] for lab in system_data if lab in active_status}
        return render_template("labnames.html", combine_data=combined_data)
    else :
        return redirect(url_for('login'))


@app.route("/lab/<lab_name>")
def lab_details(lab_name):
    if 'user' in session:
        ref = db.reference('system/')
        ref_sleep = db.reference(f'sleep/{lab_name}')  
        system_data = ref.get() or {}
        systems = system_data.get(lab_name, {})
        current_time = int(time.time())
        sleep_data = ref_sleep.get()
        sleep_status = sleep_data.get("status", "Sleep") if sleep_data else "Sleep"
        return render_template("lab.html", lab_name=lab_name,systems=systems,current_time=current_time,sleep_status=sleep_status)
    else :
        return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('homepage'))


@app.route('/sleepall/<lab_name>', methods=['POST'])
def sleep_all(lab_name):
    if 'user' in session:
        ref_sleep = db.reference(f'sleep/{lab_name}')
        sleep_data = ref_sleep.get()
        new_status = "Slept" if not sleep_data or sleep_data.get("status") == "Sleep" else "Sleep"
        ref_sleep.update({"status": new_status})
        return redirect(url_for('lab_details', lab_name=lab_name))

    else:
        return redirect(url_for('login'))

@app.route('/toggle_lab/<lab>', methods=['POST'])
def toggle_lab(lab):
    ref = db.reference(f"Active/{lab}")
    lab_data = ref.get()
    new_status = "inactive" if not lab_data or lab_data.get("status") == "active" else "active"
    ref.update({"status": new_status})
    return redirect(url_for('labnames'))

if __name__ == '__main__':
    app.run(debug=True)
