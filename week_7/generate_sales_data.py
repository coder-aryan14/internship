"""
Sales Data Generator
Creates a realistic sales dataset for analysis purposes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Product catalog
products = [
    "Laptop Pro 15", "Wireless Mouse", "Keyboard Mechanical", "USB-C Cable",
    "Monitor 27in", "Webcam HD", "Headphones Wireless", "USB Hub",
    "Laptop Stand", "Desk Lamp", "Mouse Pad", "USB Flash Drive 64GB",
    "Wireless Charger", "Laptop Bag", "Screen Cleaner", "HDMI Cable",
    "Keyboard Wrist Rest", "USB Flash Drive 128GB", "Laptop Cooling Pad",
    "Desk Organizer", "Monitor Stand", "Bluetooth Speaker", "Power Bank",
    "USB-C Adapter", "Laptop Sleeve", "Desk Mat", "Cable Management",
    "USB Microphone", "Ring Light", "External SSD 1TB"
]

# Categories
categories = {
    "Laptop Pro 15": "Computers",
    "Wireless Mouse": "Accessories",
    "Keyboard Mechanical": "Accessories",
    "USB-C Cable": "Cables",
    "Monitor 27in": "Displays",
    "Webcam HD": "Accessories",
    "Headphones Wireless": "Audio",
    "USB Hub": "Accessories",
    "Laptop Stand": "Accessories",
    "Desk Lamp": "Furniture",
    "Mouse Pad": "Accessories",
    "USB Flash Drive 64GB": "Storage",
    "Wireless Charger": "Accessories",
    "Laptop Bag": "Accessories",
    "Screen Cleaner": "Accessories",
    "HDMI Cable": "Cables",
    "Keyboard Wrist Rest": "Accessories",
    "USB Flash Drive 128GB": "Storage",
    "Laptop Cooling Pad": "Accessories",
    "Desk Organizer": "Furniture",
    "Monitor Stand": "Accessories",
    "Bluetooth Speaker": "Audio",
    "Power Bank": "Accessories",
    "USB-C Adapter": "Accessories",
    "Laptop Sleeve": "Accessories",
    "Desk Mat": "Accessories",
    "Cable Management": "Accessories",
    "USB Microphone": "Audio",
    "Ring Light": "Accessories",
    "External SSD 1TB": "Storage"
}

# Price ranges (base prices)
price_ranges = {
    "Laptop Pro 15": (1200, 1800),
    "Wireless Mouse": (15, 45),
    "Keyboard Mechanical": (80, 200),
    "USB-C Cable": (10, 30),
    "Monitor 27in": (200, 400),
    "Webcam HD": (50, 150),
    "Headphones Wireless": (60, 300),
    "USB Hub": (20, 60),
    "Laptop Stand": (30, 100),
    "Desk Lamp": (25, 80),
    "Mouse Pad": (5, 25),
    "USB Flash Drive 64GB": (10, 25),
    "Wireless Charger": (15, 50),
    "Laptop Bag": (40, 120),
    "Screen Cleaner": (5, 15),
    "HDMI Cable": (10, 40),
    "Keyboard Wrist Rest": (15, 40),
    "USB Flash Drive 128GB": (15, 40),
    "Laptop Cooling Pad": (20, 60),
    "Desk Organizer": (15, 50),
    "Monitor Stand": (30, 100),
    "Bluetooth Speaker": (30, 150),
    "Power Bank": (20, 80),
    "USB-C Adapter": (15, 50),
    "Laptop Sleeve": (20, 60),
    "Desk Mat": (15, 50),
    "Cable Management": (10, 30),
    "USB Microphone": (50, 200),
    "Ring Light": (25, 100),
    "External SSD 1TB": (80, 150)
}

# Generate sales data
num_records = 5000
start_date = datetime(2023, 1, 1)
end_date = datetime(2024, 12, 31)

sales_data = []

for _ in range(num_records):
    # Random date between start and end
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    sale_date = start_date + timedelta(days=random_days)
    
    # Random product
    product = random.choice(products)
    
    # Price with some variation
    base_min, base_max = price_ranges[product]
    price = round(random.uniform(base_min, base_max), 2)
    
    # Quantity (more likely to be 1, sometimes 2-5)
    quantity = np.random.choice([1, 2, 3, 4, 5], p=[0.7, 0.15, 0.08, 0.05, 0.02])
    
    # Revenue
    revenue = price * quantity
    
    # Customer ID
    customer_id = f"CUST{random.randint(1000, 9999)}"
    
    # Region
    region = random.choice(["North", "South", "East", "West", "Central"])
    
    sales_data.append({
        "Sale_ID": f"SALE{10000 + _}",
        "Date": sale_date.strftime("%Y-%m-%d"),
        "Product": product,
        "Category": categories[product],
        "Quantity": quantity,
        "Unit_Price": price,
        "Revenue": revenue,
        "Customer_ID": customer_id,
        "Region": region
    })

# Create DataFrame
df = pd.DataFrame(sales_data)

# Save to CSV
df.to_csv("sales_data.csv", index=False)
print(f"Sales data generated successfully!")
print(f"Total records: {len(df)}")
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Total revenue: ${df['Revenue'].sum():,.2f}")
print(f"\nFirst few records:")
print(df.head())
