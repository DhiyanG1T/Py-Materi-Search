"""
indexer.py
Membuat inverted index dari semua file di sebuah folder, lalu menyimpannya ke JSON.

Struktur index.json:
{
  "files":  { "materi/a.pdf": {"mtime": 1731..., "chunks": [{"lokasi": "hal. 1", "teks": "..."}]} },
  "terms":  { "normalisasi": { "materi/a.pdf::0": 3, "materi/b.pptx::2": 1 } }
}
- files : isi teks per file, dipecah per halaman/slide (chunk)
- terms : inverted index, kata -> {id_chunk: jumlah kemunculan}
"""

import json
import re
import time
from collections import Counter
from pathlib import Path

from extractors import extract, is_supported

INDEX_FILE = "index.json"

# Kata umum yang tidak berguna untuk pencarian
STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk", "pada",
    "adalah", "atau", "juga", "dalam", "tidak", "akan", "oleh", "sebagai", "ada",
    "bisa", "karena", "the", "of", "and", "to", "in", "is", "a", "an", "for", "on",
}

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(teks):
    """Ubah teks jadi list kata: huruf kecil, tanpa tanda baca, tanpa stopword."""
    kata = TOKEN_PATTERN.findall(teks.lower())
    return [k for k in kata if k not in STOPWORDS and len(k) > 1]


def load_index(path=INDEX_FILE):
    if Path(path).exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}, "terms": {}}


def save_index(index, path=INDEX_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)


def build_terms(files):
    """Bangun ulang inverted index dari semua chunk."""
    terms = {}
    for file_path, data in files.items():
        for i, chunk in enumerate(data["chunks"]):
            chunk_id = f"{file_path}::{i}"
            for kata, jumlah in Counter(tokenize(chunk["teks"])).items():
                terms.setdefault(kata, {})[chunk_id] = jumlah
    return terms


def index_folder(folder, index_path=INDEX_FILE):
    """
    Indeks semua file yang didukung di folder (termasuk subfolder).
    Hanya file baru/berubah yang diekstrak ulang (dicek dari waktu modifikasi).
    """
    mulai = time.time()
    index = load_index(index_path)
    files = index["files"]

    ditemukan = set()
    baru, dilewati = 0, 0

    for path in Path(folder).rglob("*"):
        if not path.is_file() or not is_supported(path):
            continue

        key = path.as_posix()
        ditemukan.add(key)
        mtime = path.stat().st_mtime

        # Lewati file yang tidak berubah sejak indexing terakhir
        if key in files and files[key]["mtime"] == mtime:
            dilewati += 1
            continue

        print(f"[+] Mengindeks {key}")
        chunks = [{"lokasi": lok, "teks": teks} for lok, teks in extract(path)]
        files[key] = {"mtime": mtime, "chunks": chunks}
        baru += 1

    # Hapus file yang sudah tidak ada di folder
    dihapus = [k for k in files if k.startswith(Path(folder).as_posix()) and k not in ditemukan]
    for k in dihapus:
        print(f"[-] Menghapus {k} dari index")
        del files[k]

    index["terms"] = build_terms(files)
    save_index(index, index_path)

    print(f"\nSelesai dalam {time.time() - mulai:.2f} detik")
    print(f"Baru/berubah: {baru} | Tidak berubah: {dilewati} | Dihapus: {len(dihapus)}")
    print(f"Total file: {len(files)} | Total kata unik: {len(index['terms'])}")
    return index


# Testing langsung: python indexer.py materi
if __name__ == "__main__":
    import sys

    folder = sys.argv[1] if len(sys.argv) > 1 else "materi"
    index_folder(folder)