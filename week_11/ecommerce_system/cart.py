"""Shopping cart implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Iterable

from .models import CartItem, Product


@dataclass
class ShoppingCart:
    user_id: str
    _items: Dict[str, CartItem] = field(default_factory=dict)

    def add_item(self, product: Product, quantity: int = 1) -> None:
        if product.id in self._items:
            self._items[product.id].increment(quantity)
        else:
            self._items[product.id] = CartItem(product=product, quantity=quantity)

    def remove_item(self, product_id: str, quantity: int = 1) -> None:
        if product_id not in self._items:
            return
        item = self._items[product_id]
        item.quantity -= quantity
        if item.quantity <= 0:
            del self._items[product_id]

    def clear(self) -> None:
        self._items.clear()

    def items(self) -> Iterable[CartItem]:
        return self._items.values()

    @property
    def total(self) -> Decimal:
        return sum(item.line_total for item in self._items.values())

    def is_empty(self) -> bool:
        return not self._items


