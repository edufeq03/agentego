from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# --- Contacts ---

class CrmContactBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: str = "whatsapp"
    status: str = "active"
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class CrmContactCreate(CrmContactBase):
    pass

class CrmContactResponse(CrmContactBase):
    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Pipelines ---

class CrmPipelineBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False
    stages: List[Dict[str, Any]] = Field(default_factory=list)

class CrmPipelineCreate(CrmPipelineBase):
    pass

class CrmPipelineResponse(CrmPipelineBase):
    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Deals ---

class CrmDealBase(BaseModel):
    pipeline_id: UUID
    stage_id: str
    contact_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    title: str
    value: float = 0.0
    currency: str = "BRL"
    status: str = "open"
    lost_reason: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class CrmDealCreate(CrmDealBase):
    pass

class CrmDealResponse(CrmDealBase):
    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Custom fields for UI rendering
    phone: Optional[str] = None
    intent: Optional[str] = None
    summary: Optional[str] = None

    class Config:
        from_attributes = True

class DealStageUpdate(BaseModel):
    stage_id: str

# --- Activities ---

class CrmActivityBase(BaseModel):
    type: str
    subject: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    done: bool = False
    done_at: Optional[datetime] = None
    deal_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None

class CrmActivityCreate(CrmActivityBase):
    pass

class CrmActivityResponse(CrmActivityBase):
    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Contexts ---

class CrmContextBase(BaseModel):
    contact_id: Optional[UUID] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)

class CrmContextCreate(CrmContextBase):
    pass

class CrmContextResponse(CrmContextBase):
    id: UUID
    empresa_id: UUID
    last_analyzed_at: datetime

    class Config:
        from_attributes = True
