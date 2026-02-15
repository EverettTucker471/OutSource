import unittest
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from passlib.context import CryptContext

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.circle import Circle
from app.models.associations import CircleMembership


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestCircleAPI(unittest.TestCase):
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
        self.user3 = self.create_user_direct("user3", "password3", "User Three")

        # Login user1
        self.token1 = self.login("user1", "password1")
        self.token2 = self.login("user2", "password2")
        self.token3 = self.login("user3", "password3")

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

    def create_circle_direct(self, name: str, public: bool, owner_id: int) -> Circle:
        """Create circle directly in database."""
        circle = Circle(name=name, public=public, owner=owner_id)
        self.db.add(circle)
        self.db.commit()
        self.db.refresh(circle)
        return circle

    def add_member_direct(self, user_id: int, circle_id: int):
        """Add member to circle directly in database."""
        membership = CircleMembership(user_id=user_id, circle_id=circle_id)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    # -----------
    # Tests - Create Circle
    # -----------

    def test_create_circle_returns_201(self):
        """Test creating a circle returns 201 and circle data."""
        res = self.client.post(
            "/circles",
            json={"name": "Test Circle", "public": True},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertEqual(body["name"], "Test Circle")
        self.assertEqual(body["public"], True)
        self.assertEqual(body["owner"], self.user1.id)
        self.assertIn("id", body)

    def test_create_private_circle(self):
        """Test creating a private circle."""
        res = self.client.post(
            "/circles",
            json={"name": "Private Circle", "public": False},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertEqual(body["public"], False)

    def test_create_circle_owner_auto_added_as_member(self):
        """Test that circle owner is automatically added as a member."""
        res = self.client.post(
            "/circles",
            json={"name": "Auto Member Circle", "public": True},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)
        circle_id = res.json()["id"]

        # Verify owner is a member
        membership = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == self.user1.id,
            CircleMembership.circle_id == circle_id
        ).first()
        self.assertIsNotNone(membership)

    # -----------
    # Tests - Get Circles
    # -----------

    def test_get_all_circles(self):
        """Test getting all circles."""
        self.create_circle_direct("Circle 1", True, self.user1.id)
        self.create_circle_direct("Circle 2", False, self.user2.id)

        res = self.client.get(
            "/circles",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

    def test_get_circle_by_id(self):
        """Test getting a specific circle by ID."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.get(
            f"/circles/{circle.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["id"], circle.id)
        self.assertEqual(body["name"], "Test Circle")
        self.assertEqual(body["owner"], self.user1.id)

    def test_get_nonexistent_circle_returns_404(self):
        """Test getting a circle that doesn't exist returns 404."""
        res = self.client.get(
            "/circles/99999",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    # -----------
    # Tests - Update Circle
    # -----------

    def test_update_circle_as_owner(self):
        """Test owner can update their circle."""
        circle = self.create_circle_direct("Old Name", True, self.user1.id)

        res = self.client.put(
            f"/circles/{circle.id}",
            json={"name": "New Name", "public": False},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["name"], "New Name")
        self.assertEqual(body["public"], False)

    def test_update_circle_partial_update(self):
        """Test partial update of circle (only name)."""
        circle = self.create_circle_direct("Old Name", True, self.user1.id)

        res = self.client.put(
            f"/circles/{circle.id}",
            json={"name": "Updated Name"},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["name"], "Updated Name")
        self.assertEqual(body["public"], True)  # Should remain unchanged

    def test_update_circle_as_non_owner_returns_403(self):
        """Test non-owner cannot update circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.put(
            f"/circles/{circle.id}",
            json={"name": "Hacked Name"},
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    # -----------
    # Tests - Delete Circle
    # -----------

    def test_delete_circle_as_owner(self):
        """Test owner can delete their circle."""
        circle = self.create_circle_direct("To Delete", True, self.user1.id)

        res = self.client.delete(
            f"/circles/{circle.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Verify circle is deleted
        deleted_circle = self.db.query(Circle).filter(Circle.id == circle.id).first()
        self.assertIsNone(deleted_circle)

    def test_delete_circle_as_non_owner_returns_403(self):
        """Test non-owner cannot delete circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.delete(
            f"/circles/{circle.id}",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    # -----------
    # Tests - Join Circle
    # -----------

    def test_join_public_circle(self):
        """Test user can join a public circle."""
        circle = self.create_circle_direct("Public Circle", True, self.user1.id)

        res = self.client.post(
            f"/circles/{circle.id}/join",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Verify user2 is now a member
        membership = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == self.user2.id,
            CircleMembership.circle_id == circle.id
        ).first()
        self.assertIsNotNone(membership)

    def test_join_private_circle_returns_403(self):
        """Test user cannot join a private circle."""
        circle = self.create_circle_direct("Private Circle", False, self.user1.id)

        res = self.client.post(
            f"/circles/{circle.id}/join",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_join_circle_already_member_returns_400(self):
        """Test joining a circle as an existing member returns 400."""
        circle = self.create_circle_direct("Public Circle", True, self.user1.id)
        self.add_member_direct(self.user2.id, circle.id)

        res = self.client.post(
            f"/circles/{circle.id}/join",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    # -----------
    # Tests - Add Member
    # -----------

    def test_add_member_as_owner(self):
        """Test owner can add members to circle."""
        circle = self.create_circle_direct("Test Circle", False, self.user1.id)

        res = self.client.post(
            f"/circles/{circle.id}/join/{self.user2.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Verify user2 is a member
        membership = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == self.user2.id,
            CircleMembership.circle_id == circle.id
        ).first()
        self.assertIsNotNone(membership)

    def test_add_member_as_non_owner_returns_403(self):
        """Test non-owner cannot add members."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.post(
            f"/circles/{circle.id}/join/{self.user3.id}",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_add_nonexistent_user_returns_404(self):
        """Test adding a nonexistent user returns 404."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.post(
            f"/circles/{circle.id}/join/99999",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    # -----------
    # Tests - Leave Circle
    # -----------

    def test_leave_circle_as_member(self):
        """Test member can leave a circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)
        self.add_member_direct(self.user2.id, circle.id)

        res = self.client.post(
            f"/circles/{circle.id}/leave",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Verify user2 is no longer a member
        membership = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == self.user2.id,
            CircleMembership.circle_id == circle.id
        ).first()
        self.assertIsNone(membership)

    def test_owner_cannot_leave_own_circle(self):
        """Test owner cannot leave their own circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)
        self.add_member_direct(self.user1.id, circle.id)

        res = self.client.post(
            f"/circles/{circle.id}/leave",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    def test_leave_circle_not_member_returns_400(self):
        """Test leaving a circle as a non-member returns 400."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.post(
            f"/circles/{circle.id}/leave",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    # -----------
    # Tests - Kick Member
    # -----------

    def test_kick_member_as_owner(self):
        """Test owner can kick members from circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)
        self.add_member_direct(self.user2.id, circle.id)

        res = self.client.post(
            f"/circles/{circle.id}/kick/{self.user2.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Verify user2 is no longer a member
        membership = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == self.user2.id,
            CircleMembership.circle_id == circle.id
        ).first()
        self.assertIsNone(membership)

    def test_kick_member_as_non_owner_returns_403(self):
        """Test non-owner cannot kick members."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)
        self.add_member_direct(self.user2.id, circle.id)
        self.add_member_direct(self.user3.id, circle.id)

        res = self.client.post(
            f"/circles/{circle.id}/kick/{self.user3.id}",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_owner_cannot_kick_self(self):
        """Test owner cannot kick themselves."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)
        self.add_member_direct(self.user1.id, circle.id)

        res = self.client.post(
            f"/circles/{circle.id}/kick/{self.user1.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)

    # -----------
    # Tests - Get Members
    # -----------

    def test_get_circle_members(self):
        """Test getting all members of a circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)
        self.add_member_direct(self.user1.id, circle.id)
        self.add_member_direct(self.user2.id, circle.id)
        self.add_member_direct(self.user3.id, circle.id)

        res = self.client.get(
            f"/circles/{circle.id}/members",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 3)

        usernames = {member["username"] for member in body}
        self.assertEqual(usernames, {"user1", "user2", "user3"})

    def test_get_members_empty_circle(self):
        """Test getting members of a circle with no members."""
        circle = self.create_circle_direct("Empty Circle", True, self.user1.id)

        res = self.client.get(
            f"/circles/{circle.id}/members",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(len(body), 0)

    # -----------
    # Tests - Get Events
    # -----------

    def test_get_circle_events(self):
        """Test getting events for a circle."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        res = self.client.get(
            f"/circles/{circle.id}/events",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        # Currently returns empty list (to be implemented later)
        body = res.json()
        self.assertIsInstance(body, list)

    # -----------
    # Tests - Authentication
    # -----------

    def test_endpoints_require_authentication(self):
        """Test that all circle endpoints require authentication."""
        circle = self.create_circle_direct("Test Circle", True, self.user1.id)

        endpoints = [
            ("GET", f"/circles"),
            ("GET", f"/circles/{circle.id}"),
            ("POST", "/circles"),
            ("PUT", f"/circles/{circle.id}"),
            ("DELETE", f"/circles/{circle.id}"),
            ("POST", f"/circles/{circle.id}/join"),
            ("POST", f"/circles/{circle.id}/join/{self.user2.id}"),
            ("POST", f"/circles/{circle.id}/leave"),
            ("POST", f"/circles/{circle.id}/kick/{self.user2.id}"),
            ("GET", f"/circles/{circle.id}/members"),
            ("GET", f"/circles/{circle.id}/events"),
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
