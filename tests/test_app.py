from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


ACTIVITY_NAME = "Chess Club"
ACTIVITY_PATH = quote(ACTIVITY_NAME, safe="")


@pytest.fixture
def test_activities():
    return {
        ACTIVITY_NAME: {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 4,
            "participants": ["alex@example.com"],
        }
    }


@pytest.fixture
def client(monkeypatch, test_activities):
    monkeypatch.setattr(app_module, "activities", test_activities)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client, test_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == test_activities


def test_signup_adds_participant(client, test_activities):
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": "sam@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up sam@example.com for Chess Club"}
    assert test_activities[ACTIVITY_NAME]["participants"] == [
        "alex@example.com",
        "sam@example.com",
    ]


def test_signup_returns_404_for_unknown_activity(client, test_activities):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "sam@example.com"},
    )

    assert response.status_code == 404
    assert test_activities[ACTIVITY_NAME]["participants"] == ["alex@example.com"]


def test_signup_rejects_duplicate_participant(client, test_activities):
    response = client.post(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": "alex@example.com"},
    )

    assert response.status_code == 400
    assert test_activities[ACTIVITY_NAME]["participants"] == ["alex@example.com"]


def test_unregister_removes_participant(client, test_activities):
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": "alex@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Removed alex@example.com from Chess Club"}
    assert test_activities[ACTIVITY_NAME]["participants"] == []


def test_unregister_returns_404_for_unknown_activity(client, test_activities):
    response = client.delete(
        "/activities/Unknown%20Club/signup",
        params={"email": "alex@example.com"},
    )

    assert response.status_code == 404
    assert test_activities[ACTIVITY_NAME]["participants"] == ["alex@example.com"]


def test_unregister_returns_404_for_unregistered_participant(client, test_activities):
    response = client.delete(
        f"/activities/{ACTIVITY_PATH}/signup",
        params={"email": "sam@example.com"},
    )

    assert response.status_code == 404
    assert test_activities[ACTIVITY_NAME]["participants"] == ["alex@example.com"]


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"

    static_response = client.get("/static/index.html")
    assert static_response.status_code == 200
    assert "Mergington High School" in static_response.text