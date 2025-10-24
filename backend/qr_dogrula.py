from eDevlet import getQRdata, getFileBarkod, checkValid

def qr_ile_dogrula(pdf_dosyasi="out.pdf"):
    """
    PDF dosyasındaki QR kodu okuyup belgeyi doğrular
    """
    try:
        # PDF'den QR kod bilgilerini al
        qr_data = getQRdata(pdf_dosyasi)
        barkod = qr_data["barkod"]
        tc = qr_data["tckn"]
        
        print(f"QR'dan okunan barkod: {barkod}")
        print(f"QR'dan okunan TC: {tc}")
        
        # Belgeyi doğrula
        if checkValid(barkod, tc):
            print("✅ Belge doğrulandı!")
            
            # Doğrulanmış belgeyi PDF olarak kaydet
            getFileBarkod(barkod, tc, "dogrulanmis_belge")
            return True
        else:
            print("❌ Belge doğrulanamadı!")
            return False
            
    except Exception as e:
        print(f"Hata: {e}")
        return False

if __name__ == "__main__":
    # Mevcut PDF'i doğrula
    qr_ile_dogrula("sicil.pdf")
