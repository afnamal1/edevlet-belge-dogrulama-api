import cv2
import numpy as np
import fitz
import base64
import io
from PIL import Image
import difflib
from typing import Dict, List, Tuple

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("EasyOCR yüklenemedi. OCR özellikleri devre dışı.")

class DocumentComparator:
    def __init__(self):
        if OCR_AVAILABLE:
         
            self.reader = easyocr.Reader(['tr', 'en'])
        else:
            self.reader = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF'den metin çıkarır"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"PDF metin çıkarma hatası: {e}")
            return ""
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Resim dosyasından OCR ile metin çıkarır"""
        if not OCR_AVAILABLE:
            return "OCR kütüphanesi yüklenemedi"
        
        try:
            results = self.reader.readtext(image_path)
            text = ""
            for (bbox, text_item, confidence) in results:
                if confidence > 0.5:  
                    text += text_item + " "
            return text.strip()
        except Exception as e:
            print(f"OCR metin çıkarma hatası: {e}")
            return ""
    
    def extract_text_from_base64_pdf(self, base64_pdf: str) -> str:
        try:
            pdf_data = base64.b64decode(base64_pdf)
            
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(pdf_data)
                temp_path = temp_file.name
            
            text = self.extract_text_from_pdf(temp_path)
            
            import os
            os.unlink(temp_path)
            
            return text
        except Exception as e:
            print(f"Base64 PDF metin çıkarma hatası: {e}")
            return ""
    
    def extract_text_from_base64_image(self, base64_image: str) -> str:
        """Base64 resim'den OCR ile metin çıkarır"""
        if not OCR_AVAILABLE:
            return "OCR kütüphanesi yüklenemedi"
        
        try:
            image_data = base64.b64decode(base64_image)
            
            image = Image.open(io.BytesIO(image_data))
            
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                image.save(temp_file.name)
                temp_path = temp_file.name
            
            text = self.extract_text_from_image(temp_path)
            
            import os
            os.unlink(temp_path)
            
            return text
        except Exception as e:
            print(f"Base64 resim OCR hatası: {e}")
            return ""
    
    def normalize_text(self, text: str) -> str:
        """Metni normalize eder (küçük harf, boşlukları düzenle)"""
        import re
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        
        logo_patterns = [
            r'fsmseh', r'univ', r'vakif', r'universitesi', r'merkezi',
            r'doga', r'belgelendirme', r'hizmetleri', r'info@', r'www\.',
            r'0216', r'392', r'92', r'32', r'com', r'tr'
        ]
        
        for pattern in logo_patterns:
            text = re.sub(pattern, '', text)
        
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """İki metin arasındaki benzerlik oranını hesaplar"""
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        if not norm_text1 or not norm_text2:
            return 0.0
        
        key_words1 = self.extract_key_words(norm_text1)
        key_words2 = self.extract_key_words(norm_text2)
        
        keyword_similarity = self.calculate_keyword_similarity(key_words1, key_words2)
        
        text_similarity = difflib.SequenceMatcher(None, norm_text1, norm_text2).ratio()
        
        final_similarity = (keyword_similarity * 0.6) + (text_similarity * 0.4)
        
        return final_similarity
    
    def extract_key_words(self, text: str) -> set:
        """Metinden anahtar kelimeleri çıkarır"""
        important_words = [
            'kurs', 'bitirme', 'belgesi', 'kursiyer', 'program', 'sertifika',
            'tc', 'kimlik', 'no', 'seviye', 'beceri', 'gelistirme', 'numara',
            'adi', 'soyadi', 'meslek', 'tehlikeli', 'cok', 'tehlikeli', 'islerde',
            'yuzey', 'temizleme', 'alan', 'metal', 'teknolojisi', 'sure', 'saat',
            'verildigi', 'yer', 'surekli', 'egitim', 'merkezi', 'egitim', 'tarihi',
            'tanzim', 'tarihi'
        ]
        
        words = text.split()
        key_words = set()
        
        for word in words:
            if len(word) > 2:  
                key_words.add(word)
        
        for important_word in important_words:
            if important_word in text:
                key_words.add(important_word)
        
        return key_words
    
    def calculate_keyword_similarity(self, keywords1: set, keywords2: set) -> float:
        """Anahtar kelime setleri arasındaki benzerliği hesaplar"""
        if not keywords1 and not keywords2:
            return 1.0
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def compare_documents(self, original_file_path: str, verified_base64: str, 
                         file_type: str = 'pdf') -> Dict:
        """Orijinal belge ile doğrulanmış belgeyi karşılaştırır (sadece PDF-PDF)"""
        try:
            if file_type.lower() != 'pdf':
                return {
                    "error": "OCR karşılaştırma sadece PDF dosyaları için desteklenmektedir",
                    "similarity_score": 0.0,
                    "similarity_percentage": 0.0,
                    "is_similar": False,
                    "comparison_status": "DESTEKLENMİYOR",
                    "analysis_note": "Resim dosyaları için OCR karşılaştırma desteklenmemektedir"
                }
            
            original_text = self.extract_text_from_pdf(original_file_path)
            
            verified_text = self.extract_text_from_base64_pdf(verified_base64)
            
            similarity = self.calculate_similarity(original_text, verified_text)
            
            key_words1 = self.extract_key_words(self.normalize_text(original_text))
            key_words2 = self.extract_key_words(self.normalize_text(verified_text))
            keyword_similarity = self.calculate_keyword_similarity(key_words1, key_words2)
            
            result = {
                "original_text_length": len(original_text),
                "verified_text_length": len(verified_text),
                "similarity_score": round(similarity, 4),
                "similarity_percentage": round(similarity * 100, 2),
                "keyword_similarity": round(keyword_similarity, 4),
                "keyword_similarity_percentage": round(keyword_similarity * 100, 2),
                "is_similar": similarity > 0.7, 
                "original_text_preview": original_text[:200] + "..." if len(original_text) > 200 else original_text,
                "verified_text_preview": verified_text[:200] + "..." if len(verified_text) > 200 else verified_text,
                "original_keywords": list(key_words1)[:10],  
                "verified_keywords": list(key_words2)[:10],
                "comparison_status": "BELGE BENZER" if similarity > 0.7 else "BELGE FARKLI",
                "analysis_note": "PDF-PDF karşılaştırması - metin katmanlarından okuma"
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Belge karşılaştırma hatası: {str(e)}",
                "similarity_score": 0.0,
                "similarity_percentage": 0.0,
                "is_similar": False,
                "comparison_status": "HATA"
            }
    
    def compare_with_base64_images(self, original_base64: str, verified_base64: str) -> Dict:
        """İki base64 resim'i karşılaştırır"""
        try:
            original_text = self.extract_text_from_base64_image(original_base64)
            verified_text = self.extract_text_from_base64_pdf(verified_base64)
            
            similarity = self.calculate_similarity(original_text, verified_text)
            
            result = {
                "original_text_length": len(original_text),
                "verified_text_length": len(verified_text),
                "similarity_score": round(similarity, 4),
                "similarity_percentage": round(similarity * 100, 2),
                "is_similar": similarity > 0.8,
                "original_text_preview": original_text[:200] + "..." if len(original_text) > 200 else original_text,
                "verified_text_preview": verified_text[:200] + "..." if len(verified_text) > 200 else verified_text,
                "comparison_status": "BELGE BENZER" if similarity > 0.8 else "BELGE FARKLI"
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Resim karşılaştırma hatası: {str(e)}",
                "similarity_score": 0.0,
                "similarity_percentage": 0.0,
                "is_similar": False,
                "comparison_status": "HATA"
            }