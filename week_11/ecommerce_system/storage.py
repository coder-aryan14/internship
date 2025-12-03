"""Persistence utilities for saving and loading platform state."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
from threading import Lock
from typing import Callable, Dict, Iterable, List, Tuple, Type

from .models import Category, Order, OrderStatus, Product
from .cart import CartItem
from .users import User


def _dt_to_str(value: datetime) -> str:
    return value.isoformat()


def _dt_from_str(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _serialize_decimal(value: Decimal) -> str:
    return format(value, "f")


def _deserialize_decimal(value: str) -> Decimal:
    return Decimal(value)


def _serialize_category(category: Category) -> Dict[str, str]:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "created_at": _dt_to_str(category.created_at),
        "updated_at": _dt_to_str(category.updated_at),
    }


def _deserialize_category(payload: Dict[str, str]) -> Category:
    category = Category(name=payload["name"], description=payload.get("description", ""))
    category.id = payload["id"]
    category.created_at = _dt_from_str(payload["created_at"])
    category.updated_at = _dt_from_str(payload["updated_at"])
    return category


def _serialize_product(product: Product) -> Dict[str, str]:
    return {
        "id": product.id,
        "name": product.name,
        "price": _serialize_decimal(product.price),
        "stock": product.stock,
        "category_id": product.category_id,
        "description": product.description,
        "metadata": product.metadata,
        "created_at": _dt_to_str(product.created_at),
        "updated_at": _dt_to_str(product.updated_at),
    }


def _deserialize_product(payload: Dict[str, str]) -> Product:
    product = Product(
        name=payload["name"],
        price=_deserialize_decimal(payload["price"]),
        stock=payload["stock"],
        category_id=payload["category_id"],
        description=payload.get("description", ""),
        metadata=payload.get("metadata", {}),
    )
    product.id = payload["id"]
    product.created_at = _dt_from_str(payload["created_at"])
    product.updated_at = _dt_from_str(payload["updated_at"])
    return product


def _serialize_cart_item(item: CartItem) -> Dict[str, str]:
    return {"product_id": item.product.id, "quantity": item.quantity}


def _serialize_order(order: Order) -> Dict[str, str]:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "items": [_serialize_cart_item(item) for item in order.items],
        "status": order.status.value,
        "payment_reference": order.payment_reference,
        "subtotal": _serialize_decimal(order.subtotal),
        "created_at": _dt_to_str(order.created_at),
        "updated_at": _dt_to_str(order.updated_at),
    }


def _deserialize_order(payload: Dict[str, str], products: Dict[str, Product]) -> Order:
    items: List[CartItem] = []
    for item_payload in payload["items"]:
        product = products[item_payload["product_id"]]
        items.append(CartItem(product=product, quantity=item_payload["quantity"]))
    order = Order(user_id=payload["user_id"], items=items)
    order.id = payload["id"]
    order.status = OrderStatus(payload["status"])
    order.payment_reference = payload.get("payment_reference")
    order.created_at = _dt_from_str(payload["created_at"])
    order.updated_at = _dt_from_str(payload["updated_at"])
    return order


def _serialize_user(user: User) -> Dict[str, str]:
    payload = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "_password_hash": user._password_hash,
        "active": user.active,
        "role": getattr(user, "role", "customer"),
    }
    if hasattr(user, "shipping_address"):
        payload["shipping_address"] = getattr(user, "shipping_address")
    if hasattr(user, "failed_attempts"):
        payload["failed_attempts"] = getattr(user, "failed_attempts")
    if hasattr(user, "locked_until") and getattr(user, "locked_until") is not None:
        payload["locked_until"] = _dt_to_str(getattr(user, "locked_until"))
    return payload


def _deserialize_user(payload: Dict[str, str], user_cls: Type[User]) -> User:
    kwargs = {
        "username": payload["username"],
        "full_name": payload["full_name"],
        "password": "placeholder",
    }
    user = user_cls.from_plain_password(**kwargs)  # type: ignore[arg-type]
    user.id = payload["id"]
    user._password_hash = payload["_password_hash"]
    user.active = payload.get("active", True)
    if hasattr(user, "shipping_address"):
        setattr(user, "shipping_address", payload.get("shipping_address", ""))
    if "failed_attempts" in payload:
        setattr(user, "failed_attempts", payload["failed_attempts"])
    if "locked_until" in payload and payload["locked_until"]:
        setattr(user, "locked_until", _dt_from_str(payload["locked_until"]))
    return user


class PlatformStorage:
    """Thread-safe JSON persistence for platform state."""

    def __init__(self, path: str = "data/platform_state.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        if not self.path.exists():
            self._write(
                {
                    "users": {},
                    "categories": {},
                    "products": {},
                    "orders": {},
                }
            )

    def _read(self) -> Dict[str, Dict]:
        with self._lock:
            with self.path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

    def _write(self, payload: Dict[str, Dict]) -> None:
        with self._lock:
            temp_path = self.path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            temp_path.replace(self.path)

    def load_catalog(self) -> Tuple[Dict[str, Category], Dict[str, Product]]:
        snapshot = self._read()
        categories = {
            cid: _deserialize_category(data) for cid, data in snapshot.get("categories", {}).items()
        }
        products = {
            pid: _deserialize_product(data) for pid, data in snapshot.get("products", {}).items()
        }
        return categories, products

    def load_orders(self, products: Dict[str, Product]) -> Dict[str, Order]:
        snapshot = self._read()
        orders = {
            oid: _deserialize_order(data, products) for oid, data in snapshot.get("orders", {}).items()
        }
        return orders

    def load_users(self) -> Dict[str, Dict]:
        snapshot = self._read()
        return snapshot.get("users", {})

    def persist_catalog(self, categories: Dict[str, Category], products: Dict[str, Product]) -> None:
        snapshot = self._read()
        snapshot["categories"] = {cid: _serialize_category(cat) for cid, cat in categories.items()}
        snapshot["products"] = {pid: _serialize_product(prod) for pid, prod in products.items()}
        self._write(snapshot)

    def persist_orders(self, orders: Dict[str, Order]) -> None:
        snapshot = self._read()
        snapshot["orders"] = {oid: _serialize_order(order) for oid, order in orders.items()}
        self._write(snapshot)

    def persist_users(self, users: Dict[str, Dict]) -> None:
        snapshot = self._read()
        snapshot["users"] = users
        self._write(snapshot)

    def persist_user_objects(self, users: Dict[str, User]) -> None:
        serialized = {username: _serialize_user(user) for username, user in users.items()}
        self.persist_users(serialized)

    def load_user_objects(self, resolver: Callable[[Dict[str, str]], Type[User]]) -> Dict[str, User]:
        raw = self.load_users()
        hydrated: Dict[str, User] = {}
        for username, payload in raw.items():
            user_cls = resolver(payload)
            hydrated[username] = _deserialize_user(payload, user_cls)
        return hydrated


