# 🛠️ Annotator Pro: Wiki Teknis & Dokumen Handover Developer

Selamat datang di Dokumentasi Teknis Utama untuk **Annotator Pro**. Dokumen ini ditulis khusus untuk membantu pengembang (*developer*) memahami arsitektur, skema basis data, mesin percakapan (*conversation state*), integrasi API AI, sistem manajemen kesalahan (*fault tolerance*), dan prosedur penyebaran (*deployment*) pada peladen produksi (VPS).

---

## 1. Ringkasan Arsitektur Sistem

Annotator Pro dirancang sebagai bot Telegram asinkron menggunakan pustaka `python-telegram-bot` (PTB) v20.x, didukung oleh ORM `SQLModel` (di atas SQLAlchemy & `asyncpg` untuk PostgreSQL).

```mermaid
graph TD
    User([Telegram User]) <-->|HTTPS Webhook / Polling| TelegramAPI[Telegram API Server]
    TelegramAPI <-->|JSON Updates| BotEngine[bot.py: Telegram Bot Application]
    
    subgraph Bot Layer
        BotEngine -->|State Management| ConversationHandlers[handlers/*.py]
        ConversationHandlers -->|Session Context| DatabaseService[user_service.py]
    end

    subgraph Service & I/O Layer
        DatabaseService <-->|Async Pool| PostgreSQL[(PostgreSQL Database)]
        ConversationHandlers -->|Async AI Evaluator| EvaluationCoordinator[services/evaluation.py]
        EvaluationCoordinator <-->|Retry Loops / Semaphores| AIClient[kie_api.py]
    end

    subgraph External AI Services
        AIClient <-->|HTTPS API| KieAI[Kie.ai Gateway]
        AIClient <-->|HTTPS API| OpenRouter[OpenRouter Gateway]
    end
```

### Karakteristik Desain Utama
*   **Asynchronous-First**: Seluruh operasi I/O (jaringan API Telegram, pemanggilan AI, dan akses basis data) bersifat non-blocking menggunakan pustaka `asyncio` Python.
*   **Billing System Terintegrasi**: Setiap interaksi AI dievaluasi harganya secara dinamis berdasarkan model yang digunakan dan tingkat kesulitan tugas. Saldo dipotong langsung dari basis data pasca evaluasi sukses.
*   **Fault-Tolerant Database**: Koneksi database menggunakan pooling tangguh dengan mekanisme pengecekan koneksi hidup (*pre-ping*) untuk kompatibilitas penuh dengan sistem pooling external (seperti PgBouncer).

---

## 2. Diagram Alur State Percakapan (Conversation State Machine)

Bot ini menggunakan modul `ConversationHandler` dari `python-telegram-bot` untuk mempertahankan status interaksi pengguna selama proses pengumpulan data input evaluasi yang bertahap.

```mermaid
stateDiagram-v2
    [*] --> START
    START --> LANGUAGE_SELECT : User mengirim /start atau /mulai
    LANGUAGE_SELECT --> MAIN_MENU : Memilih ID atau EN
    
    MAIN_MENU --> SELECT_PROJECT : Menekan Tombol Proyek
    SELECT_PROJECT --> SELECT_TASK : Memilih Proyek (e.g. CHERRY_OPAL)
    SELECT_TASK --> MAIN_MENU : Memilih Tugas Aktif
    
    MAIN_MENU --> START_EVALUATION : Menekan Tombol "Mulai Evaluasi"
    
    state START_EVALUATION {
        [*] --> COLLECT_PROMPT : Menampilkan deskripsi input
        COLLECT_PROMPT --> COLLECT_RESP_A : User mengirim Prompt Asli
        COLLECT_PROMPT --> MAIN_MENU : User menekan Batal
        
        COLLECT_RESP_A --> COLLECT_RESP_B : User mengirim Respons A / skip
        COLLECT_RESP_B --> COLLECT_RESP_C : User mengirim Respons B / skip
        COLLECT_RESP_C --> PROCESSING : User mengirim Respons C / skip
        
        PROCESSING --> SUCCESS : AI merespons sukses
        PROCESSING --> ERROR_FALLBACK : AI timeout atau error
    }
    
    SUCCESS --> MAIN_MENU : Menampilkan hasil evaluasi & memotong saldo
    ERROR_FALLBACK --> MAIN_MENU : Pesan error ditampilkan & saldo di-refund
```

### Transisi State & Auto-Recovery
Apabila terjadi pengecualian (*exception*) tak terduga di tengah-tengah transaksi state percakapan:
1.  **Global Exception Interceptor** di `bot.py` akan menangkap *exception* tersebut.
2.  Data sesi internal yang macet akan dibersihkan secara otomatis (`context.user_data.clear()`).
3.  Pembatas kecepatan (*rate limit key*) dihapus agar pengguna tidak tersangkut.
4.  Pengguna diberi arahan untuk mengetik `/start` kembali yang berfungsi memetakan ulang seluruh handler per sesi pengguna dari awal.

---

## 3. Skema Basis Data & Model ORM (`models.py`)

Aplikasi menggunakan SQLModel untuk mendefinisikan tabel relasional. Skema aslinya terbagi menjadi 5 entitas utama:

### A. Tabel `users` (`User`)
Menyimpan profil, bahasa terpilih, saldo kredit, dan state operasional pengguna.
*   `user_id` (BigInteger, Primary Key): ID unik pengguna dari Telegram.
*   `username` (String, Nullable): Username Telegram pengguna.
*   `balance` (Integer, Default: 500): Saldo poin/kredit pengguna untuk mengakses AI.
*   `is_registered` (Boolean, Default: False): Menandakan apakah pengguna sudah terdaftar di sistem.
*   `selected_lang` (String, Default: "ID"): Pilihan bahasa antarmuka ("ID" atau "EN").
*   `selected_project` (String, Nullable): Kode proyek aktif terpilih (e.g. "CHERRY_OPAL").
*   `selected_task` (String, Default: "PR"): Kode jenis tugas aktif yang dievaluasi.
*   `selected_tier` (String, Default: "BASIC"): Tingkat akun pengguna ("BASIC" atau "PREMIUM").

### B. Tabel `projects` (`Project`)
Menyimpan daftar nama proyek anotasi yang terdaftar di bot.
*   `code` (String, Primary Key): Kode unik proyek (e.g., "CHERRY_OPAL").
*   `name` (String): Nama tampilan proyek di menu Telegram.

### C. Tabel `tasks` (`Task`)
Menghubungkan tugas-tugas evaluasi spesifik dengan proyek induknya.
*   `id` (Integer, Primary Key): ID tugas otomatis.
*   `project_code` (String, Index): Relasi FK ke tabel `projects.code`.
*   `code` (String): Kode tugas evaluasi (e.g., "PR", "AFM").
*   `name` (String): Nama tampilan jenis tugas.

### D. Tabel `transactions` (`Transaction`)
Pencatatan mutasi kredit pengguna baik untuk pengisian saldo (*top-up*) maupun pemotongan biaya AI (*deduction*).
*   `id` (Integer, Primary Key): ID transaksi otomatis.
*   `user_id` (BigInteger, Index): Relasi FK ke tabel `users.user_id`.
*   `amount` (Integer): Jumlah nominal poin. Positif untuk top-up, negatif untuk pengurangan.
*   `type` (String): Kategori transaksi ("deduction" atau "topup").
*   `task_type` (String): Tipe tugas yang diakses.
*   `model_used` (String): Engine AI yang mengeksekusi request.
*   `timestamp` (DateTime dengan Timezone UTC).

### E. Tabel `evaluations` (`Evaluation`)
Riwayat hasil analisis evaluasi model AI yang berhasil diproses.
*   `id` (Integer, Primary Key): ID evaluasi otomatis.
*   `user_id` (BigInteger, Index): Relasi ke tabel `users.user_id`.
*   `task_code` (String): Kode tipe tugas (e.g., "PR", "VCG_EDIT").
*   `user_input` (String): Teks input asli yang digabungkan dari pengguna.
*   `ai_output` (String): Hasil analisis terperinci yang dihasilkan oleh engine AI.
*   `feedback` (String, Nullable): Umpan balik pengguna ("positive", "negative", atau `None`).
*   `timestamp` (DateTime dengan Timezone UTC).

---

## 4. Integrasi AI Engine & Kontrol Konkurensi (`kie_api.py`)

Annotator Pro mengintegrasikan sistem multi-engine AI yang fleksibel dengan pembagian gerbang lalu lintas antara **Kie.ai Gateway** dan **OpenRouter Gateway**.

```
                           +------------------------+
                           |  kie_api.py Evaluator  |
                           +------------------------+
                                       |
                   +-------------------+-------------------+
                   | (Global Semaphore: Limit 10 requests) |
                   v                                       v
         +------------------+                    +--------------------+
         |  Kie.ai Engine   |                    | OpenRouter Engine  |
         +------------------+                    +--------------------+
         | - Base: DeepSeek |                    | - Failover Backoff |
         | - Direct Request |                    | - Exponential Loop |
         +------------------+                    +--------------------+
```

### A. Kontrol Konkurensi Tinggi (Global Semaphore)
Untuk mencegah lonjakan request konkuren (*thundering herd*) yang dapat memicu pembatasan kecepatan (HTTP 429) dari server API utama, `kie_api.py` membatasi request aktif ke server maksimal **10 request konkuren** menggunakan Semaphore:
```python
_LLM_SEMAPHORE = asyncio.Semaphore(10)

async with _LLM_SEMAPHORE:
    # Eksekusi request API eksternal
```

### B. Mekanisme Retry & Exponential Backoff pada OpenRouter
Fungsi `call_openrouter_api` dan `call_openrouter_api_multimodal` dilengkapi dengan perlindungan transit tangguh:
```python
MAX_RETRIES = 2
RETRY_DELAY = 2.0  # detik

for attempt in range(MAX_RETRIES + 1):
    try:
        # Eksekusi request HTTP ke OpenRouter...
        return response
    except Exception as e:
        if attempt == MAX_RETRIES:
            raise e
        # Jeda bertambah secara eksponensial (2s, 4s)
        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
```

### C. Alur Dynamic Token Pricing & Balance Deduction
1.  **Harga Statis/Dinamis**: `services/evaluation.py` membaca `selected_tier` pengguna.
2.  **Pra-Verifikasi**: Sistem memanggil `check_balance` sebelum request dikirim ke AI. Jika saldo tidak cukup, request langsung dibatalkan sebelum membebani API eksternal.
3.  **Eksekusi & Pasca-Deduction**: Begitu respons sukses dari `kie_api.py` diterima, bot memanggil `deduct_balance` di basis data. Jika AI gagal/down, saldo **tidak akan dipotong** (sistem refund otomatis).

---

## 5. Sistem Ketangguhan Kesalahan (Fault Tolerance & Error Handling)

### A. Penanganan Global Exception di `bot.py`
Terdapat modul penangkap kesalahan terpusat yang didaftarkan ke aplikasi Telegram:
```python
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 1. Log detail error ke file internal
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # 2. Bebaskan rate limit agar pengguna tidak tersangkut
    if context.user_data and "last_request_time" in context.user_data:
        context.user_data.pop("last_request_time")
        
    # 3. Kirim pesan ramah pengguna jika update valid
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            text="⚠️ **Terjadi Kesalahan Sistem** 🚦\n\n"
                 "Mohon maaf, sistem mengalami gangguan teknis tidak terduga saat memproses perintah Anda.\n\n"
                 "**Solusi:**\n"
                 "1. Ketik /start untuk memuat ulang percakapan.\n"
                 "2. Jika terus berlanjut, hubungi Admin."
        )
```

### B. Database Query Protection
Seluruh pemanggilan pembacaan data di `user_service.py` dibungkus dengan blok `try-except` ketat untuk menjamin ketersediaan layanan (*high-availability*):
*   Fungsi seperti `get_projects()` akan mengembalikan list kosong `[]` saat basis data terputus, menjaga tampilan antarmuka bot tetap berjalan daripada melempar halaman *crash* hitam ke ruang obrolan Telegram.
*   Fungsi penulisan data secara otomatis memanggil `await session.rollback()` jika proses `session.commit()` mengalami kegagalan transmisi.

---

## 6. Panduan Deployment & Pemeliharaan VPS

### A. Konfigurasi File Lingkungan (`.env`)
Pastikan file `.env` di VPS terkonfigurasi dengan variabel wajib berikut secara benar:
```ini
# Token API Telegram resmi dari BotFather
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Kunci API pihak ketiga untuk kecerdasan AI
OPENROUTER_API_KEY=your_openrouter_api_key_here
KIE_API_KEY=your_kie_api_key_here

# URL Koneksi PostgreSQL asinkron (menggunakan driver asyncpg)
DATABASE_URL=postgresql://db_user:db_password@localhost:5402/annotator_db

# ID Telegram Admin untuk fitur eksklusif (seperti bypass switch engine)
ADMIN_ID=123456789
```

### B. Setup Service menggunakan PM2 (Rekomendasi Utama)
Gunakan PM2 untuk menjaga proses bot tetap hidup, melakukan restart otomatis saat crash, dan booting ulang otomatis saat server VPS dinyalakan ulang (*reboot*).

1.  **Instalasi PM2 & Setup Startup**:
    ```bash
    sudo npm install -g pm2
    pm2 startup
    # Ikuti petunjuk output di terminal untuk mengaktifkan service PM2 startup!
    ```
2.  **Menjalankan Bot**:
    Masuk ke direktori proyek dan jalankan perintah:
    ```bash
    pm2 start bot.py --name "annotator-bot" --interpreter venv/bin/python3
    ```
3.  **Menyimpan Konfigurasi**:
    ```bash
    pm2 save
    ```

### C. Monitoring & Membaca Log Secara Real-Time
Untuk mendeteksi gangguan atau memeriksa aktivitas pengguna secara langsung saat bot berjalan di latar belakang:
```bash
# Menampilkan logs dari PM2
pm2 logs annotator-bot --lines 100

# Menampilkan statistik performa CPU & Memori bot
pm2 monit

# Membaca log file cadangan lokal
tail -f bot_logs.txt
```

---
> [!NOTE]
> **Catatan Pemeliharaan**: Jika Anda mengganti struktur basis data pada berkas `models.py`, Anda wajib menjalankan naskah migrasi atau menggunakan utilitas pembantu [fix_db.py](file:///media/galangpradhana/DATA/galang/AI%20projek/Aplikasi/annotator-pro/fix_db.py) untuk memperbarui struktur tabel PostgreSQL tanpa menghapus data pengguna yang ada.
