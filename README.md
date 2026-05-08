# AI Manager Platform (SaaS) 🚀

Platform SaaS mandiri untuk mengelola multi-agent AI secara dinamis menggunakan engine **Ollama** lokal. Platform ini didesain untuk skalabilitas tinggi (Multi-Tenant) yang memungkinkan Anda menjual layanan AI Agent ke partner/klien.

## 🌟 Fitur Utama
- **Multi-Agent Support**: Buat banyak agen (ITCHA, ANE, CS-Support, dll) hanya dengan satu model dasar.
- **Dynamic Prompting**: Ubah identitas dan instruksi agen secara real-time melalui dashboard tanpa perlu build ulang model.
- **RAG (Retrieval-Augmented Generation)**: Upload dokumen (Markdown, PDF, Text) sebagai basis pengetahuan agen.
- **SaaS Logic**:
  - Manajemen Paket (Harga, Limit Agen, Kuota Pesan, Limit Storage).
  - Manajemen Klien/Partner dengan API Key unik.
  - Pelacakan penggunaan (Usage Tracking) secara real-time.
- **API Gateway**: Endpoint tunggal untuk integrasi ke aplikasi luar (Laravel, CI4, Mobile, dll).

## 🛠️ Tech Stack
- **Backend**: Python 3.10+ (Flask Framework)
- **Database**: PostgreSQL (Relational Data & Logs)
- **AI Engine**: Ollama (Running Local llama3.1:8b)
- **Frontend**: HTML5, Vanilla JS, Tailwind CSS (UI Premium & Responsive)
- **Server**: Gunicorn (WSGI HTTP Server)
- **Proxy**: Nginx (Reverse Proxy with SSL Certbot)

## 💻 OS & System Support
- **OS**: Linux (Ubuntu 22.04 LTS sangat direkomendasikan), macOS.
- **Hardware**: Minimal RAM 8GB (untuk running Llama 3.1 8B). Direkomendasikan menggunakan GPU/NPU untuk respons yang lebih cepat.

## 🚀 Cara Instalasi (Self-Hosted)

### 1. Prasyarat
Pastikan Python 3.10 dan PostgreSQL sudah terinstal di server Anda.
```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql postgresql-contrib
```

### 2. Instalasi Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

### 3. Setup Project
```bash
cd /var/www/ai-manager
python3 -m venv venv
source venv/bin/activate
pip install flask flask-sqlalchemy flask-login psycopg2-binary requests werkzeug gunicorn
```

### 4. Konfigurasi Database
Buat database di PostgreSQL:
```sql
CREATE DATABASE ai_manager_db;
GRANT ALL PRIVILEGES ON DATABASE ai_manager_db TO your_user;
```

### 5. Menjalankan Aplikasi
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

## 🔐 Credentials (Internal Access)
> [!IMPORTANT]
> Proyek ini bersifat private. Berikut adalah kredensial default untuk pengembangan:

- **Admin Login**: `https://manager.ai.mobwn.my.id/login`
  - Username: `admin`
  - Password: `admin_password`
- **PostgreSQL Info**:
  - Database: `ai_manager_db`
  - User: `postdefault`
  - Password: `VeryStronGPassWord@9290`

## 📡 API Integration
Kirim request ke gateway:
- **URL**: `https://manager.ai.mobwn.my.id/api/chat`
- **Method**: `POST`
- **Header**: `X-API-KEY: YOUR_CLIENT_KEY`
- **Payload**:
  ```json
  {
    "agent_id": 1,
    "message": "Halo, siapa nama kamu?"
  }
  ```

---
Dibuat dengan ❤️ oleh **Antigravity (AI Assistant)** untuk **Aquarink Project**.
