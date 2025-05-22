from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import os
import re
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['invoiceDB']
collection = db['invoices']

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_invoice():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        image = Image.open(filepath)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        return jsonify({"error": f"OCR failed: {str(e)}"}), 500

    amount_match = re.search(r'\$?\s?(\d{1,3}(,\d{3})*(\.\d{2})?)', text)
    due_date_match = re.search(r'(Due Date|DUE|due)[^\d]*(\d{1,2}/\d{1,2}/\d{2,4})', text, re.IGNORECASE)

    vendor = "Unknown"
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if "from" in line.lower():
            if i + 1 < len(lines):
                vendor_line = lines[i + 1].strip()
                vendor = vendor_line.split("INVOICE")[0].strip()
            break

    data = {
        "vendor": vendor,
        "amount": amount_match.group(1) if amount_match else "Unknown",
        "due_date": due_date_match.group(2) if due_date_match else "Unknown",
        "raw_text": text,
        "uploaded_at": datetime.now()
    }

    inserted = collection.insert_one(data)
    data['_id'] = str(inserted.inserted_id)

    return jsonify({"message": "Invoice processed", "data": data}), 200

@app.route('/invoices', methods=['GET'])
def get_invoices():
    invoices = list(collection.find().sort("uploaded_at", -1))
    for invoice in invoices:
        invoice['_id'] = str(invoice['_id'])  # Convert ObjectId to string
    return jsonify(invoices), 200

if __name__ == '__main__':
    app.run(debug=True)

