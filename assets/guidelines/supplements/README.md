# 📂 Folder: Supplements

Folder ini berisi **file pengetahuan tambahan** per task, seperti hasil QnA dari reviewer,
catatan klarifikasi, atau addendum dari diskusi tim.

File di sini **melengkapi** (bukan mengganti) guideline utama di folder `../`.

---

## 📋 Konvensi Penamaan

Format: `{TASK_CODE}_qna.md` atau `{TASK_CODE}_notes.md`

Contoh:
```
supplements/
├── PR_qna.md                          ← QnA reviewer untuk task Preference Ranking
├── AFM_qna.md                         ← QnA reviewer untuk task AFM Safety
├── TC_PROOFREADING_notes.md           ← Catatan tambahan TC Proofreading
└── TA_INTELLIGENT_POLLS_qna.md        ← QnA reviewer untuk Intelligent Polls
```

---

## 🔧 Cara Mengaktifkan File Baru ke Sistem RAG

1. **Taruh file** di folder ini dengan nama sesuai konvensi di atas.

2. **Daftarkan** ke `ASSET_CONFIGS` di `prompt_assembler.py`:
   ```python
   "PR": {
       "guidelines": "guidelines/pr_preference_ranking.md",
       "supplements": ["guidelines/supplements/PR_qna.md"],  # ← tambahkan di sini
       ...
   }
   ```

3. **Re-index** task tersebut:
   ```bash
   python -m rag.indexer --task PR
   ```

Selesai! Bot akan otomatis menggunakan kedua sumber saat menjawab pertanyaan GL
maupun saat melakukan evaluasi task.

---

## 📌 Format Isi File QnA

Gunakan format Markdown standar dengan heading untuk setiap topik:

```markdown
# QnA Reviewer — Task PR (Preference Ranking)

## Pertanyaan: Kapan harus pilih "Slightly Better" vs "Better"?

**Jawaban:** Gunakan "Slightly Better" jika perbedaannya ada tapi minor...

## Pertanyaan: Bagaimana jika kedua respons sama-sama buruk?

**Jawaban:** Lihat rubrik Tie — kondisi tie berlaku ketika...
```

Chunker akan otomatis memotong berdasarkan heading `##`.
