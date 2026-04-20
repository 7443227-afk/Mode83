from flask import Flask, request, jsonify, render_template
import os
from pathlib import Path
import sys

# Add the path to the directory containing png_parser.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'badge83', 'png-examples')))
from png_parser import inspect_png

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.png'):
        file_path = Path('/tmp') / file.filename
        file.save(file_path)
        report = inspect_png(file_path)
        return jsonify(report), 200
    else:
        return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    app.run(debug=True)