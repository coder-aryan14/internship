"""Payment strategies using the strategy pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict
import secrets
import uuid

from .models import Order, PaymentReceipt, PaymentStatus


class PaymentError(RuntimeError):
    pass


class PaymentStrategy(ABC):
    name: str
    requires_confirmation: bool = False

    @abstractmethod
    def pay(self, order: Order) -> PaymentReceipt:
        """Perform payment and return a receipt."""

    def complete(self, receipt: PaymentReceipt, **kwargs) -> PaymentReceipt:
        raise PaymentError(f"{self.name} does not support manual confirmation.")


@dataclass
class CardPayment(PaymentStrategy):
    name: str = "card"
    processor: str = "VISA"
    requires_confirmation: bool = True

    def pay(self, order: Order) -> PaymentReceipt:
        reference = f"{self.processor}-{uuid.uuid4().hex[:8]}"
        otp = f"{secrets.randbelow(900000) + 100000}"
        metadata = {"processor": self.processor, "challenge": "otp", "otp": otp}
        return PaymentReceipt(
            order_id=order.id,
            method=self.name,
            amount=order.subtotal,
            reference=reference,
            status=PaymentStatus.PENDING,
            metadata=metadata,
        )

    def complete(self, receipt: PaymentReceipt, **kwargs) -> PaymentReceipt:
        otp = kwargs.get("otp")
        if otp != receipt.metadata.get("otp"):
            receipt.status = PaymentStatus.FAILED
            return receipt
        receipt.status = PaymentStatus.SUCCESS
        receipt.metadata["verified_at"] = "otp"
        receipt.metadata.pop("otp", None)
        return receipt


@dataclass
class BankTransferPayment(PaymentStrategy):
    name: str = "bank_transfer"
    bank_name: str = "Demo Bank"
    requires_confirmation: bool = True

    def pay(self, order: Order) -> PaymentReceipt:
        reference = f"NEFT-{uuid.uuid4().hex[:6]}"
        return PaymentReceipt(
            order_id=order.id,
            method=self.name,
            amount=order.subtotal,
            reference=reference,
            status=PaymentStatus.PENDING,
            metadata={"bank": self.bank_name},
        )

    def complete(self, receipt: PaymentReceipt, **kwargs) -> PaymentReceipt:
        receipt.status = PaymentStatus.SUCCESS
        receipt.metadata["bank_ack"] = kwargs.get("transaction_id", "manual")
        return receipt


@dataclass
class UpiPayment(PaymentStrategy):
    name: str = "upi"
    handle: str = "merchant@upi"

    def pay(self, order: Order) -> PaymentReceipt:
        reference = f"UPI-{uuid.uuid4().hex[:10]}"
        return PaymentReceipt(
            order_id=order.id,
            method=self.name,
            amount=order.subtotal,
            reference=reference,
            status=PaymentStatus.SUCCESS,
            metadata={"handle": self.handle},
        )


@dataclass
class CashOnDeliveryPayment(PaymentStrategy):
    name: str = "cod"
    requires_confirmation: bool = True

    def pay(self, order: Order) -> PaymentReceipt:
        reference = f"COD-{uuid.uuid4().hex[:5]}"
        return PaymentReceipt(
            order_id=order.id,
            method=self.name,
            amount=order.subtotal,
            reference=reference,
            status=PaymentStatus.PENDING,
            metadata={"instructions": "Collect cash on delivery"},
        )

    def complete(self, receipt: PaymentReceipt, **kwargs) -> PaymentReceipt:
        delivered = kwargs.get("delivered", False)
        receipt.status = PaymentStatus.SUCCESS if delivered else PaymentStatus.FAILED
        return receipt


class PaymentProcessor:
    def __init__(self) -> None:
        self._strategies: Dict[str, PaymentStrategy] = {}
        self._transactions: Dict[str, PaymentReceipt] = {}

    def register(self, strategy: PaymentStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def remove(self, name: str) -> None:
        self._strategies.pop(name, None)

    def list_methods(self) -> Dict[str, PaymentStrategy]:
        return dict(self._strategies)

    def pay(self, method: str, order: Order) -> PaymentReceipt:
        strategy = self._strategies.get(method)
        if not strategy:
            raise PaymentError(f"Payment method '{method}' is not available.")
        receipt = strategy.pay(order)
        self._transactions[receipt.reference] = receipt
        return receipt

    def complete(self, reference: str, **kwargs) -> PaymentReceipt:
        receipt = self._transactions.get(reference)
        if not receipt:
            raise PaymentError("Payment reference not found.")
        strategy = self._strategies.get(receipt.method)
        if not strategy or not strategy.requires_confirmation:
            raise PaymentError(f"Payment method '{receipt.method}' cannot be confirmed manually.")
        updated = strategy.complete(receipt, **kwargs)
        self._transactions[reference] = updated
        return updated

    def get_receipt(self, reference: str) -> PaymentReceipt:
        receipt = self._transactions.get(reference)
        if not receipt:
            raise PaymentError("Payment reference not found.")
        return receipt
