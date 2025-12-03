"""Domain models backing the e-commerce platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
import uuid
from typing import Dict, Iterable, List, Optional


class InventoryError(RuntimeError):
    """Raised when inventory operations cannot be fulfilled."""


@dataclass
class TimestampedMixin:
    """Mixin that tracks when an entity is created or updated."""

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False, repr=False)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False, repr=False)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class IdentifiableMixin:
    """Mixin that guarantees the presence of a unique identifier."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)


@dataclass
class Category(IdentifiableMixin, TimestampedMixin):
    name: str
    description: str = ""

    def __hash__(self) -> int:  # Enables category sets and dict keys
        return hash(self.id)


@dataclass
class Product(IdentifiableMixin, TimestampedMixin):
    name: str
    price: Decimal
    stock: int
    category_id: str
    description: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    def adjust_stock(self, quantity: int) -> None:
        new_stock = self.stock + quantity
        if new_stock < 0:
            raise InventoryError(
                f"Insufficient stock for {self.name}. "
                f"Requested {abs(quantity)}, available {self.stock}."
            )
        self.stock = new_stock
        self.touch()


@dataclass
class CartItem:
    product: Product
    quantity: int

    def increment(self, qty: int) -> None:
        self.quantity += qty

    @property
    def line_total(self) -> Decimal:
        return self.product.price * self.quantity


class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    SHIPPED = "shipped"


class PaymentStatus(str, Enum):
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"


@dataclass
class Order(IdentifiableMixin, TimestampedMixin):
    user_id: str
    items: List[CartItem]
    status: OrderStatus = OrderStatus.CREATED
    payment_reference: Optional[str] = None

    @property
    def subtotal(self) -> Decimal:
        return sum(item.line_total for item in self.items)

    def mark_paid(self, reference: str) -> None:
        self.status = OrderStatus.PAID
        self.payment_reference = reference
        self.touch()

    def summary(self) -> str:
        return ", ".join(f"{item.product.name} x{item.quantity}" for item in self.items)


@dataclass
class PaymentReceipt:
    order_id: str
    method: str
    amount: Decimal
    reference: str
    status: PaymentStatus
    metadata: Dict[str, str] = field(default_factory=dict)


