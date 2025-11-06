from expense_manager import add_expense, view_expenses
from reports import generate_monthly_report

while True:
    print("\n1. Add Expense\n2. View Expenses\n3. Monthly Report\n4. Exit")
    choice = input("Choose an option: ")

    if choice == "1":
        add_expense()
    elif choice == "2":
        view_expenses()
    elif choice == "3":
        generate_monthly_report()
    elif choice == "4":
        break
