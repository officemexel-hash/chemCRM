from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversation import ConversationSimulationRequest, ConversationSimulationResponse
from app.services.app_settings import AppSettingsService
from app.services.audit_log import AuditLogService
from app.services.conversation_simulator import ConversationSimulator


router = APIRouter(prefix="/conversation-simulator", tags=["conversation-simulator"])


@router.post("/simulate", response_model=ConversationSimulationResponse)
def simulate_conversation(
    payload: ConversationSimulationRequest,
    db: Session = Depends(get_db),
) -> ConversationSimulationResponse:
    result = ConversationSimulator(AppSettingsService(db).get()).simulate(payload)
    AuditLogService(db).log(
        "conversation_simulated",
        "conversation_simulation",
        None,
        {
            "supplier_name": payload.supplier_name,
            "channel": payload.channel,
            "stage": payload.stage,
            "recommended_action": result.recommended_action,
            "matched_rules": result.matched_rules,
            "red_flags": result.red_flags,
            "block": result.block,
        },
    )
    db.commit()
    return result
