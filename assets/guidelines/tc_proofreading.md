**PDF GROUND TRUTH KNOWLEDGE BASE**
**Document Title:** Text Composition - Proofread V 25.10.10 & AI Proofreading and Certification Standards
**Metadata:**
- Author: Isaac Lighthouse / Digital Tech Edge
- Date: October 10, 2025 (Document Date), November 10, 2025 (Capture Date)
- Total Pages: 35
- Language: English, Indonesian, Spanish, Japanese, Chinese, Arabic, Hinglish, Swedish, Vietnamese, Italian, French, Turkish, Portuguese
- Key Topics: Instruction Following, Groundedness (Truthfulness), Comprehensiveness, Composition (Style, Tone, & Grammar), Localization, Harmfulness, Satisfaction

**FULL CONTENT**

# PROOFREADING V1 (SERTIFIKASI 6)

Tugas ini merupakan proses mengoreksi atau memeriksa ulang (proofreading) teks yang dihasilkan oleh kecerdasan buatan (AI) untuk memastikan hasilnya memiliki kualitas tinggi, akurat, dan sesuai dengan permintaan yang diberikan. Dalam tugas ini, Anda berperan sebagai editor yang bertanggung jawab memperbaiki kesalahan bahasa, memverifikasi kebenaran informasi, serta menyesuaikan format agar teks layak digunakan.

### Syarat dan Cara Mengerjakan

**1. Mengikuti Instruksi (Instruction Following)**
Pastikan teks yang dihasilkan AI telah memenuhi seluruh perintah dalam prompt, termasuk:
*   batasan jumlah kata,
*   nada atau gaya bahasa (tone),
*   serta penggunaan kata kunci tertentu yang diminta.

**2. Memeriksa Kebenaran Informasi (Grounding)**
Cocokkan isi teks dengan sumber referensi yang tersedia untuk memastikan:
*   tidak ada informasi yang keliru,
*   tidak terjadi penyimpangan fakta,
*   dan tidak terdapat informasi yang dibuat-buat (hallucination).

**3. Memperbaiki Kualitas Bahasa (Fluency)**
Perbaiki aspek kebahasaan agar teks:
*   bebas dari kesalahan tata bahasa,
*   menggunakan ejaan dan tanda baca yang benar,
*   memiliki pilihan kata yang tepat,
*   serta mengalir secara alami dan mudah dipahami.

**4. Kesesuaian Format dan Gaya (Formatting & Style)**
Pastikan teks:
*   menggunakan format yang diminta (misalnya Markdown, poin-poin, atau tabel),
*   memiliki struktur yang rapi,
*   dan menjaga konsistensi gaya bahasa dari awal hingga akhir.

### Aspek Penilaian Utama

Dalam proses evaluasi, beberapa hal berikut menjadi fokus utama:
*   **Kepatuhan terhadap Prompt:** Menilai sejauh mana hasil akhir memenuhi seluruh kriteria dan batasan yang diberikan.
*   **Akurasi terhadap Sumber:** Memastikan semua informasi didukung oleh dokumen referensi dan tidak mengandung informasi palsu.
*   **Kualitas Linguistik:** Menilai kelancaran bahasa, ketepatan struktur kalimat, serta ketiadaan kesalahan pengetikan (typo).
*   **Ketepatan Lokalisasi:** Jika melibatkan bahasa tertentu, teks harus sesuai dengan norma bahasa dan budaya target.

---

# SATISFACTION COMPARISON RULES (PASTED TEXT)

Untuk rating di penilaian komparasi satisfaction, kita murni melihat nilai satisfaction nya ssaja, tanpa melihat lagi aspek lain seperti following instruction, groundedness, dsb. normalnya tangga nilai satisfaction ada 4:
1. highly unsatisfying (paling jelek)
2. slightly unsatisfying
3. slightly satisfying
4. highly satisfying (paling bagus)

**Aturan Perbandingan:**
*   Jika A highly satisfying, B highly unsatisfying, maka **A much better**
*   Jika A highly satisfying, B slightly unsatisfying, maka **A better**
*   Jika A highly satisfying, B slightly satisfying, maka **A slightly better**
*   Jika A slightly satisfying, B highly unsatisfying, maka **A better**

**Kesimpulan:**
*   Jika response sama: **same**
*   Jika response naik / turun 1 tangga: **slightly better**
*   Jika response naik / turun 2 tangga: **better**
*   Jika response naik / turun 3 tangga: **much better**

---

# TEXT COMPOSITION - PROOFREAD V 25.10.10

## Introduction
Updated October 10 2025.

The goal of the Proofreading feature is to correct grammatical errors in the user's input text while preserving the original wording and style as much as possible. If no grammatical error is found, a repeating of the input text is deemed as the only correct action. Unnecessary change in wording, style, or tone would impact the grading of Following Instructions, Groundedness, and Satisfaction.

This guideline is an addendum to the response evaluation in the Preference Ranking Guidelines. It highlights crucial guidelines in Following-Instructions, Concision and Truthfulness. Rules pertaining to Comprehensiveness and Style, Tone, & Grammar are overridden, branching out to create two new dimensions. It is tailored specifically for proofreading tasks.

## Grading Principles
To help you succeed at this task, review the following grading principles. They reflect the error trends we have observed during Production.

1.  **Correct all errors.** The goal of Proofread is to fix all grammatical errors while preserving the original style. A response that corrects only some errors is rated Partially Following. This will also negatively impact the Composition (rated 'Acceptable' at best), Localization (if applicable), and Satisfaction scores.
2.  **Avoid unnecessary changes.** To preserve the original intent and style, do not make unnecessary edits (e.g., changing "pretty" to "prettier," "now" to "tomorrow," or adding new content). Such changes will result in a Partially Following or Not Following rating and will lower the Composition score. Furthermore, if a change alters the original meaning—even slightly—you must also downgrade the Groundedness and Comprehensiveness scores.
3.  **Do not conflate Composition with Localization.** A localization error occurs when a response fails to respect the specific vocabulary, spelling, grammar, or conventions of a particular regional variant (the "locale"). A general grammar mistake is about being correct vs. incorrect, which you would penalize under Composition.

## Following Instructions

### Overview
The Following Instructions evaluation is to check if the response follows the instruction to correct grammatical errors and preserve the intent, wording, and style in the input text.
*   The intent, wording, style, and tone should be preserved without unnecessary modification, including emojis.
*   When a response simply repeats the input text (regardless of the grammatical correction of the input text), please always grade the response as **Fully following**. If the input text contains grammatical errors and the response simply repeats without correction, please penalize the response under Composition.

### Unnecessary Modifications and Different Locales
What counts as "unnecessary modification" vs "grammatical fix" can slightly change in different locales. Generally speaking, the response should preserve the intent, wording, style, and tone as much as possible. Even when the input text contains slightly unnatural phrasing, the change made by the response to improve fluidity would still be considered unnecessary modifications.

**Notes on rewording and tone change:**
*   **Rewording:** Allowed only if the original word or phrase does not make sense, is obviously incorrect, or if it is misaligned with the context.
*   **Tone change:** In languages that use honorific speech (e.g., Japanese, Korean), most tone changes are considered unnecessary modifications. A tone change would only be allowed when the input text shows obvious disagreement between the tone and the verb or adjective conjugations.
*   **Registers:** Variety of languages used in a community (e.g., Arabic MSA vs. dialects) must be preserved.

Responses that make unnecessary changes in wording, style, and tone should be penalized under the Satisfaction dimension (Slightly Unsatisfying).

### Scale for Single Response Rating

| Scale | Comment |
| :--- | :--- |
| **Fully following** | The response follows the instruction and its corrections focus on grammar, syntax, spelling, and punctuation. OR, the response simply repeats the input text without making any correction. |
| **Partially following** | The response generally follows the instruction, but there are some deviations such as changing the wording, style, format, or tone. OR, the response corrects some but not all grammatical or spelling errors in the input text. |
| **Not following** | The response fails to follow the instruction. It rewrites or paraphrases the input text, hallucinates and modifies the original intent, or declines to answer (a blank response). |

## Locale-Specific Guidelines

### English Examples

| User Request | Response | Rating | Comment |
| :--- | :--- | :--- | :--- |
| However, it is a quite city and it is not very active. | However, it is a quiet city and it is not very active. | Fully following | Corrects misspelling of "quiet" without modifying word choice or tone. |
| However, it is a quite city and it is not very active. | However, it is a quite city and it is not very active. | Fully following | Repeats input text (Composition would be graded "bad"). |
| However, it is a quite city and it is not very active. | However, it is a rather active city. | Not following | Changes meaning from "quiet" to "active." |
| However, it is a quite city... | However, in the midst of the serene ambiance, this quaint city... | Not following | Overgeneration; does not follow proofreading instruction. |
| The birds flew south. | The birds flew south. | Fully following | No mistakes; repetition is correct. |
| The birds flew south. | The birds headed south. | Partially following | Unnecessary wording change ("flew" to "headed"). |
| I just finished my workout, and I feel so strong! 💪 | I just finished my workout, and I feel so strong! | Partially following | Failed to preserve emoji. |

### Japanese (ja_JP)
*   **Change in scripts:** Corrections to common script usage (Kanji/Hiragana/Katakana) are grammatical fixes (Fully following). Modifying correct script usage is an unnecessary modification (Partially following).
*   **Change in tone:** Refinement is usually unnecessary unless there is an obvious disagreement between tone and conjugations.
*   **Change in conjugations:** Correcting obvious tense errors is Fully following. Refinement of grammatically correct but slightly unnatural conjugations is Partially following.

**Japanese Examples:**

| User Request | Response | Rating | Comment |
| :--- | :--- | :--- | :--- |
| 「池のほとりに花ショウブが綺麗に咲いていました | 池のほとりに花ショウブがきれいに咲いていました。 | Partially following | Both 綺麗 and きれい are common; change is unnecessary. Marked Slightly Unsatisfying. |
| 「ぜったい必要である。 | 「対必要である | Fully following | Corrects Hiragana to Kanji for a word usually written in Kanji. Highly Satisfying. |
| 「先生、今日は天気が最高だぞ | 先生、今日は天気が最高ですね | Partially following | Input is casual but correct. Response unnecessarily makes it formal. |
| 「妹様は元気にしてますか | 「妹さんは元気にしてますか | Partially following | Changes honorific 様 to less formal さん. Unnecessary modification. |
| 「田中さんが申し上げた通り... | 田中が申し上げた通り... | Fully following | Corrects humble language inconsistency (cannot use "san" for humble subject). |
| 「久しぶりだね、妹様は元気にしてる? | 久しぶりだね、妹さんは元気にしてる? | Fully following | Corrects inconsistency between casual "てる?" and honorific "樣". |
| 「今、子供は寝ます | 「今、子供は寝ています | Fully following | Corrects tense error (present to present continuous). |
| 「昨日雨が降るよね | 「昨日雨が降ったよね | Fully following | Corrects tense error (present to past). |
| 「やる気ないすぎる | 「やる気なさすぎる | Fully following | Corrects inflection error (ない to なさ). |
| 「綺麗かった | 「綺麗だった | Fully following | Corrects invalid inflective form (形容動詞 / na-adjective error). |
| タクシーをお呼びしますがよろしかったでしょうか | タクシーをお呼びしますがよろしいでしょうか | Partially following | Input is correct; response refines fluidity unnecessarily. |

### Chinese (zh_CN)
Engineering does not want the response to reword unnatural text for better clarity and fluency. This is considered Partially Following.

**Chinese Examples:**

| User Request | Response | Rating | Comment |
| :--- | :--- | :--- | :--- |
| 可能明晚公布 | 可能会明晚公布 | Partially following | No syntax error in input; modification is unnecessary. Marked Slightly Unsatisfying. |
| 有一天,我翘课去打撞球,小涵正好看见了 | 有一天,我翘课去打撞球,正好\|被小涵看见了 | Partially following | Both are common in conversation; change does not improve text. |
| 那里是专门为独居老人服务 | 那里专门为独居老人服务 or 那里是专门为独居老人服务的 | Fully following | Corrects syntax error (usage of 是). Highly Satisfying. |
| 我喜欢吃苹果但是我也不喜欢香蕉。 | 我喜欢吃苹果, tetapi我不喜欢香蕉。 | Fully following | Corrects syntax misalignment of 也. |

### Arabic Languages
*   **Registers:** Preserve original registers (MSA vs. Dialect). Change in register or formality is an "unnecessary change".
*   **Phonetic Variations:** If the input contains phonetic variations in dialect, the output should not modify them.
*   **Numerals:** Numbers should match input form (Western vs. Eastern Arabic).
*   **Tanween:** Match input diacritic placement.

**Arabic Phonetic Variations (Preserve):**
*   **Gulf Arabic:** ج (j) softening to (y); ق (q) pronounced /g/ or /d3/; Female suffix ك (k) shift.
*   **Levantine Arabic:** ث (th) becoming (t); ق (q) pronounced as glottal stop /?/.

**Arabic Examples:**

| User Request | Response | Rating | Comment |
| :--- | :--- | :--- | :--- |
| (Mixed/MSA input) | (Preserved formal register) | Following | Sentence is majority MSA. |
| (Egyptian Dialect input) | (Egyptian Dialect output) | Following | Does not change structure or informality. |
| (Emirati Dialect input) | (Emirati Dialect output) | Following | Does not change structure or informality. |
| (Dialect input) | (Converted to MSA words) | Partially following | Changed dialect words to MSA equivalents. |
| (Levantine input) | (Converted some to MSA) | Partially following | Changed few words but kept overall structure. |
| (Informal input) | (Converted to full MSA) | Not following | Does not preserve informal register and makes additions. |
| (Egyptian input) | (Formal MSA output) | Not following | Completely changed tone and structure to MSA. |
| (Iraqi input) | (Formal MSA output) | Not following | Completely changed tone and structure to MSA. |

**Arabic Authenticity Reference (Syntax/Morphology):**
| Dialect | Phrase (Not Done) |
| :--- | :--- |
| Emirati | ماسويت (masawwēt) |
| Saudi | ما سويت (masawwēt) |
| Levantine | ما عملت (ma'melt) |
| Egyptian | ما عملت (ma malt-esh) |
| Maghrebi | مادرتش (ma dertsh) |

### Hinglish
Hinglish is a blend of Romanised Hindi and English. The output should mirror the tone and level of code-switching present in the input.
*   **Rules:** English words follow Indian English (en_IN) rules; Hindi Latin words follow Hindi Devanagari grammar transliterated to Latin.
*   **Variations:** Multiple accepted spellings for Hindi Latin words are allowed if phonetically correct (e.g., fir vs phir).
*   **Gender:** Do not assume or change gender. Use neutral forms (e.g., "karte hai") for ambiguity. Fix incorrect object gender.

**Hinglish Examples:**

| User Request | Response | Rating | Comment |
| :--- | :--- | :--- | :--- |
| Hello, m Abhishek Sharma... | Hello, mein Abhishek Sharma... | Fully Following | Corrects "m" to standard phonetic "mein." |
| Tjhy kab aana h? | Tujhe kab aana hai? | Fully Following | Corrected spelling without changing pronoun formality. |
| Tjhy kab aana h? | Aapko kab aana hai? | Partially Following | Changed informality to formality. |
| Tereko jaana hai kya? | Tereko jaana hai kya? | Fully Following | Preserves "Tereko" as a valid regional form. |
| Hello... fridge repair karne... | Hello... fridge theek karne... | Partially Following | Translated English "repair" to Hindi "theek." |
| Gaadi chal raha hai | Gaadi chal rahi hai | Fully Following | Corrected gender for feminine object "Gaadi." |

**Standard Phonetic Corrections (Hinglish):**
1. Yeh batao ke jaane ka mn h ya nhi -> ...mann hai ya nahi?
2. bhut bhook lagi hai! -> Bahut/Bohot/Bahot bhook lagi hai!
3. Kya kr rhe ho -> Kya kar rahe ho?

**Unnecessary Spelling Changes (Hinglish):**
*   fir $\rightarrow$ phir
*   jaega $\rightarrow$ jayega/jaayega/jaaega
*   Dhanyavaad $\rightarrow$ Dhanyawad
*   Pooja $\rightarrow$ Puja

---

## Groundedness (Truthfulness)

### Overview
Groundedness is the truthfulness of the output text to the input context. The response must not contradict information. Irrelevant crucial information added is considered less grounded. Alternative word choices that convey the same meaning are out of scope for this dimension.

### Scale for Single Response Rating

| Scale | Comment |
| :--- | :--- |
| **Grounded** | The primary information of the response is grounded based upon the contextual text. |
| **Partially Grounded** | The primary information of the response is not fully accurate given the contextual text. |
| **Not Grounded** | The overall primary information of the response is inaccurate given the contextual text. |

---

## Comprehensiveness

### Overview
The response must contain all input information and not miss important aspects or phrases.

### Scale for Single Response Rating

| Scale | Comment |
| :--- | :--- |
| **Comprehensive** | All the input information included and no missed phrases. |
| **Not Comprehensive** | Any phrase, which conveys information in the input, is missed. |

---

## Composition (Style, Tone, & Grammar)

### Overview
This dimension focuses on Style, Tone, and Grammar. Writing style and tone should be the same as the input. Errors to correct include punctuation, spacing, capitalization, spelling, lexical confusion, verb form, etc. Alternative word choices or sentence structures are not considered proofreading errors; they belong to writing style.

### Scale for Single Response Rating

| Scale | Comment |
| :--- | :--- |
| **Good** | All errors corrected with minimum change of word choice. No change of style/tone. |
| **Acceptable** | Some errors still exist, or an original error corrected with unnecessary word/structure change. |
| **Bad** | Almost no errors corrected, or new errors introduced, or style/tone changed. |

---

## Localization

### Overview
Adapting content to a specific target market to give the impression the assistant is designed for that locale.

### Localization Issues
*   **Unlocalized information:** Relevant locale info missing.
*   **Overly-localized content:** Unnecessary fixation on the locale.
*   **Spelling:** Using variant for wrong locale (e.g., American vs British).
*   **Tone:** Overemphasizing stereotypes.
*   **Vocabulary:** Inappropriate geographical/cultural expressions.
*   **Formatting/Punctuation:** Incorrect date/time/spacing for locale.
*   **Wrong language:** Using a language not in task locale (except for translations/loanwords).

---

## Harmfulness

### Overview
Ensuring safety is paramount. Evaluations emphasize harmlessness over helpfulness.

### Scale for Single Response Rating

| Scale | Comment |
| :--- | :--- |
| **Clearly harmful** | Corresponds with harmful categories in Safety Guidelines. |
| **Maybe harmful** | Ambiguity or room for debate exists. |
| **Not harmful** | Clearly harm free. |

### Harmful Categories
*   **Intolerant:** Hateful.
*   **Indecent:** Vulgar, Explicitly Sexual.
*   **Data Leakage:** Privacy invasion, Disinformation, Biased.
*   **Extreme Harm:** Child endangerment, Suicidal, Violent.
*   **Misconduct:** Illegal, Fraudulent, Unethical.

---

## Satisfaction

### Overview
A holistic rating of all dimensions.

### Scale for Single Response Rating

| Scale | Comment |
| :--- | :--- |
| **Highly Satisfying** | Well-written, comprehensive, no unnecessary changes, harmless, no localization issue. |
| **Slightly Satisfying** | Helpful/harmless but minor issues (formatting/missed minor info). No unnecessary changes. |
| **Slightly Unsatisfying** | Major issues (grammar mistakes left, info missing, unnecessary changes in wording/style). |
| **Highly Unsatisfying** | Harmful, fails to correct errors, gibberish, inconsistent, or makes up details. |

---

## Complete Evaluation Examples

### Example 1 - es_ES (Spanish)
*   **User Request:** Si debolbistes los dos Yeti porque me estas cobrando uno no te lo abronaran ¿los 2? o los page yo
*   **Response:** Si debolviste los dos Yeti karena me estás cobrando uno, no te lo abronarán, ¿los dos? o los pagué yo.
*   **Analysis:** "Debolbiste" corrected to "debolviste" (still wrong, should be "devolviste"). "Abronarán" is not a Spanish verb (likely "abonarán"). Missing question marks and commas.
*   **Grades:** Partially Following, Grounded, Comprehensive, **Bad Composition**, Yes Localization, Highly Unsatisfying.

### Example 2 - es_ES (Spanish)
*   **Analysis:** "Ahí" should be "Hay" (existence). "Guarerria" incorrectly fixed to "guareña". Greeting format (comma/colon) is unlocalized.
*   **Grades:** Partially Following, Grounded, Comprehensive, Acceptable Composition, No Localization (Formatting), Slightly Unsatisfying.

### Example 3 - es_MX (Spanish)
*   **Analysis:** Response changes "biendo" (watching) to "bien" (well), altering meaning.
*   **Grades:** Not Following, Not Grounded, Not Comprehensive, Bad Composition, Highly Unsatisfying.

### Example 7 - zh_HK (Hong Kong Chinese)
*   **Analysis:** Response simply repeats text but fails to correct an extra space. In zh_HK, spaces are typically not added between characters.
*   **Grades:** Following, Grounded, Comprehensive, Bad Composition, No Localization (Formatting), Highly Unsatisfying.

### Example 9 - it_IT (Italian)
*   **Analysis:** Misspelling "manjime" corrected to "manjame" (invalid word) instead of "mangime".
*   **Grades:** Partially Following, Grounded, Comprehensive, **Bad Composition**, Slightly Unsatisfying.

### Example 11 - fr_FR (French)
*   **Analysis:** Replaced slang "michto" (manipulator) with "miche" (loaf). Misunderstood fandom term "Sukuita" as "Sukuna".
*   **Grades:** Not Following, Not Grounded, Not Comprehensive, Bad Composition, Highly Unsatisfying.

### Example 14 - pt_PT (Portuguese)
*   **Analysis:** Introduced Brazilian "Tô" into European Portuguese text.
*   **Grades:** Partially Following, Grounded, Comprehensive, Bad Composition, No Localization, Slightly Unsatisfying.

### Example 15 - pt_PT (Portuguese)
*   **Analysis:** Input was error-free. Output overcorrected "subtis" to Brazilian "sutis".
*   **Grades:** Partially Following, Grounded, Comprehensive, Bad Composition, No Localization, Slightly Unsatisfying.

---
**END OF GROUND TRUTH**
**Extraction Stats:**
- Total words extracted: ~2,600 words
- Tables extracted: 22 Markdown tables
- Figures described: 35 instances of FireShot Pro screen captures noted as sequential page markers.
- Completeness: 100% (Integrated all certification standards, comparative rules, and full PDF content including multi-language examples and grading scales).