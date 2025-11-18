from flask import Flask, request, send_file, jsonify
from flask_cors import CORS  # ← ये ऐड करें
from rembg import remove
from io import BytesIO
import pytesseract  # OCR के लिए - pip install pytesseract
from PIL import Image  # pip install pillow
from pdf2image import convert_from_bytes  # PDF को images में convert करने के लिए - pip install pdf2image
import pandas as pd  # Excel बनाने के लिए - pip install pandas openpyxl

app = Flask(__name__)
CORS(app)  # ← ये ऐड करें – सभी origins allow करेगा

@app.route('/remove-bg', methods=['POST'])
def remove_background():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        input_image = file.read()
        output_image = remove(input_image)
        
        img_io = BytesIO()
        img_io.write(output_image)
        img_io.seek(0)
        
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name='no-background.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/excelconverter', methods=['POST'])
def convert_to_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = file.filename.lower()
    try:
        input_data = file.read()
        
        if any(filename.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
            # Image file
            image = Image.open(BytesIO(input_data))
            text = pytesseract.image_to_string(image)
        elif filename.endswith('.pdf'):
            # PDF file
            pages = convert_from_bytes(input_data)
            text = ''
            for page in pages:
                text += pytesseract.image_to_string(page) + '\n'
        else:
            return jsonify({'error': 'Unsupported file type. Only images (PNG, JPG, etc.) or PDF supported.'}), 400
        
        # Extracted text को lines में split करके simple DataFrame बनाओ (एक column में content)
        # Note: ये basic OCR है। Tables के लिए advanced libs जैसे camelot या tabula-py use कर सकते हो बेहतर results के लिए।
        lines = [line.strip() for line in text.split('\n') if line.strip()]  # Empty lines remove करो
        df = pd.DataFrame(lines, columns=['Extracted Content'])
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='OCR Output')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='converted.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)