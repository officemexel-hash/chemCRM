from pydantic import BaseModel, Field


class ConversationSimulationRequest(BaseModel):
    supplier_name: str = "Supplier"
    supplier_message: str
    channel: str = "manual"
    stage: str = "initial_contact"
    campaign_id: str | None = None
    supplier_id: str | None = None


class ConversationSimulationResponse(BaseModel):
    detected_intent: str
    recommended_action: str
    response_subject: str
    response_body: str
    matched_rules: list[str] = Field(default_factory=list)
    missing_controlled_questions: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    creates_manual_task: bool = False
    block: bool = False
    approval_required: bool = True
    training_notes: list[str] = Field(default_factory=list)
