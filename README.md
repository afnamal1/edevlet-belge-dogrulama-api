# eDevlet Belge Doğrulama API

eDevlet belgelerindeki QR kodları okuyarak belgelerin doğruluğunu kontrol eden REST API.

## Özellikler

- PDF ve resim dosyalarından QR kod okuma
- eDevlet API'si ile belge doğrulama
- Doğrulanmış belgeleri PDF olarak döndürme
- Cloud deployment desteği

## API Endpoints

### Sağlık Kontrolü

```
GET /health
```

### Dosya Yükleme

```
POST /upload
Content-Type: multipart/form-data
file: [dosya]
```

### Belge Doğrulama

```
POST /verify
Content-Type: application/json
{
    "file_id": "uploaded_file_id"
}
```

### Direkt Doğrulama

```
POST /verify-direct
Content-Type: multipart/form-data
file: [dosya]
```

## Desteklenen Formatlar

- PDF (.pdf)
- Resim dosyaları (.png, .jpg, .jpeg)

## Deployment

### Railway.app

```bash
git clone <repository>
cd <repository>
# Railway.app'e GitHub repository bağlayın
```

### Docker

```bash
docker build -t edevlet-api .
docker run -p 5000:5000 edevlet-api
```

## Lisans

MIT License
