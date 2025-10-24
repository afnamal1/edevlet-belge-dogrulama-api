from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from eDevlet import getQRdata, getFileBarkod, checkValid, getQRdataImg
import base64
import io
from ocr_comparison import DocumentComparator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

comparator = DocumentComparator()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """API sağlık kontrolü"""
    return jsonify({"status": "healthy", "message": "API çalışıyor"})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Dosya yükleme endpointi"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Dosya bulunamadı"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Dosya seçilmedi"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Desteklenmeyen dosya formatı. PDF, PNG, JPG desteklenir."}), 400
        
        # Güvenli dosya adı oluştur
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        return jsonify({
            "message": "Dosya başarıyla yüklendi",
            "file_id": unique_filename,
            "filename": filename
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Dosya yükleme hatası: {str(e)}"}), 500

@app.route('/verify', methods=['POST'])
def verify_document():
    """Belge doğrulama endpointi"""
    try:
        data = request.get_json()
        
        if not data or 'file_id' not in data:
            return jsonify({"error": "file_id gerekli"}), 400
        
        file_id = data['file_id']
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Dosya bulunamadı"}), 404
        
        # Dosya uzantısına göre QR okuma
        file_ext = file_id.split('.')[-1].lower()
        
        if file_ext == 'pdf':
            qr_data = getQRdata(filepath)
        elif file_ext in ['png', 'jpg', 'jpeg']:
            qr_data = getQRdataImg(filepath)
        else:
            return jsonify({"error": "Desteklenmeyen dosya formatı"}), 400
        
        barkod = qr_data["barkod"]
        tc = qr_data["tckn"]
        
        # Belgeyi doğrula
        is_valid = checkValid(barkod, tc)
        
        result = {
            "file_id": file_id,
            "barkod": barkod,
            "tc_kimlik": tc,
            "is_valid": is_valid,
            "message": "Belge doğrulandı" if is_valid else "Belge doğrulanamadı"
        }
        
        # Eğer belge geçerliyse, doğrulanmış PDF'i oluştur
        if is_valid:
            verified_filename = f"verified_{file_id}"
            verified_filepath = os.path.join(UPLOAD_FOLDER, verified_filename)
            getFileBarkod(barkod, tc, verified_filepath)
            
            # Doğrulanmış PDF'i base64 olarak döndür
            verified_pdf_path = verified_filepath + ".pdf"
            with open(verified_pdf_path, 'rb') as f:
                pdf_data = f.read()
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            result["verified_pdf_base64"] = pdf_base64
            
            # Geçici dosyayı sil
            os.remove(verified_pdf_path)
        
        # Geçici dosyayı sil
        os.remove(filepath)
        
        return jsonify(result), 200
        
    except Exception as e:
        # Hata durumunda geçici dosyayı sil
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({"error": f"Doğrulama hatası: {str(e)}"}), 500

@app.route('/verify-direct', methods=['POST'])
def verify_direct():
    """Direkt dosya yükleme ve doğrulama endpointi"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Dosya bulunamadı"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Dosya seçilmedi"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Desteklenmeyen dosya formatı"}), 400
        
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            file.save(temp_file.name)
            temp_filepath = temp_file.name
        
        try:
            # Dosya uzantısına göre QR okuma
            file_ext = file.filename.split('.')[-1].lower()
            
            if file_ext == 'pdf':
                qr_data = getQRdata(temp_filepath)
            elif file_ext in ['png', 'jpg', 'jpeg']:
                qr_data = getQRdataImg(temp_filepath)
            else:
                return jsonify({"error": "Desteklenmeyen dosya formatı"}), 400
            
            barkod = qr_data["barkod"]
            tc = qr_data["tckn"]
            
            # Belgeyi doğrula
            is_valid = checkValid(barkod, tc)
            
            result = {
                "filename": file.filename,
                "barkod": barkod,
                "tc_kimlik": tc,
                "is_valid": is_valid,
                "message": "Belge doğrulandı" if is_valid else "Belge doğrulanamadı"
            }
            
            # Eğer belge geçerliyse, doğrulanmış PDF'i oluştur
            if is_valid:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as verified_temp:
                    verified_filepath = verified_temp.name
                
                getFileBarkod(barkod, tc, verified_filepath)
                
                # Doğrulanmış PDF'i base64 olarak döndür
                verified_pdf_path = verified_filepath + ".pdf"
                with open(verified_pdf_path, 'rb') as f:
                    pdf_data = f.read()
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                
                result["verified_pdf_base64"] = pdf_base64
                
                # Geçici doğrulanmış dosyayı sil
                os.remove(verified_pdf_path)
            
            return jsonify(result), 200
            
        finally:
            # Geçici dosyayı sil
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        
    except Exception as e:
        return jsonify({"error": f"Doğrulama hatası: {str(e)}"}), 500

@app.route('/verify-with-tc', methods=['POST'])
def verify_with_tc():
    """TC kimlik numarası ile belge doğrulama endpointi"""
    try:
        data = request.get_json()
        
        if not data or 'file_id' not in data or 'tc_kimlik' not in data:
            return jsonify({"error": "file_id ve tc_kimlik gerekli"}), 400
        
        file_id = data['file_id']
        tc_kimlik = data['tc_kimlik']
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Dosya bulunamadı"}), 404
        
        # Dosya uzantısına göre QR okuma
        file_ext = file_id.split('.')[-1].lower()
        
        if file_ext == 'pdf':
            qr_data = getQRdata(filepath)
        elif file_ext in ['png', 'jpg', 'jpeg']:
            qr_data = getQRdataImg(filepath)
        else:
            return jsonify({"error": "Desteklenmeyen dosya formatı"}), 400
        
        barkod = qr_data["barkod"]
        
        # Belgeyi doğrula
        is_valid = checkValid(barkod, tc_kimlik)
        
        result = {
            "file_id": file_id,
            "barkod": barkod,
            "tc_kimlik": tc_kimlik,
            "is_valid": is_valid,
            "message": "Belge doğrulandı" if is_valid else "Belge doğrulanamadı"
        }
        
        # Eğer belge geçerliyse, doğrulanmış PDF'i oluştur
        if is_valid:
            verified_filename = f"verified_{file_id}"
            verified_filepath = os.path.join(UPLOAD_FOLDER, verified_filename)
            getFileBarkod(barkod, tc_kimlik, verified_filepath)
            
            # Doğrulanmış PDF'i base64 olarak döndür
            verified_pdf_path = verified_filepath + ".pdf"
            with open(verified_pdf_path, 'rb') as f:
                pdf_data = f.read()
                pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            result["verified_pdf_base64"] = pdf_base64
            
            # Geçici dosyayı sil
            os.remove(verified_pdf_path)
        
        # Geçici dosyayı sil
        os.remove(filepath)
        
        return jsonify(result), 200
        
    except Exception as e:
        # Hata durumunda geçici dosyayı sil
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({"error": f"Doğrulama hatası: {str(e)}"}), 500

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    """Yüklenen dosyayı indirme endpointi"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "Dosya bulunamadı"}), 404
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": f"İndirme hatası: {str(e)}"}), 500


@app.route('/verify-compare', methods=['POST'])
def verify_compare():
    """Belgeyi doğrula ve OCR ile karşılaştır (tek adımda)"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Dosya bulunamadı"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Dosya seçilmedi"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Desteklenmeyen dosya formatı"}), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            file.save(temp_file.name)
            temp_filepath = temp_file.name
        
        try:
            file_ext = file.filename.split('.')[-1].lower()
            
            if file_ext == 'pdf':
                qr_data = getQRdata(temp_filepath)
            elif file_ext in ['png', 'jpg', 'jpeg']:
                qr_data = getQRdataImg(temp_filepath)
            else:
                return jsonify({"error": "Desteklenmeyen dosya formatı"}), 400
            
            barkod = qr_data["barkod"]
            tc = qr_data["tckn"]
            
            is_valid = checkValid(barkod, tc)
            
            result = {
                "filename": file.filename,
                "barkod": barkod,
                "tc_kimlik": tc,
                "is_valid": is_valid,
                "message": "Belge doğrulandı" if is_valid else "Belge doğrulanamadı"
            }
            
            if is_valid:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as verified_temp:
                    verified_filepath = verified_temp.name
                
                getFileBarkod(barkod, tc, verified_filepath)
                
                verified_pdf_path = verified_filepath + ".pdf"
                with open(verified_pdf_path, 'rb') as f:
                    pdf_data = f.read()
                    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                
                result["verified_pdf_base64"] = pdf_base64
                
                comparison_result = comparator.compare_documents(temp_filepath, pdf_base64, file_ext)
                result["ocr_comparison"] = comparison_result
                
                os.remove(verified_pdf_path)
            else:
                result["ocr_comparison"] = {
                    "error": "Belge doğrulanamadığı için OCR karşılaştırması yapılamadı",
                    "similarity_score": 0.0,
                    "similarity_percentage": 0.0,
                    "is_similar": False,
                    "comparison_status": "BELGE GEÇERSİZ"
                }
            
            return jsonify(result), 200
            
        finally:
            # Geçici dosyayı sil
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        
    except Exception as e:
        return jsonify({"error": f"Doğrulama ve karşılaştırma hatası: {str(e)}"}), 500


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Dosya çok büyük. Maksimum 16MB desteklenir."}), 413

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)