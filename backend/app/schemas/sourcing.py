from pydantic import BaseModel, Field


DEFAULT_SOURCING_CHANNELS = [
    "legal_search",
    "contact_form",
    "alibaba_internal",
    "made_in_china_internal",
    "molbase_internal",
    "indiamart_internal",
    "whatsapp_business",
    "telegram_bot",
    "signal_manual",
    "threema_gateway",
    "wickr_manual",
]


class SourcingBatchImportRequest(BaseModel):
    name: str = Field(default="CAS sourcing batch", min_length=1, max_length=200)
    cas_numbers: list[str] = Field(default_factory=list)
    csv_text: str | None = None
    quantity: str | None = None
    destination_country: str | None = None
    required_grade: str | None = None
    intended_use: str | None = None
    requirements: dict = Field(default_factory=dict)
    auto_send_enabled: bool = False
    channels: list[str] = Field(default_factory=lambda: DEFAULT_SOURCING_CHANNELS.copy())
    create_campaigns: bool = True


class SourcingQueryRead(BaseModel):
    query: str
    priority: int
    source_reason: str


class SourcingTaskRead(BaseModel):
    id: str
    task_type: str
    title: str
    channel: str | None = None


class SourcingBatchItemRead(BaseModel):
    raw_cas: str
    cas: str | None = None
    status: str
    substance_id: str | None = None
    campaign_id: str | None = None
    queries: list[SourcingQueryRead] = Field(default_factory=list)
    tasks: list[SourcingTaskRead] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SourcingBatchSummary(BaseModel):
    total_inputs: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    substances_created: int = 0
    campaigns_created: int = 0
    manual_tasks_created: int = 0
    queries_generated: int = 0


class SourcingBatchRead(BaseModel):
    batch_id: str
    name: str
    created_at: str
    channels: list[str] = Field(default_factory=list)
    summary: SourcingBatchSummary
    items: list[SourcingBatchItemRead] = Field(default_factory=list)


class SourcingBatchReportRead(BaseModel):
    batch: SourcingBatchRead
    campaign_ids: list[str] = Field(default_factory=list)
    substance_ids: list[str] = Field(default_factory=list)
    manual_task_ids: list[str] = Field(default_factory=list)
    outbound_messages: int = 0
    inbound_messages: int = 0
    quotes: int = 0
    channel_plan: dict[str, str] = Field(default_factory=dict)
