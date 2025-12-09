python -m jurigged -m onyo_backend

openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 3650 -out certificate.pem -subj "/C=CH/CN=192.168.1.28" -addext "subjectAltName = DNS:localhost"