from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.policy import ChannelPolicyConfig


class CompanyProfile(BaseModel):
    legal_name: str = ""
    trading_name: str | None = None
    registration_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    website: str | None = None
    address: str | None = None
    country: str | None = None


class SenderProfile(BaseModel):
    name: str = ""
    title: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    department: str | None = "Procurement"
    signature: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_to_none(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


class ControlledQuestion(BaseModel):
    key: str
    text: str
    required: bool = True
    category: str = "general"
    risk_weight: int = 0


class ResponsePlaybookRule(BaseModel):
    name: str
    trigger_terms: list[str] = Field(default_factory=list)
    supplier_intent: str = "unknown"
    recommended_action: str = "manual_review"
    response_template: str
    creates_manual_task: bool = False
    block_if_matched: bool = False


class ConversationTrainingScenario(BaseModel):
    name: str
    supplier_message: str
    expected_action: str
    notes: str | None = None


class AppSettings(BaseModel):
    company: CompanyProfile = Field(default_factory=CompanyProfile)
    sender: SenderProfile = Field(default_factory=SenderProfile)
    default_destination_country: str | None = None
    default_intended_use: str | None = None
    default_incoterms: list[str] = Field(default_factory=lambda: ["EXW", "FOB", "CIF", "DAP", "DDP"])
    controlled_questions: list[ControlledQuestion] = Field(default_factory=list)
    response_playbook: list[ResponsePlaybookRule] = Field(default_factory=list)
    training_scenarios: list[ConversationTrainingScenario] = Field(default_factory=list)
    require_human_approval_for_simulated_responses: bool = True

    logo_url: str | None = None
    letterhead_footer: str | None = None
    pubchem_enabled: bool = False
    email_enabled: bool = False
    channel_policies: list[ChannelPolicyConfig] = Field(default_factory=list)
    default_policy_strictness: str = "standard"  # strict, standard, log_only


class AppSettingsRead(AppSettings):
    updated_at: str | None = None
