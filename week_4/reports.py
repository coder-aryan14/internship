import csv
from collections import defaultdict

def generate_monthly_report():
    expenses = defaultdict(float)
    try:
        with open("data/expenses.csv") as f:
            reader = csv.reader(f)
            for date, amount, category, note in reader:
                month = date[:7]
                expenses[month] += float(amount)
        for month, total in expenses.items():
            print(f"{month}: ₹{total:.2f}")
    except FileNotFoundError:
        print("No data available for report.")
