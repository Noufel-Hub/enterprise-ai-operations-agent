import sqlite3

import pytest
from fastapi.testclient import TestClient

import src.main as main
from src.database import get_connection, init_db


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def setup_test_database(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_operations.db"

    # Create the test database
    init_db(test_db_path)

    connection = get_connection(test_db_path)

    try:
        connection.executemany("""
            INSERT INTO equipment
                (equipment_id, name, location, status)
            VALUES (?, ?, ?, ?)
        """, [
            ("GAS-101", "Gas Analyzer 1", "Process Line A", "online"),
            ("GAS-102", "Gas Analyzer 2", "Process Line B", "warning"),
            ("GAS-103", "Gas Analyzer 3", "Process Line C", "offline")
        ])

        connection.executemany("""
            INSERT INTO measurements
                (equipment_id, timestamp, temperature, pressure)
            VALUES (?, ?, ?, ?)
        """, [
            ("GAS-101", "2026-10-11T10:00:00Z", 25.1, 101.3),
            ("GAS-101", "2026-10-11T10:01:00Z", 25.3, 101.4),
            ("GAS-102", "2026-10-11T10:00:00Z", 32.5, 102.1)
        ])

        connection.commit()

    finally:
        connection.close()

    # Redirect FastAPI database connections to our test database
    monkeypatch.setattr(
        main,
        "get_connection",
        lambda: get_connection(test_db_path)
    )

    yield test_db_path

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Enterprise AI Operations Agent is running"
    }

def test_get_equipment():
    response = client.get("/equipment")

    assert response.status_code == 200

    equipment_list = response.json()

    assert len(equipment_list) == 3
    assert equipment_list[0]["equipment_id"] == "GAS-101"
    assert equipment_list[1]["equipment_id"] == "GAS-102"
    assert equipment_list[2]["equipment_id"] == "GAS-103"

def test_create_equipment():
    new_equipment = {
        "equipment_id": "GAS-104",
        "name": "Gas Analyzer 4",
        "location": "Process Line D",
        "status": "online"
    }

    response = client.post("/equipment", json=new_equipment)

    assert response.status_code == 201
    assert response.json() == new_equipment

def test_create_duplicate_equipment():
    duplicate_equipment = {
        "equipment_id": "GAS-101",
        "name": "Duplicate Gas Analyzer",
        "location": "Process Line X",
        "status": "warning"
    }

    response = client.post("/equipment", json=duplicate_equipment)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Equipment ID already exists"
    }

def test_create_equipment_invalid_status():
    invalid_equipment = {
        "equipment_id": "GAS-105",
        "name": "Gas Analyzer 5",
        "location": "Process Line E",
        "status": "broken"
    }

    response = client.post("/equipment", json=invalid_equipment)

    assert response.status_code == 422

def test_equipment_persistence():
    new_equipment = {
        "equipment_id": "GAS-105",
        "name": "Gas Analyzer 5",
        "location": "Process Line E",
        "status": "online"
    }

    response = client.post("/equipment", json=new_equipment)
    assert response.status_code == 201

    response = client.get("/equipment")
    equipment_ids = [
        equipment["equipment_id"]
        for equipment in response.json()
    ]

    assert "GAS-105" in equipment_ids


def test_get_measurements():
    response = client.get("/measurements")

    assert response.status_code == 200

    measurements = response.json()

    assert len(measurements) == 3

    assert any(
        measurement["equipment_id"] == "GAS-101"
        and measurement["temperature"] == 25.1
        for measurement in measurements
    )

def test_create_measurement():
    new_measurement = {
        "equipment_id": "GAS-103",
        "timestamp": "2026-10-11T10:02:00Z",
        "temperature": 28.7,
        "pressure": 101.8
    }

    response = client.post("/measurements", json=new_measurement)

    assert response.status_code == 201
    assert response.json() == new_measurement

def test_create_measurement_invalid_timestamp():
    invalid_measurement = {
        "equipment_id": "GAS-103",
        "timestamp": "not_a_date",
        "temperature": 28.7,
        "pressure": 101.8
    }

    response = client.post(
        "/measurements",
        json=invalid_measurement
    )

    assert response.status_code == 422
    assert len(client.get("/measurements").json()) == 3

def test_create_measurement_negative_pressure():
    invalid_measurement = {
        "equipment_id": "GAS-103",
        "timestamp": "2026-10-11T10:02:00Z",
        "temperature": 28.7,
        "pressure": -50.0
    }

    response = client.post(
        "/measurements",
        json=invalid_measurement
    )

    assert response.status_code == 422
    assert len(client.get("/measurements").json()) == 3

def test_create_measurement_without_timezone():
    invalid_measurement = {
        "equipment_id": "GAS-103",
        "timestamp": "2026-10-11T10:02:00",
        "temperature": 28.7,
        "pressure": 101.8
    }

    response = client.post(
        "/measurements",
        json=invalid_measurement
    )

    assert response.status_code == 422
    assert len(client.get("/measurements").json()) == 3

def test_create_measurement_timezone_normalization():
    new_measurement = {
        "equipment_id": "GAS-103",
        "timestamp": "2026-10-11T12:00:00+02:00",
        "temperature": 28.7,
        "pressure": 101.8
    }

    response = client.post(
        "/measurements",
        json=new_measurement
    )

    assert response.status_code == 201
    assert response.json()["timestamp"] == "2026-10-11T10:00:00Z"
    assert len(client.get("/measurements").json()) == 4

def test_create_measurement_unknown_equipment():
    invalid_measurement = {
        "equipment_id": "GAS-999",
        "timestamp": "2026-10-11T10:02:00Z",
        "temperature": 28.7,
        "pressure": 101.8
    }

    response = client.post(
        "/measurements",
        json=invalid_measurement
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Equipment not found"
    assert len(client.get("/measurements").json()) == 3


def test_ask_agent(monkeypatch):
    class FakeMessage:
        text = "The latest temperature of GAS-101 is 28.5°C."

    class FakeAgent:
        def invoke(self, state):
            return {
                "messages": [
                    FakeMessage()
                ]
            }

    monkeypatch.setattr(main, "agent", FakeAgent())

    response = client.post(
        "/agent/ask",
        json={
            "question": "What is the latest temperature of GAS-101?"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The latest temperature of GAS-101 is 28.5°C."
    }


def test_ask_agent_empty_question():
    response = client.post(
        "/agent/ask",
        json={"question": ""}
    )

    assert response.status_code == 422