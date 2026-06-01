import asyncio
import sys
import os

# Tambahkan root project ke sys.path agar bisa import dari parent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from prompt_assembler import ASSET_CONFIGS
from rag import vector_store
from rag.indexer import index_all, show_stats

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

async def main():
    print(f"{BOLD}{BLUE}============================================================{RESET}")
    print(f"{BOLD}{BLUE}🌟 ANNOTATOR PRO — INTERACTIVE RAG INDEX ASSISTANT{RESET}")
    print(f"{BOLD}{BLUE}============================================================{RESET}")
    print("Membantu Anda mengindeks guideline per task secara aman agar laptop tidak freeze.\n")

    while True:
        # Fetch stats
        stats = await vector_store.stats()
        by_task = stats.get("by_task", {})

        print(f"{BOLD}Daftar Task & Status Indeks Saat Ini:{RESET}")
        tasks = list(ASSET_CONFIGS.keys())
        for idx, task in enumerate(tasks, 1):
            count = by_task.get(task, 0)
            status = f"{GREEN}✓ {count} chunks{RESET}" if count > 0 else f"{RED}✗ Belum Diindeks{RESET}"
            print(f"  [{idx:2d}] {BOLD}{task:<40}{RESET} : {status}")

        print(f"\n{BOLD}Menu Pilihan:{RESET}")
        print(f"  [1] Indeks satu task spesifik")
        print(f"  [2] Indeks semua task yang belum diindeks secara otomatis (dengan jeda aman)")
        print(f"  [3] Hapus semua indeks lama (Clear All)")
        print(f"  [4] Tampilkan detail statistik")
        print(f"  [5] Keluar")

        try:
            choice = input(f"\nMasukkan pilihan Anda (1-5): ").strip()
        except KeyboardInterrupt:
            print("\nSampai jumpa!")
            break

        if choice == "1":
            try:
                task_idx = int(input(f"Masukkan nomor task (1-{len(tasks)}): ").strip())
                if 1 <= task_idx <= len(tasks):
                    selected_task = tasks[task_idx - 1]
                    print(f"\n{YELLOW}Memulai indexing untuk task {selected_task}...{RESET}")
                    await index_all(clear_first=False, task_filter=selected_task)
                    print(f"\n{GREEN}Sukses mengindeks {selected_task}!{RESET}")
                    input("\nTekan [Enter] untuk kembali ke menu utama...")
                else:
                    print(f"{RED}Nomor task tidak valid!{RESET}")
            except ValueError:
                print(f"{RED}Input harus berupa angka!{RESET}")
        elif choice == "2":
            print(f"\n{YELLOW}Memulai auto-index untuk task yang belum terindeks...{RESET}")
            pending_tasks = [t for t in tasks if by_task.get(t, 0) == 0]
            if not pending_tasks:
                print(f"{GREEN}Semua task sudah terindeks!{RESET}")
                input("\nTekan [Enter] untuk kembali...")
                continue
            
            print(f"Ditemukan {len(pending_tasks)} task yang belum terindeks.")
            try:
                cooldown = int(input("Masukkan jeda istirahat antar task (dalam detik, default 5): ").strip() or "5")
            except ValueError:
                cooldown = 5

            for idx, task in enumerate(pending_tasks, 1):
                print(f"\n{BOLD}{BLUE}[{idx}/{len(pending_tasks)}] Memproses {task}...{RESET}")
                await index_all(clear_first=False, task_filter=task)
                
                if idx < len(pending_tasks):
                    print(f"\n{YELLOW}Jeda istirahat agar laptop dingin... ({cooldown} detik){RESET}")
                    for sec in range(cooldown, 0, -1):
                        print(f"Menunggu {sec} detik...", end="\r")
                        await asyncio.sleep(1)
                    print("Siap memproses task berikutnya!           ")
            
            print(f"\n{GREEN}🎉 Semua pending task telah sukses diindeks!{RESET}")
            input("\nTekan [Enter] untuk kembali ke menu utama...")
        elif choice == "3":
            confirm = input(f"{RED}{BOLD}Apakah Anda yakin ingin menghapus SEMUA indeks di DB? (y/n): {RESET}").strip().lower()
            if confirm == "y":
                print(f"\n{YELLOW}Menghapus semua data...{RESET}")
                deleted = await vector_store.clear_all()
                print(f"{GREEN}Sukses menghapus {deleted} chunks!{RESET}")
            input("\nTekan [Enter] untuk kembali...")
        elif choice == "4":
            await show_stats()
            input("Tekan [Enter] untuk kembali...")
        elif choice == "5":
            print("Keluar dari RAG Assistant. Sampai jumpa!")
            break
        else:
            print(f"{RED}Pilihan tidak valid!{RESET}")
        print("\n" + "-" * 60 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKeluar!")
