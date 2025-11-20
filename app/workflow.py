"""High-level workflow that mirrors docs/upgraded_endpoint.md."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel

from .llm import build_multistep_user_message, get_structured_model
from .schemas import (
    AcneRednessIssuesResult,
    AgingIssuesResult,
    GlobalProfile,
    GlobalProfileResult,
    IssuesCollection,
    PigmentationIssuesResult,
    TextureIssuesResult,
    UpgradedFaceAnalysisResult,
)

ProgressCallback = Optional[Callable[[str, Dict[str, Any]], None]]

STEP_SYSTEM_PROMPT = (
    "You are a meticulous esthetician. Always reply with valid JSON that matches the"
    " specified schema. Use only ML Kit region identifiers when listing facial regions"
    " and never invent extra keys."
)

STEP1_PROMPT = """TASK:
Look at the selfie and describe the overall skin profile.

Return this JSON structure:
{
  "global_profile": {
    "skin_type": {"label": "dry | oily | combination | normal | unknown", "confidence": 0-1},
    "skin_tone": {"lightness": "very_light | light | medium | tan | brown | dark", "undertone": "yellow | neutral | red | olive | unknown"},
    "skin_age": {"estimated_age": integer, "relative_to_real_age": "younger | similar | older | unknown"},
    "scores": {
      "overall": 0-100,
      "wrinkles": 0-100,
      "dark_circles": 0-100,
      "oily_shine": 0-100,
      "pores": 0-100,
      "blackheads": 0-100,
      "acne": 0-100,
      "sensitivity_redness": 0-100,
      "pigmentation": 0-100,
      "hydration": 0-100,
      "roughness": 0-100
    },
    "summary_description": "short English sentence"
  }
}
"""

STEP2_PROMPT = """TASK:
Analyze the selfie for texture, oiliness, dehydration, enlarged pores, and blackheads.
Return JSON:
{
  "issues": {
    "oily_shine": IssueItem[],
    "dryness_dehydration": IssueItem[],
    "enlarged_pores_texture": IssueItem[],
    "blackheads": IssueItem[]
  }
}
IssueItem = {"region": <ML Kit region>, "intensity": 0-1, "area": 1-10, "description": "string"}.
Cluster nearby problems and keep 1-5 entries per key.
"""

STEP3_PROMPT = """TASK:
Analyze pigmentation and color irregularities (brown spots, freckles, melasma-like patches, moles).
Return JSON with:
{
  "issues": {
    "pigmentation_brown_spots": IssueItem[],
    "freckles": IssueItem[],
    "melasma_like_patches": IssueItem[],
    "moles_or_nevi": IssueItem[]
  }
}
"""

STEP4_PROMPT = """TASK:
Analyze acne activity, post-inflammatory marks, and redness/sensitivity.
Return JSON:
{
  "issues": {
    "acne_active": IssueItem[],
    "acne_scars_post_inflammatory": IssueItem[],
    "redness_sensitivity": IssueItem[]
  }
}
"""

STEP5_PROMPT = """TASK:
Analyze aging and eye-area concerns: wrinkles/fine lines, dark circles, under-eye puffiness.
Return JSON:
{
  "issues": {
    "wrinkles_and_fine_lines": IssueItem[],
    "dark_circles": IssueItem[],
    "eye_bags": IssueItem[]
  }
}
"""

async def _invoke_step(
    schema: Type[BaseModel],
    instructions: str,
    image_bytes: bytes,
    mime_type: str,
    previous_results: Optional[Dict[str, Any]] = None,
    real_age: Optional[int] = None,
):
    model = get_structured_model(schema)
    payload = [
        {"role": "system", "content": STEP_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_multistep_user_message(
                image_bytes,
                mime_type,
                instructions,
                previous_results=previous_results,
                real_age=real_age,
            ),
        },
    ]
    return await model.ainvoke(payload)


def _build_previous_results(global_profile: Optional[GlobalProfile], issues: IssuesCollection) -> Optional[Dict[str, Any]]:
    payload: Dict[str, Any] = {}
    if global_profile is not None:
        payload["global_profile"] = global_profile.model_dump()
    issues_payload = issues.model_dump()
    if any(issues_payload.values()):
        payload["issues"] = issues_payload
    return payload or None


def _serialize_state(global_profile: Optional[GlobalProfile], issues: IssuesCollection) -> Dict[str, Any]:
    state: Dict[str, Any] = {"issues": issues.model_dump()}
    if global_profile is not None:
        state["global_profile"] = global_profile.model_dump()
    return state


def _notify(progress_callback: ProgressCallback, status: str, global_profile: Optional[GlobalProfile], issues: IssuesCollection) -> None:
    if progress_callback is None:
        return
    progress_callback(status, _serialize_state(global_profile, issues))


async def run_upgraded_workflow(
    image_bytes: bytes,
    mime_type: str,
    real_age: Optional[int] = None,
    progress_callback: ProgressCallback = None,
) -> UpgradedFaceAnalysisResult:
    issues = IssuesCollection()
    global_profile: Optional[GlobalProfile] = None

    gp_result = await _invoke_step(GlobalProfileResult, STEP1_PROMPT, image_bytes, mime_type, real_age=real_age)
    global_profile = gp_result.global_profile
    _notify(progress_callback, "global_profile_complete", global_profile, issues)

    prev = _build_previous_results(global_profile, issues)
    texture = await _invoke_step(TextureIssuesResult, STEP2_PROMPT, image_bytes, mime_type, previous_results=prev, real_age=real_age)
    issues.oily_shine.extend(texture.issues.oily_shine)
    issues.dryness_dehydration.extend(texture.issues.dryness_dehydration)
    issues.enlarged_pores_texture.extend(texture.issues.enlarged_pores_texture)
    issues.blackheads.extend(texture.issues.blackheads)
    _notify(progress_callback, "texture_complete", global_profile, issues)

    prev = _build_previous_results(global_profile, issues)
    pigmentation = await _invoke_step(PigmentationIssuesResult, STEP3_PROMPT, image_bytes, mime_type, previous_results=prev, real_age=real_age)
    issues.pigmentation_brown_spots.extend(pigmentation.issues.pigmentation_brown_spots)
    issues.freckles.extend(pigmentation.issues.freckles)
    issues.melasma_like_patches.extend(pigmentation.issues.melasma_like_patches)
    issues.moles_or_nevi.extend(pigmentation.issues.moles_or_nevi)
    _notify(progress_callback, "pigmentation_complete", global_profile, issues)

    prev = _build_previous_results(global_profile, issues)
    acne = await _invoke_step(AcneRednessIssuesResult, STEP4_PROMPT, image_bytes, mime_type, previous_results=prev, real_age=real_age)
    issues.acne_active.extend(acne.issues.acne_active)
    issues.acne_scars_post_inflammatory.extend(acne.issues.acne_scars_post_inflammatory)
    issues.redness_sensitivity.extend(acne.issues.redness_sensitivity)
    _notify(progress_callback, "acne_complete", global_profile, issues)

    prev = _build_previous_results(global_profile, issues)
    aging = await _invoke_step(AgingIssuesResult, STEP5_PROMPT, image_bytes, mime_type, previous_results=prev, real_age=real_age)
    issues.wrinkles_and_fine_lines.extend(aging.issues.wrinkles_and_fine_lines)
    issues.dark_circles.extend(aging.issues.dark_circles)
    issues.eye_bags.extend(aging.issues.eye_bags)
    _notify(progress_callback, "aging_complete", global_profile, issues)

    return UpgradedFaceAnalysisResult(global_profile=global_profile, issues=issues)
