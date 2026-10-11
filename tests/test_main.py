from fastapi.testclient import TestClient
from src.main import app, equipment_db, measurement_db
import pytest
from copy import deepcopy

client = TestClient(app)

initial_equipment = deepcopy(equipment_db)
initial_measurements = deepcopy(measurement_db)


@pytest.fixture(autouse=True)
def reset_test_data():
    equipment_db[:] = deepcopy(initial_equipment)
    measurement_db[:] = deepcopy(initial_measurements)

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

def test_modify_equipment():
    equipment_db[0].name = "Modified Analyzer"

    assert equipment_db[0].name == "Modified Analyzer"

def test_equipment_restored():
    assert equipment_db[0].name == "Gas Analyzer 1"


def test_get_measurements():
    response = client.get("/measurements")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["equipment_id"] == "GAS-101"
    assert response.json()[0]["temperature"] == 25.1

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
    assert len(measurement_db) == 3

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
    assert len(measurement_db) == 3

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
    assert len(measurement_db) == 3

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
    assert len(measurement_db) == 4

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
    assert len(measurement_db) == 3