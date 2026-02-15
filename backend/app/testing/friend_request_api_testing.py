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
from app.models.associations import Friends, FriendRequests

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestFriendRequestAPI(unittest.TestCase):
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
        self.setup_test_users()

    def tearDown(self) -> None:
        # Cleanup dependency overrides + DB
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=engine)

    # -----------
    # Helpers
    # -----------

    def setup_test_users(self):
        """Create test users and get auth tokens."""
        # Create user 1
        self.user1 = User(
            username="user1",
            password=pwd_context.hash("password123"),
            name="User One",
            preferences=[]
        )
        self.db.add(self.user1)

        # Create user 2
        self.user2 = User(
            username="user2",
            password=pwd_context.hash("password123"),
            name="User Two",
            preferences=[]
        )
        self.db.add(self.user2)

        # Create user 3
        self.user3 = User(
            username="user3",
            password=pwd_context.hash("password123"),
            name="User Three",
            preferences=[]
        )
        self.db.add(self.user3)

        self.db.commit()
        self.db.refresh(self.user1)
        self.db.refresh(self.user2)
        self.db.refresh(self.user3)

        # Login and store tokens
        login_res1 = self.client.post("/login", json={"username": "user1", "password": "password123"})
        self.token1 = login_res1.json()["access_token"]

        login_res2 = self.client.post("/login", json={"username": "user2", "password": "password123"})
        self.token2 = login_res2.json()["access_token"]

        login_res3 = self.client.post("/login", json={"username": "user3", "password": "password123"})
        self.token3 = login_res3.json()["access_token"]

    def get_auth_headers(self, token: str) -> dict:
        """Return Authorization header for authenticated requests."""
        return {"Authorization": f"Bearer {token}"}

    def create_friendship(self, user1_id: int, user2_id: int):
        """Create a friendship directly in database."""
        friendship = Friends(user1_id=user1_id, user2_id=user2_id)
        self.db.add(friendship)
        self.db.commit()
        return friendship

    def create_friend_request(self, outgoing_user_id: int, incoming_user_id: int, status: str = "pending"):
        """Create a friend request directly in database."""
        request = FriendRequests(
            outgoing_user_id=outgoing_user_id,
            incoming_user_id=incoming_user_id,
            status=status
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    # -----------
    # Tests - Create Friend Request
    # -----------

    def test_create_friend_request_success(self):
        """Test creating a friend request successfully."""
        res = self.client.post(
            "/friend-requests",
            json={"recipient_id": self.user2.id},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 201, msg=res.text)

        body = res.json()
        self.assertEqual(body["outgoing_user_id"], self.user1.id)
        self.assertEqual(body["incoming_user_id"], self.user2.id)
        self.assertEqual(body["status"], "pending")

    def test_create_friend_request_to_nonexistent_user(self):
        """Test creating friend request to non-existent user returns 404."""
        res = self.client.post(
            "/friend-requests",
            json={"recipient_id": 99999},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    def test_create_friend_request_to_self(self):
        """Test cannot send friend request to yourself."""
        res = self.client.post(
            "/friend-requests",
            json={"recipient_id": self.user1.id},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)
        self.assertIn("yourself", res.json()["detail"])

    def test_create_friend_request_when_already_friends(self):
        """Test cannot send friend request to existing friend."""
        # Create friendship
        self.create_friendship(self.user1.id, self.user2.id)

        res = self.client.post(
            "/friend-requests",
            json={"recipient_id": self.user2.id},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)
        self.assertIn("Already friends", res.json()["detail"])

    def test_create_duplicate_friend_request(self):
        """Test cannot send duplicate friend request."""
        # Create first request
        self.create_friend_request(self.user1.id, self.user2.id)

        # Try to create another
        res = self.client.post(
            "/friend-requests",
            json={"recipient_id": self.user2.id},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)
        self.assertIn("already sent", res.json()["detail"])

    def test_create_friend_request_when_reverse_exists(self):
        """Test cannot send friend request when recipient already sent one."""
        # User2 sends request to User1
        self.create_friend_request(self.user2.id, self.user1.id)

        # User1 tries to send request to User2
        res = self.client.post(
            "/friend-requests",
            json={"recipient_id": self.user2.id},
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)
        self.assertIn("already sent you", res.json()["detail"])

    # -----------
    # Tests - Accept Friend Request
    # -----------

    def test_accept_friend_request_success(self):
        """Test accepting a friend request successfully."""
        # User1 sends request to User2
        self.create_friend_request(self.user1.id, self.user2.id)

        # User2 accepts
        res = self.client.post(
            "/friend-requests/accept",
            json={"sender_id": self.user1.id},
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)
        self.assertIn("accepted", res.json()["message"])

        # Verify friendship exists in database
        friendship = self.db.query(Friends).filter(
            ((Friends.user1_id == self.user1.id) & (Friends.user2_id == self.user2.id)) |
            ((Friends.user1_id == self.user2.id) & (Friends.user2_id == self.user1.id))
        ).first()
        self.assertIsNotNone(friendship)

    def test_accept_nonexistent_friend_request(self):
        """Test accepting non-existent friend request returns 404."""
        res = self.client.post(
            "/friend-requests/accept",
            json={"sender_id": self.user1.id},
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    def test_accept_already_accepted_request(self):
        """Test cannot accept already accepted request."""
        # Create accepted request
        self.create_friend_request(self.user1.id, self.user2.id, status="accepted")

        res = self.client.post(
            "/friend-requests/accept",
            json={"sender_id": self.user1.id},
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)
        self.assertIn("not pending", res.json()["detail"])

    # -----------
    # Tests - Reject Friend Request
    # -----------

    def test_reject_friend_request_success(self):
        """Test rejecting a friend request successfully."""
        # User1 sends request to User2
        request = self.create_friend_request(self.user1.id, self.user2.id)

        # User2 rejects
        res = self.client.post(
            f"/friend-requests/{request.id}/reject",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)
        self.assertIn("rejected", res.json()["message"])

        # Verify status updated
        self.db.refresh(request)
        self.assertEqual(request.status, "rejected")

    def test_reject_friend_request_not_recipient(self):
        """Test cannot reject friend request if not the recipient."""
        # User1 sends request to User2
        request = self.create_friend_request(self.user1.id, self.user2.id)

        # User3 tries to reject (not the recipient)
        res = self.client.post(
            f"/friend-requests/{request.id}/reject",
            headers=self.get_auth_headers(self.token3)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_reject_nonexistent_friend_request(self):
        """Test rejecting non-existent friend request returns 404."""
        res = self.client.post(
            "/friend-requests/99999/reject",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    # -----------
    # Tests - Cancel Friend Request
    # -----------

    def test_cancel_friend_request_success(self):
        """Test canceling an outgoing friend request successfully."""
        # User1 sends request to User2
        request = self.create_friend_request(self.user1.id, self.user2.id)

        # User1 cancels
        res = self.client.delete(
            f"/friend-requests/{request.id}/cancel",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)
        self.assertIn("cancelled", res.json()["message"])

        # Verify request deleted
        deleted_request = self.db.query(FriendRequests).filter(FriendRequests.id == request.id).first()
        self.assertIsNone(deleted_request)

    def test_cancel_friend_request_not_sender(self):
        """Test cannot cancel friend request if not the sender."""
        # User1 sends request to User2
        request = self.create_friend_request(self.user1.id, self.user2.id)

        # User2 tries to cancel (not the sender)
        res = self.client.delete(
            f"/friend-requests/{request.id}/cancel",
            headers=self.get_auth_headers(self.token2)
        )
        self.assertEqual(res.status_code, 403, msg=res.text)

    def test_cancel_nonexistent_friend_request(self):
        """Test canceling non-existent friend request returns 404."""
        res = self.client.delete(
            "/friend-requests/99999/cancel",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    # -----------
    # Tests - Unfriend
    # -----------

    def test_unfriend_success(self):
        """Test unfriending a user successfully."""
        # Create friendship
        self.create_friendship(self.user1.id, self.user2.id)

        # User1 unfriends User2
        res = self.client.delete(
            f"/friends/{self.user2.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 200, msg=res.text)
        self.assertIn("removed", res.json()["message"])

        # Verify friendship deleted
        friendship = self.db.query(Friends).filter(
            ((Friends.user1_id == self.user1.id) & (Friends.user2_id == self.user2.id)) |
            ((Friends.user1_id == self.user2.id) & (Friends.user2_id == self.user1.id))
        ).first()
        self.assertIsNone(friendship)

    def test_unfriend_nonexistent_user(self):
        """Test unfriending non-existent user returns 404."""
        res = self.client.delete(
            "/friends/99999",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 404, msg=res.text)

    def test_unfriend_not_friends(self):
        """Test cannot unfriend user you're not friends with."""
        res = self.client.delete(
            f"/friends/{self.user2.id}",
            headers=self.get_auth_headers(self.token1)
        )
        self.assertEqual(res.status_code, 400, msg=res.text)
        self.assertIn("not friends", res.json()["detail"])

    # -----------
    # Tests - Authentication
    # -----------

    def test_endpoints_require_authentication(self):
        """Test that all friend request endpoints require authentication."""
        # Create a test request for testing
        request = self.create_friend_request(self.user1.id, self.user2.id)

        endpoints_and_methods = [
            ("POST", "/friend-requests", {"recipient_id": self.user2.id}),
            ("POST", "/friend-requests/accept", {"sender_id": self.user1.id}),
            ("POST", f"/friend-requests/{request.id}/reject", None),
            ("DELETE", f"/friend-requests/{request.id}/cancel", None),
            ("DELETE", f"/friends/{self.user2.id}", None)
        ]

        for method, endpoint, json_data in endpoints_and_methods:
            if method == "POST":
                res = self.client.post(endpoint, json=json_data)
            else:
                res = self.client.delete(endpoint)

            self.assertEqual(res.status_code, 401, msg=f"Endpoint {method} {endpoint} should require auth")


if __name__ == "__main__":
    unittest.main()
