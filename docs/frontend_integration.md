# Face Analysis Task API – Frontend Integration Guide

## Overview

The Face Analysis API provides a multi-step workflow for analyzing facial features and generating personalized skincare routines. The backend runs asynchronous multi-pass LLM workflows. Clients **start** a job with one request and **poll** for progress/final results with another. This document explains all endpoints the frontend should use.

## Base URL

- Local development: `http://localhost:8000`
- Replace with the deployed hostname in production builds.

## Quick Route Reference

| Method | Path                      | Auth    | Description                                                            |
| ------ | ------------------------- | ------- | ---------------------------------------------------------------------- |
| GET    | `/`                       | No      | Health check - verify API is running                                  |
| GET    | `/health`                 | No      | Detailed health status                                                 |
| POST   | `/start-task`             | Yes     | Upload an image to kick off background face analysis                  |
| GET    | `/tasks`                  | Yes     | List recent analyses for the signed-in user                            |
| GET    | `/tasks/{task_id}`        | Yes     | Poll task status, results, and routine (single endpoint)               |
| POST   | `/recommend`              | Yes     | Generate a routine once analysis is ready                              |
| POST   | `/analyze` (deprecated)   | No      | Legacy single-pass analysis endpoint (not recommended)                 |

---

## Detailed Endpoint Documentation

### 1. Health Check Endpoints

#### `GET /` – Root Status

**Purpose**: Verify the API is running.

**Headers**
- None required

**Query Parameters**
- None

**Request Body**
- None

**Response (200)**
```json
{
  "message": "FastAPI is running"
}
```

---

#### `GET /health` – Health Status

**Purpose**: Detailed health check for monitoring.

**Headers**
- None required

**Response (200)**
```json
{
  "status": "ok"
}
```

---

### 2. Face Analysis Workflow

#### `POST /start-task` – Initiate Face Analysis

**Purpose**: Upload an image to begin background face analysis. Returns a task ID for polling.

**Authentication**: Required (Bearer token)

**Headers**
```
Authorization: Bearer <supabase_token>
Accept: application/json
```

**Body** (Multipart Form Data)

| Field     | Type    | Required | Description                                              |
|-----------|---------|----------|----------------------------------------------------------|
| `image`   | File    | Yes      | Image file (MIME: image/jpeg, image/png, image/webp) |
| `real_age`| Integer | No       | User's actual age to help model assess perceived vs real |

**Response (200)**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**

| Status | Response Body                              | Reason                           |
|--------|--------------------------------------------|---------------------------------|
| 400    | `{"detail": "Provide a valid image file."}` | Missing or invalid image MIME type |
| 422    | `{"detail": "Unprocessable Entity"}` | Missing required fields (e.g., image) |
| 401    | `{"detail": "Unauthorized"}`         | Missing or invalid authentication token |
| 500    | `{"detail": "Internal server error"}` | Server-side processing error   |

**Sample `curl`**

```bash
curl -X POST \
  -H "Authorization: Bearer your_supabase_token" \
  -H "Accept: application/json" \
  -F "image=@/path/to/selfie.jpg" \
  -F "real_age=28" \
  http://localhost:8000/start-task
```

**Sample `fetch` (TypeScript)**

```ts
async function startAnalysis(file: File, realAge?: number, token: string) {
  const formData = new FormData();
  formData.append("image", file);
  if (realAge !== undefined) formData.append("real_age", String(realAge));

  const response = await fetch("http://localhost:8000/start-task", {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail ?? "Unable to start analysis");
  }

  return response.json(); // → { task_id }
}
```

---

#### `GET /tasks` – List Recent Analyses

**Purpose**: Retrieve the latest face analyses for the authenticated user. Useful for dashboards.

**Authentication**: Required (Bearer token)

**Headers**
```
Authorization: Bearer <supabase_token>
Accept: application/json
```

**Query Parameters**

| Parameter | Type    | Default | Description                      |
|-----------|---------|---------|----------------------------------|
| `limit`   | Integer | 10      | Maximum number of tasks to return|

**Response (200)** – Array of `TaskStatusResponse` objects

```json
[
  {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": { ... },
    "error": null,
    "routine_json": { ... }
  },
  {
    "task_id": "660e8400-e29b-41d4-a716-446655440001",
    "status": "processing",
    "result": null,
    "error": null,
    "routine_json": null
  }
]
```

**Error Responses**

| Status | Response Body               | Reason                          |
|--------|-----------------------------|---------------------------------|
| 401    | `{"detail": "Unauthorized"}` | Missing or invalid token        |
| 500    | `{"detail": "Server error"}` | Database or server error        |

**Sample `curl`**

```bash
curl -X GET \
  -H "Authorization: Bearer your_supabase_token" \
  "http://localhost:8000/tasks?limit=20"
```

**Sample `fetch` (TypeScript)**

```ts
async function listTasks(token: string, limit: number = 10) {
  const response = await fetch(
    `http://localhost:8000/tasks?limit=${limit}`,
    {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "Authorization": `Bearer ${token}`
      },
    }
  );

  if (!response.ok) throw new Error("Failed to list tasks");
  return response.json(); // → TaskStatusResponse[]
}
```

---

#### `GET /tasks/{task_id}` – Poll Task Status & Results

**Purpose**: Poll for current task status, analysis results, and routine recommendations. Use this endpoint throughout the workflow to track progress.

**Authentication**: Required (Bearer token)

**Headers**
```
Authorization: Bearer <supabase_token>
Accept: application/json
```

**Path Parameters**

| Parameter  | Type   | Description                 |
|------------|--------|-----------------------------|
| `task_id`  | String | UUID of the task to retrieve|

**Response (200)** – `TaskStatusResponse`

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "global_profile": {
      "skin_type": {
        "label": "combination",
        "confidence": 0.86
      },
      "skin_tone": {
        "lightness": "medium",
        "undertone": "neutral"
      },
      "skin_age": {
        "estimated_age": 27,
        "relative_to_real_age": "similar"
      },
      "scores": {
        "overall": 78,
        "wrinkles": 65,
        "dark_circles": 52,
        "oily_shine": 42,
        "pores": 58,
        "blackheads": 23,
        "acne": 10,
        "sensitivity_redness": 35,
        "pigmentation": 28,
        "hydration": 72,
        "roughness": 45
      },
      "summary_description": "Combination skin with mild T-zone shine and good hydration."
    },
    "issues": {
      "oily_shine": [
        {
          "region": "NoseBase",
          "intensity": 0.7,
          "area": 6,
          "description": "Oily shine across the T-zone."
        }
      ],
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
  },
  "error": null,
  "routine_json": null
}
```

**Status Values**

| Status                      | Meaning                                              | Has Partial Result? |
|-----------------------------|------------------------------------------------------|---------------------|
| `queued`                    | Task registered, awaiting processing                | No                  |
| `processing`                | Analysis is running                                 | No                  |
| `global_profile_complete`   | Step 1 done; global profile available              | Partial             |
| `texture_complete`          | Texture analysis finished                          | Partial             |
| `pigmentation_complete`     | Pigmentation analysis finished                     | Partial             |
| `acne_complete`             | Acne analysis finished                             | Partial             |
| `aging_complete`            | Aging analysis finished                            | Partial             |
| `completed`                 | All analysis steps done; full result ready         | Yes (full)          |
| `failed`                    | Analysis encountered an unrecoverable error        | No (check error)    |

**Error Responses**

| Status | Response Body                              | Reason                          |
|--------|--------------------------------------------|---------------------------------|
| 401    | `{"detail": "Unauthorized"}`               | Missing or invalid token        |
| 403    | `{"detail": "Unauthorized"}`               | Trying to access another user's task |
| 404    | `{"detail": "Task not found."}`            | Task ID doesn't exist           |
| 500    | `{"detail": "Server error"}`               | Database or server error        |

**Sample `curl`**

```bash
curl -X GET \
  -H "Authorization: Bearer your_supabase_token" \
  http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000
```

**Sample `fetch` with polling (TypeScript)**

```ts
async function pollTaskUntilComplete(
  taskId: string,
  token: string,
  maxWaitMs: number = 300000 // 5 minutes
) {
  const startTime = Date.now();
  const pollInterval = 1500; // 1.5 seconds

  while (Date.now() - startTime < maxWaitMs) {
    const response = await fetch(
      `http://localhost:8000/tasks/${taskId}`,
      {
        method: "GET",
        headers: {
          "Accept": "application/json",
          "Authorization": `Bearer ${token}`
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get task status: ${response.statusText}`);
    }

    const payload = await response.json();

    // Check for completion
    if (payload.status === "completed") {
      return payload;
    }

    // Check for failure
    if (payload.status === "failed") {
      throw new Error(payload.error || "Task failed");
    }

    // Wait before next poll
    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  throw new Error("Task polling timeout");
}
```

---

### 3. Routine Recommendation Workflow

#### `POST /recommend` – Generate Personalized Routine

**Purpose**: Generate a personalized skincare routine based on completed face analysis and user intake questionnaire. The request is queued asynchronously; poll `/tasks/{task_id}` for the result.

**Authentication**: Required (Bearer token)

**Headers**
```
Authorization: Bearer <supabase_token>
Content-Type: application/json
Accept: application/json
```

**Request Body** – `RecommendationRequest`

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "intake": {
    "sensitivity": "medium",
    "pregnancy": "no",
    "rx_topical": "no",
    "allergies": ["fragrance", "alcohol"],
    "fitzpatrick": "III-IV",
    "current_actives": ["vitamin_c", "niacinamide"],
    "country": "US",
    "budget_preference": "mid"
  }
}
```

**Intake Field Definitions**

| Field              | Type                                  | Default          | Description                                  |
|--------------------|---------------------------------------|------------------|----------------------------------------------|
| `sensitivity`      | `"low" \| "medium" \| "high" \| "unsure"` | `"unsure"` | Skin sensitivity level                       |
| `pregnancy`        | `"yes" \| "no" \| "prefer_not_to_say"` | `"prefer_not_to_say"` | Pregnancy status (affects recommendations) |
| `rx_topical`       | `"yes" \| "no" \| "unsure"`           | `"unsure"`       | Currently using prescription topicals        |
| `allergies`        | Array of strings                      | `[]`             | Known allergens (e.g., "fragrance", "alcohol") |
| `fitzpatrick`      | `"I-II" \| "III-IV" \| "V-VI" \| "unsure"` | `"unsure"` | Fitzpatrick skin tone scale                 |
| `current_actives`  | Array of strings                      | `[]`             | Currently using actives (e.g., "vitamin_c", "retinol") |
| `country`          | String or null                        | `null`           | Country (for product availability)           |
| `budget_preference`| `"budget" \| "mid" \| "premium" \| "no_pref"` | `"no_pref"` | Price tier preference             |

**Response (202)** – Request Accepted

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "poll_path": "/tasks/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**

| Status | Response Body                              | Reason                          |
|--------|--------------------------------------------|---------------------------------|
| 400    | `{"detail": "Analysis not ready."}`        | Task status not `completed` yet |
| 401    | `{"detail": "Unauthorized"}`               | Missing or invalid token        |
| 403    | `{"detail": "Unauthorized"}`               | Trying to recommend another user's task |
| 404    | `{"detail": "Task not found."}`            | Task ID doesn't exist           |
| 422    | `{"detail": "Unprocessable Entity"}`       | Invalid intake data             |
| 500    | `{"detail": "Server error"}`               | Processing error                |

**Sample `curl`**

```bash
curl -X POST \
  -H "Authorization: Bearer your_supabase_token" \
  -H "Content-Type: application/json" \
  http://localhost:8000/recommend \
  -d '{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "intake": {
      "sensitivity": "medium",
      "pregnancy": "no",
      "rx_topical": "no",
      "allergies": ["fragrance"],
      "fitzpatrick": "III-IV",
      "current_actives": ["vitamin_c"],
      "country": "US",
      "budget_preference": "mid"
    }
  }'
```

**Sample `fetch` (TypeScript)**

```ts
async function generateRoutine(
  taskId: string,
  intake: RoutineIntake,
  token: string
) {
  const response = await fetch("http://localhost:8000/recommend", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
      "Accept": "application/json"
    },
    body: JSON.stringify({
      task_id: taskId,
      intake: intake
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail ?? "Failed to generate routine");
  }

  return response.json();
}
```

**Next Step**: After receiving 202, poll `/tasks/{task_id}` until `routine_json` is non-null.

---

## 4. Response Schemas

### `TaskStatusResponse` – Task Status & Results

Used by `/tasks`, `/tasks/{task_id}`, and after `/recommend`.

```ts
interface TaskStatusResponse {
  task_id: string;
  status: "queued" | "processing" | "global_profile_complete" |
          "texture_complete" | "pigmentation_complete" | "acne_complete" |
          "aging_complete" | "completed" | "failed";
  result: UpgradedFaceAnalysisResult | null;
  error: string | null;
  routine_json: RoutinePlan | null;
}
```

---

### `UpgradedFaceAnalysisResult` – Complete Face Analysis

Returned in `TaskStatusResponse.result` when status is `completed`.

```ts
interface UpgradedFaceAnalysisResult {
  global_profile: GlobalProfile;
  issues: IssuesCollection;
}

interface GlobalProfile {
  skin_type: SkinTypeSummary;
  skin_tone: SkinToneSummary;
  skin_age: SkinAgeSummary;
  scores: ScoreBreakdown;
  summary_description: string;
}

interface SkinTypeSummary {
  label: "dry" | "oily" | "combination" | "normal" | "unknown";
  confidence: number; // 0.0 to 1.0
}

interface SkinToneSummary {
  lightness: "very_light" | "light" | "medium" | "tan" | "brown" | "dark";
  undertone: "yellow" | "neutral" | "red" | "olive" | "unknown";
}

interface SkinAgeSummary {
  estimated_age: number;
  relative_to_real_age: "younger" | "similar" | "older" | "unknown";
}

interface ScoreBreakdown {
  overall: number;      // 0-100
  wrinkles: number;     // 0-100
  dark_circles: number; // 0-100
  oily_shine: number;   // 0-100
  pores: number;        // 0-100
  blackheads: number;   // 0-100
  acne: number;         // 0-100
  sensitivity_redness: number; // 0-100
  pigmentation: number; // 0-100
  hydration: number;    // 0-100
  roughness: number;    // 0-100
}

interface IssuesCollection {
  oily_shine: IssueItem[];
  dryness_dehydration: IssueItem[];
  enlarged_pores_texture: IssueItem[];
  blackheads: IssueItem[];
  acne_active: IssueItem[];
  acne_scars_post_inflammatory: IssueItem[];
  pigmentation_brown_spots: IssueItem[];
  freckles: IssueItem[];
  melasma_like_patches: IssueItem[];
  redness_sensitivity: IssueItem[];
  wrinkles_and_fine_lines: IssueItem[];
  eye_bags: IssueItem[];
  dark_circles: IssueItem[];
  moles_or_nevi: IssueItem[];
}

interface IssueItem {
  region: IssueRegion;
  intensity: number;    // 0.0 to 1.0
  area: number;         // 1 to 10 scale
  description: string;
}

type IssueRegion =
  | "NoseBase" | "LeftEar" | "RightEar"
  | "LeftEarTip" | "RightEarTip"
  | "LeftEye" | "RightEye"
  | "LeftCheek" | "RightCheek"
  | "MouthBottom" | "MouthLeft" | "MouthRight"
  | "FaceOval"
  | "LeftEyebrowTop" | "LeftEyebrowBottom"
  | "RightEyebrowTop" | "RightEyebrowBottom";
```

---

### `RoutinePlan` – Personalized Skincare Routine

Returned in `TaskStatusResponse.routine_json` after routine generation completes.

```ts
interface RoutinePlan {
  routine: RoutineSections;
  reasons: RoutineReasons;
  warnings: string[];
  lifestyle: RoutineLifestyle;
}

interface RoutineSections {
  am: RoutineStep[];
  midday?: RoutineStep[];
  pm: RoutineStep[];
}

interface RoutineStep {
  type: "cleanser" | "active" | "moisturizer" | "sunscreen" | "refresh" | "other";
  instructions: RoutineInstruction;
  products: RoutineProduct[];
}

interface RoutineInstruction {
  how: string;        // Application method
  frequency: string;  // How often to use
  timing: string;     // When to use
}

interface RoutineProduct {
  id?: string;
  brand: string;
  name: string;
  tier: "budget" | "mid" | "premium";
  url: string;
  why: string;        // Why this product was recommended
}

interface RoutineReasons {
  prioritized_concerns: PrioritizedConcern[];
  notes: string;
}

interface PrioritizedConcern {
  key: "pigmentation" | "acne" | "oily_shine" | "dryness" | "redness" | "wrinkles";
  severity: "mild" | "moderate" | "severe";
  why: string;
}

interface RoutineLifestyle {
  sleep: string;       // Sleep recommendations
  stress: string;      // Stress management tips
  sun: string;         // Sun protection advice
  habits: string;      // General habits to develop
  routine_hygiene: string; // Hygiene tips
  diet: RoutineLifestyleDiet;
}

interface RoutineLifestyleDiet {
  increase: string[];  // Foods/nutrients to increase
  limit: string[];     // Foods/nutrients to limit
  supplements: string[]; // Recommended supplements
}
```

---

## 5. Workflow Examples

### Complete Analysis + Routine Generation Flow

```ts
// Step 1: Start analysis
const { task_id } = await startAnalysis(imageFile, realAge, token);

// Step 2: Poll until analysis is complete
const analysisResult = await pollTaskUntilComplete(task_id, token);

// Step 3: Generate routine based on analysis
const intake: RoutineIntake = {
  sensitivity: "medium",
  pregnancy: "no",
  rx_topical: "no",
  allergies: ["fragrance"],
  fitzpatrick: "III-IV",
  current_actives: ["vitamin_c"],
  country: "US",
  budget_preference: "mid"
};

const { poll_path } = await generateRoutine(task_id, intake, token);

// Step 4: Poll for routine until it's generated
let routineTask = await pollTaskUntilComplete(task_id, token);
while (!routineTask.routine_json) {
  await new Promise(r => setTimeout(r, 1500));
  routineTask = await fetch(poll_path, {
    headers: { "Authorization": `Bearer ${token}` }
  }).then(r => r.json());
}

// Step 5: Use the complete data
console.log("Analysis:", routineTask.result);
console.log("Routine:", routineTask.routine_json);
```

---

## 6. Legacy Endpoint (Deprecated)

### `POST /analyze` – Single-Pass Face Analysis

**Status**: Legacy endpoint for backward compatibility only. **Do not use in new implementations.**

**Headers**
```
Accept: application/json
```

**Body** (Multipart Form Data)

| Field   | Type | Required | Description          |
|---------|------|----------|----------------------|
| `image` | File | Yes      | Image file (MIME: image/*) |

**Response (200)** – `FaceAnalysisResult` (legacy schema)

---

## 7. Frontend Tips

- **Validation**: Show immediate feedback if the user selects a non-image file before hitting the start button.
- **Progress UI**: Use the status strings to show step-by-step progress bars or text updates.
- **Timeouts/Retries**: If a task remains in the same status for too long, allow the user to cancel and retry; tasks are stored in-memory and will disappear when the server restarts.
- **Config**: Inject the API base URL through environment-specific configuration to avoid hardcoding hosts.
- **Routine rendering**: Poll `/tasks/{id}` until `routine_json` is non-null, then render/cache the structured JSON so you can rebuild the UI without another fetch.
- **Polling interval**: 1–2 seconds balances responsiveness and quota usage. Adjust based on your needs.
- **Error handling**: Always check the `error` field when status is `failed` and display to the user.
