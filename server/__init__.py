from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

app = Flask(__name__)
app.config.from_pyfile('config.py')

db.init_app(app)

import server.views
