import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from ecommerce_system.platform import bootstrap_platform
from ecommerce_system.storage import PlatformStorage
from ecommerce_system.users import AdminUser, CustomerUser, AuthenticationError
from ecommerce_system.models import OrderStatus, PaymentStatus


def _make_platform(tmp_path: Path):
    storage = PlatformStorage(path=str(tmp_path / "state.json"))
    return bootstrap_platform(storage=storage)


def test_upi_checkout_succeeds(tmp_path):
    platform = _make_platform(tmp_path)
    admin = platform.auth_service.get_user("admin")
    customer = platform.auth_service.get_user("alice")
    category = platform.create_category("Books", "All books", admin)
    product = platform.add_product("Novel", Decimal("15.00"), 5, category.id, admin)

    platform.add_to_cart(customer.id, product.id, 1)
    order = platform.checkout(customer.id, "upi")

    assert order.status == OrderStatus.PAID
    assert order.subtotal == Decimal("15.00")
    assert product.stock == 4


def test_card_checkout_requires_confirmation(tmp_path):
    platform = _make_platform(tmp_path)
    admin = platform.auth_service.get_user("admin")
    customer = platform.auth_service.get_user("alice")
    category = platform.create_category("Electronics", "Gadgets", admin)
    product = platform.add_product("Tablet", Decimal("199.99"), 3, category.id, admin)

    platform.add_to_cart(customer.id, product.id, 1)
    order = platform.checkout(customer.id, "card")
    assert order.status == OrderStatus.CREATED
    receipt = platform.payment_processor.get_receipt(order.payment_reference)
    otp = receipt.metadata["otp"]

    platform.confirm_payment(order.payment_reference, otp=otp)
    assert order.status == OrderStatus.PAID
    assert product.stock == 2


def test_failed_confirm_restocks_inventory(tmp_path):
    platform = _make_platform(tmp_path)
    admin = platform.auth_service.get_user("admin")
    customer = platform.auth_service.get_user("alice")
    category = platform.create_category("Home", "Home goods", admin)
    product = platform.add_product("Lamp", Decimal("30.00"), 2, category.id, admin)

    platform.add_to_cart(customer.id, product.id, 1)
    order = platform.checkout(customer.id, "card")
    assert product.stock == 1

    platform.confirm_payment(order.payment_reference, otp="000000")
    assert order.status == OrderStatus.FAILED
    assert product.stock == 2


def test_account_lockout(tmp_path):
    platform = _make_platform(tmp_path)
    auth = platform.auth_service

    for _ in range(auth.MAX_FAILED_ATTEMPTS):
        with pytest.raises(AuthenticationError):
            auth.login("alice", "wrong")
    with pytest.raises(AuthenticationError):
        auth.login("alice", "password")

