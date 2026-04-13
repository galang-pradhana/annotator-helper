## 2. FORM (PERTANYAAN) - JANGAN UBAH SATU KARAKTER PUN

**Fase 1 - Review Original Input Text**

Could you provide a reason why you want to skip the task?
[] Input text is gibberish or impossible to understand without further context
[] Expertise mismatch
[] Ungradable UI issue
[] The language or content in the input text is not typical of this locale

What is the formality level of the input text?
a. Formal (Government, legal, academic research)
b. Other (Semi-formal, informal, colloquial)

Q1. Does the input text contain errors that hinder comprehension or readability, considering its intended formality level? (Consider only errors that require correction under the minimal edit principle)
a. No errors - The input is appropriately clear and readable for its formality level.
b. Yes - The input contains errors that hinder comprehension or readability.
c. The input is too ambiguous. Cannot assess without additional context.

**Fase 2 - Evaluasi tiap Response (A, B, C)**

Q2. Did the assistant make changes to the input?
a. Yes, the response is different from the input.
b. No, the response is identical to the input.

**Correctness**

[Jika Q1 = a dan Q2 = a]  
Q3. Did any edits alter the original meaning, tone, style, or register?
a. Yes, at least one edit altered the original meaning, tone, style, or register.
b. No, none of the edits altered the original meaning, tone, style, or register.

[Jika Q1 = b dan Q2 = a]  
Q4. Are all the edits in the response necessary?
a. Yes, all edits in the response are necessary.
b. Mixed, only some edits are necessary.
c. No, all edits are unnecessary.

[Jika Q4 = a]  
Q4.1. The following question is for NECESSARY CHANGES ONLY. For the necessary edits only, are they all correct?
a. Yes, all necessary edits are correct.
b. Most necessary edits are correct (80% or more)
c. Only some or few necessary edits are correct (less than 80%)

[Jika Q4.1 = b atau c]  
Q4.1.1. Select all errors appeared in the response.
[] Punctuation
[] Spacing
[] Introduce new errors that alter meanings
[] Impede comprehension
[] Out-of-locale
[] Wrong article/preposition use
[] Voice alteration
[] Formality alteration
[] Word choice alteration
[] Change level of code-switching
[] Register alteration
[] Other

[Jika Q4 = b atau c]  
Q4.2. The following question is for UNNECESSARY CHANGES ONLY.  
Select what best describes the unnecessary edits
a. All unnecessary edits are for minor formatting changes
b. One or more unnecessary edits altered some mechanical aspects
c. One or more unnecessary edits altered the core content, style, or tone.

[Jika Q4.2 = a/b/c]  
Q4.2.1 / Q4.2.2. Select all errors appeared in the response.
[] Punctuation change (that does not touch on syntax, expressivity, or the meaning)
[] Optional capitalization
[] Spacing
[] Mechanical issues (that may affect how a sentence is expressed)
[] Incorrect handling of abbreviations

**Completeness**

[Jika Q1 = b dan Q2 = a]  
Q5. How completely does the response catch all errors that require correction?
a. Complete - Identifies all errors
b. Nearly complete - Misses only a small portion (<20%)
c. Partial - Misses a significant portion (≥20%)
d. Incomplete - Misses most or all errors

[Jika Q5 = b/c/d]  
Q5.1. Categorize the uncorrected or improperly corrected errors in the response
[] Incorrect handling of abbreviations
[] Awkward and unnatural edits
[] Punctuation and formatting issues that do not impede comprehension
[] Punctuation and formatting issues that impede comprehension
[] Common grammatical mix-ups
[] Spelling errors
[] Incorrect word usage that changes meaning or causes grammatical errors
[] Other

[Jika Q1 = c dan Q2 = a]  
Q6. Did any edits alter the original meaning, tone, style, or register?
a. Yes, at least one edit altered the original meaning, tone, style, or register.
b. No, none of the edits altered the original meaning, tone, style, or register.

**Setelah semua jawaban terisi untuk satu response, berikan Grading Summary untuk Response [A/B/C] (WAJIB DIISI)**

**1. Correctness (Kebenaran)**  
Dimensi ini memverifikasi apakah semua perubahan (edit) yang dilakukan oleh asisten sudah diperlukan (necessary) dan benar (correct) sesuai dengan Minimal Edit Principle.  
Skala:  
- Excellent  
- Good  
- Fair  
- Poor  

Kriteria:  
- Necessity: apakah semua edit benar-benar diperlukan (tidak mengubah style, tone, meaning, register).  
- Accuracy: apakah edit yang dilakukan sudah benar atau malah memperkenalkan kesalahan baru.

**2. Completeness (Kelengkapan)**  
Dimensi ini memverifikasi apakah asisten berhasil mendeteksi dan memperbaiki semua kesalahan yang ada pada teks input asli.  
Skala:  
- Excellent  
- Good  
- Fair  
- Poor  

Tingkat Kelengkapan:  
- Complete: mengidentifikasi dan memperbaiki semua kesalahan  
- Nearly Complete: misses <20%  
- Partial: misses ≥20%  
- Incomplete: misses most/all errors  

Catatan penting: Jika asisten memperbaiki semua kesalahan asli tapi memperkenalkan kesalahan baru, tetap beri nilai Complete di Completeness, tapi penalti di Correctness.

**Fase 3 - Pairwise Comparison**
Hanya bandingkan berdasarkan hasil grading summary dari tiap response, tanpa menambah apapun.

A ke B  
How do these two responses compare in terms of overall quality?  
a. A Much Better b. A Slightly Better c. Same d. B Slightly Better e. B Much Better

A ke C  
How do these two responses compare in terms of overall quality?  
a. A Much Better b. A Slightly Better c. Same d. C Slightly Better e. C Much Better

B ke C  
How do these two responses compare in terms of overall quality?  
a. B Much Better b. B Slightly Better c. Same d. C Slightly Better e. C Much Better

Please briefly describe your observations and insights. (Essay dalam bahasa Inggris)

Jelaskan alasan tiap pilihan jawabanmu dalam bahasa Indonesia (1 kalimat yang lengkap dan padat).

d) Justifikasi Draf (Komentar): Buat draf komentar penutup yang logis, profesional, dan berbasis data untuk sistem anotasi dalam bahasa Indonesia dan inggris hanya dalam satu kalimat.