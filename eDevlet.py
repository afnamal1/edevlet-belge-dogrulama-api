import base64
import requests
import json
from qrtest import *

base_url = "https://m.turkiye.gov.tr"
api = "/api.php"
p = "?p=belge-dogrulama&"

def getJson(barkod:str,tc) -> dict:
    """
    Barkod numarası ve tckimlik ile apiden dönen jsonu çeker.
    """
    global base_url
    global api
    global p
    qr = f"qr=barkod:{barkod};tckn:{tc}"
    req = base_url + api + p + qr
    print("Json alınıyor")
    #print(req)
    r = requests.get(req)
    return r.json()

def checkValid(barkod:str,tc) -> bool:
    """
    Barkod numarası ve tckimlik ile belgenin geçerli olup olmadığını kontrol eder.
    """
    bilgi = getJson(barkod,tc)
    if bilgi['return'] == False:
        print(bilgi['messageArr'])
        return False
    return True

def checkValidJson(json:dict) -> bool:
    """
    Json ile belgenin geçerli olup olmadığını kontrol eder.
    """
    if json['return'] == False:
        print(json['messageArr'])
        return False
    return True

def getFileJson(json:dict,filename: str = "out" ):
    """
    Json'da base64 kodlanmış belgeyi pdfye çevirir ve kaydeder.
    """
    data = json['data']
    b64Encoded = data['barkodluBelge']
    b64Decoded = base64.b64decode(b64Encoded)
    f = open(f"{filename}.pdf","wb")
    f.write(b64Decoded)
    print(f"{filename}.pdf kaydedildi")
    f.close()

def getFileBarkod(barkod:str,tc,filename:str = "out"):
    """
    Barkod numarası ve tckimlik ile belgenin pdf halini kaydeder.
    """
    bilgi = getJson(barkod,tc)
    #print(bilgi)
    if not checkValidJson(bilgi):
        print("Belge doğrulanamadı")
        print(bilgi['messageArr'])
        return
    getFileJson(bilgi,filename)
    
def parseQRdata(qrData:str) -> dict:
    """
    qrtest.readQR()'den okunmuş qr bilgisini {'barkod':barkod,'tckn':tckn} olarak returnler.
    """
    if qrData == "null":
        raise Exception("QR okunamadı.")
    
    # QR data'yı temizle (bytes string'den normal string'e çevir)
    if qrData.startswith("b'") and qrData.endswith("'"):
        qrData = qrData[2:-1]  # b'...' formatından temizle
    
    # Eğer barkodlubelgedogrulama:// prefix'i varsa (sicil belgesi gibi)
    if "barkodlubelgedogrulama://" in qrData:
        qrData = qrData.replace("barkodlubelgedogrulama://", "")
    
    # URL kısmını temizle (transkript belgesi gibi)
    if "https://" in qrData:
        qrData = qrData.split("https://")[0].rstrip(";")
    
    # Eğer barkod: ve tckn: formatında ise
    if "barkod:" in qrData and "tckn:" in qrData:
        f1 = qrData.index("barkod:") + len("barkod:")
        f2 = qrData.index(";")
        barkod = qrData[f1:f2]
        f1 = qrData.index("tckn:") + len("tckn:")
        # Son noktalı virgülü bul, yoksa string sonuna kadar al
        f2 = qrData.find(";",f1)
        if f2 == -1:
            tckn = qrData[f1:]
        else:
            tckn = qrData[f1:f2]
        return {
            "barkod": barkod,
            "tckn": tckn
        }
    # Eğer sadece barkod numarası ise (askerlik belgesi gibi)
    else:
        # TC kimlik numarası kullanıcıdan istenecek
        barkod = qrData.strip()
        # API için input() yerine exception fırlat
        raise Exception(f"Barkod '{barkod}' için TC kimlik numarası gerekiyor. Bu belge türü için TC kimlik numarası ayrıca gönderilmelidir.")

def getQRdata(file:str = "belge.pdf") -> dict:
    """
    Girilen pdf belgesindeki qr kodunu arar ve bulursa {'barkod':barkod,'tckn':tckn} olarak returnler.
    """
    return parseQRdata(readQRPdf(file))

def getQRdataImg(file:str = "img.jpg") -> dict:
    """
    Girilen resim dosyasında qr kodunu arar ve bulursa {'barkod':barkod,'tckn':tckn} olarak returnler.
    """
    return parseQRdata(readQRImg(file))