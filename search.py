"""
search.py
Mencari di index.json dengan ranking TF-IDF, lalu menampilkan potongan kalimat yang di-highlight.

Contoh query:
  normalisasi database
  normalisasi file:basis        -> hanya cari di file yang path-nya mengandung "basis"
"""

import math
import re

from rich.console import Console
from rich.markup import escape

from indexer import load_index, tokenize

console = Console()

FILTER_PATTERN = re.compile(r"file:(\S+)", re.IGNORECASE)


def parse_query(query):
    """Pisahkan filter file:xxx dari kata kunci biasa."""
    filters = [f.lower() for f in FILTER_PATTERN.findall(query)]
    sisa = FILTER_PATTERN.sub("", query)
    return tokenize(sisa), filters


def get_chunk(index, chunk_id):
    file_path, i = chunk_id.rsplit("::", 1)
    return file_path, index["files"][file_path]["chunks"][int(i)]


def search(query, index=None, limit=10):
    """
    Return list hasil: [(skor, file_path, lokasi, teks), ...] terurut dari skor tertinggi.

    TF-IDF:
      TF  = seberapa sering kata muncul di halaman itu   -> 1 + log(tf)
      IDF = seberapa langka kata itu di seluruh materi    -> log(N / df)
      Kata yang langka tapi sering muncul di satu halaman = skor tinggi.
    """
    if index is None:
        index = load_index()
    kata_query, filters = parse_query(query)
    if not kata_query:
        return []

    terms = index["terms"]
    total_chunk = sum(len(f["chunks"]) for f in index["files"].values())

    skor = {}
    cocok = {}  # berapa kata query yang ditemukan di tiap chunk
    for kata in kata_query:
        postings = terms.get(kata, {})
        if not postings:
            continue
        idf = math.log((total_chunk + 1) / len(postings)) + 1
        for chunk_id, tf in postings.items():
            skor[chunk_id] = skor.get(chunk_id, 0) + (1 + math.log(tf)) * idf
            cocok[chunk_id] = cocok.get(chunk_id, 0) + 1

    hasil = []
    for chunk_id, s in skor.items():
        file_path, chunk = get_chunk(index, chunk_id)
        if filters and not all(f in file_path.lower() for f in filters):
            continue
        # Bonus untuk halaman yang memuat lebih banyak kata query
        s *= cocok[chunk_id] / len(kata_query)
        hasil.append((s, file_path, chunk["lokasi"], chunk["teks"]))

    hasil.sort(key=lambda x: x[0], reverse=True)
    return hasil[:limit]


def make_snippet(teks, kata_query, lebar=90):
    """Ambil potongan teks di sekitar kata pertama yang cocok, lalu beri highlight."""
    teks = re.sub(r"\s+", " ", teks).strip()
    pola = re.compile("|".join(re.escape(k) for k in kata_query), re.IGNORECASE)

    m = pola.search(teks)
    mulai = max(0, m.start() - lebar // 2) if m else 0
    potong = teks[mulai:mulai + lebar * 2]
    awal = "..." if mulai > 0 else ""
    akhir = "..." if mulai + lebar * 2 < len(teks) else ""

    # Escape dulu supaya karakter [ ] di teks tidak dianggap markup rich
    potong = escape(potong)
    potong = pola.sub(lambda x: f"[bold yellow]{x.group(0)}[/bold yellow]", potong)
    return f"{awal}{potong}{akhir}"


def show_results(query, hasil):
    kata_query, _ = parse_query(query)
    if not hasil:
        console.print(f"[red]Tidak ada hasil untuk:[/red] {escape(query)}")
        return

    skor_max = hasil[0][0]
    console.print(f"\n[bold]{len(hasil)} hasil untuk:[/bold] {escape(query)}\n")
    for no, (s, file_path, lokasi, teks) in enumerate(hasil, start=1):
        console.print(
            f"[bold cyan][{no}][/bold cyan] [green]{escape(file_path)}[/green] "
            f"[dim]({lokasi})  skor {s / skor_max:.2f}[/dim]"
        )
        console.print(f"    {make_snippet(teks, kata_query)}\n")


# Testing langsung: python search.py "normalisasi database"
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print('Cara pakai: python search.py "kata kunci"')
        sys.exit()

    q = " ".join(sys.argv[1:])
    show_results(q, search(q))