Nice catch re: ML Kit — that changes things a *lot* in a good way 👍

You basically now have:

* **Exact facial regions from ML Kit** (landmarks + contours) via `react-native-mlkit` in Expo. ([Infinite Red Docs][1])
* **Gemini Flash 2.5 Vision** that can read the selfie and emit **structured JSON**, but no masks/polygons.

So the plan is:

* **No more (x, y)** from Gemini.
* Every local issue is anchored to a **ML Kit region name**, with:

  * `region`: *exact ML Kit landmark/contour string*
  * `intensity`: 0–1
  * `area`: 1–10 (for your dot size)
  * `description`: human-readable text

And we’ll run Gemini in **multiple passes** (global → clusters), each time feeding previous JSON into the next prompt.

Below is:

1. The **final JSON shape** you should aim for.
2. The **valid `region` values** from ML Kit.
3. The **multi-step Gemini prompting algorithm** (global + clusters).
4. A clear **FastAPI flow** using these steps.

---

## 1. Final JSON result shape

This is what your FastAPI endpoint should ultimately return to the app for one selfie:

```jsonc
{
  "global_profile": {
    "skin_type": {
      "label": "combination",            // "dry" | "oily" | "combination" | "normal" | "unknown"
      "confidence": 0.86
    },
    "skin_tone": {
      "lightness": "medium",             // "very_light" | "light" | "medium" | "tan" | "brown" | "dark"
      "undertone": "neutral"             // "yellow" | "neutral" | "red" | "olive" | "unknown"
    },
    "skin_age": {
      "estimated_age": 27,
      "relative_to_real_age": "similar"  // "younger" | "similar" | "older" | "unknown"
    },
    "scores": {
      "overall": 78,                     // 0–100, 100 = best
      "wrinkles": 65,
      "dark_circles": 52,
      "oily_shine": 40,
      "pores": 55,
      "blackheads": 60,
      "acne": 70,
      "sensitivity_redness": 50,
      "pigmentation": 45,
      "hydration": 55,
      "roughness": 60
    },
    "summary_description": "Combination skin with some T-zone shine, visible pores on the cheeks, mild brown spots and under-eye dark circles."
  },
  "issues": {
    "oily_shine": [],
    "dryness_dehydration": [],
    "enlarged_pores_texture": [],
    "blackheads": [],
    "acne_active": [],
    "acne_scars_post_inflammatory": [],
    "pigmentation_brown_spots": [],
    "freckles": [],
    "melasma_like_patches": [],
    "redness_sensitivity": [],
    "wrinkles_and_fine_lines": [],
    "eye_bags": [],
    "dark_circles": [],
    "moles_or_nevi": []
  }
}
```

Each entry inside `issues.*` is an **IssueItem**:

```jsonc
{
  "region": "leftCheekCenter",          // must be a valid ML Kit landmark/contour
  "intensity": 0.8,                     // 0–1, 1 = very severe/obvious
  "area": 6,                            // 1–10, 10 = largest/widest region
  "description": "Oily shine with enlarged pores on the left cheek."
}
```

No `image_quality`, no `eye_eyelid_details`, no raw coordinates.

---

## 2. Valid `region` values from ML Kit

You’re using the Expo `react-native-mlkit` wrapper, which exposes:

### 2.1 FaceLandmarkType values (points) ([Infinite Red Docs][1])

From the docs:

* `leftEye`
* `leftMouth`
* `leftEar`
* `noseBase`
* `leftCheek`
* `rightEye`
* `rightMouth`
* `rightEar`
* `rightCheek`
* `bottomMouth`
* `leftEarTip`
* `rightEarTip`

These are the classic ML Kit face landmarks: eyes, nose, cheeks, mouth, ears. ([Google for Developers][2])

### 2.2 FaceContourType values (curves / regions) ([Infinite Red Docs][1])

Also available in the same package:

* `faceOval`
* `leftEyebrowTop`
* `leftEyebrowBottom`
* `rightEyebrowTop`
* `rightEyebrowBottom`
* `leftEye`
* `rightEye`
* `upperLipTop`
* `upperLipBottom`
* `lowerLipTop`
* `lowerLipBottom`
* `noseBridge`
* `noseBottom`
* `leftCheekCenter`
* `rightCheekCenter`

For skin analysis, the **most useful** ones will be:

* Cheeks: `leftCheek`, `rightCheek`, `leftCheekCenter`, `rightCheekCenter`
* Nose/T-zone: `noseBase`, `noseBridge`, `noseBottom`, `faceOval` (for overall)
* Eyes / under-eye area: `leftEye`, `rightEye`, `leftEyebrowBottom`, `rightEyebrowBottom`
* Mouth / lower face: `upperLipTop`, `upperLipBottom`, `lowerLipTop`, `lowerLipBottom`, `bottomMouth`, `leftMouth`, `rightMouth`

Your **IssueItem.region** should be **one of these strings**, exactly as the library uses them.

---

## 3. Gemini strategy: multi-pass “global → clusters”

You said:

> we can ask gemini all at once
> try to get info one by one
> at the same not too granular, try cluster
> start from global
> after every we get result they must be put in prompt before next prompt for context

So we’ll use **one image**, but **multiple Gemini calls**, each focused on a “cluster” of issues, and **we embed previous JSON output in later prompts** as context.

### 3.1 Shared system instructions (for all calls)

You’ll reuse this **base instruction** for Gemini Flash Vision:

```text
You are an expert cosmetic skin analysis assistant.

You will be given:
- A selfie image of a single person's face.
- Optional prior JSON results from earlier analysis steps.

Rules:
- Focus ONLY on visual, cosmetic skin features (no medical diagnoses).
- Use the ML Kit face regions listed below for "region" values:
  FaceLandmarkType: ["leftEye","leftMouth","leftEar","noseBase","leftCheek",
                     "rightEye","rightMouth","rightEar","rightCheek",
                     "bottomMouth","leftEarTip","rightEarTip"]
  FaceContourType: ["faceOval","leftEyebrowTop","leftEyebrowBottom",
                    "rightEyebrowTop","rightEyebrowBottom","leftEye",
                    "rightEye","upperLipTop","upperLipBottom","lowerLipTop",
                    "lowerLipBottom","noseBridge","noseBottom",
                    "leftCheekCenter","rightCheekCenter"]

Output rules:
- Always return ONLY valid JSON, no markdown, no comments.
- For localised issues, use this IssueItem shape:
  {
    "region": <one of the ML Kit region strings above>,
    "intensity": <number 0–1, 0 none, 1 very severe>,
    "area": <integer 1–10, 1 smallest, 10 largest>,
    "description": <short description in plain English>
  }
- Be conservative: if an issue is unclear due to makeup/lighting, lower intensity instead of guessing.
```

Then each step has its own **task-specific prompt body + output schema**.

---

## 3.2 Step 1 – Global profile

**Goal:** overall skin personality + scores, **no per-region issues yet**.

Prompt (body):

```text
TASK:
Look at the selfie and describe the overall skin profile.

If prior JSON is provided under "previous_results", use it only as context if present; otherwise ignore.

Return this JSON shape:

{
  "global_profile": {
    "skin_type": {
      "label": "dry" | "oily" | "combination" | "normal" | "unknown",
      "confidence": <number 0–1>
    },
    "skin_tone": {
      "lightness": "very_light" | "light" | "medium" | "tan" | "brown" | "dark",
      "undertone": "yellow" | "neutral" | "red" | "olive" | "unknown"
    },
    "skin_age": {
      "estimated_age": <integer>,
      "relative_to_real_age": "younger" | "similar" | "older" | "unknown"
    },
    "scores": {
      "overall": <number 0–100>,
      "wrinkles": <number 0–100>,
      "dark_circles": <number 0–100>,
      "oily_shine": <number 0–100>,
      "pores": <number 0–100>,
      "blackheads": <number 0–100>,
      "acne": <number 0–100>,
      "sensitivity_redness": <number 0–100>,
      "pigmentation": <number 0–100>,
      "hydration": <number 0–100>,
      "roughness": <number 0–100>
    },
    "summary_description": <short English sentence summarising the skin>
  }
}

Scoring rules:
- 90–100 = very healthy / almost no issue.
- 70–89 = mild issue.
- 50–69 = moderate.
- 30–49 = strong.
- 0–29  = very severe.
```

**Result:** `global_profile` JSON. You store it server-side and also pass it into later prompts as `"previous_results": { "global_profile": ... }`.

---

## 3.3 Step 2 – Texture / oil / pores cluster

**Goal:** where is skin oily/dry, rough, pore-y, **mapped to ML Kit regions**, but not super granular spot-by-spot.

Prompt body:

```text
TASK:
Analyze the selfie for skin texture, oiliness and roughness.

You are given:
- "previous_results": { "global_profile": { ... } }

Use the previous scores only as context. Now produce per-region issues.

Return:

{
  "issues": {
    "oily_shine": IssueItem[],
    "dryness_dehydration": IssueItem[],
    "enlarged_pores_texture": IssueItem[]
  }
}

Where each IssueItem is:
{
  "region": <one ML Kit region string>,
  "intensity": <0–1>,
  "area": <1–10>,
  "description": <short explanation>
}

Guidelines:
- Use 1–5 IssueItems per key (oily_shine, dryness_dehydration, enlarged_pores_texture), not hundreds.
- Cluster nearby problems into one IssueItem with larger "area" instead of many tiny ones.
- Example descriptions:
  - "Strong oily shine across the T-zone around the nose."
  - "Mild dehydration on both cheeks."
  - "Visible enlarged pores on the nose and inner cheeks."
```

You then **merge** these returned `issues` into your accumulating `issues` object.

---

## 3.4 Step 3 – Pigmentation cluster

Covers: brown spots, freckles, melasma-ish patches, moles.

Prompt body:

```text
TASK:
Analyze pigmentation and color irregularities on the face:
- brown spots (sun spots / age spots),
- freckles,
- larger patchy pigmentation (melasma-like),
- moles/beauty marks.

Input context:
- "previous_results": { "global_profile": { ... }, "issues": { ... from texture/oil step } }

Return:

{
  "issues": {
    "pigmentation_brown_spots": IssueItem[],
    "freckles": IssueItem[],
    "melasma_like_patches": IssueItem[],
    "moles_or_nevi": IssueItem[]
  }
}

IssueItem as before (region, intensity, area, description).

Guidelines:
- Distinguish:
  - small scattered freckles vs larger brown spots.
  - broad, patchy pigmentation vs isolated spots.
- Example descriptions:
  - "Cluster of small brown sun spots on the upper cheeks."
  - "Light dusting of freckles across the nose bridge."
  - "Single dark mole on the right cheek center."
```

Again you merge these lists into your final `issues`.

---

## 3.5 Step 4 – Acne + redness cluster

Covers: active acne, post-acne marks, redness/sensitivity.

Prompt body:

```text
TASK:
Analyze acne and redness / sensitivity.

Input context:
- "previous_results": { "global_profile": ..., "issues": ... }

Return:

{
  "issues": {
    "acne_active": IssueItem[],
    "acne_scars_post_inflammatory": IssueItem[],
    "redness_sensitivity": IssueItem[]
  }
}

Guidelines:
- "acne_active": red, raised, inflamed pimples, pustules, nodules, whiteheads.
- "acne_scars_post_inflammatory": flat brown or purple marks and textural scars.
- "redness_sensitivity": diffuse flushing or persistent red patches, not just one pimple.
- Example descriptions:
  - "Cluster of inflamed pimples on the chin area near bottomMouth."
  - "Faint brown post-acne marks on leftCheekCenter."
  - "Diffuse redness around the noseBase and noseBridge."
```

Merge into your accumulated `issues`.

---

## 3.6 Step 5 – Aging & eye area cluster

Covers: wrinkles/fine lines, dark circles, eye bags.

Prompt body:

```text
TASK:
Analyze visible signs of aging and eye-area concerns:
- wrinkles and fine lines (forehead, eye area, mouth/nasolabial),
- dark circles (pigmented / vascular / shadow),
- under-eye puffiness (eye bags).

Input context:
- "previous_results": { "global_profile": ..., "issues": ... }

Return:

{
  "issues": {
    "wrinkles_and_fine_lines": IssueItem[],
    "dark_circles": IssueItem[],
    "eye_bags": IssueItem[]
  }
}

Guidelines:
- Use regions like:
  - "leftEyebrowBottom"/"rightEyebrowBottom" for forehead/outer eye lines,
  - "leftEye"/"rightEye" for under-eye area,
  - "leftCheekCenter"/"rightCheekCenter" or "faceOval" for nasolabial/cheek folds.
- In description, explain the type:
  - "Fine horizontal lines on the forehead."
  - "Pigmented dark circles under both eyes."
  - "Mild under-eye puffiness below the leftEye."
```

Merge into `issues`.

At the end of Step 5, you have:

* `global_profile` from Step 1
* `issues` aggregated from Steps 2–5

→ This is your **final FastAPI response**.

---

## 4. FastAPI algorithm – clear flow

Here’s a straightforward algorithm for your backend.

### 4.1 Endpoint contract

`POST /analyze-skin`

Request body:

* `image`: selfie (file upload or base64)
* optionally `real_age`: integer
* optionally anything else (user id, etc.)

Response body: the **final JSON** defined in section 1.

### 4.2 High-level steps

1. **Receive request** in FastAPI.

2. Optionally run a quick sanity check:

   * Ensure at least one face (but you’re already doing this on-device via ML Kit).

3. **Call Gemini – Step 1 (global)** → `global_profile`.

4. **Call Gemini – Step 2 (texture/oil)** using:

   * the same image, and
   * `previous_results = { "global_profile": global_profile }`.

5. **Call Gemini – Step 3 (pigmentation)** using:

   * same image,
   * `previous_results = { "global_profile": ..., "issues": {...from step 2} }`.

6. **Call Gemini – Step 4 (acne/redness)** with the accumulated results.

7. **Call Gemini – Step 5 (aging/eyes)** with the accumulated results.

8. **Assemble final result**:

   ```python
   final_result = {
       "global_profile": global_profile,
       "issues": {
           "oily_shine":        issues_from_step2["oily_shine"],
           "dryness_dehydration": issues_from_step2["dryness_dehydration"],
           "enlarged_pores_texture": issues_from_step2["enlarged_pores_texture"],
           "blackheads":        issues_from_step3["blackheads"] if you add that here,
           "acne_active":       issues_from_step4["acne_active"],
           "acne_scars_post_inflammatory": issues_from_step4["acne_scars_post_inflammatory"],
           "pigmentation_brown_spots": issues_from_step3["pigmentation_brown_spots"],
           "freckles":          issues_from_step3["freckles"],
           "melasma_like_patches": issues_from_step3["melasma_like_patches"],
           "redness_sensitivity": issues_from_step4["redness_sensitivity"],
           "wrinkles_and_fine_lines": issues_from_step5["wrinkles_and_fine_lines"],
           "eye_bags":          issues_from_step5["eye_bags"],
           "dark_circles":      issues_from_step5["dark_circles"],
           "moles_or_nevi":     issues_from_step3["moles_or_nevi"]
       }
   }
   ```

9. **Return JSON** to the app.

You can later plug a **product-recommendation layer** on top of this:

* e.g. if `scores.oily_shine < 60` + strong `oily_shine` issues on `noseBase`, recommend **oil-control cleanser + light gel moisturizer**.
* Or if `pigmentation` score is low + `pigmentation_brown_spots` on `leftCheekCenter`, recommend **vitamin C / niacinamide + SPF 50**.

---

If you want, next step I can:

* Turn this into a **concrete FastAPI code skeleton** (with pydantic models for `IssueItem`, `GlobalProfile`, `FinalResult`), and
* Give you **ready-to-paste Gemini prompts** as Python strings with f-string placeholders for previous JSON and age.

[1]: https://docs.infinite.red/react-native-mlkit/face-detection/types/ "Types | Open Source at Infinite Red"
[2]: https://developers.google.com/android/reference/com/google/mlkit/vision/face/FaceLandmark "FaceLandmark  |  ML Kit  |  Google for Developers"
