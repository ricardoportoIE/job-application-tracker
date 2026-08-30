from app.core.security import hash_password, verify_password


def test_hash_password_does_not_return_plaintext() -> None:
    password = "secure-password-123"

    hashed = hash_password(password)

    assert hashed != password


def test_hash_password_creates_argon2_hash() -> None:
    hashed = hash_password("secure-password-123")

    assert hashed.startswith("$argon2")


def test_verify_password_accepts_correct_password() -> None:
    password = "secure-password-123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_rejects_incorrect_password() -> None:
    hashed = hash_password("secure-password-123")

    assert verify_password("wrong-password", hashed) is False


def test_same_password_generates_different_hashes() -> None:
    password = "secure-password-123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash

    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True


def test_password_whitespace_is_preserved() -> None:
    password = "  secure-password-123  "
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password(password.strip(), hashed) is False
