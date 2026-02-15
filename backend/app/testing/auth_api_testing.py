import unittest
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestAuthAPI(unittest.TestCase):
    def setUp(self) -> None:
        # Create tables for this test
        Base.metadata.create_all(bind=engine)
        self.db: Session = TestingSessionLocal()

        # Override the app DB dependency to use the test session
        def override_get_db() -> Generator[Session, None, None]:
            yield self.db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        # Cleanup dependency overrides + DB
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # -----------
    # Helpers
    # -----------

    def create_user_direct(self, username: str, password: str, name: str):
        """Create user directly via authenticated endpoint and return token."""
        # First, create a test user that we can use to authenticate
        # For the very first user, we'll need to bypass auth temporarily
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

    def login(self, username: str, password: str):
        """Login a user and return the response."""
        return self.client.post(
            "/login",
            json={"username": username, "password": password}
        )

    def get_auth_headers(self, token: str) -> dict:
        """Return Authorization header dict for authenticated requests."""
        return {"Authorization": f"Bearer {token}"}

    def signup(self, username: str, password: str, name: str, preferences=None):
        """Sign up a new user and return the response."""
        return self.client.post(
            "/signup",
            json={
                "username": username,
                "password": password,
                "name": name,
                "preferences": preferences or []
            }
        )

    # -----------
    # Tests - Signup
    # -----------

    def test_signup_with_valid_data_returns_201_and_token(self):
        """Test signup with valid data returns 201 and JWT token."""
        res = self.signup("newuser", "securepass123", "New User", ["sports", "music"])
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertIn("access_token", body)
        self.assertIn("token_type", body)
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(len(body["access_token"]) > 0)

    def test_signup_creates_user_in_database(self):
        """Test signup actually creates the user in the database."""
        res = self.signup("testuser", "password123", "Test User")
        self.assertEqual(res.status_code, 201, msg=res.text)

        # Verify user exists in database
        user = self.db.query(User).filter(User.username == "testuser").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.name, "Test User")

    def test_signup_hashes_password(self):
        """Test signup stores hashed password, not plaintext."""
        res = self.signup("testuser", "mypassword", "Test User")
        self.assertEqual(res.status_code, 201, msg=res.text)

        # Verify password is hashed
        user = self.db.query(User).filter(User.username == "testuser").first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password, "mypassword")
        self.assertTrue(user.password.startswith("$2b$"))  # bcrypt hash prefix

    def test_signup_with_duplicate_username_returns_400(self):
        """Test signup with existing username returns 400 error."""
        # Create first user
        self.signup("johndoe", "password1", "John Doe")

        # Try to create second user with same username
        res = self.signup("johndoe", "password2", "Jane Doe")
        self.assertEqual(res.status_code, 400, msg=res.text)

        body = res.json()
        self.assertIn("detail", body)
        self.assertEqual(body["detail"], "Username already exists")

    def test_signup_token_can_be_used_immediately(self):
        """Test that token from signup can be used to access protected endpoints."""
        res = self.signup("alice", "password123", "Alice Smith", ["coding"])
        self.assertEqual(res.status_code, 201, msg=res.text)

        token = res.json()["access_token"]

        # Use token to access protected endpoint
        user_res = self.client.get(
            "/users/current",
            headers=self.get_auth_headers(token)
        )
        self.assertEqual(user_res.status_code, 200, msg=user_res.text)

        user_body = user_res.json()
        self.assertEqual(user_body["username"], "alice")
        self.assertEqual(user_body["name"], "Alice Smith")
        self.assertEqual(user_body["preferences"], ["coding"])

    def test_signup_user_can_login_after_signup(self):
        """Test that user can login with credentials after signup."""
        # Signup
        signup_res = self.signup("bob", "mypassword", "Bob Johnson")
        self.assertEqual(signup_res.status_code, 201, msg=signup_res.text)

        # Login with same credentials
        login_res = self.login("bob", "mypassword")
        self.assertEqual(login_res.status_code, 200, msg=login_res.text)

        login_body = login_res.json()
        self.assertIn("access_token", login_body)
        self.assertTrue(len(login_body["access_token"]) > 0)

    def test_signup_with_empty_preferences_returns_201(self):
        """Test signup with no preferences succeeds."""
        res = self.signup("minimaluser", "password123", "Minimal User", [])
        self.assertEqual(res.status_code, 201, msg=res.text)

        # Verify user has empty preferences
        user = self.db.query(User).filter(User.username == "minimaluser").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.preferences, [])

    def test_signup_stores_preferences_correctly(self):
        """Test signup correctly stores user preferences."""
        preferences = ["basketball", "reading", "gaming"]
        res = self.signup("userprefs", "password123", "Pref User", preferences)
        self.assertEqual(res.status_code, 201, msg=res.text)

        # Verify preferences stored correctly
        user = self.db.query(User).filter(User.username == "userprefs").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.preferences, preferences)

    # -----------
    # Tests - Login
    # -----------

    def test_login_with_valid_credentials_returns_200_and_token(self):
        """Test login with correct credentials returns token."""
        # Create a user
        user = self.create_user_direct("testuser", "password123", "Test User")

        # Login
        res = self.login("testuser", "password123")
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIn("access_token", body)
        self.assertIn("token_type", body)
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(len(body["access_token"]) > 0)

    def test_login_with_invalid_username_returns_401(self):
        """Test login with non-existent username returns 401."""
        res = self.login("nonexistent", "password123")
        self.assertEqual(res.status_code, 401, msg=res.text)

        body = res.json()
        self.assertIn("detail", body)
        self.assertEqual(body["detail"], "Incorrect username or password")

    def test_login_with_invalid_password_returns_401(self):
        """Test login with wrong password returns 401."""
        # Create a user
        user = self.create_user_direct("testuser", "password123", "Test User")

        # Login with wrong password
        res = self.login("testuser", "wrongpassword")
        self.assertEqual(res.status_code, 401, msg=res.text)

        body = res.json()
        self.assertIn("detail", body)
        self.assertEqual(body["detail"], "Incorrect username or password")

    def test_logout_returns_200(self):
        """Test logout endpoint returns success."""
        res = self.client.post("/logout")
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIn("message", body)
        self.assertEqual(body["message"], "Successfully logged out")

    def test_protected_endpoint_without_token_returns_401(self):
        """Test accessing protected endpoint without token returns 401."""
        res = self.client.get("/users")
        self.assertEqual(res.status_code, 401, msg=res.text)

    def test_protected_endpoint_with_valid_token_returns_200(self):
        """Test accessing protected endpoint with valid token succeeds."""
        # Create user and login
        user = self.create_user_direct("testuser", "password123", "Test User")
        login_res = self.login("testuser", "password123")
        self.assertEqual(login_res.status_code, 200)

        token = login_res.json()["access_token"]

        # Access protected endpoint
        res = self.client.get("/users", headers=self.get_auth_headers(token))
        self.assertEqual(res.status_code, 200, msg=res.text)

    def test_protected_endpoint_with_invalid_token_returns_401(self):
        """Test accessing protected endpoint with malformed token returns 401."""
        res = self.client.get(
            "/users",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        self.assertEqual(res.status_code, 401, msg=res.text)

    def test_get_current_user_returns_authenticated_user(self):
        """Test /users/current returns the authenticated user."""
        # Create user and login
        user = self.create_user_direct("alice", "password123", "Alice Smith")
        login_res = self.login("alice", "password123")
        self.assertEqual(login_res.status_code, 200)

        token = login_res.json()["access_token"]

        # Get current user
        res = self.client.get(
            "/users/current",
            headers=self.get_auth_headers(token)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["name"], "Alice Smith")


if __name__ == "__main__":
    unittest.main()
