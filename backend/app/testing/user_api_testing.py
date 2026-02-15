from typing import List
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
from app.models.associations import Friends, CircleMembership

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestUsersAPI(unittest.TestCase):
    def setUp(self) -> None:
        # Create tables for this test
        Base.metadata.create_all(bind=engine)
        self.db: Session = TestingSessionLocal()

        # Override the app DB dependency to use the test session
        def override_get_db() -> Generator[Session, None, None]:
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Create an initial user for authentication in tests
        self.setup_auth_user()

    def tearDown(self) -> None:
        # Cleanup dependency overrides + DB
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # -----------
    # Helpers
    # -----------

    def setup_auth_user(self):
        """Create an initial user directly in DB for authentication."""
        user = User(
            username="testadmin",
            password=pwd_context.hash("password123"),
            name="Test Admin",
            preferences=[]
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Login and store token
        login_res = self.client.post(
            "/login",
            json={"username": "testadmin", "password": "password123"}
        )
        self.auth_token = login_res.json()["access_token"]

    def get_auth_headers(self) -> dict:
        """Return Authorization header for authenticated requests."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    def create_user_direct(self, username: str, password: str, name: str):
        """Create user directly in database (bypasses authentication)."""
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

    # -----------
    # Tests
    # -----------

    def test_get_user_by_id(self):
        """Test getting a user by ID with authentication."""
        created = self.create_user_direct("alice", "password123", "Alice")
        user_id = created.id

        res = self.client.get(f"/users/{user_id}", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["id"], user_id)
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["name"], "Alice")

    def test_get_current_user_returns_authenticated_user(self):
        """Test GET /me returns the authenticated user from JWT."""
        res = self.client.get("/me", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["username"], "testadmin")
        self.assertEqual(body["name"], "Test Admin")

    def test_get_current_user_without_token_returns_401(self):
        """Test GET /me without authentication returns 401."""
        res = self.client.get("/me")
        self.assertEqual(res.status_code, 401, msg=res.text)

    def test_get_all_users(self):
        """Test getting all users with authentication."""
        # Should have the testadmin user initially
        res0 = self.client.get("/users", headers=self.get_auth_headers())
        self.assertEqual(res0.status_code, 200, msg=res0.text)
        initial_users = res0.json()
        self.assertEqual(len(initial_users), 1)
        self.assertEqual(initial_users[0]["username"], "testadmin")

        # Add two more users directly to database
        self.create_user_direct("u1", "password123", "User One")
        self.create_user_direct("u2", "password123", "User Two")

        # Should now have 3 users total
        res = self.client.get("/users", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 3)
        usernames = {u["username"] for u in body}
        self.assertEqual(usernames, {"testadmin", "u1", "u2"})

    def test_get_all_users_without_auth_returns_401(self):
        """Test getting all users without authentication returns 401."""
        res = self.client.get("/users")
        self.assertEqual(res.status_code, 401, msg=res.text)

    def test_get_user_friends(self):
        """Test GET /users/{id}/friends returns user's friends."""
        # Create test users
        user1 = self.create_user_direct("user1", "pass", "User One")
        user2 = self.create_user_direct("user2", "pass", "User Two")
        user3 = self.create_user_direct("user3", "pass", "User Three")

        # Create friendships
        self.create_friendship(user1.id, user2.id)
        self.create_friendship(user1.id, user3.id)

        # Get user1's friends
        res = self.client.get(f"/users/{user1.id}/friends", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        friend_usernames = {friend["username"] for friend in body}
        self.assertEqual(friend_usernames, {"user2", "user3"})

    def test_get_user_friends_empty_list(self):
        """Test GET /users/{id}/friends returns empty list when user has no friends."""
        user = self.create_user_direct("loner", "pass", "Lonely User")

        res = self.client.get(f"/users/{user.id}/friends", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 0)

    def test_get_user_friends_nonexistent_user(self):
        """Test GET /users/{id}/friends returns 404 for nonexistent user."""
        res = self.client.get("/users/99999/friends", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 404, msg=res.text)

    def test_get_user_circles(self):
        """Test GET /users/{id}/circles returns user's circles."""
        # Create test user
        user = self.create_user_direct("circleuser", "pass", "Circle User")

        # Create circles
        circle1 = self.create_circle("Tech Circle", user.id, public=True)
        circle2 = self.create_circle("Book Club", user.id, public=False)

        # Add user to circles
        self.add_to_circle(user.id, circle1.id)
        self.add_to_circle(user.id, circle2.id)

        # Get user's circles
        res = self.client.get(f"/users/{user.id}/circles", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)

        circle_names = {circle["name"] for circle in body}
        self.assertEqual(circle_names, {"Tech Circle", "Book Club"})

    def test_get_user_circles_empty_list(self):
        """Test GET /users/{id}/circles returns empty list when user has no circles."""
        user = self.create_user_direct("nocircles", "pass", "No Circles User")

        res = self.client.get(f"/users/{user.id}/circles", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 0)

    def test_get_user_circles_nonexistent_user(self):
        """Test GET /users/{id}/circles returns 404 for nonexistent user."""
        res = self.client.get("/users/99999/circles", headers=self.get_auth_headers())
        self.assertEqual(res.status_code, 404, msg=res.text)

    def test_user_endpoints_require_authentication(self):
        """Test that user endpoints require authentication."""
        # Create a test user
        user = self.create_user_direct("testuser", "pass", "Test User")

        endpoints = [
            f"/users/{user.id}/friends",
            f"/users/{user.id}/circles"
        ]

        for endpoint in endpoints:
            res = self.client.get(endpoint)
            self.assertEqual(res.status_code, 401, msg=f"Endpoint {endpoint} should require auth")



if __name__ == "__main__":
    unittest.main()