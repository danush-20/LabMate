from flask import Flask, render_template
import firebase_admin
from firebase_admin import credentials, db


app = Flask(__name__)
app.secret_key = "mysecretkey"

