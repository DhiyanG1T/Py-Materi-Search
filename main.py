"""
main.py
CLI utama Materi Search.

Cara pakai:
  python main.py index materi           -> indeks folder materi
  python main.py search "normalisasi"   -> cari sekali
  python main.py search "sql" -n 5      -> batasi 5 hasil
  python main.py stats                  -> statistik index
  python main.py                        -> mode interaktif
"""

import argparse
import time

from rich.console import Console
from rich.table import Table

from indexer import index_folder, load_index
from search import search, show_results

console = Console()


def cmd_index(args):
    index_folder(args.folder)


def cmd_search(args):
    index = load_index()
    if not index["files"]:
        console.print("[red]Index masih kosong. Jalankan dulu: python main.py index materi[/red]")
        return
    mulai = time.perf_counter()
    hasil = search(args.query, index, limit=args.n)
    durasi = (time.perf_counter() - mulai) * 1000
    show_results(args.query, hasil)
    console.print(f"[dim]Pencarian selesai dalam {durasi:.1f} ms[/dim]")


def cmd_stats(args):
    index = load_index()
    files = index["files"]
    if not files:
        console.print("[red]Index masih kosong.[/red]")
        return

    table = Table(title="Isi Index")
    table.add_column("File", style="green")
    table.add_column("Halaman/Bagian", justify="right")
    for path, data in sorted(files.items()):
        table.add_row(path, str(len(data["chunks"])))
    console.print(table)

    total_chunk = sum(len(d["chunks"]) for d in files.values())
    console.print(
        f"Total file: [bold]{len(files)}[/bold] | "
        f"Total halaman/bagian: [bold]{total_chunk}[/bold] | "
        f"Kata unik: [bold]{len(index['terms'])}[/bold]"
    )


def interactive(folder="materi"):
    console.print("[bold cyan]Materi Search[/bold cyan] - mode interaktif")
    console.print("[dim]Ketik kata kunci untuk mencari. Perintah: :index, :stats, :q (keluar)[/dim]\n")
    index = load_index()

    while True:
        try:
            query = console.input("[bold]cari> [/bold]").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not query:
            continue
        if query in (":q", ":quit", "exit"):
            break
        if query == ":index":
            index = index_folder(folder)
            continue
        if query == ":stats":
            cmd_stats(None)
            continue

        mulai = time.perf_counter()
        hasil = search(query, index)
        durasi = (time.perf_counter() - mulai) * 1000
        show_results(query, hasil)
        console.print(f"[dim]{durasi:.1f} ms[/dim]\n")

    console.print("Sampai jumpa!")


def main():
    parser = argparse.ArgumentParser(description="Mini search engine untuk materi kuliah")
    sub = parser.add_subparsers(dest="command")

    p_index = sub.add_parser("index", help="Indeks folder materi")
    p_index.add_argument("folder", nargs="?", default="materi")
    p_index.set_defaults(func=cmd_index)

    p_search = sub.add_parser("search", help="Cari kata kunci")
    p_search.add_argument("query")
    p_search.add_argument("-n", type=int, default=10, help="Jumlah hasil maksimal")
    p_search.set_defaults(func=cmd_search)

    p_stats = sub.add_parser("stats", help="Tampilkan statistik index")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if args.command is None:
        interactive()
    else:
        args.func(args)


if __name__ == "__main__":
    main()