"""Autonomous conversation engine — manages initial-phase supplier conversations
across all channels (email, marketplace, messengers, forms).

With safety bypass active, this engine auto-replies to inbound messages,
generates follow-ups, and collects missing RFQ information until either:
- All controlled questions are answered
- Maximum follow-up rounds reached (default: 3)
- Supplier explicitly declines or sends fraud/evasion language
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.safety_bypass import SafetyBypassState
from app.services.conversation_simulator import ConversationSimulator
from app.schemas.conversation import ConversationSimulationRequest

logger = logging.getLogger(__name__)

MAX_AUTO_FOLLOWUP_ROUNDS = 3


@dataclass
class ConversationState:
    """Tracks the state of a conversation with one supplier."""
    thread_id: str
    campaign_id: str
    supplier_id: str
    contact_id: str
    channel: str
    round: int = 0
    status: str = "active"  # active, answered_all, declined, blocked, max_rounds
    questions_answered: list[str] = field(default_factory=list)
    questions_missing: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    last_action: str = ""
    messages_sent: int = 0
    messages_received: int = 0
    started_at: str = ""


@dataclass
class ConversationResult:
    """Result of processing one turn of a conversation."""
    thread_id: str
    should_reply: bool
    reply_subject: str | None = None
    reply_body: str | None = None
    reply_channel: str = "email"
    conversation_status: str = "active"
    action: str = ""  # auto_reply, escalate_to_manual, block, done
    reason: str = ""


class ConversationEngine:
    """Drives autonomous initial-phase conversations with suppliers.

    Uses ConversationSimulator to analyze inbound messages and generate
    appropriate responses. With safety bypass active, automatically sends
    replies without human approval.
    """

    def __init__(self, app_settings=None):
        self.simulator = ConversationSimulator(app_settings)

    def process_inbound(
        self,
        inbound_body: str,
        supplier_name: str,
        state: ConversationState | None = None,
        channel: str = "email",
    ) -> ConversationResult:
        """Process an inbound supplier message and determine next action.

        Returns a ConversationResult with the recommended reply (if any)
        and updated conversation status.
        """
        if state is None:
            state = ConversationState(
                thread_id="new",
                campaign_id="",
                supplier_id="",
                contact_id="",
                channel=channel,
                started_at=datetime.now(timezone.utc).isoformat(),
            )

        state.round += 1
        state.messages_received += 1

        # Run the simulator to analyze the supplier message
        sim_request = ConversationSimulationRequest(
            supplier_name=supplier_name or "Supplier",
            supplier_message=inbound_body,
            channel=channel,
            stage="followup" if state.round > 1 else "initial_contact",
        )
        sim_result = self.simulator.simulate(sim_request)
        state.red_flags.extend(sim_result.red_flags)
        state.questions_missing = list(sim_result.missing_controlled_questions)
        state.questions_answered = [
            q for q in getattr(self.simulator, 'app_settings', None)
            and self.simulator.app_settings.controlled_questions
            or []
            if hasattr(q, 'key')
        ]

        # Decision logic
        bypass_active = SafetyBypassState.is_active()

        # Block on fraud/evasion
        if sim_result.block:
            state.status = "blocked"
            return ConversationResult(
                thread_id=state.thread_id,
                should_reply=False,
                conversation_status="blocked",
                action="block",
                reason="Fraud/evasion language detected — conversation blocked",
            )

        # All questions answered — stop auto-replies
        if not sim_result.missing_controlled_questions and state.round > 0:
            state.status = "answered_all"
            return ConversationResult(
                thread_id=state.thread_id,
                should_reply=True if bypass_active else False,
                reply_subject=sim_result.response_subject,
                reply_body=sim_result.response_body,
                reply_channel=channel,
                conversation_status="answered_all",
                action="auto_reply" if bypass_active else "create_manual_task",
                reason="All controlled questions answered — final acknowledgment",
            )

        # Max rounds reached — escalate to manual
        if state.round > MAX_AUTO_FOLLOWUP_ROUNDS:
            state.status = "max_rounds"
            return ConversationResult(
                thread_id=state.thread_id,
                should_reply=False,
                conversation_status="max_rounds",
                action="escalate_to_manual",
                reason=f"Maximum auto-followup rounds ({MAX_AUTO_FOLLOWUP_ROUNDS}) reached",
            )

        # Auto-reply with follow-up questions
        if bypass_active:
            state.status = "active"
            state.messages_sent += 1
            state.last_action = "auto_reply"
            return ConversationResult(
                thread_id=state.thread_id,
                should_reply=True,
                reply_subject=sim_result.response_subject,
                reply_body=sim_result.response_body,
                reply_channel=channel,
                conversation_status="active",
                action="auto_reply",
                reason=f"Auto-reply round {state.round}/{MAX_AUTO_FOLLOWUP_ROUNDS} — {len(sim_result.missing_controlled_questions)} questions pending",
            )
        else:
            # Without bypass, create manual task
            state.status = "requires_approval"
            return ConversationResult(
                thread_id=state.thread_id,
                should_reply=False,
                conversation_status="requires_approval",
                action="create_manual_task",
                reason=f"Reply draft ready — review before sending (round {state.round}/{MAX_AUTO_FOLLOWUP_ROUNDS})",
            )

    def generate_initial_outreach(
        self,
        substance_name: str,
        substance_cas: str,
        supplier_name: str,
        quantity: str = "",
        destination: str = "",
        intended_use: str = "",
    ) -> dict:
        """Generate the initial RFQ outreach message for a new supplier contact."""
        body_lines = [
            f"Dear {supplier_name},",
            "",
            f"We are interested in procuring {substance_name} (CAS: {substance_cas}).",
        ]
        if quantity:
            body_lines.append(f"Quantity: {quantity}")
        if destination:
            body_lines.append(f"Destination: {destination}")
        if intended_use:
            body_lines.append(f"Intended use: {intended_use}")

        body_lines.extend([
            "",
            "Please provide the following information:",
            "- Certificate of Analysis (COA)",
            "- Safety Data Sheet (SDS/MSDS)",
            "- Specification sheet / TDS",
            "- Country of origin",
            "- Minimum Order Quantity (MOQ)",
            "- Price per kg (with price breaks for larger quantities)",
            "- Lead time",
            "- Incoterms offered",
            "- Payment terms",
            "- Sample availability",
            "- REACH registration status (for EU destination)",
            "- ADR/DG class and UN number",
            "- HS code",
            "",
            "We require accurate product, safety, shipping, and invoice documentation.",
            "We cannot proceed with any workaround of applicable rules or false declarations.",
            "",
            "Kind regards,",
        ])

        subject = f"RFQ: {substance_name} / CAS {substance_cas}"
        if quantity:
            subject += f" / {quantity}"

        return {
            "subject": subject,
            "body": "\n".join(body_lines),
        }
