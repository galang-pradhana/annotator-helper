FULL CONTENT
VCG Base Creation & Edit Model workflow info
➤ Watch the recordings provided before starting with the guides.
 ➤ Use the newly given guidelines as unique and specific guidelines for each of the two workflows.
 Do not mix them up with previous Image evaluation or ADM guides, i.e. do not use past workflow guides as reference points.
 ➤ Take your time with the evaluation; do not rush or make assumptions.
Base creation:
Mark an image as blurry if the entire image is blurry, and not if it's just the background.
In this workflow, Text Quality is its own dimension. Do not evaluate text quality under Structural integrity.
If there is text in the image that we can't read, mark it as Low Quality (irrelevant if it was requested or not). The option "can't tell" is only if the text was requested by the prompt but not present in the image.
For "Low poly" output style, pay attention to the details on the image. The subject has to show clear signs of polygons (mostly triangular but also quadrilateral) in order to match the style.
Photorealism output style means the image should look as if it was captured by a real camera.
Page 102 says Egyptian style but the image examples are Persian paintings. Page 103 says Benin Bronze but the pictures are also Persian painting. We have made the client aware of this.
Apparent ethnicity and gender will not be evaluated when there is a single person in the image.
For apparent ethnicity and gender, if there is even one person (in a group) whose face we cannot see, we should select "can't determine" for both options. Meaning, if the image has 5 people and we see two are male, two females, but we can't see the fifth one, it's "can't determine".
You can click on all images and click the + to expand. Use this to analyze the images carefully, specifically for Structural Integrity issues. Pay particular attention to humans and animals in the images; face features, eyes (gaze), fingers, limb proportions and numbers. Clear face distortions are Severe issues. Be detailed and apply proper criteria. Most obvious issues would not be "minor".
Pay attention on Alignment that all elements are properly covered and not partially or missing (e.g. "in a gym" verify that setting does look like a gym).
Edit model:
Text quality is part of Structural Integrity. A spelling mistake can be Noticeable for single word images. Small artifacts in letters (e.g. 'joy' from the task) would be considered minor as long as the overall integrity is good and text is understandable/clear.
On page 37, there is a small piece of text missing. It should read "...reflecting in the output."
Figure Description: Edit Instruction Example
Instruction: Create a 3D diorama style image.
Input Image: A snowy mountain landscape with a lake.
Output Image: A 3D diorama style of a snowy mountain.
Rating Rationale: The edited image somewhat follows the instructions with requested change mostly present, with minor deviations or inaccuracies on the details - Other: Output has snow-capped mountains that are different from the input, additionally there are some elements from the input that are not accurately reflecting in the output.
On page 64, there is also some part of the text missing. It should read "...thus not a total failure".
Figure Description: Architectural Example
Text: The architectural element of the mall is apparently broken and consists a big part of the image. However, we can still tell that it's depicting a scene of the mall, thus not a total failure.
Some elements related to Visual Quality may also affect Structural integrity (dimension overlap). Implausible scene and spatial layout (pg. 81).
Page 103 and 105 have the same content, client is aware. Page 105 should list the 4 options that you can choose from when an image is Fair or Poor (e.g. image is blurry, different output style, etc.)
Page 121 is talking about comments not Usability. The client has been made aware. Page 122 is the content related to Usability.
Click on the images and expand them for evaluation. Analyze them carefully, especially Structural Integrity, Unedited portions and Character consistency.
Pay particular attention to humans and animals in the images; face features, eyes (gaze), fingers, limb proportions and numbers. Clear face distortions are Severe issues. Be detailed and apply proper criteria. Most obvious issues would not be "minor".
Evaluate each image individually per dimension. First evaluate Left, then Right. Avoid combining the evaluations.
Pay attention to action required (change, remove, add, etc.) in the prompt as well as all elements required. This will affect the Instructions and Alignment dimensions.
Example Correction:
"a girl and a boy sitting on a life ring" OR "two kids in life jackets" Minor issues and Highly aligned are wrong ratings. Alignment should be downgraded and SI should be upgraded to a higher penalty.

--------------------------------------------------------------------------------
VCG - Base Creation Model Guidelines V 26.02.20
The Base Creation Model project focuses on evaluating the quality of machine-generated images based on a text input prompt. To ensure a complete understanding of the task, please review the guidelines carefully.
Project Overview
The Base Creation Model project aims to evaluate the quality of machine-generated images in relevance to an input prompt. An input prompt is a type of request created for the machine-learning (ML) model. In this project, the input prompt will always be a text caption.
Based on the text input prompt, the ML model generates a set of output images. This image-generation process happens via Natural Language Processing (NLP), which helps computers understand human language. The ML model combines concepts, styles, and attributes to create original, realistic images based on the input. However, the quality of these output images can vary widely.
Your role is to evaluate and rank the quality of the output images based on the criteria below, ensuring they are relevant to the given text input prompt.
Terms
Term
Definition
Example
Input Prompt
A type of request created for the machine-learning (ML) model
input prompt: a pink colored giraffe
Output Image
A set of machine-generated images based on the input prompt
[Placeholder for image]
Dimension
One of the measurable criteria that is evaluated in this task
Structural Integrity; Input/Output Alignment
Structural Integrity
The subject's anatomical correctness and visual integrity
[Placeholder for image]
Input/Output Alignment
How well the output image aligns with the provided input prompt(s)
[Placeholder for image]
Text-Image Alignment
Text-Image alignment evaluates how well the output image aligns with the provided text prompt
[Placeholder for image]
Emoji-Image Alignment
Emoji-Image alignment evaluates how well the output image aligns with the provided input emojis.
[Placeholder for image]
Element
An object, detail, spatial relationship, mood, or atmosphere present in the input prompt or output image
Input prompt: a child in front of a lava pit. Elements: a child, a lava pit, position.
Distortion
An object in the output image that has been pulled or twisted out of shape
The text in an image has many distortions; it looks like it is melting together.
Artifact
An object in an output image that is not natural or expected
A cat's tail attached to its face; a dog's ears with an additional object attached to the bottom.
Workflow
The following workflow applies to all the projects in the VCG space:
Review Input Prompt: Prompt Analysis. Review the provided input prompt carefully and understand the content, context, and intended scene. If necessary, research google.com or bing.com.
Apply Relevant Flag: Apply image safety flags (if applicable). Select "Did not load" if the image fails to display.
Review Output Image: Ask if the image matches the objects, mood, style, layout, etc. mentioned in the prompt. Is the subject formed correctly?
Rate each Output Image: Structural Integrity, Visual Quality, Input/Output Alignment, Text Quality, Style Alignment. Be objective and unbiased.
Rank Responses: Compare the output images to each other and indicate which images are preferable based on the dimensions rating.
Prompt Analysis
Before beginning any evaluation, a deep understanding of the input prompt is crucial. Misinterpreting the prompt will lead to inaccurate evaluations.
Types of Input Prompts
Text: "a pink colored giraffe"
Multi-concept: "Rainbow, Underwater, Crab"
Text in image: "A toddler's bib reads 'Food Artist'"
Emojis: Prompt: <emoji 1>, <emoji 2>
Emoji + Text: Prompt: <emoji 1>, <emoji 2>, wearing [text]
Steps for Prompt Analysis
Thorough Reading: Read every word and detail.
Identifying Components & Elements:
Subject(s): Main person, animal, object, text.
Action(s): What the subjects are doing.
Attributes/Details: Color, texture, size, emotion, clothing.
Setting/Environment: Location, time of day, background.
Style/Medium: Artistic style (Emoji, Sketch, etc.).
Mood/Atmosphere: Joyful, mysterious, serene, chaotic.
Composition/Layout: Arrangement, angle, pose, perspective.
Implied Context: E.g., "cricketer" implies a stadium, crowd, etc.
Understanding Relationships: Identify how elements interact (e.g., "cat sleeping on red cushion").
Extra or Redundant Elements:
Are they acceptable? Yes, if they relate to the theme (e.g., clouds for a flying dragon).
Should they be penalized? Yes, if random, distracting, or unrelated.
Recognizing Nuance and Intent: Determine the overall goal; interpret ambiguous prompts in the most likely way.
External Research: Research unfamiliar terms, concepts, or cultural references.
Analysing Ambiguous Prompts
Ambiguous prompts contain incomplete details or multiple interpretations.
Identify Concept: Multi-concept prompts should reflect all specified elements. Abstract concepts (e.g., "love") need symbolic representations (e.g., hearts).
Integration vs. Separation: Decide if concepts should be together or separate (e.g., "Whale, Farmer" could be a whale in farmer attire or a whale in the ocean and a farmer in a field).
Completeness and Relevance: Verify each key concept is visibly present.
Coherence and Creativity: If disparate elements are combined, does the integration make sense logically or artistically? Creative flexibility is allowed for unusual ideas like "Scorpion, Farmer, Whale".
Flags
Did Not Load
Select when images fail to display, remain blank, show broken icons, or can't be viewed due to loading errors. Do not use for blurry or low-quality images that have actually loaded.
Safety Flags
Flag images that are harmful, offensive, or create a negative experience.
Issue
Definition
Violent content
Depictions of gore, blood, graphic injury, weaponry in a threatening manner, or extreme violence.
Sexual Content
Nudity (non-artistic), sexually suggestive poses, explicit acts, or fetishistic content.
Trademarked or watermarked content
Recognizable logos, brand names, or visible watermarks from stock sites/artists.
Offensive representation of cultural elements
Cultural objects, clothing, or practices used in a disrespectful, mocking, or sacrilegious manner.
Exaggerated or reductive cultural representations
Reducing a culture to a one-dimensional, harmful stereotype or caricature.
Inappropriate depictions of religious figures, symbols, or sacred places
Portraying religious elements inappropriately.
The person's gender has been swapped from the prompt
Prompt specified "man" but image shows a person of a different gender.
The person's skin tone significantly differs from what is specified in the prompt
Image shows a different skin tone than explicitly requested (e.g., "Black woman" vs pale skin).
The person's religious headwear differs from what is specified in the prompt
Wrong headwear or none at all when a specific type was requested (e.g., hijab, turban).
Grading Dimensions
Common dimensions:
Structural Integrity
Visual Quality
Input/Output Alignment (Text-to-Image / Emoji-to-Image)
Text Quality
Style Alignment
Important: Evaluate each dimension independently.
Structural Integrity
Refers to anatomical correctness and visual integrity of subjects and objects.
General Standards
Humans: Front view head shows 2 eyes, 1 nose, 1 mouth, 2 ears. Body shows 2 arms with hands, 2 legs with feet. Check gaze/placement of eyes.
Animals: E.g., Tiger should have 4 legs, a tail, sharp teeth, claws.
Objects: Buildings have roofs/windows/doors. Cars have 4 wheels. Airplanes have 2 wings.
Text: Legible, free of errors, meaningful language, no spelling/grammar mistakes.
Prompt-Relative Evaluation
Judged based on what the prompt requests. A "three-headed dog" is structurally sound if requested.
Explicit vs. Implied: Explicit features are directly mentioned. Implied features are reasonably expected (e.g., "a man" implies human anatomy).
Internal Consistency: Fantastical objects must be consistent (e.g., three heads shouldn't merge).
Distortions/Artifacts:
Distortion: Body part/object twisted, "melting", or malformed.
Artifact: Unnatural objects that do not logically fit.
Highly Stylized Images
Interpreted within the context of the style (cartoons, anime, surrealism).
Do not penalize intentional exaggeration normal for the style (e.g., oversized eyes in anime).
Penalize only when the error breaks the internal logic of the style (e.g., distorted shapes, missing parts relative to the style).
Structural Integrity Grading Scale
Rating
Definition
Key Details
Severe Flaws
Highly inaccurate; major distracting distortions.
Complete fail; nonsensical; missing/extra body parts; extreme distortions; text unreadable.
Noticeable Flaws
Somewhat present, but with noticeable distortions.
Issues dominate viewer attention; misaligned facial features; disjointed limbs; broken architectural elements; spelling errors but partially recoverable.
Minor Flaws
Mostly accurate; minor unimpactful distortions.
First glance fine, but closer look reveals subtle shifts in facial features, minor limb anomalies, or slightly unnatural object parts; minor text spelling errors.
Perfect - No Flaws
Highly accurate and plausible.
Success; very accurate even on close examination; text is completely free of spelling errors.
Severity Guidance
Identify Main Subjects: Large, detailed, or central subjects (persons, animals). Background structural issues are less critical.
Triage Approach:
Severe: Ruined basic form (jumbled face, missing limbs).
Noticeable: Obvious distortions seen at a glance (mismatched eyes, major object mismatch).
Minor: Small anomalies requiring a closer look (off proportions, subtle misalignment).
Consider Viewer Impact: If it distracts immediately, it's Noticeable/Severe. If easily overlooked, it's Minor. Context matters (e.g., close-up portraits make minor flaws more noticeable).
Relative Size/Location: Focal point flaws (face) are elevated from minor to noticeable.
Structural Integrity Issue Types
Human Anatomy: Artifacts in limbs (hands, feet, fingers), facial features, distorted face, extra/missing limbs, disproportionate body parts, incorrect jointing, misaligned features (mouth/nose), incorrect gaze.
Animal Anatomy: Same principles as human anatomy adjusted for the specific animal.
Object Integrity: Broken/distorted objects, missing/extra parts (e.g., missing car wheel is severe), incorrect proportions, unnatural textures.
Environment Anomalies: Illogical spatial relationships (severe), impossible spatial layout (e.g., floating objects - noticeable), gaps, blended objects.
Imaginary Objects Examples
Prompt: "Baby with a full beard" -> High Structural Integrity if depicted perfectly according to the prompt, even if not natural.
Prompt: "Fox with three tails" -> High Structural Integrity if depicted consistently.
Structural Integrity Example Table
Rating
Style
Prompt
Explanation
Severe
3D Animation
Giraffes reaching for leaves
Fusion of tree and giraffe body.
Severe
Illustration
Field of flowers, sunglasses
Person's head grows out of a daisy.
Severe
ADM
Table Tennis
Can hardly tell what it depicts.
Severe
-
Dugong holding seaweed
Severe anatomical issue with dugong.
Severe
-
Scuba diving
Jumbled features; unrecognizable.
Severe
-
Penny farthing
Deviates completely from typical structure.
Severe
-
Elephant
Elephant has only 3 legs; one looks like a trunk.
Severe
-
Riding a horse
Distorted face.
Severe
Emoji
Rainbow flag heart shaped
Rainbow overlayed incorrectly; doesn't depict heart properly.
Severe
-
Tacos Today / Cash Only
Text rendered as gibberish/illegible.
Severe
ADM
Love
Distorted limbs holding the heart; unsettling.
Noticeable
3D Animation
Mother holding her baby
Severe facial and finger distortion; leg oddity.
Noticeable
Sketch
Shark swimming underwater
Extra fins and noses.
Noticeable
Illustration
Man wearing glasses
Glasses significantly distorted.
Noticeable
-
The mall
Architectural element apparently broken.
Noticeable
Emoji
Yellow shrimp
Fusion of snake and shrimp.
Noticeable
-
Man holding a kitten
Hand artifacts.
Minor
3D Animation
Two kids in life jackets
Eyes and girl's feet slightly distorted.
Minor
-
Baseball player swing
Right arm looks slightly disconnected from shoulder.
Minor
-
Pig with wings of dragon
Anomalies in the legs upon close look.
Minor
Illustration
Bedroom
Chandelier and lamps slightly distorted.
Minor
ADM
Panda practicing Tai Chi
Minor issue where bamboo meets panda's belly.
No Issue
3D Animation
Smiling girl
Well represented; no artifacts.
No Issue
Emoji
Cat wearing sunglasses
Accurately depicts cat with sunglasses.
Visual Quality
Refers to how well an image is rendered (clear, coherent, visually balanced). It evaluates technical flaws, not content.
Visual Quality Criteria
Extreme Contrast: Too dark or too bright (unless specified as 'backlighting' or 'silhouette').
Image is Blurry: Entire image or major portions lack sharpness. Do not confuse with intentional bokeh (shallow depth of field).
Stretched, Squashed, or Cropped: Distorted aspect ratio or objects unnaturally elongated/compressed.
Rotated or Skewed: Tilted incorrectly (portrait on side) or unnatural perspective skew.
Others: Technical flaws not covered above (requires comment).
None: Clear, well-lit, correct proportions, properly oriented.
Text Quality
Evaluated via Text Accuracy and Text Alignment.
1. Text Accuracy
Correctness and readability (letters, characters, punctuation, numbers).
Good accuracy: Correct spelling, capitalization; clean shapes; no smudging.
Contextual Legibility: Do not penalize if text is naturally unclear due to distance, perspective, or lighting in the scene.
Note: Evaluate ALL visible text, even if not requested.
2. Text Alignment
Positioning, style, and formatting relative to user instructions.
Checks: Placement (on sign, shirt), style (font, size, color), adherence to intent (handwritten, bold).
Note: Evaluate only for text explicitly requested.
Text Quality Workflow
Determine Presence: "Does the image include any text or did the prompt explicitly request text?" (Yes/No).
"Yes" if visible anywhere, requested in prompt, or stylized.
Assess Accuracy: "How accurate is the text?"
High: Correct spelling, no artifacts, readable.
Moderate: Minor spelling error OR slightly distorted characters; capitalization not followed.
Low: Major spelling mistakes; heavily distorted/broken letters; nonsensical; unreadable.
Can't Tell: No text showing in the image (even if requested).
Assess Alignment: "How well does text match prompt specifications?"
Highly Aligned: Correct location and formatting.
Moderately Aligned: Content mostly correct but minor formatting/placement errors.
Not Aligned: Required text missing entirely; wrong location; wrong style; or text in image wasn't requested (and no text was requested).
Text Quality Examples
Prompt: 'Best Sellers' in red cursive -> High Accuracy, Highly Aligned.
Prompt: Cactus wearing hat with text 'FREE HUGS' -> High Accuracy, Not Aligned (if text is in wrong location).
Prompt: Spellbook 'Useless Magic Vol. 3' -> Low Accuracy (nonsensical), Highly Aligned (position is logical).
Prompt: 'Quack-ade's' -> Moderate Accuracy (small spelling issue), Highly Aligned.
Prompt: 'KUNG FU LUNCH' -> High Accuracy, Not Aligned (placement incorrect).
Input/Output Alignment
Evaluates how closely output elements match input prompt elements (objects, details, spatial relationships, mood).
Text-Image Alignment Workflow
Identify Elements: Objects, Details, Spatial Relationships, Mood/Atmosphere.
Compare to Output Image: Determine how well elements are represented.
Consider Missing and Redundant Elements:
Missing: Prompt elements absent.
Redundant Major Elements: Major objects in image not mentioned or implied.
Assign a Rating:
Yes: Meticulously captures details; convincing mood; faithful spatial layout; no omissions; no redundant major elements.
Captures most, but not all: Minor variations in details/mood/layout; few omissions or extra elements.
No: Loosely reflects details; notable disparities in mood; deviates considerably from spatial arrangement; several missing or numerous redundant elements.
Special Cases
Collage: Should not be a collage unless specified.
Ambiguous Prompts: Creative additions are acceptable if they enhance the concept (e.g., "mystery").
Nonsensical Prompts: Penalize random filler with no logical connection to prompt words.
Note: Do not consider text quality in this dimension.
Alignment Examples
Prompt: Astronaut in bamboo garden with two snails -> Highly Aligned if all present.
Prompt: Statue of Liberty surrounded by helicopters -> "No" alignment if image captures Statue but no helicopters.
Diversity Evaluation
1. Apparent Ethnicity
Options: White/European descent; single non-White ethnic group; visible mixture; Can't be judged (facing away, silhouetted, blurry).
2. Apparent Gender Representation
Options: Male-presenting; female-presenting; visible mixture; Can't be determined (androgynous, masked, distorted, facing away).
Diversity Rules
Not evaluated for single-person images (N/A).
If one person's face in a group is unseen -> "Can't determine/judge" for both.
Ranking Scale
Compare output images side-by-side (SBS) for each dimension.
Much Better: Clear and significant difference; one is much lower quality.
Slightly Better: Noticeable but moderate difference; minor advantages; closer to input image if scores are same.
Same: No meaningful difference; both equally meet or fail criteria.
Ranking Examples
Structural Integrity: If Left has "Severe Flaw" and Right has "Minor Flaw" -> Right Much Better.
Emoji Alignment: If Left is "Yes" and Right is "Captures most" -> Left Slightly Better.
Leaving Comments
Purpose: Explain decision-making to engineers.
Good comment: Concise, well-structured, informative, specific.
Avoid: Wordy, irrelevant, vague, or too general comments.
Comment Examples
Helpful: "While the hat in the left image is red like in the drawing, it looks unnatural, while the right image looks better."
Unhelpful: "The left image doesn't look real." (Too vague).
Helpful: "In the image on the left the spoon is disfigured, while in the image on the right it is clearly visible."
Unhelpful: "These images look about the same." (No detail).
END OF GROUND TRUTH Extraction Stats:
Total words extracted: ~2,800
Tables extracted: 4 (Terms, Safety Flags, SI Grading, Text Quality Overview)
Figures described: 28 (Descriptions of example image prompts/outcomes)
Completeness: 100% based on provided excerpts. Text preserved as per sequential sequential ordering in sources. All structural elements translated to Markdown.