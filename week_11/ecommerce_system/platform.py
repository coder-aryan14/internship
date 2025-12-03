"""Core orchestration layer tying domain, users, cart, and payments together."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

from .cart import ShoppingCart
from .models import Category, Order, OrderStatus, PaymentStatus, Product
from .payments import (
    PaymentProcessor,
    CardPayment,
    BankTransferPayment,
    CashOnDeliveryPayment,
    UpiPayment,
)
from .storage import PlatformStorage
from .users import AdminUser, AuthService, AuthorizationError, CustomerUser, User


class NotFoundError(RuntimeError):
    pass


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise AuthorizationError("Administrator privileges required.")


@dataclass
class ECommercePlatform:
    auth_service: AuthService
    payment_processor: PaymentProcessor
    storage: Optional[PlatformStorage] = None
    categories: Dict[str, Category] = field(default_factory=dict)
    products: Dict[str, Product] = field(default_factory=dict)
    carts: Dict[str, ShoppingCart] = field(default_factory=dict)
    orders: Dict[str, Order] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.storage:
            categories, products = self.storage.load_catalog()
            self.categories.update(categories)
            self.products.update(products)
            self.orders.update(self.storage.load_orders(self.products))

    # ---- Category management ----
    def create_category(self, name: str, description: str, acting_user: User) -> Category:
        _require_admin(acting_user)
        category = Category(name=name, description=description)
        self.categories[category.id] = category
        self._persist_catalog()
        return category

    def delete_category(self, category_id: str, acting_user: User) -> None:
        _require_admin(acting_user)
        if category_id in self.categories:
            del self.categories[category_id]
        for product in list(self.products.values()):
            if product.category_id == category_id:
                del self.products[product.id]
        self._persist_catalog()

    # ---- Product management ----
    def add_product(
        self,
        name: str,
        price: Decimal,
        stock: int,
        category_id: str,
        acting_user: User,
        description: str = "",
    ) -> Product:
        _require_admin(acting_user)
        if category_id not in self.categories:
            raise NotFoundError("Category not found.")
        product = Product(
            name=name,
            price=price,
            stock=stock,
            category_id=category_id,
            description=description,
        )
        self.products[product.id] = product
        self._persist_catalog()
        return product

    def remove_product(self, product_id: str, acting_user: User) -> None:
        _require_admin(acting_user)
        self.products.pop(product_id, None)
        self._persist_catalog()

    # ---- Cart operations ----
    def get_cart(self, user_id: str) -> ShoppingCart:
        if user_id not in self.carts:
            self.carts[user_id] = ShoppingCart(user_id=user_id)
        return self.carts[user_id]

    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> None:
        product = self.products.get(product_id)
        if not product:
            raise NotFoundError("Product not found.")
        if product.stock < quantity:
            raise ValueError("Insufficient stock.")
        product.adjust_stock(-quantity)
        cart = self.get_cart(user_id)
        cart.add_item(product, quantity)
        self._persist_catalog()

    def remove_from_cart(self, user_id: str, product_id: str, quantity: int = 1) -> None:
        cart = self.get_cart(user_id)
        cart.remove_item(product_id, quantity)
        product = self.products.get(product_id)
        if product:
            product.adjust_stock(quantity)
            self._persist_catalog()

    # ---- Checkout ----
    def checkout(self, user_id: str, payment_method: str) -> Order:
        cart = self.get_cart(user_id)
        if cart.is_empty():
            raise ValueError("Cart is empty.")
        order = Order(user_id=user_id, items=list(cart.items()))
        receipt = self.payment_processor.pay(payment_method, order)
        if receipt.status == PaymentStatus.SUCCESS:
            order.mark_paid(receipt.reference)
        elif receipt.status == PaymentStatus.FAILED:
            order.status = OrderStatus.FAILED
            order.payment_reference = receipt.reference
            for item in order.items:
                item.product.adjust_stock(item.quantity)
            self._persist_catalog()
        else:
            order.payment_reference = receipt.reference
        self.orders[order.id] = order
        self._persist_orders()
        cart.clear()
        return order

    def list_orders(self, acting_user: User) -> List[Order]:
        _require_admin(acting_user)
        return list(self.orders.values())

    def confirm_payment(self, reference: str, **kwargs) -> Order:
        receipt = self.payment_processor.complete(reference, **kwargs)
        order = next((o for o in self.orders.values() if o.payment_reference == reference), None)
        if not order:
            raise NotFoundError("Order for reference not found.")
        if receipt.status == PaymentStatus.SUCCESS:
            order.mark_paid(reference)
        else:
            order.status = OrderStatus.FAILED
            for item in order.items:
                item.product.adjust_stock(item.quantity)
            self._persist_catalog()
        self._persist_orders()
        return order

    def _persist_catalog(self) -> None:
        if self.storage:
            self.storage.persist_catalog(self.categories, self.products)

    def _persist_orders(self) -> None:
        if self.storage:
            self.storage.persist_orders(self.orders)


def bootstrap_platform(storage: Optional[PlatformStorage] = None) -> ECommercePlatform:
    """Helper that wires a working platform with defaults for demos/tests."""
    storage = storage or PlatformStorage()
    auth = AuthService(storage=storage)
    payment_processor = PaymentProcessor()
    payment_processor.register(CardPayment())
    payment_processor.register(BankTransferPayment())
    payment_processor.register(UpiPayment())
    payment_processor.register(CashOnDeliveryPayment())

    platform = ECommercePlatform(
        auth_service=auth,
        payment_processor=payment_processor,
        storage=storage,
    )

    if not auth.get_user("admin"):
        admin = AdminUser.from_plain_password("admin", "Admin User", "admin123")
        auth.register_user(admin)
    else:
        admin = auth.get_user("admin")

    if auth.get_user("alice") is None and admin:
        default_customer = CustomerUser.from_plain_password("alice", "Alice Customer", "password")
        auth.register_user(default_customer, acting_user=admin)

    return platform


