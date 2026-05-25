from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RecommendationRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Skincare query from the user.")
    history: dict[str, Any] | None = Field(default=None, description="Optional caller-provided history.")
    use_saved_history: bool = Field(default=True, description="Merge data/user_history.json when available.")
    save_history: bool = Field(default=False, description="Persist this interaction to the history store.")
    generate_visualization: bool = Field(default=False, description="Generate visualizedData.pdf for this request.")


class SafetySummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    notes: list[str]
    hard_constraints_applied: dict[str, Any]


class RoutineStep(BaseModel):
    model_config = ConfigDict(extra="allow")

    step: str
    label: str
    title: str
    product_type: str | None = None
    why: str | None = None


class RoutineResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    morning: list[RoutineStep] = Field(default_factory=list)
    night: list[RoutineStep] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    title: str
    brand: str | None = None
    product_type: str | None = None
    price: float | None = None
    rating: float | None = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    recommendation_reason: str | None = None


class CatalogResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    catalog_title: str
    catalog_type: str
    score: float | None = None
    products: list[ProductResponse]


class UIComponent(BaseModel):
    model_config = ConfigDict(extra="allow")

    component_id: str
    component_type: str
    title: str | None = None
    priority: int = 0
    layout: str | None = None


class UIQueryMeta(BaseModel):
    raw: str
    normalized: str | None = None
    intent: str | None = None
    language: str | None = None


class UIDetectedContext(BaseModel):
    skin_type: str | None = None
    user_age: int | None = None
    age_group: str | None = None
    product_type: str | None = None
    skin_concerns: list[str] = Field(default_factory=list)
    requested_ingredients: list[str] = Field(default_factory=list)
    avoided_ingredients: list[str] = Field(default_factory=list)
    safety_flags: dict[str, Any] = Field(default_factory=dict)


class UIResponseSummary(BaseModel):
    component_count: int
    primary_component_id: str | None = None
    safety_severity: str | None = None


class UIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    response_type: str = "ui_components"
    request_id: str
    generated_at: str
    query: UIQueryMeta
    detected_context: UIDetectedContext
    summary: UIResponseSummary
    components: list[UIComponent] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile: dict[str, Any]
    catalogs: list[CatalogResponse]
    routine: RoutineResponse
    safety_summary: SafetySummary
    components: list[UIComponent] = Field(default_factory=list)


class DataValidationReport(BaseModel):
    valid: bool
    dataset_path: str
    row_count: int = 0
    column_count: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
