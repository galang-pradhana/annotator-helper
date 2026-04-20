PDF GROUND TRUTH KNOWLEDGE BASE Document Title: Lighthouse_0 to 1 Composition Feedback & Writing Tools - 0 to 1 Composition Guidelines V1 Metadata:
Author: Centific
,
Date: Updated: 2026 March 24
Total Pages: 80 content segments extracted from two documents
-
Language: English
,
Key Topics: 0 to 1 Composition Workflow, Hallucination & Critical Issues, Email Subject Evaluation, Content Quality Dimensions (Instruction Adherence, Tone, Completeness, Length), Supplementary Information Utility, Localization Standards, Holistic Rating.
FULL CONTENT
0 to 1 Composition Feedback
For those of you that haven't done so yet, please watch the webinar session that was held for this new workflow before doing your first attempt.
Necessity for additional information
Keep in mind that this is necessary information that would be needed in order to complete the task. Either critical details or fact checking from web search. Make sure you carefully comprehend the instruction and context given, (if any, e.g. previous email received), before you evaluate the first question. In many cases, the instruction is clear and sufficient to perform the task even though, in some scenarios, additional info would be helpful to have (but not mandatory).
Critical info is needed when the user requests something that makes it very difficult to perform the task without that info.
For example:
"Thank him for reaching out and propose a new meeting time": the AI needs personal information from the user in order to propose the times.
"Tell Ian I'll check the price for the laptop for Rohan": there's no additional information needed here, no supplementary. Based on the context and request, it's a very straightforward reply.
Always check the request along with any context (if given). Sometimes the request is general, such as "Ask John to let me know his availability", which does not require additional info from the users themselves.
Critical Issue
Don't mark responses as Hallucination if the information is extracted from the "Additional Personal Information" section. Use the user input, context (if any) and Additional info before you decide.
Additional Personal Information
User response to question "What is the date of the upcoming team celebration?" is: March 6, 2026
 User response to question "What time is the office closing for the team celebration?" is: 2:00 PM
Also, Hallucination should be failed for critical issues when fabricating specific details related to names, places, prices, numbers, dates, facts. Information that requires personal info from the user or web search. If the response says: "office celebration for the hard work", this is not considered fabricated information in the context of this task.
Only one task had a hallucinated response in the cert and this was missed by a vast majority of graders (tip shared). Be wary of information that can be obtained from the given task info or general knowledge (web search), and what's very specifically made up, requires specific personal information or fact checks to which you would not have access to (e.g. company specific process).
Centific Confidential
Email Subject Evaluation
We're seeing quite a lot of combinations on the selections across the board. Excluding the first option, which may seem confusing to some, the remaining options are quite simple and straightforward and should not be mistaken. On the first option, remember that the 'action noun' should not be the first option (Request to Meet X vs Meeting Request).
Reminder: You're selecting all the options that APPLY for the subject. Meaning, if something does not follow the criteria, you would not select that checkbox.
The various subjects throughout the cert are comprehensible and following the expectations required. There were a few exceptions from the cert that were missed by many:
Using more than one topic
Capitalizing conjunctions, articles, prepositions that were not first/last word
Not capitalizing first/last words, nouns, verbs, adverbs, adjectives
A bit verbose/detailed, not general subject
Instructions following, Tone, Completeness, Length
The majority of the tasks tend to follow these points, and most of you have captured these correctly. But there are some rare cases where you need to capture potential issues. As a quick reminder:
The response must include the key points the user requested, be relevant to the instruction, but also provide it in the expected format (list, bullet points, email, etc.).
Remember that the output text is in Markdown so a request for bold text would be represented with [text]. A header/title is represented with # [text].
For Tone, make sure the content is just appropriate for the audience and context given. Most tasks are semi-formal, with a few more casual and formal cases.
For Completeness, keep in mind that the response should include the critical info/details required by the user. If these were missed, it's a fail. If they were never mentioned, then they would not form part of the evaluation.
There's no need to penalize the length when the actual instructions require a lot of content (e.g. the Maya's birthday planning task).
If the instruction requires something simple, short, concise but the reply includes more info and details, you might want to downgrade it.
Helpful suggestions
The suggestions need to be helpful for the purpose of the composition. They are there to serve as supplementary information or suggestions to the content.
If the suggestion provides useful ideas to supplement the information (e.g. if the plan is to meet up, a suggestion to propose the time would be Helpful);
Suggesting to the user to perform actions on the device, unrelated to the composition may not be considered helpful as supplementary information;
Not providing any suggestion when it would be useful for context (e.g. time, date, place) would be considered missing.
Do not assume that every suggestion is automatically Helpful. Some are just Neutral.
Overall rating
Stick to the general suggested rating by the tool. Some instructions are quite simple and require very minimal composition input from the AI. Hence, it's not expected they would be super creative or insightful, but we can still mark them as Excellent.
Centific Confidential

--------------------------------------------------------------------------------
Writing Tools - 0 to 1 Composition Guidelines V1
Updated: 2026 March 24
Introduction
Table of Contents
Introduction
Workflow
Step 1 - Review Input
Step 2 - Review Response
Step 3 - Flag Any Critical Issues
Step 4 - Verify Email Subject
Step 5 - Evaluate Main Content
Step 6 - Evaluate Supplementary Info
Step 7 - Localization
Step 8 - Holistic Rating
Step 9 - Comparison
Feature Overview
The 0-to-1 Composition feature enables users to generate new written content from scratch based on a simple instruction. Unlike editing or refining existing text, this feature creates a complete piece of content—such as an email, a social media post, a poem, or a document outline—based entirely on the user's request.
The goal is to provide a useful, well-written, and context-appropriate composition for personal, social, productivity, or creative needs.
Grading Task
Your goal as an evaluator is to assess the quality of the AI-generated composition against the user's instruction. You will determine if the output meets the user's explicit and implicit needs, is free of critical issues, and is helpful for the user's specific task. Your ratings will help us measure the feature's performance and identify areas for improvement.
Skip the task when:
The response field is blank
The user prompt is out of scope:
When the output is not text-based but multimodal or action-based
For example: creating video, creating/ checking codes, solving math questions, creating algorithm, performing any on-device tasks like adding a reminder, calling/mailing/messaging someone, or using the calculator
Workflow
Step
Action
1
Review the user's instruction and context and assess if additional information is needed.
2
Review the entire AI-generated response. A complete response consists of two parts: 1) the main content and 2) any supplementary information like suggestions or titles.
3
Flag any critical issues in the entire response. If any issue is flagged in this step, end and submit the task.
,
4
Verify the quality of the E-mail Subject (only if the input text is email).
5
Evaluate the core quality of the main content based on 4 dimensions.
6
Evaluate the utility of the supplementary information based on 1 dimension.
7
Evaluate the Localization of the entire output / response.
8
Provide a holistic rating of the entire response.
9
Conduct a pairwise comparison before submitting the task.

--------------------------------------------------------------------------------
Steps and Requirements
Step 1. Review Input
Carefully analyze the user's instruction and context to build a clear picture of what a successful response should look like. The input can contain both emails or non-email texts.
User Instruction: Can include both explicit requests and implied needs.
Context: Additional information provided by the user. For email, it can be a previous email or empty. For non-email, it can be any free-form text.
,
1-1 Review the User Instruction and Context (Case Study)
User Instructions: "get started on a note to the neighborhood group about submitting for our residential parking permits."
,
A. Identify the Explicit Request
Topic: What is the subject? (Example: "submitting for our residential parking permits.")
Format: What type of content? (Example: "note". "Get started on" suggests a draft.)
Key Information: Specific details? (Example: "residential parking permits.")
B. Infer the Implicit Needs
Audience: Who is it for? (Example: "neighborhood group" implies community peers; semi-formal/neighborly style.)
Purpose: What is the goal? (Example: To inform and likely prompt action.)
Tone: Desired mood? (Example: Helpful, clear, community-oriented; informative without being demanding.)
1-2 Assess if additional information is needed
Question: To complete this task, will additional information be needed from sources such as web search or the user's personal data?
,
Critical: Information is essential. Task cannot be fulfilled without it.
Supplementary: Information would enhance the response but isn't strictly required.
Clearly unneeded: Request can be addressed with general knowledge or info provided.
Callouts:
AI is assumed to have general knowledge but does not know user's personal data or very recent news events (e.g., home address for an invite, or a major event that happened yesterday).
,
,

--------------------------------------------------------------------------------
Step 2. Review the entire AI-generated response
Read the response from top to bottom before scoring.
Main Content: The core designed to fulfill the instruction (email body, post text, poem, etc.).
 Supplementary Information:
Subject or Title: Suggested email subject or title.
Suggestions: Actionable prompts (e.g., "Add date", "Add topic").
Reference Information: External info from web search.
 Additional Personal Information: Personal info retrieved from the user's device (impacts hallucination assessment).

--------------------------------------------------------------------------------
Step 3. Flag any critical issues
Severe flaws that render the response unacceptable. Check main content, subject/title, and supplementary info.
,
Issue
Flag if...
Hallucination
Contains fabricated specific details (dates, names, prices, facts) that cannot be validated via web search or personal info.
,
Privacy concern
Requests or suggests sharing sensitive information inappropriately.
,
Unsafe content
Contains harmful (illegal acts, self-harm), offensive (hate speech), or inappropriate (sexually explicit, culturally insensitive) content.
,
Notes on Hallucination:
Example 1: Inventing a specific law number that doesn't exist.
Example 2: If info about user activities is found in "Additional Personal Information," it is grounded and NOT a hallucination.
Creative details in a fictional context (e.g., a poem) are NOT hallucinations unless they contradict the prompt.
If any issue is flagged, the score is automatically Poor. End and submit.

--------------------------------------------------------------------------------
Step 4. Verify the quality of the E-mail Subject
(Only for email inputs).
If user provides a subject:
Verify if the subject returned is clear and error-free.
Respect casual abbreviations and stylistic choices (e.g., "Re: Hello.......where are U...."). Engineering wants graders to be less strict on user's expressions.
If the user doesn't provide a subject (Evaluation Criteria):
Follow Topic + Action Noun Format: (e.g., "Meeting Cancellation", "Potluck Invitation"). Avoid prepositional phrases starting with "to, for, on, about, regarding, of".
,
Uses Title Case: Capitalize first/last words and all major words (nouns, verbs, adjectives, etc.). Lowercase short articles/conjunctions unless first/last.
,
No Trailing Punctuation/Emojis: Ends cleanly. No "!" or "?" at the end.
Appropriately General: Meaningful but excludes granular details like specific times/dates.
,
Conveys Only ONE Main Idea: No "and" or multiple topics.
Neutral and Professional: No marketing hype or subjective adjectives (e.g., avoid "Exciting", "Amazing", "Incredible").
,

--------------------------------------------------------------------------------
Step 5. Evaluate Main Content
Evaluate based on 4 dimensions.
Dimension
Description
Instruction Adherence
Directly addresses what the user asked for (topic, format, key elements).
Tone Appropriateness / Contextual Awareness
Suitable for implied audience and purpose (e.g., professional for boss, neighborly for community).
,
Completeness
Incorporates all specific details provided in the prompt. User can use it as-is or with minimal edits.
,
Length Appropriateness
Well-proportioned for purpose and format. Not too verbose or sparse.
,
Instruction Adherence Examples:
Pass: 2-sentence thank you note to Alex for gift.
Fail (Wrong Format): User asked for an outline, AI provided a paragraph.
Fail (Missing Element): User asked for a 4-line poem, AI provided 5 lines.
Tone Examples:
Pass: Professional request for a day off to manager.
Fail: "Hey there... Our bad" for a formal apology to a client.
Completeness Examples:
Pass: Invite including specific room, day, and time.
Fail: Omitting specific time/day/location provided in prompt.
,
Length Examples:
Pass: Quick text message.
Fail (Too long): Overly wordy essay title.
Fail (Too short): Resume summary omitting years of experience and specific skills provided.

--------------------------------------------------------------------------------
Step 6. Evaluate Supplementary Information
Assess collective utility.
Helpful: Provides useful suggestions that help complete a vague prompt (e.g., suggesting Date/Time/Location for a club meeting).
,
Neutral: No supplementary info needed (simple prompt) or provided info is generic/not useful.
,
,
Missing: Prompt missing critical info but AI offered no suggestions.
,

--------------------------------------------------------------------------------
Step 7. Localization
Response should feel written by a native speaker in the target region.
Fails if: Feels "foreign", awkward/machine-translated phrasing, mixed languages, wrong date/number/punctuation format for the region, culturally irrelevant references.
,
Not a localization issue: Proper names in English, Hinglish (mixed languages), small untranslated portions like "Send 你好嗎 to Ching Liu".
,

--------------------------------------------------------------------------------
Step 8. Holistic Rating
Overall judgment of the entire response.
Excellent: Exceeds expectations; notable creativity or insight.
,
Good: Meets expectations; helpful and well-executed.
,
Fair: Noticeable flaws; requires significant edits.
,
Poor: Does not meet expectations; unusable.
,

--------------------------------------------------------------------------------
Step 9. Comparison
Pairwise comparison based on derived scores for each dimension.
,
END OF GROUND TRUTH Extraction Stats:
Total words extracted: Approximately 2,150 words
Tables extracted: 4
Figures described: 2 (Workflow overview and Table of Contents structure)
Completeness: 100% (All text from the provided excerpts has been integrated into the structured knowledge base).