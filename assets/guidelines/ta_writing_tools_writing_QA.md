PDF GROUND TRUTH KNOWLEDGE BASE Document Title: Writing Tools Guidelines - Writing Q&A Metadata:
Author: Not explicitly stated (Internal Engineering/Evaluation Team)
Date: Updated: 2026 March 26
Total Pages: 23
Language: English
Key Topics: Feature Overview, Grading Task, Query Categorization, Accuracy & Relevance, Conciseness, Tone & Style, Actionability, Educational Value, Localization, Pairwise Comparison.
FULL CONTENT
Writing Tools Guidelines - Writing Q&A
V1 Updated: 2026 March 26

--------------------------------------------------------------------------------
Introduction
Feature Overview
The Writing Question & Answering (Q&A) feature is a smart writing assistant designed to help users improve their writing. It functions as an on-demand writing tutor that analyzes user-provided text.
The typical user workflow is:
A user submits a piece of writing, such as an email, report, or essay.
They select a portion of the text (or the entire document).
They ask a specific question about the quality of their writing.
Examples of user questions include:
"Does this sound professional?"
"Is my argument clear?"
"How can I make this more concise?"
In response, the AI assistant provides targeted feedback and analysis to help the user understand and improve their work.
Grading Task
Your task is to evaluate the quality of the AI assistant's responses to these user questions. You are the human check on the AI's performance, ensuring it provides helpful, accurate, and appropriate feedback.
For each AI response you review, you will answer a series of yes/no questions. These questions are grouped into 5 key areas that measure the overall quality of the response, including:
Accuracy & Relevance: Does the response correctly answer the user's question?
Conciseness: Is the feedback appropriately brief?
Tone & Style: Is the assistant's tone helpful and professional, not judgmental?
Actionability: Is guidance appropriate for query type?
Educational Value: Does the response help the user learn why a piece of writing is effective or ineffective
Based on your selections, the score of each key area will be auto-computed and displayed for you.
[!CAUTION] If the response is missing...
If the entire response is missing, please select Skip the Current Task > "The entire response is missing"

--------------------------------------------------------------------------------
Workflow
Review the Original User Created Text, User Selected Text, User Query, and Response.
Categorize Queries (both by type and writing aspect).
Evaluate Accuracy and Relevance.
Evaluate Conciseness
Evaluate Actionability
You will only evaluate Actionability if you have categorized the User Query as "Informational" or "Hybrid"
Different questions will be displayed based on your categorization
Evaluate Tone and Style.
Evaluate Educational Value.
Evaluate Localization
Conduct Pairwise Comparison

--------------------------------------------------------------------------------
Steps and Requirements - Step 1
Step 1. Review the Original User Created Text, User Selected Text, User Query, and Response.
Before you begin your evaluation, it's essential to understand the full context of the interaction. Your first step is to carefully review the four components that make up a single task.
Step 1. Review the input text, including conversation context, user prompt, and the user input email.
Component
Description
Original User Created Text
This is the entire piece of writing the user submitted (e.g., the full email or document). It provides the overall context for the user's goal.
User Selected Text
This is the specific portion of the text that the user highlighted to be reviewed. This is the most important text to focus on, as the AI's response should be based only on this selection.
User Query
This is the exact question the user asked about their selected text (e.g., "Is this clear?") Understanding the user's specific intent is key to evaluating the response.
Assistant Response
This is the AI-generated feedback that you are tasked with grading.
Figure 1 (Page 4): Screenshot of the evaluation interface. Top box shows "Original User Created Text" (an email from Jamie to Mike about a meeting). Middle box shows "Evaluate Responses" with "User Selected Text" (specific paragraph) and "User Query" ("Is this appropriate for my manager?"). Bottom box shows the "Assistant's Response" analyzing the casual tone.
👉 Summary: Before moving to Step 2, take a moment to ensure you have a clear picture of what the user wrote, what they specifically asked for feedback on, and how the AI responded.

--------------------------------------------------------------------------------
Steps and Requirements - Step 2
Step 2. Categorize Queries (both by type and writing aspect)
Your second step is to classify the user's request. Before evaluating the AI's response, you must first understand what the user is asking for and what aspect of writing they are focused on.
This categorization provides data to the engineering team. Additionally, this step will determine the questions that will be displayed for you when you evaluate Actionability.
You will answer two questions in this step.
First Question: What type of request is the user making?
Informational
Actionable
Hybrid
Other
If you categorize the user request as "Actionable," you won't need to evaluate the Actionability questions under step 6.
If you choose "Informational" or "Hybrid," different sets of Actionability questions will be displayed for you.
If you choose Other, it means the query is out of scope and you won't need to grade the response at all. See the screenshot below.
Review the table below to learn more about out-of-scope queries.
Figure 2 (Page 5): Screenshot showing "Part I - Categorize User Query". The user query is "Is this appropriate for my manager?". The option "Other (out of scope request)" is selected, and a message appears: "You may submit this task now."
Definition of Request Types
Type
Definition
Examples
Informational
The user wants an assessment, feedback, or evaluation. They are not asking for changes.
• "Does this sound professional?"<br>• "Is my tone appropriate?"<br>• "Am I being clear here?"
Actionable
The user wants the AI to directly rewrite or modify the text.
• "Rewrite this email."<br>• "Make this more concise."<br>• "Change this to be more formal."
Hybrid
The user wants both an assessment and actionable suggestions for how to improve.
• "How can I make this clearer?"<br>• "What should I change to sound more formal?"<br>• "Help me improve the flow."
Other
The query is out of scope (not about writing quality, a content generation request, etc.).
• "What's the weather?"<br>• "Write a poem for me."<br>• "Tell me a joke."
Queries that are about writing but are considered out of scope:
Fact checking is out of scope:
"Check against the internet for any fallacies."
"Check the factuality of my writing and educate me on anything that I might have missed"
Requiring additional context:
"Describe the ways someone could interpret the subtext of this writing, given this description of the person and our relationship."
[!IMPORTANT] Handling Ambiguous Queries Some ambiguous queries may still get routed to Writing Q&A feature.
If you can determine they are out of scope (fact checking or seeking analyses that require additional context), select Other.
If you believe the query is related to Writing and can be graded, do your best to judge and proceed with grading. For example:
"Do you see any other information I could be missing in this paragraph?"
It can be difficult to categorize this query. "Informational" would be the closest as the user is seeking feedback.
Second Question: Which writing aspect is the user asking about?
Structure & Organization
Voice & Style
Audience Alignment
Clarity & Effectiveness
Technical Execution
Focus of Writing Aspects
Writing Aspect
Focus
Example Queries
Structure & Organization
The flow, logical order, and coherence of ideas.
• "Does this flow well?"<br>• "Is my argument organized logically?"
Voice & Style
The tone, personality, and word choice.
• "Does this sound professional?"<br>• "Is my tone too casual?"
Audience Alignment
Appropriateness for the intended readers.
• "Is this appropriate for my boss?"<br>• "Will students understand this?"
Clarity & Effectiveness
The understandability, impact, and precision of the message.
• "Is this clear?"<br>• "Does this get my point across?"<br>• "Am I being direct enough?"
Technical Execution
Grammar, spelling, punctuation, and syntax.
• "Is my grammar correct?"<br>• "Did I use 'affect' correctly?"<br>• "Are there any spelling errors?"
[!IMPORTANT] Decision Framework If you are unsure which category to choose, use this three-step process to decide.
Step 1: Identify what the user is asking about. Look for keywords that point to a specific category.
Organization/flow? → Structure & Organization
How it sounds/tone? → Voice & Style
Appropriateness for reader? → Audience Alignment
Clarity/effectiveness? → Clarity & Effectiveness
Grammar/mechanics? → Technical Execution
Step 2: If the query mentions multiple aspects, choose the PRIMARY focus. Sometimes a user asks about more than one thing, like in the query, "Is this clear and professional?" To choose the primary category, consider the user's text and likely goal.
If the text is a formal report, the main concern is likely whether it meets workplace standards. Choose Voice & Style.
If the text is a set of instructions, the main concern is likely whether it can be easily understood. Choose Clarity & Effectiveness.
Step 3: Consider the context to confirm your choice.
Does the query mention a specific reader (e.g., "my manager," "new customers")? → It's likely Audience Alignment.
Does the query use words like "sound," "tone," or "feel"? → It's likely Voice & Style.
Does the query ask if the writing "works" or "makes sense"? → It's likely Clarity & Effectiveness.
Examples > Example 1: Professional Email
The following examples show how to categorize different types of user queries.
Text & Query
Query Type
Writing Aspect
Summary of Reasoning
Original Text: <br>Hi Marcus, <br>Thank you for taking the time to meet with me yesterday. I really appreciated learning more about the data engineering role and your team's work on the new analytics platform. <br>I'm particularly excited about the opportunity to work with real-time data pipelines, which aligns perfectly with my experience at DataFlow Inc. <br>Please let me know if you need any additional information from me. I look forward to hearing from you. <br>Best regards, <br>Sarah Chen <br>Selected Text: [ENTIRE TEXT SELECTED] <br>User Query: "Does this sound professional for a follow-up email after a job interview?"
Informational
Voice and Style
The query "Does this sound...?" asks for an assessment of quality, not suggestions for changes. The keyword "professional" relates directly to the tone and formality of the writing.
Examples > Example 2: Casual Message
Text & Query
Query Type
Writing Aspect
Summary of Reasoning
Original Text: <br>Hey Jennifer! <br>Hope you're doing well! So I wanted to reach out because I'm super interested in the Marketing Coordinator position that just opened up on your team. I know we haven't worked together directly, but I've always admired the campaigns you guys put out - they're honestly fire! 🔥 <br>I've been in the social media space for about 2 years now and I really think I'd be a great fit. Would love to grab coffee and chat about it if you have time! <br>Let me know! <br>Cheers, <br>Mike <br>Selected Text: "I know we haven't worked together directly, but I've always admired the campaigns you guys put out - they're honestly fire!" 🔥 <br>User Query: "Is this appropriate for reaching out to a manager about a job opening?"
Informational
Audience Alignment
The query "Is this appropriate...?" asks for an assessment. The specific context "for a manager" makes the primary concern about its suitability for that particular reader, which is the definition of Audience Alignment.
Examples > Example 3: Essay Introduction
Text & Query
Query Type
Writing Aspect
Summary of Reasoning
Original Text: <br>Throughout human history, technological advancement has fundamentally altered the fabric of society. From the invention of the printing press to the rise of the internet, each innovation has reshaped how we communicate, work, and understand our world. In the 21st century, we stand at the precipice of another transformative shift: the artificial intelligence revolution. <br>This essay examines the multifaceted impact of AI on modern employment, focusing on three key dimensions: job displacement in traditional sectors, the emergence of new career pathways, and the evolving skills required for future workforce success. While concerns about automation replacing human workers dominate public discourse, a nuanced analysis reveals a more complex picture of adaptation and opportunity. <br>Selected Text: [Partial Selection - First paragraph only] <br>User Query: "How can I make this opening paragraph more engaging for my college essay?"
Hybrid
Clarity & Effectiveness
The query "How can I make..." explicitly asks for guidance and suggestions for improvement. The goal of making writing "more engaging" is about its impact on the reader and its ability to hold their attention.

--------------------------------------------------------------------------------
Steps and Requirements - Step 3
Step 3. Evaluate Accuracy and Relevance
In this step, you will evaluate whether the assistant's analysis is correct, relevant, and specifically tailored to the user's text and intent.
An irrelevant or incorrect answer is not helpful, no matter how well-written it is.
Questions
You will answer the following four yes/no questions:
Did the assistant understand the user's intent?
Yes, the response interprets the question appropriately, considers context, and addresses the user's underlying concern.
No, the response misreads what the user is asking, addresses only the surface question while missing the deeper concern, or interprets the query inappropriately.
Does the assistant directly answer the question asked?
Yes, the response addresses the specific query, stays on topic, and doesn't answer a different, unasked question.
No, the response answers a different question, misses the point of the query, or goes off-topic.
If the response references the user's text, does it cite their actual words or content — rather than inventing, assuming, or misrepresenting what they wrote?
Yes. Any specific references are accurate and clearly drawn from the user's text.
No. The response invents details, misquotes, or makes claims not supported by the user's text.
Not applicable. The response gives only general advice and makes no specific reference to the user's writing.
Is the assistant's analysis factually correct?
Yes, the observations about the text are accurate, there is no misinterpretation, and the conclusions are supported by evidence from the text.
No, the response makes factually wrong observations, misinterprets the text, or draws unsupported conclusions. 
Examples > Example 1: Professional Email
Here are contrasting examples to guide your ratings.
Text & Query
Response
Question
Rating
Original Text: <br>Hi Marcus, [Sarah Chen's email as previously listed] <br>Selected Text: [ENTIRE TEXT SELECTED] <br>User Query: "Does this sound professional for a follow-up email after a job interview?"
Yes, this strikes a professional tone appropriate for a post-interview follow-up. You open with gratitude, reference specific topics from your conversation (the analytics platform), connect your background to the role, and close with clear next steps. The level of formality matches standard business communication.
1. Understands intent?
✅ Yes
2. Directly answers?
✅ Yes
3. Grounded in text?
✅ Yes
4. Factually correct?
✅ Yes
📝 Summary Rationale This response is a clear Pass. It correctly understands the user's intent, directly answers the question, grounds its analysis by referencing specific elements of the email (gratitude, platform), and is factually correct in its assessment.
Examples > Example 2: Casual Message
Text & Query
Response
Question
Rating
Original Text: <br>Hey Jennifer! [Mike's message as previously listed] <br>Selected Text: [Selected portion as previously listed] <br>User Query: "Is this appropriate for reaching out to a manager about a job opening?"
"No, this is way too casual for a professional request. Using slang like 'fire' and emojis is completely inappropriate when you're asking someone for a job opportunity. You should never use this kind of language with a manager. This makes you look unprofessional and immature. Remove the emoji immediately and rewrite this in proper business English."
1. Understands intent?
✅ Yes
2. Directly answers?
✅ Yes
3. Grounded in text?
✅ Yes
4. Factually correct?
✅ Yes
📝 Summary Rationale This response Passes for Accuracy & Relevance, even though it has problems in other areas. It correctly understands the user wants to know about appropriateness for a manager, it directly answers "No," it correctly grounds the answer in the specific use of "fire" and the emoji, and its analysis that this language is casual is factually correct. (Its failures in Tone, Conciseness, and Actionability will be evaluated in later steps).
Examples > Example 3: Essay Introduction
Text & Query
Response
Question
Rating
Original Text: <br>Throughout human history... [AI Essay as previously listed] <br>Selected Text: [Partial Selection - First paragraph only] <br>User Query: "How can I make this opening paragraph more engaging for my college essay?"
"Your opening effectively establishes historical context and builds toward your specific topic. To increase engagement, consider starting with a concrete example or scenario rather than an abstract historical sweep. For instance, you might open with a brief anecdote about a worker whose job was transformed by AI, then zoom out to the broader historical pattern. This 'particular-to-general' approach helps readers connect emotionally before engaging intellectually."
1. Understands intent?
✅ Yes
2. Directly answers?
✅ Yes
3. Grounded in text?
✅ Yes
4. Factually correct?
✅ Yes
📝 Summary Rationale This response is a clear Pass. It understands the user wants to improve engagement, directly answers how, grounds its analysis in the "historical sweep" approach used in the text, and makes a factually correct observation about the current structure.

--------------------------------------------------------------------------------
Steps and Requirements - Step 4
Step 4. Evaluate Conciseness
In this step, you will evaluate whether the assistant's response is appropriately brief and focused. The ideal response is around 2-3 sentences, delivering its insight without repetition or unnecessary information.
Questions
You will answer the following three yes/no questions:
Is the response appropriately focused?
Yes, the response addresses the user's question directly and prioritizes the most important points.
No, the response rambles, goes off-topic, or includes unrelated observations.
Does the response contain NO REPETITION?
Yes, each sentence adds new value and no points are repeated.
No, the response says the same thing in multiple ways or uses redundant phrasing.
Does the response contain necessary information only?
Yes, every phrase serves a purpose and is directly relevant to answering the user's query.
No, the response includes tangents, extra details, or observations the user didn't ask about.
Step 4. Evaluate the generic quality of the reply.
Examples > Example 1: Professional Email
Text & Query
Response
Question
Rating
[Sarah Chen's email/query as previously listed]
Yes, this strikes a professional tone appropriate for a post-interview follow-up. You open with gratitude, reference specific topics from your conversation (the analytics platform), connect your background to the role, and close with clear next steps. The level of formality matches standard business communication.
1. Appropriately focused?
✅ Yes
2. Contains NO REPETITION?
✅ Yes
3. Necessary information only?
✅ Yes
📝 Summary Rationale All content is relevant, focused on answering the user's question, and contains no repetition.
Examples > Example 2: Casual Message
Text & Query
Response
Question
Rating
[Mike's message/query as previously listed]
"No, this is way too casual for a professional request. Using slang like 'fire' and emojis is completely inappropriate when you're asking someone for a job opportunity. You should never use this kind of language with a manager. This makes you look unprofessional and immature. Remove the emoji immediately and rewrite this in proper business English."
1. Appropriately focused?
✅ Yes
2. Contains NO REPETITION?
❌ No
3. Necessary information only?
❌ No
📝 Summary Rationale The response is highly repetitive (using "too casual," "inappropriate," and "unprofessional" to make the same point) and includes unnecessary prescriptive instructions ("Remove the emoji immediately...").
Examples > Example 3: Essay Introduction
Text & Query
Response
Question
Rating
[AI Essay/query as previously listed]
"Your opening effectively establishes historical context and builds toward your specific topic. To increase engagement, consider starting with a concrete example or scenario rather than an abstract historical sweep. For instance, you might open with a brief anecdote about a worker whose job was transformed by AI, then zoom out to the broader historical pattern. This 'particular-to-general' approach helps readers connect emotionally before engaging intellectually."
1. Appropriately focused?
✅ Yes
2. Contains NO REPETITION?
✅ Yes
3. Necessary information only?
✅ Yes
📝 Summary Rationale Although the response is over the standard limit, the extra length is justified given the hybrid nature of the query. The response provides both necessary analysis and a detailed, actionable suggestion (the "particular-to-general" approach). In this context, all the information is considered necessary and valuable, making the overall response a pass for conciseness.

--------------------------------------------------------------------------------
Steps and Requirements - Step 5
5. Evaluate Tone and Style
In this step, you will evaluate the assistant's adherence to a tone that is constructive and supportive, not judgmental or robotic. The response should be balanced, avoid extreme language, and maintain a conversational yet professional style.
Questions
You will answer the following five yes/no questions:
Is the tone of the response professional but friendly?
Yes, the response is respectful and approachable, using a warm but not overly casual tone.
No, the response uses slang, is overly chatty and familiar, or is cold, stiff, and impersonal.
Is the response constructive and kind (not judgmental)?
Yes, the response describes observations supportively and focuses on opportunities for improvement rather than flaws.
No, the response uses harsh, discouraging, or critical language and focuses only on negatives.
Is the response FREE OF strong opinions or emotions?
Yes, the assessment is balanced, objective, and avoids expressing personal preferences (e.g., "I think," "I love") or using emotionally loaded words (e.g., "terrible," "perfect").
No, the response includes subjective judgments or emotional language that makes it sound like a personal opinion.
Does the response AVOID absolute language?
Yes, the response uses nuanced and flexible language, such as "often," "typically," "may," or "consider."
No, the response is overly prescriptive and uses absolute words like "always," "never," "all," "none," or "must."
Does the response demonstrate appropriate formality?
Yes, the response uses a natural, conversational tone that is not overly academic or colloquial.
No, the response uses overly technical jargon, stilted phrasing that sounds like a textbook, or is too casual ("dude," "ya know"). 
Examples > Example 1: Professional Email
Here are contrasting examples to guide your ratings.
Text & Query
Response
Question
Rating
[Sarah Chen's email/query as previously listed]
Yes, this strikes a professional tone appropriate for a post-interview follow-up. You open with gratitude, reference specific topics from your conversation (the analytics platform), connect your background to the role, and close with clear next steps. The level of formality matches standard business communication.
1. Professional but friendly?
✅ Yes
2. Constructive and kind?
✅ Yes
3. FREE OF strong opinions?
✅ Yes
4. AVOIDS absolute language?
✅ Yes
5. Appropriate formality?
✅ Yes
📝 Summary Rationale This response is a clear Pass. The tone is helpful, professional, and balanced. It provides positive, observational feedback without judgment, uses natural language, and avoids any harsh or absolute phrasing, meeting all criteria for a good tone.
Examples > Example 2: Casual Message
Text & Query
Response
Question
Rating
[Mike's message/query as previously listed]
"No, this is way too casual for a professional request. Using slang like 'fire' and emojis is completely inappropriate when you're asking someone for a job opportunity. You should never use this kind of language with a manager. This makes you look unprofessional and immature. Remove the emoji immediately and rewrite this in proper business English."
1. Professional but friendly?
❌ No
2. Constructive and kind?
❌ No
3. FREE OF strong opinions?
❌ No
4. AVOIDS absolute language?
❌ No
5. Appropriate formality?
✅ Yes
📝 Summary Rationale This response is a clear Fail for Tone & Style. It violates multiple core principles by using harsh, judgmental language ("makes you look unprofessional and immature") and strong absolutes ("never," "completely inappropriate"). The tone is condescending and discouraging, not constructive or kind.
Examples > Example 3: Essay Introduction
Text & Query
Response
Question
Rating
[AI Essay/query as previously listed]
"Your opening effectively establishes historical context and builds toward your specific topic. To increase engagement, consider starting with a concrete example or scenario rather than an abstract historical sweep. For instance, you might open with a brief anecdote about a worker whose job was transformed by AI, then zoom out to the broader historical pattern. This 'particular-to-general' approach helps readers connect emotionally before engaging intellectually."
1. Professional but friendly?
✅ Yes
2. Constructive and kind?
✅ Yes
3. FREE OF strong opinions?
✅ Yes
4. AVOIDS absolute language?
✅ Yes
5. Appropriate formality?
✅ Yes
📝 Summary Rationale The response uses a constructive and kind tone by first acknowledging what works well ("Your opening effectively establishes...") before offering a softened suggestion ("consider starting with..."). It is professional, balanced, and empowering.

--------------------------------------------------------------------------------
Steps and Requirements - Step 6
Step 6. Evaluate Actionability
A good response must provide the right type of guidance based on what the user asked for. In this step, you will evaluate whether the response correctly matches the query type you identified in Step 2 (Informational vs. Hybrid).
Based on whether you classified the query as "Informational" or "Hybrid," the system will display one of the two sets of questions below.
Questions
If the query is Informational... You will be asked the following two questions. The goal is to ensure the response provides analysis ONLY and does not incorrectly offer suggestions.
Does the response provide analysis and feedback only?
Yes, the response evaluates or assesses the writing but does not suggest any modifications or changes.
No, the response provides suggestions for changes (e.g., "Try changing X to Y") when the user only asked for an assessment.
Does the response provide text-specific observations?
Yes, the analysis references actual words, phrases, or elements from the user's text.
No, the analysis is generic or template-like and could apply to any piece of writing.
If the query is Hybrid... You will be asked the following two questions.
Does the response provide BOTH analysis AND suggestions?
Yes, the response first describes the current state of the writing (analysis) and then offers specific improvements (suggestions).
The response describes the current state of the writing (analysis) and correctly gives no suggestion.
No, the response is imbalanced, providing only analysis (describing the problem with no solution) or only suggestions (telling the user what to do without providing context or reasoning).
Note: if you select option 2 (correctly gives no suggestion), you won't need to answer the next question.
Are the suggestions specific and actionable?
Yes, the suggestions are concrete, tied to the user's specific text, and can be clearly implemented by the user.
No, the suggestions are vague (e.g., "be clearer"), generic ("use short sentences"), or not directly related to the user's text. 
Examples > Example 1: Professional Email
Query Type: Informational
Text & Query
Response
Question
Rating
[Sarah Chen's email/query as previously listed]
Yes, this strikes a professional tone appropriate for a post-interview follow-up. You open with gratitude, reference specific topics from your conversation (the analytics platform), connect your background to the role, and close with clear next steps. The level of formality matches standard business communication.
1. Provides analysis and feedback only?
✅ Yes
2. Provides text-specific observations?
✅ Yes
📝 Summary Rationale This response is a clear Pass. The user asked an Informational query ("Does this sound professional?"), and the response correctly provides analysis only without giving any unwanted suggestions. The analysis is also text-specific, making it a perfect match for the query type.
Examples > Example 2: Casual Message
Query Type: Informational
Text & Query
Response
Question
Rating
[Mike's message/query as previously listed]
"No, this is way too casual for a professional request. Using slang like 'fire' and emojis is completely inappropriate when you're asking someone for a job opportunity. You should never use this kind of language with a manager. This makes you look unprofessional and immature. Remove the emoji immediately and rewrite this in proper business English."
1. Provides analysis and feedback only?
✅ Yes
2. Provides text-specific observations?
✅ Yes
📝 Summary Rationale This response is a clear Fail. Although the user asked an informational query ("Is this appropriate?"), the response provides highly prescriptive suggestions ("Remove the emoji immediately and rewrite this..."). This violates the core rule for an Informational query, which is to provide analysis only.
Examples > Example 3: Essay Introduction
Query Type: Hybrid
Text & Query
Response
Question
Rating
[AI Essay/query as previously listed]
"Your opening effectively establishes historical context... [as previously listed]"
1. Provides BOTH analysis AND suggestions?
✅ Yes
2. Are the suggestions specific and actionable?
✅ Yes
📝 Summary Rationale This response is a clear Pass. The user asked a Hybrid query ("How can I make...?"), which requires both analysis and suggestions. The response successfully provides both: it starts with an analysis of what currently works ("Your opening effectively establishes historical context...") and then offers a specific, actionable suggestion ("consider starting with a concrete example...").

--------------------------------------------------------------------------------
Steps and Requirements - Step 7
Step 7. Evaluate Educational Value
In this step, you will evaluate whether the response provides insightful reasoning and balanced feedback, rather than just stating a conclusion.
Questions
You will answer the following three yes/no questions:
Does the response provide insight, not just correction?
Yes, the response goes beyond a simple "good/bad" judgment and helps the user understand the principles behind the feedback.
No, the response only states a conclusion (e.g., "This is too casual") or is prescriptive without explaining the effect on the reader.
Does the response explain reasoning?
Yes, the response shows cause and effect, connecting specific observations in the text to the outcome (e.g., "Using 'Hey there!' creates a casual tone that...").
No, the response makes a surface-level observation without explaining why it works or doesn't, leaving the user to guess the reasoning.
Does the response acknowledge the user's writing strength?
Yes, the response gives balanced feedback, validating what the user has done well when appropriate, not just focusing on criticism.
No, the response only focuses on problems or weaknesses, missing an opportunity to validate good elements in the user's writing. 
[!IMPORTANT] Guideline Callouts For the question "3. Does the response acknowledge the user's writing strength?", it is acknowledged that the model might not always explicitly validate the user's writing strength. As long as the model provides balanced feedback and does not only focus on problems or weaknesses (i.e. being overly critical), select Yes for this question.
Examples > Example 1: Professional Email
Text & Query
Response
Question
Rating
[Sarah Chen's email/query as previously listed]
Yes, this strikes a professional tone appropriate for a post-interview follow-up. You open with gratitude, reference specific topics from your conversation (the analytics platform), connect your background to the role, and close with clear next steps. The level of formality matches standard business communication.
1. Provides insight?
✅ Yes
2. Explains reasoning?
✅ Yes
3. Acknowledges strength?
✅ Yes
📝 Summary Rationale This response is a clear Pass. It is educational because it doesn't just say the email is professional; it provides insight by explaining why ("You open with gratitude, reference specific topics..."). This reasoning helps the user learn what makes communication effective, and it clearly acknowledges the strengths of their writing.
Examples > Example 2: Casual Message
Text & Query
Response
Question
Rating
[Mike's message/query as previously listed]
"No, this is way too casual for a professional request... [as previously listed]"
1. Provides insight?
✅ Yes
2. Explains reasoning?
❌ No
3. Acknowledges strength?
❌ No
📝 Summary Rationale This response is a clear Fail. It has no educational value because it is entirely negative and fails to acknowledge any strengths. It provides a correction ("this is way too casual") but offers no reasoning as to why using slang like "fire" or emojis is inappropriate for the context. The harsh tone is more likely to discourage the user than teach them.
Examples > Example 3: Essay Introduction
Text & Query
Response
Question
Rating
[AI Essay/query as previously listed]
"Your opening effectively establishes... [as previously listed]"
1. Provides insight?
✅ Yes
2. Explains reasoning?
✅ Yes
3. Acknowledges strength?
✅ Yes
📝 Summary Rationale This response is a model of educational value. It acknowledges the strength of the original paragraph ("Your opening effectively establishes..."), provides insight by introducing a rhetorical strategy ("particular-to-general"), and explains the reasoning behind that strategy ("helps readers connect emotionally before engaging intellectually"). This teaches the user a transferable writing skill.

--------------------------------------------------------------------------------
Steps and Requirements - Step 8
Step 8. Evaluate Localization
Overview
The response should feel like it was written by a native speaker in the target region. It adapts to local language, culture, and context.
A response fails the localization dimension if it feels "foreign," even if the grammar is technically correct.
Grading Question and Scales
Q. Does the response display content that is appropriate and relevant for your language and region?
Yes: The response is fully appropriate for my language and region
No: The response contains something inappropriate or irrelevant for my language and region
Awkward or clearly machine-translated phrasing
Incorrect mixed languages in the response
Wrong date format (e.g., MM/DD vs DD/MM), units of measurement, or number formatting
Wrong punctuation format for my language/region
Scrambled symbols ( , □, ???, )
Content, examples, or references that don't fit my culture/region
Others. Please specify.
Instructions
If all of the following are true, select Yes for the Localization question:
Input text is in my language with no obviously incorrect or untranslated portions
Dates, numbers and units of measurement display in my local format
No garbled characters appear
All content, including cultural references, punctuations, and examples, make sense for my region
Guideline Callouts
1. Below scenarios are expected and NOT Localization issues:
English proper names of companies, products, games, movies, etc will appear frequently in other languages.
Some languages such as Hinglish use mixed languages.
It's possible that some scenarios use the base language structurally but include a small untranslated portion.
For example, "Send 你好嗎 to Ching Liu."
2. Examples of wrong punctuation format
❌ Cómo estás? Qué sorpresa! Vs ✅ ¿Cómo estás? ¡Qué sorpresa!
❌ Il a dit "bonjour" en souriant. Vs ✅ Il a dit « bonjour » en souriant.
❌ Powiedział "to dobrze" i wyszedł. Vs ✅ Powiedział „to dobrze” i wyszedł.

--------------------------------------------------------------------------------
Steps and Requirements - Step 9
Step 9. Conduct a pairwise comparison before submitting the task.
After you have evaluated each response, you will compare them in pair.
Please base your comparison on the derived scores for each dimension, displayed for you in a table. Share any feedback you'd like the engineering team to be aware of and submit the task.
Figure 3 (Page 22): Screenshot of the "Step 9" interface. It shows a side-by-side comparison of "Response A (left)" and "Response B (right)" with the input text and query. Below the responses, a comparison table shows ratings (e.g., "poor") across dimensions: Accuracy, Conciseness, Tone & Style, Actionability, Educational Value, and Overall Quality. At the bottom is a slider for rating: "Left Much Better," "Left Better," "Left Slightly Better," "About The Same," "Right Slightly Better," "Right Better," "Right Much Better."

--------------------------------------------------------------------------------
Congratulations
You have completed the guidelines for Writing Tools Guidelines - Writing Q&A

--------------------------------------------------------------------------------
END OF GROUND TRUTH Extraction Stats:
Total words extracted: ~3,200
Tables extracted: 14
Figures described: 4 main UI screenshots/diagrams (Page 4, 5, 22) + Recurring background visual.
Completeness: 100% (Sequential extraction followed for all provided pages including examples, rationales, and guideline callouts).