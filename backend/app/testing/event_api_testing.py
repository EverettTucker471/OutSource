import unittest
from typing import Generator
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from passlib.context import CryptContext

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.event import Event, EventState
from app.models.associations import EventOwnership


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestEventAPI(unittest.TestCase):
    def setUp(self) -> None:
        # Create tables for this test
        Base.metadata.create_all(bind=engine)
        self.db: Session = TestingSessionLocal()

        # Override the app DB dependency to use the test session
        def override_get_db() -> Generator[Session, None, None]:
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Create test users
        self.user1 = self.create_user_direct("user1", "password1", "User One")
        self.user2 = self.create_user_direct("user2", "password2", "User Two")

        # Login users
        self.token1 = self.login("user1", "password1")
        self.token2 = self.login("user2", "password2")

    def tearDown(self) -> None:
        # Cleanup dependency overrides + DB
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # -----------
    # Helpers
    # -----------

    def create_user_direct(self, username: str, password: str, name: str):
        """Create user directly in database."""
        user = User(
            username=username,
            password=pwd_context.hash(password),
            name=name,
            preferences=[]
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, username: str, password: str) -> str:
        """Login and return auth token."""
        res = self.client.post(
            "/login",
            json={"username": username, "password": password}
        )
        return res.json()["access_token"]

    def get_auth_headers(self, token: str) -> dict:
        """Get authorization headers."""
        return {"Authorization": f"Bearer {token}"}

    def create_event_direct(self, name: str, description: str, start_at: datetime, end_at: datetime, state: EventState) -> Event:
        """Create event directly in database."""
        event = Event(
            name=name,
            description=description,
            start_at=start_at,
            end_at=end_at,
            state=state
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def add_event_owner_direct(self, user_id: int, event_id: int):
        """Add event owner directly in database."""
        ownership = EventOwnership(user_id=user_id, event_id=event_id)
        self.db.add(ownership)
        self.db.commit()
        self.db.refresh(ownership)
        return ownership

    # -----------
    # Tests - Create Event
    # -----------

    def test_create_event_returns_201(self):
        """Test creating an event returns 201 and event data."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/events",
            json={
                "name": "Test Event",
                "description": "A test event",
                "start_at": start.isoformat(),
                "end_at": end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertEqual(body["name"], "Test Event")
        self.assertEqual(body["description"], "A test event")
        self.assertEqual(body["state"], "upcoming")
        self.assertIn("id", body)

    def test_create_event_without_description(self):
        """Test creating an event without description."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/events",
            json={
                "name": "Test Event",
                "start_at": start.isoformat(),
                "end_at": end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertIsNone(body["description"])

    def test_create_event_with_end_before_start_returns_400(self):
        """Test creating event with end before start returns 400."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start - timedelta(hours=1)  # End before start

        res = self.client.post(
            "/events",
            json={
                "name": "Invalid Event",
                "start_at": start.isoformat(),
                "end_at": end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    def test_create_event_creator_auto_added_as_owner(self):
        """Test that event creator is automatically added as owner."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/events",
            json={
                "name": "Test Event",
                "start_at": start.isoformat(),
                "end_at": end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)
        event_id = res.json()["id"]

        # Verify creator is an owner
        ownership = self.db.query(EventOwnership).filter(
            EventOwnership.user_id == self.user1.id,
            EventOwnership.event_id == event_id
        ).first()
        self.assertIsNotNone(ownership)

    def test_create_event_state_set_to_upcoming_for_future_event(self):
        """Test event state is set to upcoming for future events."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/events",
            json={
                "name": "Future Event",
                "start_at": start.isoformat(),
                "end_at": end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)
        self.assertEqual(res.json()["state"], "upcoming")

    def test_create_event_state_set_to_passed_for_past_event(self):
        """Test event state is set to passed for past events."""
        now = datetime.now()
        start = now - timedelta(days=1)
        end = start + timedelta(hours=2)

        res = self.client.post(
            "/events",
            json={
                "name": "Past Event",
                "start_at": start.isoformat(),
                "end_at": end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)
        self.assertEqual(res.json()["state"], "passed")

    # -----------
    # Tests - Get Event
    # -----------

    def test_get_event_by_id_as_owner(self):
        """Test owner can get event details."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.get(
            f"/events/{event.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["id"], event.id)
        self.assertEqual(body["name"], "Test Event")
        self.assertEqual(body["description"], "Description")

    def test_get_event_by_id_as_non_owner_returns_403(self):
        """Test non-owner cannot get event details."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.get(
            f"/events/{event.id}",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_get_nonexistent_event_returns_404(self):
        """Test getting event that doesn't exist returns 404."""
        res = self.client.get(
            "/events/99999",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    # -----------
    # Tests - Update Event
    # -----------

    def test_update_event_as_owner(self):
        """Test owner can update their event."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Old Name", "Old Desc", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        new_start = now + timedelta(days=2)
        new_end = new_start + timedelta(hours=3)

        res = self.client.put(
            f"/events/{event.id}",
            json={
                "name": "New Name",
                "description": "New Desc",
                "start_at": new_start.isoformat(),
                "end_at": new_end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["name"], "New Name")
        self.assertEqual(body["description"], "New Desc")

    def test_update_event_partial_update(self):
        """Test partial update of event (only name)."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Old Name", "Original Desc", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.put(
            f"/events/{event.id}",
            json={"name": "Updated Name"},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["name"], "Updated Name")
        self.assertEqual(body["description"], "Original Desc")  # Should remain unchanged

    def test_update_event_state(self):
        """Test updating event state."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.put(
            f"/events/{event.id}",
            json={"state": "passed"},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["state"], "passed")

    def test_update_event_invalid_state_returns_400(self):
        """Test updating event with invalid state returns 400."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.put(
            f"/events/{event.id}",
            json={"state": "invalid_state"},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    def test_update_event_as_non_owner_returns_403(self):
        """Test non-owner cannot update event."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.put(
            f"/events/{event.id}",
            json={"name": "Hacked Name"},
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_update_event_with_end_before_start_returns_400(self):
        """Test updating event with end before start returns 400."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        new_start = now + timedelta(days=2)
        new_end = new_start - timedelta(hours=1)  # End before start

        res = self.client.put(
            f"/events/{event.id}",
            json={
                "start_at": new_start.isoformat(),
                "end_at": new_end.isoformat()
            },
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    # -----------
    # Tests - Delete Event
    # -----------

    def test_delete_event_as_owner(self):
        """Test owner can delete their event."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("To Delete", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.delete(
            f"/events/{event.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Verify event is deleted
        deleted_event = self.db.query(Event).filter(Event.id == event.id).first()
        self.assertIsNone(deleted_event)

    def test_delete_event_as_non_owner_returns_403(self):
        """Test non-owner cannot delete event."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)
        self.add_event_owner_direct(self.user1.id, event.id)

        res = self.client.delete(
            f"/events/{event.id}",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_delete_nonexistent_event_returns_404(self):
        """Test deleting nonexistent event returns 404."""
        res = self.client.delete(
            "/events/99999",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    # -----------
    # Tests - Authentication
    # -----------

    def test_endpoints_require_authentication(self):
        """Test that all event endpoints require authentication."""
        now = datetime.now()
        start = now + timedelta(days=1)
        end = start + timedelta(hours=2)

        event = self.create_event_direct("Test Event", "Description", start, end, EventState.UPCOMING)

        endpoints = [
            ("GET", f"/events/{event.id}"),
            ("POST", "/events"),
            ("PUT", f"/events/{event.id}"),
            ("DELETE", f"/events/{event.id}"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                res = self.client.get(endpoint)
            elif method == "POST":
                res = self.client.post(endpoint, json={})
            elif method == "PUT":
                res = self.client.put(endpoint, json={})
            elif method == "DELETE":
                res = self.client.delete(endpoint)

            self.assertEqual(res.status_code, 401, msg=f"Endpoint {method} {endpoint} should require auth")


if __name__ == "__main__":
    unittest.main()
