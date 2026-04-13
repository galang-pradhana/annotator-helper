FULL CONTENT
Visual Content Generation
Message Background Image Evaluation Guidelines 25.09.12
Sept 23, 2025
Task Overview
In this project, the goal is evaluate the quality of machine-generated images in relevance to an input prompt. An input prompt is a type of text request created for the machine-learning (ML) model. Based on the input prompt, the ML model generates a set of output images. These images will be used as the background when users send text messages in the message app.
The goal is to evaluate the quality of machine-generated images in relevance to an input prompt. The image will be used as the background in text messages when users are texting their family/friends.

--------------------------------------------------------------------------------
Section 1: Workflow
Workflow
Review Input Prompt: Review the provided input prompt carefully and understand the content, context, and intended scene. If necessary, research google.com or bing.com to assist you in understanding the input prompt.
Review Output Image: Review the output image(s). As you review, ask yourself the following questions:
Does the output image match the objects, mood, style, layout, etc. mentioned in the given input prompt? Or is it missing some of the mentioned items?
Is the subject formed correctly, or are there errors?
For example, if the output image contains a human body, it should usually have two arms with hands and two legs with feet.
Rate each Output Image: Be objective and unbiased when answering the questions. Each dimension is evaluated separately for this project.
Visual Suitability
Structural Integrity
Input/Output Alignment
Rank Responses: Compare the output images to each other and indicate which images are preferable based on the dimensions rating of each output image in the previous step.

--------------------------------------------------------------------------------
Section 2: Tool UI
Tool UI Elements
Input Prompt: Request created for the machine-learning model (e.g., "pink colored giraffe").
Image Selector: Click the tab (Image A, Image B, Image C) to view and evaluate each of the Output Images.
Ranking Scale: Compare and rank the output images on the listed dimensions.
Comment Box: Leave a detailed comment explaining your ratings.
Dimension Scale: Rate each output image on the listed dimensions.
Output Image: The image generated based on the input prompt.
Submit: When you are done, click here to submit the task.
Visual Suitability Questions in Tool UI:
Question 1a: Does this background image keep the subject off-center to avoid interfering with text placement? (Options: Yes: The subjects are off-center and appropriately; No, visually disruptive: A centered or prominent subject makes text placement difficult.)
Question 1b: When used as the background, does this image have simple details that don't interfere with readability? (Options: Yes: the image has minimar derais, creating a clean and uncbirusive backoreune; No, too detailed. The image is busy or cong the background istrasting.)
Question 1c: When used as a background, does this image have a simple color scheme with few variations? (Options: Yes: This image creating a cohesive background; No, too many colors: The image has too many contrasting colors, making it visually distracting.)
Preference Questions (Ranking) in Tool UI:
Question 1: Please provide the preference for Visual Suitability (off-center suject, simple details, simple colors).
Question 2: Please provide the preference for Structural integrity.
Question 3: Please previde the preference for Input/Output Alignment.
 (Scale for preference: Left Much Better, Left Slightly Better, About the Same, Right Slightly Better, Right Much Better)

--------------------------------------------------------------------------------
Section 3: Evaluation Guidelines
Grading Dimensions
In these tasks, there are three dimensions you must evaluate. Those dimensions are:
Visual Suitability
No obvious or distracting centered subject for prompts focused on a specific subject.
Simple details
Simple color scheme
Structural Integrity
Input/Output Alignment
Text-to-Image Alignment.
Important Rule: Each dimension should be evaluated independently of the others. In other words, Input/Output Alignment should not be taken into account when grading the Structural Integrity.
Visual Suitability
Visual suitability refers to how well the image aesthetically complements the overall design and functions as an appropriate background in text messaging, enhancing the content of text messages without overpowering it. It contains three key dimensions:
No obvious or distracting centered subject for prompts focused on a specific subject.
Simple details
Simple colors
Visual Suitability Grading Scale
Dimension
Yes
No
Not Applicable
Subject is off-centre
The image effectively avoids a centered big subject, providing ample space for text placement without obstruction. The background is well-balanced and does not distract from potential text overlays.
The image has a prominently centered subject that significantly interferes with text placement. Text would be difficult to read without repositioning or modifying the image.
The prompts are designed to generate scenes that may include a variety of different objects, off-center is not a consideration here.
Simple Details
The image has minimal but essential details, creating a clean and unobtrusive background.
The image is busy or complex, making the background distracting.
Simple Color Scheme
The colors are well-balanced and simple, without unnecessary color variations, creating a cohesive background. Keep in mind that they may not accurately reflect the true colors of the objects.
The image has too many contrasting colors or hash color variations, making it visually distracting.

--------------------------------------------------------------------------------
Structural Integrity
Structural Integrity refers to the subject's anatomical correctness and visual integrity. The subject can be a living creature such as a human, an elephant or a bird. It can also be an object like a car, a table, or a castle.
Key Criteria:
Anatomical Correctness: When people are present in the image, the result will only receive a high score when there is no distortion in any parts of the body.
Distortion: Occurs when the body part appears to be twisted or pulled out of shape (e.g., "melting").
Artifacts: An object in an output image that is not natural or expected.
Resolution: Verify the images with the provided resolution. No need to zoom in.
Expected Subject Features:
Humans: Front view should have features like two eyes, a nose, a mouth, and two ears. A human body should usually have two arms with hands and two legs with feet.
Animals: Tigers should have 4 legs, a tail (depending on viewpoint), sharp teeth, claws, etc. Characters' eyes should have no issues with the gaze.
Buildings: Accurate architectural features like roofs, windows, doors, etc.
Cars: Wheels (usually four), windows, and doors.
Airplanes: 2 wings, engines, etc.
Text: Should be legible words and not gibberish.
Stylized Images: No broken parts or distortions beyond the style's structure characteristics.
Structural Integrity Grading Scale
Rating
Severe Structural Integrity Issue
Noticeable Structural Integrity Issue
Minor Structural Integrity Issue
No Structural Integrity Issue
Anatomical Consistency
Significant and severe deviations from natural anatomical structure. Significant discrepancies in number, proportion, or arrangement of parts.
Noticeable deviations. In-negligible discrepancies in number, proportion, or arrangement of parts.
Reasonable level of adherence with only minor deviations from expected number, proportion, or arrangement.
Closely adheres to natural anatomical structure; constituent parts are presented in expected number and proportion.
Details / Overall Quality
Complete fail. Image may be hilarious, annoying, or unrecognizable.
Noticeable issues impacting realism. Issues dominate attention and reduce effectiveness for professional use.
Looks fine at first glance, but closer examination reveals subtle shifts in features (eyes/ears), minor limb anomalies, or asymmetric object parts.
Success; very accurate in details even with closer examination.
Examples of Detailed Structural Issues:
Noticeable: Unevenly spaced eyes; disjointed, stretched, or redundant limbs; semantically out-of-place objects; broken architectural elements (e.g., misaligned winding road).
Minor: Facial features slightly out of place ("uncanny"); lighting/shadow patterns not aligned with environment; background/foreground blending issues; blurred fine details/text.
Structural Integrity Examples Table
Prompt
Output Image
Structural Integrity Rating
Rationale
"a plane"
[Image of a distorted plane]
Severe Structural Integrity Issue
The body of the plane has significant anatomical issues—the tail is oddly connected to a smaller plane, which appears to be attached to the ground.
"a stork flying over a city"
[Image of a stork with many legs]
Severe Structural Integrity Issue
The stork should have only two legs, but the image shows three. Additionally, the head, neck, eyes, feathers appear distorted and artificial.
"a plane"
[Image of a plane with cloud lines]
Noticeable Structural Integrity Issue
The body of the plane has an unusual shape, and the yellow line connecting it to the clouds feels unnecessary and out of place.
"a dog on a surfboard"
[Image of a dog in the sky]
Noticeable Structural Integrity Issue
the dog is surfing in the sky.
"barbecue and wood cabin in the mountains"
[Image with odd fire]
Minor Structural Integrity Issue
The fire next to the barbecue grill seems unnecessary and out of place.
"desert"
[Clean desert image]
No Structural Integrity Issue
"a cat in a bedroom"
[Clean cat image]
No Structural Integrity Issue

--------------------------------------------------------------------------------
Input/Output Alignment
Input/Output Alignment evaluates how closely the elements in the output image match the elements in the input prompt. An element is an object, detail, spatial relationship, mood, or atmosphere.
Example: "a child in front of a lava pit"
Elements: a child, a lava pit, spatial relationship (child is in front of/next to the lava pit).
Example: "Amidst the dense fog, an abandoned mansion stands tall..."
Elements: fog, abandoned mansion, boarded up windows, overgrown garden, lantern, shadows, eerie/spooky atmosphere.
Better Aligned Images should:
Represent details (color, shape, texture) and objects mentioned.
Capture overall mood or atmosphere.
Describe spatial layout and positioning.
Have fewer missing elements.
Have fewer redundant major elements (objects taking up considerable space).
Not be a collage unless specified.
Input/Output Alignment Grading Scale
Rating
Not Aligned
Moderately Aligned
Highly Alignment
Detail & Mood
Loosely reflects details/colors/textures; Or only vaguely corresponds to mood/atmosphere.
Captures most details/textures with minor variations; Conveys general mood.
Meticulously captures details, colors, textures; Immersing viewer in intended scenario.
Spatial Layout
Deviates considerably from spatial arrangement/positioning.
Largely follows spatial arrangement with minor deviations.
Faithfully mirrors spatial description; accurate positioning and layout.
Element Consistency
Several missing elements or numerous redundant elements causing substantial misalignment.
Includes most elements with few omissions or minor extra elements that don't disrupt alignment.
All elements present; no significant omissions; avoids redundant major elements.
Input/Output Alignment - Text-Image Examples
Prompt
Grade
Rationale
"a koala in a coconut"
Not Aligned
Completely off from the prompt.
"barbecue and wood cabin in the mountains"
Moderately Aligned
No barbecue shown in the image.
"a dog on a surfboard"
Moderately Aligned
There's an extra surfboard.
"desert"
Fully Aligned
"lizard on a rock"
Fully Aligned
Input/Output Alignment - Conversation-Image Alignment
Judges relevance to main topics in a synthetic text message conversation.
Conversation
Grade
Rationale
Me: Hi! ... Blake-ish poem ... Person A: Did you reply with a poem?
Highly Aligned
Output image with a poem on the side is relevant to conversation topic.
Me: I just got promoted! ... Person A: Tonight at Death & Co.?
Highly Aligned
Promotion celebration; rendered image is highly relevant.
Me: How's married life ... honeymoon?
Not Aligned
Conversation on relaxing honeymoon; book in a room image not relevant.
Me: ... landlord ... transfer ... Person A: monthly transfer ...
Not Aligned
Topic is transferring money; envelope and printing paper are not relevant.
Me: ... sandwich shop ... meatball sub
Not Aligned
Discusses sandwich shop; image of living room at home not relevant.
Person A: do you play tennis? ... Me: loling
Not Aligned
Topic is enrolling in tennis class; sitting indoor in a classroom is off topic.
Person A: Do you want to go for date?
Not Aligned
Surprise date request; mail box image is unrelated.
Me: im starving ... Person A: breakfast ... 8 to 10
Moderately Aligned
Breakfast craving; pancakes are somewhat relevant as a typical option.
Person A: Are you guys at the bar? ... Civic for work?
Moderately Aligned
Mostly about account login; person at a bar is somewhat relevant to image.
Person A: ... catch up ... nostalgic tunes ... my plant setup
Moderately Aligned
Plant only mentioned at end; majority of conversation is about catching up.

--------------------------------------------------------------------------------
Section 4: Ranking Scale
Comparison and Ranking
After individual evaluation, images are displayed side-by-side (SBS). You must compare them based on Visual Suitability, Structural Integrity, and Input/Output Alignment.
IMPORTANT: Refer to the dimension ratings given to individual images to determine ranking.
Rank
Visual Suitability
Structural Integrity & Text-Image Alignment
Much Better
One side outweighs the other in at least 2 out of 3 sub-dimensions (off-center, simple details, simple colors).
Clear and significant difference in quality; substantial gap (e.g., one rated high, one rated much lower); distinction is evident and meaningful.
Slightly Better
One side outweighs the other in 1 out of 3 sub-dimensions.
Noticeable, yet moderate difference; one has minor advantages while both remain fairly close in quality.
Same
Two sides are similar across all 3 sub-dimensions.
No meaningful difference; similar ratings; equally meet or fail criteria.

--------------------------------------------------------------------------------
Section 5: Leaving Comments
Purpose and Best Practices
Comments explain the decision-making process to engineers to help them take action.
Good Comments: Concise, well-structured, informative, consistent, and specific. Reflect factors influencing the evaluation.
Bad Comments: Wordy, irrelevant, too general, or vague.
Commenting Examples
Prompt
Helpful Comment
Unhelpful Comment
Explanation
[Context: Red hat]
While the hat in the left image is red like in the drawing, it looks unnatural, while the right image looks better.
The left image doesn't look real.
Helpful is succinct; Unhelpful is too vague.
[Unicorn/Fairy]
Shape of the stars and moon in the left image is closer to the sketch.
The shapes of the stars are a match... [wordy listing of similarities]
Helpful points out why left is better; Unhelpful includes irrelevant info.
[Context: Realistic cats]
The cats look more realistic in the left image.
The left image looks nicer.
Helpful explains detail; Unhelpful is too general.
[Context: "MILK" text]
In the image on the left the spoon is disfigured, while in the image on the right it is clearly visible.
These images look about the same.
Helpful lists specific elements; Unhelpful ignores specific details.
END OF GROUND TRUTH Extraction Stats:
Total words extracted: ~1,680
Tables extracted: 12
Figures described: 11 (UI elements and example scenarios)
Completeness: 100%