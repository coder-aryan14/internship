from typing import List, Dict, Any

from .repository import ProductRepository, StockRepository, SalesRepository


class InventoryService:
    def list_products(self) -> List[Dict[str, Any]]:
        return ProductRepository.list_products()

    def create_product(
        self,
        sku: str,
        name: str,
        category: str,
        cost_price: float,
        selling_price: float,
        initial_stock: int = 0,
    ) -> None:
        product_id = ProductRepository.create_product(sku, name, category, cost_price, selling_price)
        if initial_stock:
            StockRepository.set_stock(product_id, initial_stock)

    def update_product(
        self,
        product_id: int,
        sku: str,
        name: str,
        category: str,
        cost_price: float,
        selling_price: float,
    ) -> None:
        ProductRepository.update_product(product_id, sku, name, category, cost_price, selling_price)

    def delete_product(self, product_id: int) -> None:
        ProductRepository.delete_product(product_id)

    def adjust_stock(self, product_id: int, delta: int) -> None:
        StockRepository.adjust_stock(product_id, delta)


class SalesService:
    def record_sale(self, product_id: int, quantity: int, unit_price: float) -> None:
        SalesRepository.record_sale(product_id, quantity, unit_price)

    def sales_history(self) -> List[Dict[str, Any]]:
        return SalesRepository.sales_summary()


class ReportingService:
    def inventory_report(self) -> List[Dict[str, Any]]:
        return ProductRepository.list_products()

    def low_stock_report(self, threshold: int = 5) -> List[Dict[str, Any]]:
        products = ProductRepository.list_products()
        return [p for p in products if p.get("quantity", 0) <= threshold]


