# Student Grade Calculator

students = []
num_students = int(input("Enter number of students: "))

for i in range(num_students):
    name = input(f"\nEnter student {i+1} name: ")
    marks = int(input("Enter marks (out of 100): "))

    # Determine grade
    if marks >= 90:
        grade = "A+"
        comment = "Excellent"
    elif marks >= 75:
        grade = "A"
        comment = "Very Good"
    elif marks >= 60:
        grade = "B"
        comment = "Good"
    elif marks >= 40:
        grade = "C"
        comment = "Needs Improvement"
    else:
        grade = "F"
        comment = "Failed"

    students.append([name, marks, grade, comment])

print("\n--- Student Grades ---")
for student in students:
    print(f"Name: {student[0]}, Marks: {student[1]}, Grade: {student[2]}, Comment: {student[3]}")
