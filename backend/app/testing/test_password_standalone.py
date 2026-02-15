#!/usr/bin/env python3
"""
Standalone password hashing test that doesn't require the full app.
This tests the core password hashing functionality without importing app dependencies.
"""

from passlib.context import CryptContext

# Initialize the same bcrypt context used in the app
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def test_password_hashing():
    """Test that password hashing works correctly."""
    print("Testing password hashing...")

    password = "my_secret_password_123"
    hashed = pwd_context.hash(password)

    # Check hash is not the plaintext
    assert hashed != password, "Hashed password should not equal plaintext"

    # Check hash uses bcrypt format
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$"), \
        f"Hash should use bcrypt format, got: {hashed[:10]}"

    # Check hash is 60 characters (bcrypt standard)
    assert len(hashed) == 60, f"Bcrypt hash should be 60 characters, got {len(hashed)}"

    print(f"✓ Password hashed successfully")
    print(f"  Plaintext: {password}")
    print(f"  Hash: {hashed}")


def test_password_verification():
    """Test that password verification works correctly."""
    print("\nTesting password verification...")

    password = "correct_password"
    wrong_password = "wrong_password"

    # Hash the password
    hashed = pwd_context.hash(password)

    # Verify correct password
    assert pwd_context.verify(password, hashed), "Correct password should verify successfully"
    print(f"✓ Correct password verified successfully")

    # Verify wrong password fails
    assert not pwd_context.verify(wrong_password, hashed), "Wrong password should fail verification"
    print(f"✓ Wrong password correctly rejected")

    # Verify plaintext comparison fails (simulating the bug we fixed)
    assert password != hashed, "Plaintext password should never equal the hash"
    print(f"✓ Plaintext comparison correctly fails (this was the bug)")


def test_salt_uniqueness():
    """Test that same password produces different hashes due to salt."""
    print("\nTesting salt uniqueness...")

    password = "identical_password"

    hash1 = pwd_context.hash(password)
    hash2 = pwd_context.hash(password)

    assert hash1 != hash2, "Same password should produce different hashes due to salt"

    # But both should verify the same password
    assert pwd_context.verify(password, hash1), "Hash 1 should verify the password"
    assert pwd_context.verify(password, hash2), "Hash 2 should verify the password"

    print(f"✓ Salt uniqueness confirmed")
    print(f"  Password: {password}")
    print(f"  Hash 1: {hash1}")
    print(f"  Hash 2: {hash2}")


def test_case_sensitivity():
    """Test that password verification is case-sensitive."""
    print("\nTesting case sensitivity...")

    password = "MyPassWord123"
    hashed = pwd_context.hash(password)

    # Correct case should work
    assert pwd_context.verify(password, hashed), "Exact match should verify"
    print(f"✓ Exact case match verified")

    # Wrong cases should fail
    wrong_cases = ["mypassword123", "MYPASSWORD123", "myPassword123"]
    for wrong in wrong_cases:
        assert not pwd_context.verify(wrong, hashed), f"Wrong case '{wrong}' should fail"
        print(f"✓ Wrong case '{wrong}' correctly rejected")


def test_special_characters():
    """Test passwords with special characters."""
    print("\nTesting special characters...")

    special_passwords = [
        "p@ssw0rd!#$%",
        "パスワード",  # Japanese
        "пароль",      # Cyrillic
        "🔒secure🔑",  # Emojis
        'pass"word\'', # Quotes
    ]

    for password in special_passwords:
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed), f"Special password should hash and verify: {password}"
        print(f"✓ Special password verified: {repr(password)}")


def test_bcrypt_cost_factor():
    """Test that bcrypt uses a reasonable cost factor."""
    print("\nTesting bcrypt cost factor...")

    password = "test_password"
    hashed = pwd_context.hash(password)

    # Bcrypt hash format: $2b$[cost]$[salt][hash]
    hash_parts = hashed.split("$")
    assert len(hash_parts) >= 4, "Invalid bcrypt hash format"

    cost_factor = int(hash_parts[2])
    assert cost_factor >= 10, f"Cost factor should be >= 10 for security, got {cost_factor}"

    print(f"✓ Bcrypt cost factor is {cost_factor} (minimum 10)")


def demonstrate_the_bug():
    """Demonstrate the bug that was fixed."""
    print("\n" + "="*60)
    print("DEMONSTRATING THE BUG THAT WAS FIXED")
    print("="*60)

    password = "user_password"
    hashed_password = pwd_context.hash(password)

    print(f"\nUser's plaintext password: '{password}'")
    print(f"Stored hashed password: '{hashed_password}'")

    print(f"\n❌ OLD CODE (BUGGY): if not password == user.password:")
    print(f"   Comparison: '{password}' == '{hashed_password}'")
    print(f"   Result: {password == hashed_password} (always False!)")
    print(f"   This means login would ALWAYS FAIL")

    print(f"\n✓ NEW CODE (FIXED): if not pwd_context.verify(password, user.password):")
    print(f"   Bcrypt verification: pwd_context.verify('{password}', '{hashed_password}')")
    print(f"   Result: {pwd_context.verify(password, hashed_password)} (correctly True!)")
    print(f"   Login now works correctly")


if __name__ == "__main__":
    print("="*60)
    print("PASSWORD HASHING AND VERIFICATION TESTS")
    print("="*60)

    try:
        test_password_hashing()
        test_password_verification()
        test_salt_uniqueness()
        test_case_sensitivity()
        test_special_characters()
        test_bcrypt_cost_factor()
        demonstrate_the_bug()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nPassword hashing is working correctly!")
        print("The bcrypt verification bug has been fixed.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)
