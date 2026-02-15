from typing import List
import unittest
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User  # Import the User model to register it with Base


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

    def tearDown(self) -> None:
        # Cleanup dependency overrides + DB
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # -----------
    # Helpers
    # -----------

    def create_user(self, username: str, name: str, password: str = "password123"):
        return self.client.post("/users", json={"username": username, "name": name, "password": password})

    # -----------
    # Tests
    # -----------

    def test_create_user_returns_201(self):
        res = self.create_user("jdking7", "Jacob King")
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertIn("id", body)
        self.assertEqual(body["username"], "jdking7")
        self.assertEqual(body["name"], "Jacob King")

    def test_get_user_by_id(self):
        created = self.create_user("alice", "Alice")
        self.assertEqual(created.status_code, 201, msg=created.text)
        user_id = created.json()["id"]

        res = self.client.get(f"/users/{user_id}")
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["id"], user_id)
        self.assertEqual(body["username"], "alice")
        self.assertEqual(body["name"], "Alice")

    def test_get_current_user_uses_header(self):
        created = self.create_user("bob", "Bob")
        self.assertEqual(created.status_code, 201, msg=created.text)
        user_id = created.json()["id"]

        res = self.client.get("/users/current", headers={"x-user-id": str(user_id)})
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertEqual(body["id"], user_id)
        self.assertEqual(body["username"], "bob")
        self.assertEqual(body["name"], "Bob")

    def test_get_current_user_missing_header_returns_422(self):
        res = self.client.get("/users/current")
        self.assertEqual(res.status_code, 422, msg=res.text)

    def test_get_all_users(self):
        # Empty at first
        res0 = self.client.get("/users")
        self.assertEqual(res0.status_code, 200, msg=res0.text)
        self.assertEqual(res0.json(), [])

        # Add two users
        r1 = self.create_user("u1", "User One")
        r2 = self.create_user("u2", "User Two")
        self.assertEqual(r1.status_code, 201, msg=r1.text)
        self.assertEqual(r2.status_code, 201, msg=r2.text)

        res = self.client.get("/users")
        self.assertEqual(res.status_code, 200, msg=res.text)

        body = res.json()
        self.assertIsInstance(body, list)
        usernames = {u["username"] for u in body}
        self.assertEqual(usernames, {"u1", "u2"})


if __name__ == "__main__":
    unittest.main()