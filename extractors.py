"""
extractors.py
Mengambil teks dari berbagai format file.

Setiap extractor mengembalikan list of tuple: (lokasi, teks)
contoh: [("hal. 1", "isi halaman 1"), ("hal. 2", "isi halaman 2")]

Untuk menambah format baru cukup buat fungsi baru dengan decorator @register.
"""

from pathlib import Path

# Registry: ekstensi -> fungsi extractor
EXTRACTORS = {}


def register(*extensions):
    """Decorator untuk mendaftarkan fungsi extractor ke ekstensi tertentu."""
    def wrapper(func):
        for ext in extensions:
            EXTRACTORS[ext.lower()] = func
        return func
    return wrapper


# ---------- OCR (untuk PDF hasil scan dan gambar) ----------

OCR_LANG = "ind+eng"
TESSERACT_WINDOWS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
MIN_TEKS_PDF = 20  # halaman PDF dengan teks kurang dari ini dianggap hasil scan

_ocr_cache = {}


def get_ocr():
    """Siapkan pytesseract. Return None kalau Tesseract belum terinstall."""
    if "engine" in _ocr_cache:
        return _ocr_cache["engine"]

    engine = None
    try:
        import shutil
        import pytesseract

        # Di Windows, Tesseract sering tidak masuk PATH
        if shutil.which("tesseract") is None and Path(TESSERACT_WINDOWS).exists():
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_WINDOWS
        pytesseract.get_tesseract_version()
        engine = pytesseract
    except Exception:
        print("[!] Tesseract belum terinstall, OCR dilewati")

    _ocr_cache["engine"] = engine
    return engine


def ocr_image(img):
    """Jalankan OCR ke objek PIL Image."""
    ocr = get_ocr()
    if ocr is None:
        return ""
    # Pakai bahasa yang tersedia saja (ind dan/atau eng)
    tersedia = ocr.get_languages()
    lang = "+".join(l for l in OCR_LANG.split("+") if l in tersedia) or "eng"
    return ocr.image_to_string(img.convert("L"), lang=lang)


@register(".pdf")
def extract_pdf(path):
    from pypdf import PdfReader

    reader = PdfReader(path)
    hasil = []
    halaman_scan = []
    for i, page in enumerate(reader.pages, start=1):
        teks = page.extract_text() or ""
        if len(teks.strip()) >= MIN_TEKS_PDF:
            hasil.append((f"hal. {i}", teks))
        else:
            halaman_scan.append((i, teks))

    if not halaman_scan:
        return hasil

    # Halaman tanpa teks -> render jadi gambar lalu OCR
    if get_ocr():
        try:
            import pymupdf
        except ImportError:
            import fitz as pymupdf  # versi PyMuPDF lama
        from PIL import Image

        doc = pymupdf.open(path)
        for i, teks_asli in halaman_scan:
            pix = doc[i - 1].get_pixmap(dpi=200)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            teks = ocr_image(img)
            if teks.strip():
                hasil.append((f"hal. {i} (OCR)", teks))
            elif teks_asli.strip():
                hasil.append((f"hal. {i}", teks_asli))
        doc.close()
    else:
        # Tanpa OCR, tetap simpan teks pendek yang ada
        hasil += [(f"hal. {i}", t) for i, t in halaman_scan if t.strip()]
        hasil.sort(key=lambda x: int(x[0].split()[1]))
    return hasil


@register(".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
def extract_image(path):
    from PIL import Image

    with Image.open(path) as img:
        teks = ocr_image(img)
    return [("gambar (OCR)", teks)] if teks.strip() else []


@register(".docx")
def extract_docx(path):
    from docx import Document

    doc = Document(path)
    paragraf = [p.text for p in doc.paragraphs if p.text.strip()]
    # Gabungkan per 10 paragraf supaya lokasi hasil pencarian tetap jelas
    hasil = []
    for i in range(0, len(paragraf), 10):
        bagian = "\n".join(paragraf[i:i + 10])
        hasil.append((f"paragraf {i + 1}", bagian))
    return hasil


@register(".pptx")
def extract_pptx(path):
    from pptx import Presentation

    prs = Presentation(path)
    hasil = []
    for i, slide in enumerate(prs.slides, start=1):
        teks = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                teks.append(shape.text_frame.text)
        gabung = "\n".join(t for t in teks if t.strip())
        if gabung:
            hasil.append((f"slide {i}", gabung))
    return hasil


@register(".txt", ".md", ".py", ".php", ".js", ".html", ".css", ".sql", ".csv")
def extract_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        baris = f.readlines()
    # Gabungkan per 50 baris
    hasil = []
    for i in range(0, len(baris), 50):
        bagian = "".join(baris[i:i + 50])
        if bagian.strip():
            hasil.append((f"baris {i + 1}", bagian))
    return hasil


def extract(path):
    """Ekstrak teks dari satu file. Return [] kalau format tidak didukung atau gagal dibaca."""
    path = Path(path)
    func = EXTRACTORS.get(path.suffix.lower())
    if func is None:
        return []
    try:
        return func(path)
    except Exception as e:
        print(f"[!] Gagal membaca {path.name}: {e}")
        return []


def is_supported(path):
    return Path(path).suffix.lower() in EXTRACTORS


# Testing langsung: python extractors.py materi/namafile.pdf
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Cara pakai: python extractors.py <path_file>")
        print("Format didukung:", ", ".join(sorted(EXTRACTORS)))
        sys.exit()

    for lokasi, teks in extract(sys.argv[1]):
        print(f"--- {lokasi} ---")
        print(teks[:300])
        print()