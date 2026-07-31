from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


RepairCategory = Literal["electric", "water", "gas", "other"]
RepairUrgency = Literal["low", "middle", "high"]
RepairStatus = Literal["pending", "processing", "completed", "cancelled"]


class RepairCreate(BaseModel):
    repair_type: str = Field(..., max_length=50)
    category: Optional[RepairCategory] = None
    urgency: RepairUrgency = "middle"
    address: str = Field(..., max_length=255)
    contact_name: str = Field(..., max_length=50)
    contact_phone: str = Field(..., max_length=20)
    description: str
    image_urls: Optional[List[str]] = None


class RepairOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: Optional[int] = None
    repair_type: Optional[str] = None
    category: Optional[RepairCategory] = None
    urgency: RepairUrgency
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    status: RepairStatus
    created_at: datetime
    updated_at: datetime
    progress_timeline: Optional[List[Dict[str, Any]]] = None
