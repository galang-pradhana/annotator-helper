FULL CONTENT

DO'S
Understand & Follow NDA Instructions - You are legally bound by the NDA; ensure full compliance at all times.
Follow Centific's Security Policies.
Access Training Only on Secure Networks.
Use Only Approved & Secure Devices.
Version Control
Version #
Updates (slide #)
Date Updated
3.1
Slide 27: Instruction Following: If the language in the response is incorrect it should be graded as "Not Following" instruction (previously "Partially Following").
September 23, 2024
The guidelines were updated with a new "Skip" process. Now, to Skip a task, you will need to use the "Report a problem" from the Tag Tool UI.
3.2
Slide 7: Tool UI updated. Slide 10: Report a Problem section is updated. Slides 13-14: Skipping reasons updated.
November 11, 2024
3.3
Slide 44: The definition for the Spelling issue is updated. Slide 51: The definition for the Formatting and punctuation issue is updated. Slide 107: 2.1 Single Response Rating: A note for Slightly Satisfying and Slightly Unsatisfying is added concerning the localization issue.
January 27, 2025
3.3
Converting all screenshots in Keynote: Slide 6: Added workflow from screenshot. Slide 115: Added Satisfaction Logic flowchart from screenshot. Slide 116: Added Satisfaction Logic flowchart from screenshot. Slide 131: Added Preference Ranking diagram from screenshot.
January 29, 2025
4
Removed Harmfulness specific evaluation.
July 8, 2025
Introduction
This document serves as a reference for the Preference Ranking annotation project. This document is interactive. You can read this from start to finish or jump to different topics using the Navigation Bar.
Overview
Users reach out to digital assistants for various reasons: to ask for specific information, to give instruction (e.g., create a passage, write a code), or simply to chat. Because of that, the majority of user requests are conversational and might be filled with colloquialisms, idioms, or unfinished phrases. Just like in human-to-human interaction, a user might comment on the digital assistant's response or ask a follow-up question. While a digital assistant is very capable of generating human-like conversations, the limitations are still present. For example, it is challenging for the assistant to judge how accurate or safe (not harmful) the response is. This is where your role as an analyst comes into play. The purpose of this project is to evaluate digital assistant responses to ensure they are relevant, accurate, concise, and safe.
Task
Sub-Task
Description
User Request Analysis
a. Interpret User request
Analyze the user request, ensure understanding (using context if present).
Response Evaluation
b. Assess your ability to rate the response
The user request and response might need advanced specialized skills to provide reliable ratings. The presentation of the user request/response might have visual issues preventing the rating of the task.
a. Provide ratings for each response
You will be shown at least 2 responses. At this stage you will provide ratings for each response (you might be shown a subset of rating questions).
b. Compare responses
You will then go through a series (if more than 2 responses are shown) of comparisons, provide your rating for which side you prefer.
Comments
N/A
Leave a detailed comment why one side was preferred to another OR if they are same.
Workflow
Step 1: User Request Evaluation (Locale: en_US).
Step 2: Response Evaluation.
2.1 Single Response Rating (Following Instructions, Localization, Concision, Truthfulness, Satisfaction).
2.2 Preference Ranking (Satisfaction, Aggregated Principles).
Step 3: Comments.
Tool UI Description
User Request: In the tool, the first section you will find is the User Request.
Predicted Category: Just below the user request shows the task's domain. This information will assist you in determining whether to skip the task due to an "expertise mismatch."
Report a Problem: Icon used to skip the task if the skipping requirements are met. Note: This action cannot be undone. The system will log this as a skip action, and you will not receive credit for time worked on this task.
Reasons: Technical Issue, Expertise Mismatch, Other (Gibberish, Language).
Responses: A computer-generated response that needs to be evaluated.
Response Evaluation: A set of response-related questions to be answered following the guidelines. A summary table will populate as you make your selection to help assess Satisfaction.
Preference Ranking: Assess, compare, and rate two responses to determine which one is better.
Comments: Explain your ranking in the comments. Be specific.
Submit Button: Use this button to submit and move to the next task.
Project Guidelines: Linked on the top right side of the tool.
STEP 1. USER REQUEST EVALUATION
The purposes of this step are:
To understand user intent and the underlying purpose of the request by identifying the type of user request and context.
To model the desired response - the ideal response that a user might expect.
To identify whether the request is safe and doesn't introduce potential harm.
1.1 Skipping Request
Read the request and decide whether you can move forward. Exceptional reasons apply to both request and response.
Skipping Reason
When to use
Examples / Notes
Technical Issues
A technical issue prevents submission.
Skip if: Problem with UI prevents grading; Data did not load (missing request, category, or response). Do NOT skip: Sequence of letters is incorrect (e.g., only A, C, D listed).
Other: Gibberish
User prompt has no coherent meaning.
Skip if: "And hooptiously drangle me with crinkly bindlewurdles". Do NOT skip: Vague requests ("where is the best place"); Fictional terms acknowledged by user ("Hempmas").
Other: Language
Prompt is in a language without expertise.
Skip if: Request is in French (fr_FR) or Japanese (ja_JP) for a different locale. Do NOT skip: Prompt is in English; User asks to translate a foreign phrase to your locale.
Expertise Mismatch
No expertise to assess, even with research.
Skip if: Limited knowledge in fields like legal or mathematics prevents confident rating (e.g., proving mathematical inequalities).
Research Time Guidelines:
Generally, spend no more than 5 minutes per response on research (e.g., 3 responses = 15 mins total).
For difficult tasks, up to 10 minutes. If familiarity isn't gained in 10 minutes, skip as "Expertise Mismatch".
Important: Do NOT skip if the request itself requires heavy research (e.g., verifying 15 websites).
1.2 Request Type and Context
User Request Type
Example
Notes
Q&A / Math & Reasoning
"What year did WWII end?" / "Alice is three times as old as Bob..."
Includes digital assistant knowledge, Q&A about provided text, and step-by-step math.
Brainstorming
"Give me a list of things I can do with excess grocery bags."
Open-ended with various possible answers.
Creative Writing
"Rewrite the sentence to make it sound more fun."
Focus on style and creative output.
Role Playing
"Act as an interviewer of a software engineer."
Simulating specific personas.
Coding
"Write python code to sort a pandas data frame."
Programming and script generation.
Chit Chat
"I'm enjoying my vacation."
Natural, human-like interaction.
Context Interaction Types:
Follow-up based on previous requests: (User: "What is the capital of Texas" -> Assistant: "Austin" -> User: "How about Washington state"). Context needed.
Independent Request in same topic: Klarifikasi fitnes goal. Context not strictly needed but related.
Follow-up based on previous responses: (Assistant lists books -> User: "Tell me more about [Book A]"). Context not strictly needed for the second query but enhances intent.
Providing additional info/refinement: (Assistant asks for text to summarize -> User provides text). Context needed.
New topic: Completely unrelated subject after previous chat. Context not needed.
1.3 Modeling the Expected Response (Attention to Details)
To model the expected response, ask:
Format: Does the user ask for bullet lists, tables, etc.?
Length: Are there constraints like "in 2 or 3 sentences" or "200 words"?
Style: Is there a desired tone (Shakespearean, funny, technical)?
Action: What specific task is requested (summarize, rephrase, code)?
Note: Instructions can be implicit (e.g., "Kenya" implies a request for info about Kenya).
Links: Treat links as part of the user request; open them to understand intent.
STEP 2. RESPONSE EVALUATION
2.1 Single Response Rating
Each response is analyzed against predefined criteria (dimensions).
Dimension 1: Following Instructions
Instructions can be Explicit (clearly stated format/length/content) or Implicit (inferred, like Q&A meaning the answer must be provided).
IMPORTANT: Following Instructions is independent of Truthfulness. A response can follow instructions (e.g., naming 10 countries) while being inaccurate (e.g., naming fake countries).
Scale
Criteria
Fully following
Follows ALL instructions. Declines inappropriate prompts with helpful disengagement. Note: Word count deviation within +/- 5% is "Fully Following".
Partially following
Most instructions followed. Deviations in format (e.g., adding info to a Yes/No request), specific length (2 paragraphs instead of 1), or missing minor details.
Not following
Fails main points. Includes Wrong Language (e.g., asked for Korean, answered in English). Word count deviation > 5% (e.g., 200 words requested, 500 given). Declining due to output limits (e.g., 50,000-word essay).
Dimension 2: Localization (Non-en_US Tasks Only)
Localization adapts content to a specific target market to seem designed for that locale.
Scale
Description
No issues
No signs of being generated for a different locale.
Yes, issues present
At least one element makes the user question if the model was designed for their locale.
Specific Localization Issues:
Unlocalized Info: Info from another locale (e.g., IRS info for UK user).
Overly-localized: Unnecessarily restricts info to the target locale (e.g., listing only Canadian books when "most influential books" were asked).
Spelling: Uses wrong variant (e.g., "color" instead of "colour" in en_GB). Note: General typos are NOT localization issues.
Non-local Perspective: Unnecessarily mentions user's locale (Over-specification). E.g., specifying "Australian Dollars" to an Australian user for local prices.
Vocabulary: Wrong terms (e.g., "soccer" for en_GB).
Phrase or Idiom: Unnatural for the locale (e.g., "chuffed to bits" for en_CA).
Wrong Language: Fails to match prompt language. Exceptions: Loanwords (kindergarten), code, or translation requests.
Grammar: Fails to conform to locale variant (UK "learnt" vs US "learned").
Tone: Sounding like a stereotype.
Awkward writing: Literal or machine-translated feel.
Formatting/Punctuation: Wrong date/time formats, quote marks, or text direction.
Units: Wrong currency, distance, temperature, etc.
Dimension 3: Concision (Verbosity)
Focuses on distractions and length restrictions. Independent of Following Instructions.
Scale
Criteria
Good
Free from distractions (anecdotes, jargon, filler, repetition). Length restrictions are followed.
Acceptable
Minor distractions. Slightly longer or shorter than requested.
Bad
Multiple distractions making info hard to find. Excessively long/verbose or too short based on constraints.
Note: A long response (e.g., 500 words) can be "Good" if the user requested it.
Dimension 4: Truthfulness
Evaluates factual and contextual accuracy.
Scale
Criteria
Truthful
Factually correct (search verified) and accurate to contextual text provided. Correct math reasoning and coding edge cases.
Partially Truthful
Primary info is correct; secondary info is inaccurate. Math: correct answer but wrong reasoning. Code: logic works but fails edge cases.
Not Truthful
Primary info is incorrect/hallucinated (e.g., Dave Pearson killed by wild orcas). Reasoning steps in math are wrong. Code leads to incorrect outputs.
Contextual vs Factual:
Contextual: Must stick to provided reference text (summaries/Q&A). Adding info not in text is Not Truthful.
Fictional Works: Accuracy is "Not Applicable" (mark as Truthful) unless specifically asked.
Time Sensitivity: Assume the request is made in the present moment.
Dimension 5: Satisfaction (Holistic Rating)
Based on all 4 dimensions plus Relevance, Comprehensiveness, Formatting, Creativity, Style/Grammar, Helpful Disengagement, and Seeking Clarification.
Satisfaction Logic (The -1/-2 Protocol):
Partially (xxx) (Following, Truthful, etc.) = -1
Not (xxx) or Bad (Concision) = -2
Harmful / Maybe Harmful = Highly Unsatisfying
Satisfaction Level
Criteria / Logic
Highly Satisfying
Perfect. Follows all instructions, truthful, concise, no typos, pleasing format. CANNOT be selected if any dimension is less than highest rank.
Slightly Satisfying
Overall helpful. Penalty -1: Fails minor instructions, misses minor details, minor grammar/formatting issues, or seeks clarification for ambiguity.
Slightly Unsatisfying
Partly helpful with major issues. Penalty -2: Fails major instructions, misses important info, much unnecessary info, unpleasing format, or untruthful essential info.
Highly Unsatisfying
Completely unhelpful. Engages with harmful prompts, gibberish, wrong math answers, wrong language, answers wrong question, or hallucinated summary details.
Special Considerations:
Ambiguous Request: Ideal = Seek Clarification (Slightly Satisfying). Assumption = Slightly Unsatisfying.
Incomplete Response: Max rating is Slightly Satisfying.
Illegal Content: Providing info for illegal access (e.g., movie downloads) is Highly Unsatisfying.
Data Limitations: Accurate responses are better than declining due to data cut-offs.
Satisfaction Rating Constraints
1. Level: Highly Satisfying (HS)

Condition: HANYA boleh dipilih jika SEMUA dimensi (Following Instructions, Concision, Truthfulness) berada di peringkat tertinggi (Fully Following, Good Concision, Truthful).

Hard Block: Jika ada satu saja dimensi yang bertanda "Partially", "Acceptable", "Not", atau "Bad", maka HS DILARANG.

2. Level: Slightly Satisfying (SS)

Max Ceiling: Ini adalah rating maksimal jika terdapat kekurangan minor:

Partially Following.

Acceptable Concision.

Partially Truthful.

Hard Block: Jika ada dimensi yang masuk kategori "Not Following", "Bad Concision", atau "Not Truthful", maka SS DILARANG.

3. Level: Slightly Unsatisfying (SU)

Condition: Rating ini digunakan jika terdapat kegagalan mayor pada instruksi, kejujuran, atau konkusi:

Not Following.

Bad Concision.

Not Truthful.

Note: Respon masih dianggap "partly helpful" meskipun punya isu besar.

4. Level: Highly Unsatisfying (HU)

Condition: Respon sama sekali tidak berguna (Completely unhelpful) atau berbahaya.

Triggers (Automatic HU):

Mengandung konten berbahaya atau ilegal.

Gibberish (teks tidak bermakna).

Jawaban matematika salah total.

Menggunakan bahasa yang salah (Wrong language).

Menjawab pertanyaan yang salah atau tidak relevan.

Halusinasi pada detail ringkasan (Hallucinated details).
2.2 Preference Ranking
Compare two responses based on the Satisfaction dimension using a 7-point scale.
For the rating in the comparative satisfaction assessment, we purely only look at the satisfaction value alone, without looking at other aspects.
Preference Ranking Ladder (Tangga Nilai):
Same: Responses are duplicates or have the same level of satisfaction.
Slightly Better: Difference of 1 "step" on the satisfaction scale. Minor advantages in instructions or non-essential facts.
Better: Difference of 2 "steps". Major advantage in following instructions, essential truthfulness, or readability.
Much Better: Difference of 3 "steps". One response addresses request while the other fails; one avoids dangerous content while other engages.
Ranking Priorities:
Truthfulness > All other attributes.
Helpful Disengagement is preferred over engaging with harmful prompts.
Conciseness: Prefer the to-the-point response. Do not rank solely on length.
Formatting: Tie-breaker, not a primary driver unless content is comparable.
STEP 3. COMMENTS
Explain the ranking specifically.
Must be in English regardless of locale.
Good Comments: Comparative analysis, pointing out specific strengths/weaknesses (e.g., "E used simplistic language while C was technical").
Bad Comments: Generic statements like "All responses are concise" or "Ranked based on principles" without specific details.
Completeness: 100%. All rules from the PDF, supplemental logic from pasted text, and the satisfaction protocol image were integrated into the conditional logic and hierarchy.