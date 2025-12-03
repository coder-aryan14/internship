"""User management and authentication helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Dict, Optional, Type
import uuid


class AuthenticationError(RuntimeError):
    pass


class AuthorizationError(RuntimeError):
    pass


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def _verify_password(password: str, hashed: str) -> bool:
    salt, digest = hashed.split("$", 1)
    check = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(check, digest)


@dataclass
class User:
    username: str
    full_name: str
    _password_hash: str
    active: bool = True
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def verify_password(self, password: str) -> bool:
        return _verify_password(password, self._password_hash)

    @classmethod
    def from_plain_password(cls, username: str, full_name: str, password: str) -> "User":
        return cls(username=username, full_name=full_name, _password_hash=_hash_password(password))

    def set_password(self, password: str) -> None:
        self._password_hash = _hash_password(password)

    def is_locked(self) -> bool:
        now = datetime.now(timezone.utc)
        return bool(self.locked_until and self.locked_until > now)

    def register_failed_login(self, max_attempts: int, lock_duration: timedelta) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + lock_duration
            self.failed_attempts = 0

    def reset_lock(self) -> None:
        self.failed_attempts = 0
        self.locked_until = None


@dataclass
class AdminUser(User):
    role: str = "admin"


@dataclass
class CustomerUser(User):
    shipping_address: str = ""
    role: str = "customer"


@dataclass
class SupportUser(User):
    role: str = "support"


@dataclass
class FulfillmentUser(User):
    role: str = "fulfillment"


class AuthService:
    """Authentication + authorization with persistence hooks."""

    MAX_FAILED_ATTEMPTS = 5
    LOCK_DURATION = timedelta(minutes=15)

    def __init__(self, storage=None) -> None:
        self._storage = storage
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, str] = {}
        self._reset_tokens: Dict[str, Dict[str, datetime]] = {}
        if self._storage:
            self._users = self._storage.load_user_objects(self._resolve_user_class)

    def register_user(self, user: User, acting_user: Optional[User] = None) -> None:
        if isinstance(user, AdminUser) and acting_user is not None and acting_user.role != "admin":
            raise AuthorizationError("Only admins may create other admins.")
        if user.username in self._users:
            raise ValueError(f"User {user.username} already exists.")
        self._users[user.username] = user
        self._persist()

    def login(self, username: str, password: str) -> str:
        user = self._users.get(username)
        if not user or not user.active:
            raise AuthenticationError("Invalid credentials.")
        if user.is_locked():
            raise AuthenticationError("Account temporarily locked.")
        if not user.verify_password(password):
            user.register_failed_login(self.MAX_FAILED_ATTEMPTS, self.LOCK_DURATION)
            self._persist()
            raise AuthenticationError("Invalid credentials.")
        user.reset_lock()
        token = secrets.token_urlsafe(24)
        self._sessions[token] = user.id
        self._persist()
        return token

    def logout(self, token: str) -> None:
        self._sessions.pop(token, None)

    def resolve_user(self, token: str) -> User:
        user_id = self._sessions.get(token)
        if not user_id:
            raise AuthenticationError("Session expired.")
        for user in self._users.values():
            if user.id == user_id:
                return user
        raise AuthenticationError("User no longer exists.")

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def delete_user(self, username: str, acting_user: User) -> None:
        require_admin(acting_user)
        if username == acting_user.username:
            raise AuthorizationError("Admins cannot delete themselves.")
        self._users.pop(username, None)
        self._persist()

    def list_users(self) -> Dict[str, User]:
        return dict(self._users)

    def request_password_reset(self, username: str) -> str:
        user = self._users.get(username)
        if not user:
            raise AuthenticationError("User not found.")
        token = secrets.token_urlsafe(16)
        expiry = datetime.now(timezone.utc) + timedelta(minutes=30)
        self._reset_tokens[token] = {"username": username, "expires_at": expiry}
        return token

    def reset_password(self, token: str, new_password: str) -> None:
        payload = self._reset_tokens.get(token)
        if not payload or payload["expires_at"] < datetime.now(timezone.utc):
            raise AuthenticationError("Reset token invalid or expired.")
        username = payload["username"]
        user = self._users[username]
        user.set_password(new_password)
        user.reset_lock()
        self._reset_tokens.pop(token, None)
        self._persist()

    def unlock_user(self, username: str, acting_user: User) -> None:
        require_admin(acting_user)
        user = self._users.get(username)
        if not user:
            raise AuthenticationError("User not found.")
        user.reset_lock()
        self._persist()

    def _persist(self) -> None:
        if self._storage:
            self._storage.persist_user_objects(self._users)

    @staticmethod
    def _resolve_user_class(payload: Dict[str, str]) -> Type[User]:
        role = payload.get("role", "customer")
        registry: Dict[str, Type[User]] = {
            "admin": AdminUser,
            "customer": CustomerUser,
            "support": SupportUser,
            "fulfillment": FulfillmentUser,
        }
        return registry.get(role, CustomerUser)


def require_admin(user: User) -> None:
    if getattr(user, "role", None) != "admin":
        raise AuthorizationError("Administrator privileges required.")
