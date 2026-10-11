from datetime import timezone
from pydantic import BaseModel, Field, AwareDatetime, field_validator


class Measurement(BaseModel):
    equipment_id: str
    timestamp: AwareDatetime
    temperature: float
    pressure: float = Field(ge=0)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value):
        return value.astimezone(timezone.utc)