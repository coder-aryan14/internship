# ------------------------------------------------------------
# Library Management System - Interactive OOP Project
# Week 5: Object-Oriented Programming Basics
# ------------------------------------------------------------

class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.available = True

    def mark_borrowed(self):
        self.available = False

    def mark_returned(self):
        self.available = True

    def __str__(self):
        status = "Available" if self.available else "Borrowed"
        return f"{self.title} by {self.author} (ISBN: {self.isbn}) - {status}"


class Member:
    def __init__(self, name, member_id):
        self.name = name
        self.member_id = member_id
        self.borrowed_books = []

    def borrow_book(self, book):
        if book.available:
            book.mark_borrowed()
            self.borrowed_books.append(book)
            print(f"\n✅ {self.name} borrowed '{book.title}'")
        else:
            print(f"\n❌ Sorry, '{book.title}' is already borrowed.")

    def return_book(self, book):
        if book in self.borrowed_books:
            book.mark_returned()
            self.borrowed_books.remove(book)
            print(f"\n🔁 {self.name} returned '{book.title}'")
        else:
            print(f"\n⚠️ {self.name} has not borrowed '{book.title}'")

    def __str__(self):
        borrowed_titles = [book.title for book in self.borrowed_books]
        return f"{self.name} (ID: {self.member_id}) | Borrowed: {borrowed_titles}"


class Library:
    def __init__(self):
        self.books = []
        self.members = []

    def add_book(self, book):
        self.books.append(book)
        print(f"\n📚 Book '{book.title}' added to the library!")

    def add_member(self, member):
        self.members.append(member)
        print(f"\n👤 Member '{member.name}' added to the system!")

    def find_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def find_member(self, member_id):
        for member in self.members:
            if member.member_id == member_id:
                return member
        return None

    def borrow_book(self, member_id, isbn):
        member = self.find_member(member_id)
        book = self.find_book(isbn)
        if member and book:
            member.borrow_book(book)
        else:
            print("\n⚠️ Member or Book not found!")

    def return_book(self, member_id, isbn):
        member = self.find_member(member_id)
        book = self.find_book(isbn)
        if member and book:
            member.return_book(book)
        else:
            print("\n⚠️ Member or Book not found!")

    def display_books(self):
        print("\n===== 📚 Library Books =====")
        if not self.books:
            print("No books in the library yet.")
        for book in self.books:
            print(book)

    def display_members(self):
        print("\n===== 👥 Library Members =====")
        if not self.members:
            print("No members in the system yet.")
        for member in self.members:
            print(member)


# -------------------- MAIN PROGRAM --------------------
def main():
    library = Library()

    while True:
        print("\n========== Library Management System ==========")
        print("1️⃣  Add Book")
        print("2️⃣  Add Member")
        print("3️⃣  Borrow Book")
        print("4️⃣  Return Book")
        print("5️⃣  Display All Books")
        print("6️⃣  Display All Members")
        print("7️⃣  Exit")
        print("===============================================")

        choice = input("Enter your choice (1-7): ")

        if choice == "1":
            title = input("Enter book title: ")
            author = input("Enter author name: ")
            isbn = input("Enter ISBN: ")
            library.add_book(Book(title, author, isbn))

        elif choice == "2":
            name = input("Enter member name: ")
            member_id = input("Enter member ID: ")
            library.add_member(Member(name, member_id))

        elif choice == "3":
            member_id = input("Enter member ID: ")
            isbn = input("Enter ISBN of the book to borrow: ")
            library.borrow_book(member_id, isbn)

        elif choice == "4":
            member_id = input("Enter member ID: ")
            isbn = input("Enter ISBN of the book to return: ")
            library.return_book(member_id, isbn)

        elif choice == "5":
            library.display_books()

        elif choice == "6":
            library.display_members()

        elif choice == "7":
            print("\n👋 Exiting the Library Management System. Goodbye!")
            break

        else:
            print("\n❌ Invalid choice. Please enter a number from 1 to 7.")


if __name__ == "__main__":
    main()
