from app.db.session import SessionLocal
from app.services.audit_log import AuditLogService
from app.workers.celery_app import celery_app


def _log_task(action: str, object_type: str | None = None, object_id: str | None = None, details: dict | None = None) -> None:
    with SessionLocal() as db:
        AuditLogService(db).log(action, object_type, object_id, details or {})
        db.commit()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enrich_substance_task(self, substance_id: str) -> dict:
    _log_task("task_enrich_substance_started", "substance", substance_id)
    return {"status": "queued", "substance_id": substance_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def discovery_task(self, campaign_id: str | None = None, substance_id: str | None = None) -> dict:
    _log_task("task_discovery_started", "campaign" if campaign_id else "substance", campaign_id or substance_id)
    return {"status": "queued", "campaign_id": campaign_id, "substance_id": substance_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def fetch_page_task(self, url: str) -> dict:
    _log_task("task_fetch_page_started", "url", None, {"url": url})
    return {"status": "queued", "url": url}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def extract_supplier_task(self, snapshot_id: str) -> dict:
    _log_task("task_extract_supplier_started", "raw_snapshot", snapshot_id)
    return {"status": "queued", "snapshot_id": snapshot_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def classify_supplier_task(self, supplier_id: str) -> dict:
    _log_task("task_classify_supplier_started", "supplier", supplier_id)
    return {"status": "queued", "supplier_id": supplier_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_rfq_task(self, campaign_id: str, supplier_id: str) -> dict:
    _log_task("task_generate_rfq_started", "campaign", campaign_id, {"supplier_id": supplier_id})
    return {"status": "queued", "campaign_id": campaign_id, "supplier_id": supplier_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def evaluate_policy_task(self, outbound_message_id: str) -> dict:
    _log_task("task_evaluate_policy_started", "outbound_message", outbound_message_id)
    return {"status": "queued", "outbound_message_id": outbound_message_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_email_task(self, outbound_message_id: str) -> dict:
    _log_task("task_send_email_started", "outbound_message", outbound_message_id)
    return {"status": "queued", "outbound_message_id": outbound_message_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def submit_form_task(self, outbound_message_id: str) -> dict:
    _log_task("task_submit_form_started", "outbound_message", outbound_message_id)
    return {"status": "queued", "outbound_message_id": outbound_message_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def poll_inbox_task(self) -> dict:
    _log_task("task_poll_inbox_started")
    return {"status": "queued"}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def parse_inbound_message_task(self, inbound_message_id: str) -> dict:
    _log_task("task_parse_inbound_started", "inbound_message", inbound_message_id)
    return {"status": "queued", "inbound_message_id": inbound_message_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def extract_quote_task(self, inbound_message_id: str) -> dict:
    _log_task("task_extract_quote_started", "inbound_message", inbound_message_id)
    return {"status": "queued", "inbound_message_id": inbound_message_id}


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_followup_task(self, inbound_message_id: str) -> dict:
    _log_task("task_generate_followup_started", "inbound_message", inbound_message_id)
    return {"status": "queued", "inbound_message_id": inbound_message_id}
