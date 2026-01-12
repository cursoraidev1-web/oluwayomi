from flask import Blueprint, render_template, request, jsonify, current_app
import os
from .video_processor import process_video_task
import threading

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/process', methods=['POST'])
def process():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Run processing in background to avoid blocking
    thread = threading.Thread(target=process_video_task, args=(url, current_app.config['UPLOAD_FOLDER']))
    thread.start()
    
    return jsonify({'status': 'Processing started', 'url': url})
