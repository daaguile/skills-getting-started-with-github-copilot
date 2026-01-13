"""Tests for the activities endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Test the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self):
        """Test that get_activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Soccer Team" in data
        assert "Basketball Team" in data

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)

    def test_get_activities_participants_are_strings(self):
        """Test that participants are string email addresses."""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_info in data.items():
            for participant in activity_info["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity."""
        email = "test@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self):
        """Test signup for a nonexistent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self):
        """Test that duplicate signups are rejected."""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_different_activities_same_student(self):
        """Test that a student can sign up for multiple activities."""
        email = "new_student@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Sign up for Soccer Team
        response2 = client.post(
            "/activities/Soccer Team/signup",
            params={"email": email}
        )
        assert response2.status_code == 200

        # Verify in both
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Soccer Team"]["participants"]


class TestUnregister:
    """Test the POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_from_activity_success(self):
        """Test successful unregister from an activity."""
        # First add a participant
        email = "unregister_test@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )

        # Then unregister
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from a nonexistent activity returns 404."""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_signed_up(self):
        """Test unregister for a student not signed up returns 400."""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "not_signed_up@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Verify they're signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]

        # Unregister
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200

        # Verify they're no longer signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities["Chess Club"]["participants"]
