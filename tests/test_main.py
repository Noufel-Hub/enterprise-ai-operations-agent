from fastapi.testclient import TestClient
from src.main import app
import pytest
from src.main import equipment_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_equipment_db():
    del equipment_db[3:]

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