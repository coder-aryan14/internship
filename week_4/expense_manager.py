import csv
from datetime import datetime

FILE = "data/expenses.csv"

def add_expense():
    amount = input("Enter amount: ")
    category = input("Enter category: ")
    note = input("Enter note: ")
    date = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([date, amount, category, note])
        print("Expense added successfully!")
    except Exception as e:
        print("Error writing to file:", e)

def view_expenses():
    try:
        with open(FILE, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)
    except FileNotFoundError:
        print("No expenses found yet.")
