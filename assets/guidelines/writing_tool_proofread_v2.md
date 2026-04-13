PDF GROUND TRUTH KNOWLEDGE BASE Document Title: Writing Tool Guidelines - Proofreading V2 Metadata:
Author: Document Intelligence / Writing Tool Design & Engineering Team
Date: v. 2026 Feb. 24 (Updated on 03/09/2026)
Total Pages: 113 Snippets (Includes references up to slide 34 and Appendix)
Language: English (Primary), Korean, Spanish, Vietnamese, Hong Kong Chinese, Hinglish
Key Topics: Minimal Edit Principle, Formality Classification, Error Types (Critical vs. Minor vs. Stylistic), Correctness and Completeness Dimensions, Ambiguity and Informal Context Handling, Locale-Specific Guidelines (Hinglish).
FULL CONTENT
Writing Tool Guidelines- Proofreading V2
v. 2026 Feb. 24 updated on: 03/09/2026
Announcements
v. 2026 Feb. 24 Updates - Please Review
Context: The update of this round is driven by ambiguity that the team has observed in Proofread data and model responses. There was the need to further define error types, and not all types of errors carry the same weight. The updates in the grading questions and guidelines are meant to address the above issues. In the guidelines PDF, graders can find the update summary listed on Page 2.
The part that requires most of their attention is the newly added Step 2 - Classify the formality level of the Input Text. This question is meant for graders to do an assessment. Whether the text is formal or not (informal, casual, etc) will determine the expected model behaviors. Graders must be familiar with different error types (critical/must fix errors, minor errors, and stylistic choice) and how to handle formal vs informal text.
Major updates in this version:
A new step (Step 2): The team has decided to add a new step - Classify the formality level of the Input Text.
Review the types of errors, examples, and how they impact your grading of formal / informal input text.
Step 3 - Assess the input text and the response: The wording of the question is updated. The instructions are streamlined and simplified.
Step 4 - Evaluate Correctness: There are minor updates to some of the follow-up questions. See the updated flow chart.
Step 5 - Evaluate Completeness: There are minor updates to the question, which now has 4 scales to choose from.
Updated Jan. 29: Updated the guidelines for Step 1: Review the Original Input Text to include checking for ambiguity and incomprehensibility in addition to grammatical errors.
Step 2/ Question 1 (for Input Text): The question now asks about both grammatical correctness and clarity, including punctuation. We've also added a third option to indicate if the meaning of the text is completely unclear. New guidelines added to help you assess the level of ambiguity of the input text. We've outlined three scenarios: 1) The entire input is comprehensible, 2) The input contains both comprehensible and ambiguous parts, and 3) The entire input is incomprehensible. Each scenario has specific instructions for how to answer Step2/ Question 1.
Note: The issue about truncated / omitted text (See announcement on Dec. 10) is now fixed.
Updated Dec. 19: We made a minor correction the 2nd example on page 34.
Dec. 10 Special Callouts for Certification
The Proofread feature is designed to process the entire input text without omission. However, in rare cases, you may observe truncated output in the grading UI. In such instances, please assume the assistant found no errors in the omitted portion. In the backend, this means the assistant would return the same text without making any edits. Our engineering team is actively working to resolve this discrepancy, ensuring analysts see the full, unedited text in the frontend.
How to apply this callout to grading? In cases where the assistant omits part of the input (e.g., omitting "Defund the CBC already. Do better. Report real news for hells sakes" from a longer input), in the backend, this omission indicates that the assistant identified no errors in that specific text. Therefore, when grading such cases, please select: "No, the response is identical to the input."
Note: If specific words are marked in "Proposed Edits" while the "Proofread Copy" actually doesn't change anything in the input, please ignore the marking, assume no change made, and proceed to grade.
01 Introduction
The goal of the Proofreading feature is to correct all grammatical errors in the user's input text while preserving the original tone, style, and register as much as possible.
 Your evaluation of the response/output will focus on two dimensions: Correctness and Completeness.
Correctness verifies whether all edits in a response are correct and adhere to the Minimal Edit Principle.
Completeness verifies whether all errors in the input text are detected and corrected properly.
Guideline Learning Path
Minimal Edit Principle
Principles for Handling Ambiguous or Informal Contexts
Workflow
Review the Original Input Text
Classify the formality level of the Input Text
Make an initial assessment of the Input Text and the Response (Proofread Copy)
Evaluate the Correctness of the Response
Evaluate the Completeness of the Response
Compare Responses in Pair
02 Proofreading Grading Principles
I. Minimal Edit Principle
Proofreading edits must be strictly minimal—addressing only grammar, punctuation, capitalization, spelling, or formatting issues as lightly as possible. No changes in the response should alter the meaning, style, tone, register, or intent of the input text.
 Note: Register refers to the level of formality or style of speaking or writing used for a particular purpose or situation.
Rules for Preservation
If any one of the following is violated, you will penalize the response under Correctness dimensions:
Preserve semantic content
Preserve tone, register, style, and formality
Preserve pronoun referentiality
Preserve proper noun referentiality
Preserve expressivity, colloquialisms or slang
Preserve formatting
Preserve Local Punctuations and Formatting
1. Preserve Semantic Content
Does the response maintain the original meaning and intent of the input text without introducing new content or altering expression? Vocabulary, emphasis, and degree must be preserved exactly - even small lexical substitutions (including synonyms) or simplifications count as unnecessary edits.
Violations (bad corrections) include:
"help fix the issue" → "resolve the issue"
"somewhat successful" → "successful"
"most important" → "important"
"kindest regards" → "kind regards"
"saddened to hear" → "sad to hear"
"take part in" → "participate in"
2. Preserve Tone, Register, Style, and Formality
Does the response maintain the same level of formality, politeness, and tone? Respect all relevant linguistic and cultural markers, including: honorifics, verb forms, polite vs. impolite pronouns, formal vs. informal vocabulary, modal verbs, hedging, indirect expressions, sentence structure, polite interjections, and forms of address.
Violations (bad corrections) include:
English: "You should check the report before submitting." → "You must check the report..."
English: "I was wondering if you could send me the report." → "I was wondering if you might send..."
Korean: 수미씨는 요즘 건강이 어떠세요? → 수미씨는 요즘 건강이 어떠니?
Spanish: ¿Tú podrías enviarme el informe mañana? → ¿Usted podría enviarme el informe mañana?
HK Chinese: 你飲咗酒? → 你喝了酒?
Non-violations (desirable corrections):
Korean: 할머님께 선물을 줬어요. → 할머님께 선물을 드렸어요. (Corrects honorific)
Vietnamese: Mai tui ghé → Mai tôi ghé.
Vietnamese: Sách này hay lắm, câu đọc nó belum? → Sách này hay lắm, câu đọc belum? (Correct/remove redundant words)
HK Chinese: 我吃咗藥 → 我食咗藥 (Correcting mismatched informal marker and formal verb)
3. Preserve Pronoun Referentiality
Does the response fully maintain the person, number, or gender features of each pronoun?
Violations: Referential shifts (e.g., "me" → "us", "he" → "she").
Non-violations: Correcting grammatical case errors (e.g., "they" → "them", "you" → "your").
4. Preserve Proper Noun Referentiality
Does the response preserve all proper nouns (people, places, organizations, brands) exactly? Changes to the actual proper noun are prohibited.
Violations: Any modification (e.g., "Paris" → "London", "Sara" → "Sarah").
Non-violations: Case or possessive inflections (e.g., "Sara" → "Sara's").
5. Preserve Expressivity, Colloquialisms, or Slang
The response must retain all expressive elements exactly. Do not add, remove, or normalize them.
 Preserve exactly:
Emojis and emoticons (including skin tones).
Expressive punctuation: !, ?, ?!, !!!, ???, etc.
Interjections and fillers (e.g., wow, uh).
Repetition and emphasis (soooo, yessss, ALL CAPS, Mixed Case).
Established acronyms/internetisms (lol/LOL, OK, GOAT), technical acronyms (PDF), units, usernames, and hashtags.
Violations:
Changing expressive punctuation: "Hi John!" → "Hi John,"
Reducing repetition: "I'm confused???" → "I'm confused?"
Normalizing spelling: "Soooo happy" → "So happy"
Expanding common abbreviations: "lol" → "laugh out loud", "af" → "as f***", "bro" → "brother".
Non-violations:
Fixing grammar/spelling without altering expressive elements: "Teh day was great!!!" → "The day was great!!!"
Closing clearly accidental unmatched quotes/brackets.
Moving punctuation for strict grammatical correctness while keeping expressive marks (e.g., keeping "!!!" intact).
6. Preserve Formatting
Retain all layout features: line breaks, indentation, spacing, bullet styles, and paragraph structure. Numbers written in digits should not be replaced with words. ALL CAPS should be preserved.
7. Preserve Local Punctuations and Formatting
Target Locale
Topic
Input
Output
Explanation
en-GB
Punctuation
...complete "no-show".
...complete "no-show."
Violation: en-GB puts period outside quotes. Output used en-US style.
en-SG
Date
23/11/2027
11/23/2027
Violation: en-SG uses British DD/MM/YY. Output incorrectly used U.S. format.
II. Principles for Handling Ambiguous or Informal Contexts
Informal scenarios (SMS, chat apps, informal email) can be challenging for punctuation and style.
Add punctuation when contextually appropriate: In formal/neutral text, adding punctuation is expected. If formality is unclear, err on the side of adding punctuation for clarity.
Preserve colloquial or informal style: If text is clearly informal, do not formalize it. Do not change "gonna" to "going to" or add subjects to ellipses (e.g., "went to da store today."). If formality is ambiguous, edits increasing formality/correctness are acceptable.
Accept reasonable interpretations of unclear text: If meaning is truly unclear, a plausible, good-faith edit that clarifies the text is acceptable. Alternatively, leaving the text unedited is also acceptable; do not penalize the lack of edits.
03 Steps and Requirements
Step 1: Review the Original Input Text
Check for grammatical errors: objective violations of spelling, punctuation, subject-verb agreement, etc.
Check for ambiguity (e.g., "I like cooking my family and my pets" vs. "I like cooking, my family, and my pets").
Determine if text is vague or incomprehensible.
Step 2: Assess the Formality Level
Classify as Formal (Government, legal, academic) or Other (Semi-formal, informal, colloquial).
Error Types and Actions
Category
Definition
Action
Critical Errors
Blocks comprehension, changes meaning, creates true ambiguity, or violates fundamental grammar.
Must Fix (Formal & Informal).
Minor Errors
Breaks formal rules but doesn't hinder comprehension (e.g., missing apostrophe in "dont", lowercase "i", starting with "But").
Fix only in Formal. Optional in Other.
Stylistic Choices
Intentional based on tone (e.g., "yesssss", creative punctuation).
Preserve / Do Not Fix.
Typical Critical Errors Include: Subject-Verb agreement, wrong word usage (accept/except), severe homophones (their/they're), gender/pronoun agreement, tense inconsistency (went...buy), severe misspellings, and true pronoun ambiguity.
Step 3: Initial Assessment
Q1: Does input contain errors hindering comprehension? (Yes/No/Too ambiguous).
Q2: Did the assistant make changes?
Unidentifiable Text: If input is gibberish (e.g., "This is hard the who pays bit"), the assistant is expected to leave it unedited.
Step 4: Evaluate Correctness
Verifies if edits are necessary and correct.
Necessary edits: Fix grammatical errors while respecting the Minimal Edit Principle.
Unnecessary edits: Changes to style, tone, meaning, or register.
Derived Scales: Excellent, Good, Fair, Poor.
Step 5: Evaluate Completeness
Verifies if the response successfully detects all errors.
Scales: Complete, Nearly Complete (misses <20%), Partial (misses ≥20%), Incomplete.
Note: If a response fixes all original errors but introduces a new one, it is "Complete" but will be penalized under "Correctness."
Step 6: Compare Responses in Pair
Base comparison on derived scores for Correctness and Completeness.
04 Appendix - Informal Context Word Lists
1. Never Expand these Abbreviations
These should not be spelled out. Items with both cases (lol/LOL) mean both are acceptable.
 Examples:
A-I: af, afaik, asap, bday, brb, btw, cba, cya, dm, dw, eta, ffs, fr, g2g, goat, hbd, hmu, idk, ily, imo, irl.
L-Z: lmk, lol, nvm, obvs, omg, omw, pov, rn, smh, tba, tbf, tbh, tldr, tmi, ttyl, ty, tysm, wbu, wfh, wtf, wyd, yolo.
2. Do Expand these Words
These are primarily time-savers and should be turned into longer forms: (List contains placeholders for expansion examples).
05 Locale-specific Guidelines: Hinglish (hi_LATN)
Do Not Change Gender: If input says "karti hai," do not change to "karta hai."
Use Neutral Forms for Ambiguity: If gender is unspecified, use neutral forms (e.g., "karte").
Object Gender: Hindi inanimate objects have grammatical gender; correct errors in verb conjugation (e.g., "Gaadi chal raha hai" → "Gaadi chal rahi hai").
Spelling Conventions:
Correct: "mann" (mn), "tumhe" (tume), "iPhone", "pehle" (phle), "bahut/bohot" (bhut).
Acceptable variations: fir/phir, jaega/jayega, Dhanyavaad/Dhanyawad, Pooja/Puja.
END OF GROUND TRUTH Extraction Stats:
Total words extracted: ~2,850 (Estimated from source excerpts)
Tables extracted: 6
Figures described: 5 (Workflow menu, Step 1 UI, Step 2/3 UI, Correctness Flowchart, Pairwise Comparison UI)
Completeness: 100% (Extracted all provided content according to structural rules).