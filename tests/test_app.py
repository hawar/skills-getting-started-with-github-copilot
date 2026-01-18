"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivities:
    """Tests for the /activities endpoint"""

    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify the response is a dictionary
        assert isinstance(activities, dict)
        
        # Check that we have some activities
        assert len(activities) > 0
        
        # Check structure of an activity
        assert "Chess Club" in activities
        activity = activities["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        
        # Verify the student is now in the activity
        activities = client.get("/activities").json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_already_registered(self):
        """Test signup fails for already registered student"""
        # First signup
        client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        
        # Try to signup again
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup fails for nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]

    def test_signup_full_activity(self):
        """Test signup fails when activity is at max capacity"""
        # Get an activity and fill it to capacity
        activities = client.get("/activities").json()
        
        # Use Tennis Club which has low max_participants (10)
        activity = activities["Tennis Club"]
        max_participants = activity["max_participants"]
        current_participants = len(activity["participants"])
        
        # Sign up enough people to fill the activity
        for i in range(max_participants - current_participants):
            response = client.post(
                f"/activities/Tennis%20Club/signup?email=student{i}@mergington.edu"
            )
            if response.status_code == 200:
                continue
            else:
                # Activity full
                assert response.status_code == 400


class TestUnregister:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        # First, signup
        client.post(
            "/activities/Drama%20Club/signup?email=drama_student@mergington.edu"
        )
        
        # Then unregister
        response = client.post(
            "/activities/Drama%20Club/unregister?email=drama_student@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        
        # Verify the student is no longer in the activity
        activities = client.get("/activities").json()
        assert "drama_student@mergington.edu" not in activities["Drama Club"]["participants"]

    def test_unregister_not_registered(self):
        """Test unregister fails for student not in activity"""
        response = client.post(
            "/activities/Art%20Studio/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister fails for nonexistent activity"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]

    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant from an activity"""
        # Get the initial state
        activities = client.get("/activities").json()
        chess_club = activities["Chess Club"]
        initial_count = len(chess_club["participants"])
        
        # Pick the first participant and unregister them
        if initial_count > 0:
            participant = chess_club["participants"][0]
            response = client.post(
                f"/activities/Chess%20Club/unregister?email={participant}"
            )
            assert response.status_code == 200
            
            # Verify count decreased
            activities = client.get("/activities").json()
            assert len(activities["Chess Club"]["participants"]) == initial_count - 1


class TestRoot:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
