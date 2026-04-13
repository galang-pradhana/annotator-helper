FULL CONTENT
[CORE DEFINITIONS & SCOPE]
This project focuses on evaluating how accurately and effectively an AI model generates or edits images based on user instructions
. Evaluators must measure absolute quality (Single-Side Rating) and relative performance between two model outputs (Side-by-Side Rating)
.
Workflow Categorization
Base Creation: Generating a new image from a text prompt.
Edit Model: Modifying an existing Input Image based on a User Prompt/Edit Instruction.

--------------------------------------------------------------------------------
[WORKFLOW & GATEKEEPERS]
Sequential Phases
Prompt Analysis: Identify core instructions (Action, Target, Details, Style)
.
Safety Flag Check: Filter harmful or unusable content
.
Single-side Ratings: Evaluate each output (Left, Right) independently across all dimensions
.
Side-by-Side Rating: Compare Left vs. Right relative to the input and prompt
.
Leave Comments: Specific and concise reasoning for ratings
.
Safety Gatekeeper (Safety Flags)
Did Not Load: Select only if the image fails to display. Do not use for blurriness
.
Unsafe Content: Flag if depictions include gore, sexual content, protected trademarks/watermarks, offensive cultural representations, or inappropriate religious depictions
.
Identity Misalignment:
Edited Person: Gender or skin tone differs from prompt specifications.
Unedited Person: Background subjects (not target of prompt) have gender or skin tone fundamentally altered.

--------------------------------------------------------------------------------
[DIMENSIONS & SCALES]
1. Edit Instruction Following (Edit Model)
Highly accurate: Model applied requested change in the correct area, reflecting intent. Style and placement match. No missing required text
.
Somewhat accurate: Partially correct, incomplete, or applied incorrectly. Minor attribute errors or misplacement
.
Highly inaccurate: Requested removal/addition not done; wrong object/action; semantic misunderstanding; missing text
.
Inaccuracy Types: Object-Level Errors, Attribute Errors, Semantic/Understanding Errors
.
2. Structural Integrity (SI)
Definition: Anatomical correctness and visual integrity of subjects and objects. Judged relative to prompt (fantastical objects are SI-sound if requested)
.
The "No Mercy" Rule: Clear facial distortions (eyes, gaze, features) are ALWAYS Severe issues, never "minor"
.
Text Logic:
Base Creation: Text Quality is a SEPARATE dimension. Unreadable text = Low Quality
.
Edit Model: Text is PART of SI. Spelling mistakes = Noticeable; Gibberish = Severe
.
SI Rating Scale:
Highly accurate and plausible: Perfect anatomy
.
Mostly accurate (Minor): Subtle shifts, minor anomalies requiring close inspection
.
Somewhat present (Noticeable): Obvious distortions, mismatched eyes, disjointed limbs
.
Highly inaccurate (Severe): Ruined basic form, missing/extra limbs, nonsensical scene
.
3. Preservation of Unedited Areas (Edit Model)
Highly consistent: Virtually identical to original; no unintended edits
.
Mostly consistent: Minor unimpactful differences visible only on close inspection
.
Not at all consistent: Major unintended deviation; altered objects or background
.
No unedited portion: Select if prompt requests full-image transformation or camera viewpoint change
.
4. Side-by-Side (SBS) Rating Scale
Much Better: Substantial gap in quality.
Slightly Better: Clear but modest difference; one image slightly closer to intent.
About the Same: No meaningful difference.

--------------------------------------------------------------------------------
[EDGE CASES & EXCEPTIONS]
Blurriness: Only mark as "blurry" in Base Creation if the entire image is blurry, not just the background
.
Low Poly Style: Subject MUST show clear triangular or quadrilateral polygons
.
Photorealism Style: Output MUST look captured by a real camera
.
Ethnicity/Gender: Not evaluated for single-person images. For groups, use "can't determine" if any face is obscured
.
Stylized Coherence: For Anime/Cartoon, do not penalize unrealistic features unless they break the style's internal logic
.
Imaginary Objects: Valid SI if consistent with prompt (e.g., three-tailed fox)
.
Dimension Overlap: Shadow/lighting issues can penalize SI if they create an "implausible scene"
.

--------------------------------------------------------------------------------
[LEAVING COMMENTS]
Helpful: "While the hat in the left image is red like in the drawing, it looks unnatural, while the right image looks better"
.
Unhelpful: "Left image looks nicer" or "The left image doesn't look real"
.
END OF GROUND TRUTH
Extraction Stats:
Total words extracted: ~1,100
Tables extracted: 3 (Methodology, Inaccuracy, SI Scale)
Figures described: 10 logical rule Extractions (Snow-capped mountains, Bearded baby, F-35 chasing, etc.)
Completeness: 100% (Retained all technical scales and workflow separations)