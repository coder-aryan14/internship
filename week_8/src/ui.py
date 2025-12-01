import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from .database import init_db
from .services import InventoryService, SalesService, ReportingService


class InventoryApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Premium Inventory Management System")
        self.geometry("1100x650")
        self.minsize(1000, 600)

        # Services
        init_db()
        self.inventory_service = InventoryService()
        self.sales_service = SalesService()
        self.reporting_service = ReportingService()

        self._configure_style()
        self._build_layout()
        self._load_products()
        self._load_sales()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#f4f5f7")
        style.configure("Header.TFrame", background="#1f2933")
        style.configure("Header.TLabel", background="#1f2933", foreground="white", font=("Segoe UI", 16, "bold"))
        style.configure("Nav.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Card.TFrame", background="white", relief="raised", borderwidth=1)
        style.configure("TButton", padding=6)

    def _build_layout(self) -> None:
        # Header
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(header, text="Inventory Management Dashboard", style="Header.TLabel").pack(
            side=tk.LEFT, padx=20, pady=10
        )

        # Navigation
        nav = ttk.Frame(header, style="Header.TFrame")
        nav.pack(side=tk.RIGHT, padx=10)

        self.section_var = tk.StringVar(value="products")
        ttk.Button(nav, text="Products", style="Nav.TButton", command=lambda: self._show_section("products")).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(nav, text="Sales", style="Nav.TButton", command=lambda: self._show_section("sales")).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(nav, text="Reports", style="Nav.TButton", command=lambda: self._show_section("reports")).pack(
            side=tk.LEFT, padx=5
        )

        # Main content
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        self.frames = {}
        for name in ("products", "sales", "reports"):
            frame = ttk.Frame(main)
            frame.pack(fill=tk.BOTH, expand=True)
            self.frames[name] = frame

        self._build_products_section(self.frames["products"])
        self._build_sales_section(self.frames["sales"])
        self._build_reports_section(self.frames["reports"])
        self._show_section("products")

    # ---------- Products Section ----------
    def _build_products_section(self, container: ttk.Frame) -> None:
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # Product list
        list_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(list_card, text="Products", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        columns = ("id", "sku", "name", "category", "cost_price", "selling_price", "quantity")
        self.product_tree = ttk.Treeview(list_card, columns=columns, show="headings", height=15)
        for col in columns:
            self.product_tree.heading(col, text=col.replace("_", " ").title())
            width = 60 if col == "id" else 100
            self.product_tree.column(col, width=width, anchor="center")
        self.product_tree.pack(fill=tk.BOTH, expand=True)
        self.product_tree.bind("<<TreeviewSelect>>", self._on_product_select)

        # Form
        form_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        form_card.grid(row=0, column=1, sticky="nsew")

        ttk.Label(form_card, text="Product Details", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.selected_product_id: Optional[int] = None

        labels = ["SKU", "Name", "Category", "Cost Price", "Selling Price", "Initial Stock"]
        self.product_entries = {}
        for idx, label in enumerate(labels, start=1):
            ttk.Label(form_card, text=label + ":").grid(row=idx, column=0, sticky="e", pady=3, padx=(0, 5))
            entry = ttk.Entry(form_card, width=22)
            entry.grid(row=idx, column=1, sticky="w", pady=3)
            self.product_entries[label.lower().replace(" ", "_")] = entry

        btn_frame = ttk.Frame(form_card)
        btn_frame.grid(row=len(labels) + 1, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="New", command=self._clear_product_form).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Save", command=self._save_product).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Delete", command=self._delete_product).pack(side=tk.LEFT, padx=3)

    def _load_products(self) -> None:
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        for p in self.inventory_service.list_products():
            self.product_tree.insert(
                "", tk.END, values=(p["id"], p["sku"], p["name"], p["category"], p["cost_price"], p["selling_price"], p["quantity"])
            )

    def _on_product_select(self, event) -> None:
        selected = self.product_tree.selection()
        if not selected:
            return
        values = self.product_tree.item(selected[0], "values")
        self.selected_product_id = int(values[0])
        self.product_entries["sku"].delete(0, tk.END)
        self.product_entries["sku"].insert(0, values[1])
        self.product_entries["name"].delete(0, tk.END)
        self.product_entries["name"].insert(0, values[2])
        self.product_entries["category"].delete(0, tk.END)
        self.product_entries["category"].insert(0, values[3])
        self.product_entries["cost_price"].delete(0, tk.END)
        self.product_entries["cost_price"].insert(0, values[4])
        self.product_entries["selling_price"].delete(0, tk.END)
        self.product_entries["selling_price"].insert(0, values[5])
        self.product_entries["initial_stock"].delete(0, tk.END)

    def _clear_product_form(self) -> None:
        self.selected_product_id = None
        for entry in self.product_entries.values():
            entry.delete(0, tk.END)

    def _save_product(self) -> None:
        try:
            sku = self.product_entries["sku"].get().strip()
            name = self.product_entries["name"].get().strip()
            category = self.product_entries["category"].get().strip()
            cost_price = float(self.product_entries["cost_price"].get() or 0)
            selling_price = float(self.product_entries["selling_price"].get() or 0)
            initial_stock = int(self.product_entries["initial_stock"].get() or 0)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please check numeric fields.")
            return

        if not sku or not name:
            messagebox.showerror("Missing Data", "SKU and Name are required.")
            return

        try:
            if self.selected_product_id:
                self.inventory_service.update_product(
                    self.selected_product_id, sku, name, category, cost_price, selling_price
                )
            else:
                self.inventory_service.create_product(
                    sku, name, category, cost_price, selling_price, initial_stock
                )
            self._load_products()
            # Also refresh sales section combobox so new products can be selected for sales
            self._load_sales()
            self._clear_product_form()
            messagebox.showinfo("Success", "Product saved successfully.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def _delete_product(self) -> None:
        if not self.selected_product_id:
            messagebox.showwarning("No Selection", "Please select a product to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this product?"):
            return
        try:
            self.inventory_service.delete_product(self.selected_product_id)
            self._load_products()
            self._clear_product_form()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    # ---------- Sales Section ----------
    def _build_sales_section(self, container: ttk.Frame) -> None:
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # Sales history
        sales_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        sales_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(sales_card, text="Sales History", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        columns = ("id", "sku", "name", "quantity", "unit_price", "total_price", "sold_at")
        self.sales_tree = ttk.Treeview(sales_card, columns=columns, show="headings", height=15)
        for col in columns:
            self.sales_tree.heading(col, text=col.replace("_", " ").title())
            self.sales_tree.column(col, width=90, anchor="center")
        self.sales_tree.pack(fill=tk.BOTH, expand=True)

        # New sale form
        form_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        form_card.grid(row=0, column=1, sticky="nsew")

        ttk.Label(form_card, text="Record Sale", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        ttk.Label(form_card, text="Product:").grid(row=1, column=0, sticky="e", pady=3, padx=(0, 5))
        self.sale_product_var = tk.StringVar()
        self.sale_product_combo = ttk.Combobox(form_card, textvariable=self.sale_product_var, state="readonly", width=25)
        self.sale_product_combo.grid(row=1, column=1, sticky="w", pady=3)

        ttk.Label(form_card, text="Quantity:").grid(row=2, column=0, sticky="e", pady=3, padx=(0, 5))
        self.sale_qty_entry = ttk.Entry(form_card, width=10)
        self.sale_qty_entry.grid(row=2, column=1, sticky="w", pady=3)

        ttk.Label(form_card, text="Unit Price:").grid(row=3, column=0, sticky="e", pady=3, padx=(0, 5))
        self.sale_price_entry = ttk.Entry(form_card, width=10)
        self.sale_price_entry.grid(row=3, column=1, sticky="w", pady=3)

        ttk.Button(form_card, text="Record Sale", command=self._record_sale).grid(
            row=4, column=0, columnspan=2, pady=10
        )

    def _load_sales(self) -> None:
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)
        for s in self.sales_service.sales_history():
            self.sales_tree.insert(
                "", tk.END, values=(s["id"], s["sku"], s["name"], s["quantity"], s["unit_price"], s["total_price"], s["sold_at"])
            )

        # Refresh product list for combo
        products = self.inventory_service.list_products()
        display = [f'{p["id"]} - {p["name"]} (Stock: {p["quantity"]})' for p in products]
        self.sale_product_combo["values"] = display
        if display:
            self.sale_product_combo.current(0)

    def _record_sale(self) -> None:
        product_text = self.sale_product_var.get()
        if not product_text:
            messagebox.showwarning("Missing Data", "Please select a product.")
            return
        try:
            product_id = int(product_text.split(" - ")[0])
            quantity = int(self.sale_qty_entry.get())
            unit_price = float(self.sale_price_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please check quantity and unit price.")
            return

        try:
            self.sales_service.record_sale(product_id, quantity, unit_price)
            self._load_sales()
            self._load_products()
            self.sale_qty_entry.delete(0, tk.END)
            self.sale_price_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Sale recorded successfully.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    # ---------- Reports Section ----------
    def _build_reports_section(self, container: ttk.Frame) -> None:
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        # Inventory report
        inv_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        inv_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(inv_card, text="Inventory Report", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        columns = ("sku", "name", "category", "selling_price", "quantity")
        self.report_inv_tree = ttk.Treeview(inv_card, columns=columns, show="headings", height=15)
        for col in columns:
            self.report_inv_tree.heading(col, text=col.replace("_", " ").title())
            self.report_inv_tree.column(col, width=100, anchor="center")
        self.report_inv_tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(inv_card, text="Refresh", command=self._refresh_reports).pack(pady=5, anchor="e")

        # Low stock report
        low_card = ttk.Frame(container, style="Card.TFrame", padding=10)
        low_card.grid(row=0, column=1, sticky="nsew")

        header_frame = ttk.Frame(low_card)
        header_frame.pack(fill=tk.X)

        ttk.Label(header_frame, text="Low Stock (<= threshold)", font=("Segoe UI", 12, "bold")).pack(
            side=tk.LEFT, pady=(0, 8)
        )

        self.low_threshold_var = tk.StringVar(value="5")
        ttk.Entry(header_frame, textvariable=self.low_threshold_var, width=5).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Label(header_frame, text="Threshold:").pack(side=tk.RIGHT)

        columns = ("sku", "name", "quantity")
        self.report_low_tree = ttk.Treeview(low_card, columns=columns, show="headings", height=15)
        for col in columns:
            self.report_low_tree.heading(col, text=col.replace("_", " ").title())
            self.report_low_tree.column(col, width=120, anchor="center")
        self.report_low_tree.pack(fill=tk.BOTH, expand=True)

        ttk.Button(low_card, text="Refresh", command=self._refresh_reports).pack(pady=5, anchor="e")

        self._refresh_reports()

    def _refresh_reports(self) -> None:
        for item in self.report_inv_tree.get_children():
            self.report_inv_tree.delete(item)
        for p in self.reporting_service.inventory_report():
            self.report_inv_tree.insert(
                "", tk.END, values=(p["sku"], p["name"], p["category"], p["selling_price"], p["quantity"])
            )

        for item in self.report_low_tree.get_children():
            self.report_low_tree.delete(item)

        try:
            threshold = int(self.low_threshold_var.get())
        except ValueError:
            threshold = 5

        for p in self.reporting_service.low_stock_report(threshold):
            self.report_low_tree.insert("", tk.END, values=(p["sku"], p["name"], p["quantity"]))

    # ---------- Navigation ----------
    def _show_section(self, name: str) -> None:
        self.section_var.set(name)
        # Refresh data when switching sections to keep UI in sync
        if name == "products":
            self._load_products()
        elif name == "sales":
            self._load_sales()
        elif name == "reports":
            self._refresh_reports()

        for key, frame in self.frames.items():
            if key == name:
                frame.lift()
            else:
                frame.lower()


def main() -> None:
    app = InventoryApp()
    app.mainloop()


if __name__ == "__main__":
    main()


