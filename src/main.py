from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException

from src.models.equipment import Equipment, EquipmentStatus
from src.models.measurement import Measurement


app = FastAPI(
    title="Enterprise AI Operations Agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "Enterprise AI Operations Agent is running"}


# Temporary in-memory equipment storage
equipment_db = [
    Equipment(
        equipment_id="GAS-101",
        name="Gas Analyzer 1",
        location="Process Line A",
        status=EquipmentStatus.ONLINE,
    ),
    Equipment(
        equipment_id="GAS-102",
        name="Gas Analyzer 2",
        location="Process Line B",
        status=EquipmentStatus.WARNING,
    ),
    Equipment(
        equipment_id="GAS-103",
        name="Gas Analyzer 3",
        location="Process Line C",
        status=EquipmentStatus.OFFLINE,
    ),
]


@app.get("/equipment", response_model=list[Equipment])
def get_equipment():
    return equipment_db


@app.post("/equipment", response_model=Equipment, status_code=201)
def create_equipment(equipment: Equipment):

    for existing_equipment in equipment_db:
        if existing_equipment.equipment_id == equipment.equipment_id:
            raise HTTPException(
                status_code=409,
                detail="Equipment ID already exists"
            )

    equipment_db.append(equipment)
    return equipment


measurement_db = [
    Measurement(
        equipment_id="GAS-101",
        timestamp=datetime(2026, 10, 11, 10, 0, 0, tzinfo=timezone.utc),
        temperature=25.1,
        pressure=101.3
    ),
    Measurement(
        equipment_id="GAS-101",
        timestamp=datetime(2026, 10, 11, 10, 1, 0, tzinfo=timezone.utc),
        temperature=25.3,
        pressure=101.4
    ),
    Measurement(
        equipment_id="GAS-102",
        timestamp=datetime(2026, 10, 11, 10, 0, 0, tzinfo=timezone.utc),
        temperature=32.5,
        pressure=102.1
    )
]


@app.get("/measurements", response_model=list[Measurement])
def get_measurements():
    return measurement_db


@app.post("/measurements", response_model=Measurement, status_code=201)
def create_measurement(measurement: Measurement):
    equipment_exists = any(
        equipment.equipment_id == measurement.equipment_id
        for equipment in equipment_db
    )

    if not equipment_exists:
        raise HTTPException(
            status_code=404,
            detail="Equipment not found"
        )

    measurement_db.append(measurement)
    return measurement