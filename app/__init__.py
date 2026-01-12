from flask import Flask
from threading import Thread
import schedule
import time

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-change-this-in-prod'
    app.config['UPLOAD_FOLDER'] = 'downloads'
    
    from .routes import main
    app.register_blueprint(main)
    
    return app

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)
