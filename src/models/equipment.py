from enum import Enum

from pydantic import BaseModel


class EquipmentStatus(str, Enum):
    ONLINE = "online"
    WARNING = "warning"
    OFFLINE = "offline"


class Equipment(BaseModel):
    equipment_id: str
    name: str
    location: str
    status: EquipmentStatus