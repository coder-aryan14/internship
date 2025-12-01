from typing import List, Optional, Dict, Any

from .database import get_connection


class ProductRepository:
    @staticmethod
    def create_product(sku: str, name: str, category: str, cost_price: float, selling_price: float) -> int:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO products (sku, name, category, cost_price, selling_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sku, name, category, cost_price, selling_price),
        )
        product_id = cur.lastrowid

        # Initialize stock
        cur.execute(
            "INSERT INTO stock (product_id, quantity) VALUES (?, 0)",
            (product_id,),
        )

        conn.commit()
        conn.close()
        return product_id

    @staticmethod
    def update_product(
        product_id: int,
        sku: str,
        name: str,
        category: str,
        cost_price: float,
        selling_price: float,
    ) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE products
            SET sku = ?, name = ?, category = ?, cost_price = ?, selling_price = ?
            WHERE id = ?
            """,
            (sku, name, category, cost_price, selling_price, product_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete_product(product_id: int) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def list_products() -> List[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.sku, p.name, p.category, p.cost_price, p.selling_price,
                   IFNULL(s.quantity, 0) as quantity
            FROM products p
            LEFT JOIN stock s ON p.id = s.product_id
            ORDER BY p.name
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_product(product_id: int) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.sku, p.name, p.category, p.cost_price, p.selling_price,
                   IFNULL(s.quantity, 0) as quantity
            FROM products p
            LEFT JOIN stock s ON p.id = s.product_id
            WHERE p.id = ?
            """,
            (product_id,),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None


class StockRepository:
    @staticmethod
    def adjust_stock(product_id: int, delta: int) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE stock
            SET quantity = quantity + ?, last_updated = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (delta, product_id),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def set_stock(product_id: int, quantity: int) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE stock
            SET quantity = ?, last_updated = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (quantity, product_id),
        )
        conn.commit()
        conn.close()


class SalesRepository:
    @staticmethod
    def record_sale(product_id: int, quantity: int, unit_price: float) -> int:
        total_price = quantity * unit_price
        conn = get_connection()
        cur = conn.cursor()

        # Record sale
        cur.execute(
            """
            INSERT INTO sales (product_id, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, quantity, unit_price, total_price),
        )

        # Deduct stock
        cur.execute(
            """
            UPDATE stock
            SET quantity = quantity - ?, last_updated = CURRENT_TIMESTAMP
            WHERE product_id = ?
            """,
            (quantity, product_id),
        )

        sale_id = cur.lastrowid
        conn.commit()
        conn.close()
        return sale_id

    @staticmethod
    def sales_summary() -> List[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.id, p.sku, p.name, s.quantity, s.unit_price, s.total_price, s.sold_at
            FROM sales s
            JOIN products p ON s.product_id = p.id
            ORDER BY s.sold_at DESC
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows


