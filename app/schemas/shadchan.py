from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShadchanCreate(BaseModel):
    name: str
    phone: str
    email: str


class ShadchanUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None


class ShadchanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    email: str
    created_at: datetime
    updated_at: datetime
