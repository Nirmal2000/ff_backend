"""Pydantic models used for structured LLM output."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class AttributeScore(BaseModel):
    value: int = Field(..., description="Category code for the detected attribute.")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence for the attribute."
    )


class SkinTypeDetails(BaseModel):
    oily: float = Field(..., ge=0.0, le=1.0, description="Confidence for oily skin.")
    dry: float = Field(..., ge=0.0, le=1.0, description="Confidence for dry skin.")
    normal: float = Field(..., ge=0.0, le=1.0, description="Confidence for normal skin.")
    mixed: float = Field(..., ge=0.0, le=1.0, description="Confidence for mixed skin.")


class SkinTypeScore(AttributeScore):
    value: int = Field(..., ge=0, le=3, description="Skin type code 0=oily ... 3=mixed.")
    details: SkinTypeDetails = Field(..., description="Fine-grained skin type scores.")


class FaceAnalysisResult(BaseModel):
    left_eyelids: AttributeScore
    right_eyelids: AttributeScore
    eye_pouch: AttributeScore
    dark_circles: AttributeScore
    forehead_wrinkle: AttributeScore
    crows_feet: AttributeScore
    eye_fine_lines: AttributeScore
    glabella_wrinkle: AttributeScore
    nasolabial_fold: AttributeScore
    skin_type: SkinTypeScore
    forehead_pores: AttributeScore
    left_cheek_pores: AttributeScore
    right_cheek_pores: AttributeScore
    jaw_pores: AttributeScore
    blackhead: AttributeScore
    acne: AttributeScore
    mole: AttributeScore
    skin_spot: AttributeScore


IssueRegion = Literal[
    "NoseBase",
    "LeftEar",
    "RightEar",
    "LeftEarTip",
    "RightEarTip",
    "LeftEye",
    "RightEye",
    "LeftCheek",
    "RightCheek",
    "MouthBottom",
    "MouthLeft",
    "MouthRight",
    "FaceOval",
    "LeftEyebrowTop",
    "LeftEyebrowBottom",
    "RightEyebrowTop",
    "RightEyebrowBottom",
]


class IssueItem(BaseModel):
    region: IssueRegion = Field(..., description="ML Kit region identifier where the issue is located.")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Severity between 0 and 1.")
    area: int = Field(..., ge=1, le=10, description="Relative coverage area, 1–10 scale.")
    description: str = Field(..., description="Short natural language explanation of the issue.")


class IssuesCollection(BaseModel):
    oily_shine: list[IssueItem] = Field(default_factory=list)
    dryness_dehydration: list[IssueItem] = Field(default_factory=list)
    enlarged_pores_texture: list[IssueItem] = Field(default_factory=list)
    blackheads: list[IssueItem] = Field(default_factory=list)
    acne_active: list[IssueItem] = Field(default_factory=list)
    acne_scars_post_inflammatory: list[IssueItem] = Field(default_factory=list)
    pigmentation_brown_spots: list[IssueItem] = Field(default_factory=list)
    freckles: list[IssueItem] = Field(default_factory=list)
    melasma_like_patches: list[IssueItem] = Field(default_factory=list)
    redness_sensitivity: list[IssueItem] = Field(default_factory=list)
    wrinkles_and_fine_lines: list[IssueItem] = Field(default_factory=list)
    eye_bags: list[IssueItem] = Field(default_factory=list)
    dark_circles: list[IssueItem] = Field(default_factory=list)
    moles_or_nevi: list[IssueItem] = Field(default_factory=list)


SkinTypeLabel = Literal["dry", "oily", "combination", "normal", "unknown"]
SkinToneLightness = Literal[
    "very_light",
    "light",
    "medium",
    "tan",
    "brown",
    "dark",
]
SkinToneUndertone = Literal["yellow", "neutral", "red", "olive", "unknown"]
RelativeAge = Literal["younger", "similar", "older", "unknown"]


class SkinTypeSummary(BaseModel):
    label: SkinTypeLabel
    confidence: float = Field(..., ge=0.0, le=1.0)


class SkinToneSummary(BaseModel):
    lightness: SkinToneLightness
    undertone: SkinToneUndertone


class SkinAgeSummary(BaseModel):
    estimated_age: int = Field(..., ge=0)
    relative_to_real_age: RelativeAge


class ScoreBreakdown(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    wrinkles: int = Field(..., ge=0, le=100)
    dark_circles: int = Field(..., ge=0, le=100)
    oily_shine: int = Field(..., ge=0, le=100)
    pores: int = Field(..., ge=0, le=100)
    blackheads: int = Field(..., ge=0, le=100)
    acne: int = Field(..., ge=0, le=100)
    sensitivity_redness: int = Field(..., ge=0, le=100)
    pigmentation: int = Field(..., ge=0, le=100)
    hydration: int = Field(..., ge=0, le=100)
    roughness: int = Field(..., ge=0, le=100)


class GlobalProfile(BaseModel):
    skin_type: SkinTypeSummary
    skin_tone: SkinToneSummary
    skin_age: SkinAgeSummary
    scores: ScoreBreakdown
    summary_description: str


class GlobalProfileResult(BaseModel):
    global_profile: GlobalProfile


class TextureIssues(BaseModel):
    oily_shine: list[IssueItem] = Field(default_factory=list)
    dryness_dehydration: list[IssueItem] = Field(default_factory=list)
    enlarged_pores_texture: list[IssueItem] = Field(default_factory=list)
    blackheads: list[IssueItem] = Field(default_factory=list)


class TextureIssuesResult(BaseModel):
    issues: TextureIssues


class PigmentationIssues(BaseModel):
    pigmentation_brown_spots: list[IssueItem] = Field(default_factory=list)
    freckles: list[IssueItem] = Field(default_factory=list)
    melasma_like_patches: list[IssueItem] = Field(default_factory=list)
    moles_or_nevi: list[IssueItem] = Field(default_factory=list)


class PigmentationIssuesResult(BaseModel):
    issues: PigmentationIssues


class AcneRednessIssues(BaseModel):
    acne_active: list[IssueItem] = Field(default_factory=list)
    acne_scars_post_inflammatory: list[IssueItem] = Field(default_factory=list)
    redness_sensitivity: list[IssueItem] = Field(default_factory=list)


class AcneRednessIssuesResult(BaseModel):
    issues: AcneRednessIssues


class AgingIssues(BaseModel):
    wrinkles_and_fine_lines: list[IssueItem] = Field(default_factory=list)
    dark_circles: list[IssueItem] = Field(default_factory=list)
    eye_bags: list[IssueItem] = Field(default_factory=list)


class AgingIssuesResult(BaseModel):
    issues: AgingIssues


class UpgradedFaceAnalysisResult(BaseModel):
    global_profile: GlobalProfile
    issues: IssuesCollection


class TaskCreatedResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    routine_json: Optional[Dict[str, Any]] = None


class RoutineIntake(BaseModel):
    sensitivity: Literal["low", "medium", "high", "unsure"] = "unsure"
    pregnancy: Literal["yes", "no", "prefer_not_to_say"] = "prefer_not_to_say"
    rx_topical: Literal["yes", "no", "unsure"] = "unsure"
    allergies: list[str] = Field(default_factory=list)
    fitzpatrick: Literal["I-II", "III-IV", "V-VI", "unsure"] = "unsure"
    current_actives: list[str] = Field(default_factory=list)
    country: Optional[str] = None
    budget_preference: Literal["budget", "mid", "premium", "no_pref"] = "no_pref"


class RecommendationRequest(BaseModel):
    task_id: str
    intake: RoutineIntake


class RecommendationResponse(BaseModel):
    task_id: str
    poll_path: str


RoutineStepType = Literal["cleanser", "active", "moisturizer", "sunscreen", "refresh", "other"]
RoutineTier = Literal["budget", "mid", "premium"]
ConcernKey = Literal["pigmentation", "acne", "oily_shine", "dryness", "redness", "wrinkles"]
ConcernSeverity = Literal["mild", "moderate", "severe"]


class RoutineInstruction(BaseModel):
    how: str
    frequency: str
    timing: str


class RoutineProduct(BaseModel):
    id: Optional[str]
    brand: str
    name: str
    tier: RoutineTier
    why: str


class RoutineStep(BaseModel):
    type: RoutineStepType
    instructions: RoutineInstruction
    products: list[RoutineProduct]


class RoutineSections(BaseModel):
    am: list[RoutineStep]
    midday: Optional[list[RoutineStep]] = None
    pm: list[RoutineStep]


class PrioritizedConcern(BaseModel):
    key: ConcernKey
    severity: ConcernSeverity
    why: str


class RoutineReasons(BaseModel):
    prioritized_concerns: list[PrioritizedConcern]
    notes: str


class RoutineLifestyleDiet(BaseModel):
    increase: list[str]
    limit: list[str]
    supplements: list[str]


class RoutineLifestyle(BaseModel):
    sleep: str
    stress: str
    sun: str
    habits: str
    routine_hygiene: str
    diet: RoutineLifestyleDiet


class RoutinePlan(BaseModel):
    routine: RoutineSections
    reasons: RoutineReasons
    warnings: list[str]
    lifestyle: RoutineLifestyle
