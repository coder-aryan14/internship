# Contact Management System

contacts = {}

def add_contact(name, phone):
    contacts[name] = phone
    print(f"✅ Contact {name} added successfully!")

def search_contact(name):
    if name in contacts:
        print(f"📞 {name}: {contacts[name]}")
    else:
        print("❌ Contact not found.")

def display_contacts():
    if not contacts:
        print("No contacts to show.")
    else:
        print("\n--- Contact List ---")
        for name, phone in contacts.items():
            print(f"{name}: {phone}")

while True:
    print("\n1. Add Contact")
    print("2. Search Contact")
    print("3. Display All Contacts")
    print("4. Exit")
    
    choice = input("Enter your choice: ")

    if choice == "1":
        name = input("Enter name: ")
        phone = input("Enter phone number: ")
        add_contact(name, phone)

    elif choice == "2":
        name = input("Enter name to search: ")
        search_contact(name)

    elif choice == "3":
        display_contacts()

    elif choice == "4":
        print("Goodbye!")
        break

    else:
        print("Invalid choice! Try again.")
