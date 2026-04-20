from flask import Flask, request, jsonify, render_template
import os
from pathlib import Path
import sys
import logging
import base64

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        logger.debug("No file part")
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        logger.debug("No selected file")
        return jsonify({"error": "No selected file"}), 400
    if file and file.filename.endswith('.png'):
        file_path = Path('/tmp') / file.filename
        file.save(file_path)
        report = inspect_png(file_path)
        
        # Ensure the image data is included in the report
        if 'image_data' in report:
            report['image_data'] = base64.b64encode(open(file_path, "rb").read()).decode('utf-8')
        
        logger.debug(f"Report: {report}")
        return jsonify(report), 200
    else:
        logger.debug("Invalid file format")
        return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    app.run(debug=True)