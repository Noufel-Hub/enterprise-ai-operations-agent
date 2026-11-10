import sqlite3
from fastapi import FastAPI, HTTPException

from src.models.equipment import Equipment
from src.models.measurement import Measurement
from src.database import get_connection

from langchain_core.messages import HumanMessage

from src.agent.graph import agent
from src.models.agent import AgentRequest, AgentResponse


app = FastAPI(
    title="Enterprise AI Operations Agent",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "Enterprise AI Operations Agent is running"}


@app.get("/equipment", response_model=list[Equipment])
def get_equipment():
    connection = get_connection()

    try:
        cursor = connection.execute("SELECT * FROM equipment")
        equipment = [dict(row) for row in cursor.fetchall()]
        return equipment

    finally:
        connection.close()


@app.post("/equipment", response_model=Equipment, status_code=201)
def create_equipment(equipment: Equipment):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO equipment (
                equipment_id,
                name,
                location,
                status
            )
            VALUES (?, ?, ?, ?)
        """, (
            equipment.equipment_id,
            equipment.name,
            equipment.location,
            equipment.status.value
        ))

        connection.commit()
        return equipment

    except sqlite3.IntegrityError:
        connection.rollback()
        raise HTTPException(
            status_code=409,
            detail="Equipment ID already exists"
        )

    finally:
        connection.close()



@app.get("/measurements", response_model=list[Measurement])
def get_measurements():
    connection = get_connection()

    try:
        cursor = connection.execute("""
            SELECT equipment_id, timestamp, temperature, pressure
            FROM measurements
            ORDER BY timestamp
        """)

        measurements = [dict(row) for row in cursor.fetchall()]
        return measurements

    finally:
        connection.close()


@app.post("/measurements", response_model=Measurement, status_code=201)
def create_measurement(measurement: Measurement):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO measurements (
                equipment_id,
                timestamp,
                temperature,
                pressure
            )
            VALUES (?, ?, ?, ?)
        """, (
            measurement.equipment_id,
            measurement.timestamp.isoformat(),
            measurement.temperature,
            measurement.pressure
        ))

        connection.commit()
        return measurement

    except sqlite3.IntegrityError:
        connection.rollback()
        raise HTTPException(
            status_code=404,
            detail="Equipment not found"
        )

    finally:
        connection.close()


@app.post("/agent/ask", response_model=AgentResponse)
def ask_agent(request: AgentRequest):
    result = agent.invoke({
        "messages": [
            HumanMessage(content=request.question)
        ]
    })

    final_message = result["messages"][-1]

    return AgentResponse(answer=final_message.text)