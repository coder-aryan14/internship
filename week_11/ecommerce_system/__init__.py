"""High-level entry points for the advanced e-commerce system."""

from .platform import ECommercePlatform, bootstrap_platform
from .payments import (
    PaymentProcessor,
    PaymentStrategy,
    CardPayment,
    BankTransferPayment,
    UpiPayment,
    CashOnDeliveryPayment,
)
from .storage import PlatformStorage

__all__ = [
    "ECommercePlatform",
    "bootstrap_platform",
    "PlatformStorage",
    "PaymentProcessor",
    "PaymentStrategy",
    "CardPayment",
    "BankTransferPayment",
    "UpiPayment",
    "CashOnDeliveryPayment",
]

