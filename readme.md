# Materi Search

Mini search engine berbasis Python untuk mencari isi materi kuliah (PDF, PPTX, DOCX, gambar, dan lainnya) langsung dari terminal.

Cukup ketik `normalisasi database`, dan Materi Search akan menampilkan file, halaman atau slide, serta potongan kalimat yang relevan dalam hitungan milidetik. Pencarian ini membaca **isi** file, bukan hanya nama file. PDF hasil scan dan foto catatan juga bisa dicari berkat OCR.

```
$ python main.py search "normalisasi database"

3 hasil untuk: normalisasi database

[1] materi/Basis Data/Pertemuan 5.pdf (hal. 12)  skor 1.00
    ...tujuan normalisasi database adalah mengurangi redundansi data dan...

[2] materi/Basis Data/Slide Normalisasi.pptx (slide 3)  skor 0.74
    Bentuk normal pertama (1NF) pada database relasional...

[3] materi/Catatan/foto_papan_tulis.jpg (gambar (OCR))  skor 0.41
    ...langkah normalisasi: 1NF, 2NF, 3NF...

Pencarian selesai dalam 0.8 ms
```

---

## Daftar Isi

- [Fitur](#fitur)
- [Cara Kerja](#cara-kerja)
- [Struktur Project](#struktur-project)
- [Persyaratan](#persyaratan)
- [Instalasi](#instalasi)
- [Cara Menjalankan](#cara-menjalankan)
- [Format File yang Didukung](#format-file-yang-didukung)
- [Troubleshooting](#troubleshooting)
- [Pengembangan Selanjutnya](#pengembangan-selanjutnya)

---

## Fitur

- **Full-text search**: mencari isi dokumen, bukan hanya nama file.
- **Ranking TF-IDF**: hasil diurutkan berdasarkan relevansi, bukan sekadar urutan file.
- **Lokasi tepat**: menunjukkan halaman (PDF), slide (PPTX), atau paragraf (DOCX) tempat kata kunci ditemukan.
- **Highlight kata kunci** pada potongan kalimat hasil pencarian.
- **OCR**: membaca PDF hasil scan dan foto catatan (`.jpg`, `.png`, dll.) menggunakan Tesseract, dengan dukungan Bahasa Indonesia dan Inggris.
- **Incremental indexing**: hanya file baru atau yang berubah yang diproses ulang, sehingga indexing berikutnya jauh lebih cepat.
- **Filter file**: batasi pencarian ke file tertentu dengan `file:nama`.
- **Mode interaktif**: cari berkali-kali tanpa mengetik ulang perintah.
- **Arsitektur plugin**: menambah format baru cukup dengan menulis satu fungsi.

---

## Cara Kerja

```
  Folder materi/
        |
        v
 [1] extractors.py   ->  Ambil teks dari tiap file (per halaman/slide/paragraf)
        |                PDF scan & gambar -> OCR (Tesseract)
        v
 [2] indexer.py      ->  Pecah teks jadi kata (regex), buang stopword,
        |                bangun inverted index, simpan ke index.json
        v
 [3] search.py       ->  Cocokkan query ke index, hitung skor TF-IDF,
        |                buat snippet + highlight
        v
 [4] main.py         ->  CLI: index, search, stats, mode interaktif
```

**Inverted index** mencatat setiap kata muncul di halaman mana dan berapa kali:

```json
"normalisasi": { "materi/basisdata.pdf::11": 3, "materi/slide.pptx::2": 1 }
```

Karena itu, saat mencari, program tidak perlu membaca ulang file sama sekali, cukup melihat index.

**TF-IDF** menentukan skor relevansi:

- **TF (Term Frequency)**: seberapa sering kata muncul di halaman tersebut.
- **IDF (Inverse Document Frequency)**: seberapa langka kata itu di seluruh materi.

Kata spesifik seperti "normalisasi" mendapat bobot tinggi, sedangkan kata umum seperti "data" mendapat bobot rendah. Halaman yang memuat lebih banyak kata dari query juga mendapat skor tambahan.

---

## Struktur Project

```
materi-search/
├── extractors.py      # Ekstraksi teks per format file + OCR
├── indexer.py         # Tokenisasi, inverted index, simpan/muat index.json
├── search.py          # Pencarian TF-IDF, snippet, highlight
├── main.py            # CLI utama (argparse)
├── requirements.txt   # Daftar library Python
├── .gitignore
├── README.md
├── materi/            # Taruh file materi kuliah di sini (tidak ikut di-push)
└── index.json         # Dibuat otomatis saat indexing (tidak ikut di-push)
```

---

## Persyaratan

- **Python 3.10** atau lebih baru
- **Tesseract OCR** (opsional, hanya untuk PDF hasil scan dan gambar)

Library Python (tercantum di `requirements.txt`):

| Library | Fungsi |
|---|---|
| `pypdf` | Membaca teks dari PDF |
| `python-docx` | Membaca file Word (.docx) |
| `python-pptx` | Membaca file PowerPoint (.pptx) |
| `rich` | Tampilan terminal berwarna dan tabel |
| `pytesseract` | Penghubung Python ke Tesseract OCR |
| `pymupdf` | Mengubah halaman PDF menjadi gambar untuk OCR |
| `pillow` | Memproses gambar |

---

## Instalasi

### 1. Clone repository

```bash
git clone https://github.com/DhiyanG1T/materi-search.git
cd materi-search
```

### 2. Buat dan aktifkan virtual environment

**Windows (PowerShell / terminal VS Code):**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

Jika berhasil, akan muncul `(venv)` di awal baris terminal.

> Di Windows, jika muncul error *"running scripts is disabled on this system"*, jalankan perintah ini sekali, lalu aktifkan ulang venv:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 3. Install library Python

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR (opsional)

Langkah ini hanya diperlukan jika ingin membaca **PDF hasil scan** atau **gambar**. Tanpa Tesseract, file lain tetap bisa diindeks seperti biasa.

**Windows:**

1. Download installer dari [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2. Saat instalasi, pada bagian **Additional language data**, centang **Indonesian**.
3. Gunakan lokasi instalasi default: `C:\Program Files\Tesseract-OCR`. Program akan menemukannya secara otomatis.

**macOS:**

```bash
brew install tesseract tesseract-lang
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt install tesseract-ocr tesseract-ocr-ind
```

Cek instalasi:

```bash
tesseract --version
```

### 5. Siapkan folder materi

Buat folder `materi` lalu salin file materi kuliah ke dalamnya. Subfolder juga didukung, misalnya:

```
materi/
├── Basis Data/
│   ├── Pertemuan 1.pdf
│   └── Slide Normalisasi.pptx
└── Statistik/
    ├── Modul Statistik.docx
    └── foto_papan_tulis.jpg
```

---

## Cara Menjalankan

> Pastikan virtual environment sudah aktif (`(venv)` muncul di terminal) sebelum menjalankan perintah apa pun.

### 1. Indexing materi

```bash
python main.py index materi
```

Contoh output:

```
[+] Mengindeks materi/Basis Data/Pertemuan 1.pdf
[+] Mengindeks materi/Basis Data/Slide Normalisasi.pptx
[+] Mengindeks materi/Statistik/foto_papan_tulis.jpg

Selesai dalam 4.21 detik
Baru/berubah: 3 | Tidak berubah: 0 | Dihapus: 0
Total file: 3 | Total kata unik: 1842
```

Jalankan perintah ini lagi setiap kali menambah, mengubah, atau menghapus file di folder `materi`. File yang tidak berubah akan otomatis dilewati.

### 2. Mencari

```bash
python main.py search "normalisasi database"
```

Batasi jumlah hasil dengan `-n`:

```bash
python main.py search "uji hipotesis" -n 5
```

Batasi pencarian ke file tertentu dengan `file:` (cukup sebagian nama file atau folder):

```bash
python main.py search "normalisasi file:basis"
python main.py search "regresi file:statistik"
```

### 3. Mode interaktif

Jalankan tanpa argumen:

```bash
python main.py
```

```
Materi Search - mode interaktif
Ketik kata kunci untuk mencari. Perintah: :index, :stats, :q (keluar)

cari> normalisasi
cari> distribusi normal file:statistik
cari> :q
```

| Perintah | Fungsi |
|---|---|
| `kata kunci` | Mencari |
| `:index` | Indexing ulang folder `materi` |
| `:stats` | Menampilkan isi index |
| `:q` | Keluar |

### 4. Melihat statistik index

```bash
python main.py stats
```

Menampilkan tabel berisi semua file yang terindeks, jumlah halaman/bagian per file, dan total kata unik.

### 5. Mengetes satu file

Berguna untuk mengecek apakah teks sebuah file berhasil dibaca:

```bash
python extractors.py "materi/Basis Data/Pertemuan 1.pdf"
```

> **Penting:** jika nama file atau folder mengandung spasi, bungkus path dengan tanda kutip (`"..."`).

### Ringkasan perintah

| Perintah | Fungsi |
|---|---|
| `python main.py index materi` | Indexing folder materi |
| `python main.py search "kata kunci"` | Mencari |
| `python main.py search "kata kunci" -n 5` | Mencari, maksimal 5 hasil |
| `python main.py search "kata file:nama"` | Mencari di file tertentu |
| `python main.py` | Mode interaktif |
| `python main.py stats` | Statistik index |
| `python main.py --help` | Bantuan |
| `python extractors.py "path/file"` | Tes ekstraksi satu file |

---

## Format File yang Didukung

| Kategori | Ekstensi | Lokasi hasil |
|---|---|---|
| PDF | `.pdf` | `hal. N` atau `hal. N (OCR)` untuk halaman hasil scan |
| PowerPoint | `.pptx` | `slide N` |
| Word | `.docx` | `paragraf N` |
| Gambar (OCR) | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.webp` | `gambar (OCR)` |
| Teks & kode | `.txt`, `.md`, `.csv`, `.py`, `.php`, `.js`, `.html`, `.css`, `.sql` | `baris N` |

Format lama `.doc` dan `.ppt` belum didukung. Simpan ulang sebagai `.docx`/`.pptx` terlebih dahulu.

### Menambah format baru

Cukup tambahkan satu fungsi di `extractors.py` dengan decorator `@register`:

```python
@register(".xlsx")
def extract_xlsx(path):
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True)
    hasil = []
    for sheet in wb.worksheets:
        teks = "\n".join(
            " ".join(str(c) for c in row if c is not None)
            for row in sheet.iter_rows(values_only=True)
        )
        hasil.append((f"sheet {sheet.title}", teks))
    return hasil
```

Setiap extractor mengembalikan list `(lokasi, teks)`. Bagian lain program tidak perlu diubah.

---

## Troubleshooting

| Masalah | Solusi |
|---|---|
| `ModuleNotFoundError: No module named ...` | Virtual environment belum aktif atau library belum terinstall. Aktifkan venv lalu jalankan `pip install -r requirements.txt`. |
| `running scripts is disabled on this system` | Jalankan `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, lalu aktifkan ulang venv. |
| File tidak ditemukan padahal ada | Nama file/folder mengandung spasi. Bungkus path dengan tanda kutip: `"materi/nama file.pdf"`. |
| `[!] Tesseract belum terinstall, OCR dilewati` | Install Tesseract (lihat [Instalasi langkah 4](#4-install-tesseract-ocr-opsional)). Jika diinstall di lokasi lain, ubah `TESSERACT_WINDOWS` di `extractors.py`. |
| `Index masih kosong` | Jalankan `python main.py index materi` terlebih dahulu. |
| Hasil OCR kurang akurat | Gunakan scan/foto yang jelas, tegak, dan beresolusi cukup. Tulisan tangan umumnya kurang akurat. |
| Indexing pertama lama | Wajar untuk PDF scan karena OCR memproses sekitar 1–3 detik per halaman. Indexing berikutnya hanya memproses file baru/berubah. |
| VS Code menandai import sebagai error | Tekan `Ctrl+Shift+P` → **Python: Select Interpreter** → pilih interpreter dari folder `venv`. |

---

## Pengembangan Selanjutnya

- [ ] Web UI menggunakan Flask
- [ ] Fuzzy search agar typo tetap menemukan hasil
- [ ] Stemming Bahasa Indonesia (misalnya "menormalisasikan" → "normalisasi")
- [ ] Pencarian frasa persis dengan tanda kutip
- [ ] Dukungan `.xlsx`, `.epub`, dan `.html` dengan pembersihan tag
- [ ] Membuka file langsung dari hasil pencarian

---

## Teknologi

- **Python 3**
- **Regex (`re`)**: tokenisasi, filter `file:`, dan highlight kata kunci
- **File handling (`pathlib`, `json`)**: penelusuran folder, incremental indexing, penyimpanan index
- **`argparse`**: antarmuka command line
- **Tesseract OCR**: pengenalan teks pada gambar

---

Dibuat oleh **Rafi** sebagai project pembelajaran Python, khususnya regex dan file handling.