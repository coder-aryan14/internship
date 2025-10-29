students = {}

def add_student(name, age, grade):
    students[name] = {"Age": age, "Grade": grade}

def display_students():
    for name, info in students.items():
        print(f"{name} -> Age: {info['Age']}, Grade: {info['Grade']}")

add_student("Kratos", 21, "A")
add_student("Arjun", 20, "B")
display_students()
