from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class OperationMode(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"

class CallOutcome(str, Enum):
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    FAILED = "failed"

class TaskData(BaseModel):
    task_id: str
    customer_phone: str
    operation_mode: OperationMode
    retry_count: int = 0
    last_call_time: Optional[datetime] = None
    call_outcome: Optional[CallOutcome] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class CallRequest(BaseModel):
    task_id: str
    phone_number: str
    operation_mode: OperationMode
    webhook_url: str

class CallResult(BaseModel):
    call_sid: str
    task_id: str
    status: str
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    outcome: CallOutcome

class WebhookEvent(BaseModel):
    CallSid: str
    CallStatus: str
    CallDuration: Optional[str] = None
    RecordingUrl: Optional[str] = None
    task_id: Optional[str] = None 