import pytest
from fastapi.testclient import TestClient

from src import app as api


@pytest.fixture
def client():
	return TestClient(api.app)


@pytest.fixture
def activities_data(monkeypatch):
	test_activities = {
		"Chess Club": {
			"description": "Learn chess",
			"schedule": "Fridays",
			"max_participants": 12,
			"participants": ["existing@example.com"],
		}
	}
	monkeypatch.setattr(api, "activities", test_activities)
	return test_activities


def test_root_redirects_to_frontend(client):
	# Arrange
	# The client fixture provides a fresh TestClient for the app.
	# Act
	response = client.get("/", follow_redirects=False)

	# Assert
	assert response.status_code == 307
	assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client, activities_data):
	# Arrange
	# activities_data is replaced with a fresh fixture for this test.
	# Act
	response = client.get("/activities")

	# Assert
	assert response.status_code == 200
	assert response.json() == activities_data


def test_signup_adds_participant(client, activities_data):
	# Arrange
	new_email = "new@example.com"
	# Act
	response = client.post(
		"/activities/Chess Club/signup", params={"email": new_email}
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {"message": f"Signed up {new_email} for Chess Club"}
	assert new_email in activities_data["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client, activities_data):
	# Arrange
	existing_email = "existing@example.com"
	# Act
	response = client.post(
		"/activities/Chess Club/signup", params={"email": existing_email}
	)

	# Assert
	assert response.status_code == 400
	assert response.json() == {
		"detail": "Student already signed up for this activity"
	}
	assert activities_data["Chess Club"]["participants"] == ["existing@example.com"]


def test_signup_returns_not_found_for_unknown_activity(client, activities_data):
	# Arrange
	# The unknown activity is not present in the activities_data fixture.
	# Act
	response = client.post(
		"/activities/Unknown/signup", params={"email": "new@example.com"}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email(client, activities_data):
	# Arrange
	# Omit the required email query parameter.
	# Act
	response = client.post("/activities/Chess Club/signup")

	# Assert
	assert response.status_code == 422


def test_unregister_removes_participant(client, activities_data):
	# Arrange
	registered_email = "existing@example.com"
	# Act
	response = client.delete(
		"/activities/Chess Club/signup", params={"email": registered_email}
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {
		"message": f"Unregistered {registered_email} from Chess Club"
	}
	assert activities_data["Chess Club"]["participants"] == []


def test_unregister_returns_not_found_for_unknown_activity(client, activities_data):
	# Arrange
	# The unknown activity is not present in the activities_data fixture.
	# Act
	response = client.delete(
		"/activities/Unknown/signup", params={"email": "new@example.com"}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_not_found_for_unregistered_participant(
	client, activities_data
):
	# Arrange
	missing_email = "missing@example.com"
	# Act
	response = client.delete(
		"/activities/Chess Club/signup", params={"email": missing_email}
	)

	# Assert
	assert response.status_code == 404
	assert response.json() == {
		"detail": "Student is not signed up for this activity"
	}
	assert activities_data["Chess Club"]["participants"] == ["existing@example.com"]


def test_unregister_requires_email(client, activities_data):
	# Arrange
	# Omit the required email query parameter.
	# Act
	response = client.delete("/activities/Chess Club/signup")

	# Assert
	assert response.status_code == 422
