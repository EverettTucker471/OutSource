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
from app.models.circle import Circle
from app.models.event import Event, EventState
from app.models.associations import Friends, CircleMembership, EventOwnership, FriendRequests

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestMeAPI(unittest.TestCase):
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
        self.setup_test_data()

    def tearDown(self) -> None:
        # Cleanup dependency overrides + DB
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # -----------
    # Helpers
    # -----------

    def setup_test_data(self):
        """Create test users and get auth token for main user."""
        # Create main test user
        self.main_user = User(
            username="mainuser",
            password=pwd_context.hash("password123"),
            name="Main User",
            preferences=["coding", "music"]
        )
        self.db.add(self.main_user)

        # Create friend users
        self.friend1 = User(
            username="friend1",
            password=pwd_context.hash("password123"),
            name="Friend One",
            preferences=[]
        )
        self.friend2 = User(
            username="friend2",
            password=pwd_context.hash("password123"),
            name="Friend Two",
            preferences=[]
        )
        self.db.add(self.friend1)
        self.db.add(self.friend2)

        # Create non-friend user
        self.other_user = User(
            username="otheruser",
            password=pwd_context.hash("password123"),
            name="Other User",
            preferences=[]
        )
        self.db.add(self.other_user)

        self.db.commit()
        self.db.refresh(self.main_user)
        self.db.refresh(self.friend1)
        self.db.refresh(self.friend2)
        self.db.refresh(self.other_user)

        # Login and store token
        login_res = self.client.post(
            "/login",
            json={"username": "mainuser", "password": "password123"}
        )
        self.auth_token = login_res.json()["access_token"]

    def get_auth_headers(self) -> dict:
        """Return Authorization header for authenticated requests."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    def create_friendship(self, user1_id: int, user2_id: int):
        """Create a friendship between two users."""
        friendship = Friends(user1_id=user1_id, user2_id=user2_id)
        self.db.add(friendship)
        self.db.commit()
        return friendship

    def create_circle(self, name: str, owner_id: int, public: bool = False):
        """Create a circle."""
        circle = Circle(name=name, owner=owner_id, public=public)
        self.db.add(circle)
        self.db.commit()
        self.db.refresh(circle)
        return circle

    def add_to_circle(self, user_id: int, circle_id: int):
        """Add user to circle."""
        membership = CircleMembership(user_id=user_id, circle_id=circle_id)
        self.db.add(membership)
        self.db.commit()
        return membership

    def create_event(self, name: str, description: str = None):
        """Create an event."""
        event = Event(
            name=name,
            description=description,
            start_at=datetime.now() + timedelta(days=1),
            end_at=datetime.now() + timedelta(days=2),
            state=EventState.UPCOMING
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def add_event_ownership(self, user_id: int, event_id: int):
        """Add event ownership."""
        ownership = EventOwnership(user_id=user_id, event_id=event_id)
        self.db.add(ownership)
        self.db.commit()
        return ownership

    def create_friend_request(self, outgoing_user_id: int, incoming_user_id: int):
        """Create a friend request."""
        request = FriendRequests(
            outgoing_user_id=outgoing_user_id,
            incoming_user_id=incoming_user_id,
            status="pending"
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    # -----------
    # Tests
    # -----------

    def test_get_me_returns_current_user(self):
        """Test GET /me returns current user information."""
        res = self.client.get("/me", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["id"], self.main_user.id)
        self.assertEqual(body["username"], "mainuser")
        self.assertEqual(body["name"], "Main User")
        self.assertEqual(body["preferences"], ["coding", "music"])
        # Ensure password is not returned
        self.assertNotIn("password", body)

    def test_get_me_without_auth_returns_401(self):
        """Test GET /me without authentication returns 401."""
        res = self.client.get("/me")
        self.assertEqual(res.status_code, 401, msg=res.text)

    def test_get_me_friends_returns_friends_list(self):
        """Test GET /me/friends returns list of friends."""
        # Create friendships
        self.create_friendship(self.main_user.id, self.friend1.id)
        self.create_friendship(self.main_user.id, self.friend2.id)

        res = self.client.get("/me/friends", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        usernames = {friend["username"] for friend in body}
        self.assertEqual(usernames, {"friend1", "friend2"})

    def test_get_me_friends_returns_empty_when_no_friends(self):
        """Test GET /me/friends returns empty list when user has no friends."""
        res = self.client.get("/me/friends", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 0)

    def test_get_me_circles_returns_user_circles(self):
        """Test GET /me/circles returns circles user belongs to."""
        # Create circles
        circle1 = self.create_circle("Tech Group", self.main_user.id, public=True)
        circle2 = self.create_circle("Book Club", self.other_user.id, public=False)

        # Add main user to both circles
        self.add_to_circle(self.main_user.id, circle1.id)
        self.add_to_circle(self.main_user.id, circle2.id)

        res = self.client.get("/me/circles", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        circle_names = {circle["name"] for circle in body}
        self.assertEqual(circle_names, {"Tech Group", "Book Club"})

    def test_get_me_circles_returns_empty_when_no_circles(self):
        """Test GET /me/circles returns empty list when user has no circles."""
        res = self.client.get("/me/circles", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 0)

    def test_get_me_events_returns_user_events(self):
        """Test GET /me/events returns user's events."""
        # Create events
        event1 = self.create_event("Team Meeting", "Weekly sync")
        event2 = self.create_event("Conference", "Tech conference")

        # Assign events to main user
        self.add_event_ownership(self.main_user.id, event1.id)
        self.add_event_ownership(self.main_user.id, event2.id)

        res = self.client.get("/me/events", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        event_names = {event["name"] for event in body}
        self.assertEqual(event_names, {"Team Meeting", "Conference"})

    def test_get_me_events_returns_empty_when_no_events(self):
        """Test GET /me/events returns empty list when user has no events."""
        res = self.client.get("/me/events", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 0)

    def test_get_incoming_friend_requests(self):
        """Test GET /me/friend-requests/incoming returns incoming requests."""
        # Create friend requests TO main user
        self.create_friend_request(self.friend1.id, self.main_user.id)
        self.create_friend_request(self.other_user.id, self.main_user.id)

        res = self.client.get("/me/friend-requests/incoming", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        sender_usernames = {req["user"]["username"] for req in body}
        self.assertEqual(sender_usernames, {"friend1", "otheruser"})

        # Verify all have pending status
        for req in body:
            self.assertEqual(req["status"], "pending")

    def test_get_outgoing_friend_requests(self):
        """Test GET /me/friend-requests/outgoing returns outgoing requests."""
        # Create friend requests FROM main user
        self.create_friend_request(self.main_user.id, self.friend1.id)
        self.create_friend_request(self.main_user.id, self.friend2.id)

        res = self.client.get("/me/friend-requests/outgoing", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        recipient_usernames = {req["user"]["username"] for req in body}
        self.assertEqual(recipient_usernames, {"friend1", "friend2"})

    def test_update_preferences(self):
        """Test PUT /me/preferences updates user preferences."""
        new_preferences = ["sports", "travel", "photography"]

        res = self.client.put(
            "/me/preferences",
            headers=self.get_auth_headers(),
            json={"preferences": new_preferences}
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["preferences"], new_preferences)

        # Verify in database
        self.db.refresh(self.main_user)
        self.assertEqual(self.main_user.preferences, new_preferences)

    def test_update_preferences_to_empty_list(self):
        """Test PUT /me/preferences can set preferences to empty list."""
        res = self.client.put(
            "/me/preferences",
            headers=self.get_auth_headers(),
            json={"preferences": []}
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["preferences"], [])

        # Verify in database
        self.db.refresh(self.main_user)
        self.assertEqual(self.main_user.preferences, [])

    def test_me_endpoints_require_authentication(self):
        """Test that all /me endpoints require authentication."""
        endpoints = [
            "/me",
            "/me/friends",
            "/me/circles",
            "/me/events",
            "/me/friend-requests/incoming",
            "/me/friend-requests/outgoing"
        ]

        for endpoint in endpoints:
            res = self.client.get(endpoint)
            self.assertEqual(res.status_code, 401, msg=f"Endpoint {endpoint} should require auth")

        # Test PUT endpoint
        res = self.client.put("/me/preferences", json={"preferences": []})
        self.assertEqual(res.status_code, 401, msg="/me/preferences should require auth")


if __name__ == "__main__":
    unittest.main()
