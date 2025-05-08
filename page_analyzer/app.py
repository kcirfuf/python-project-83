from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import psycopg2


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')

def get_db():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@app.route('/')
def index():
    return render_template('index.html')

