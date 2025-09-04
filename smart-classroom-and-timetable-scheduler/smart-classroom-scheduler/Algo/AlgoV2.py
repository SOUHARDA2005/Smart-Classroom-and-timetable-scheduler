from ortools.sat.python import cp_model
from prettytable import PrettyTable

# Define Basic Classes

# Represents a classroom with ID and capacity
class Room:
    def __init__(self, number, capacity):
        self.number = number
        self.capacity = capacity

# Represents a meeting time slot (id + time)
class MeetingTime:
    def __init__(self, id, time):
        self.id = id
        self.time = time
 
# Represents a teacher with an id and name
class Teacher:
    def __init__(self, id, name):
        self.id = id
        self.name = name

# Represents a course with course number, name, allowed teachers, and student count
class Course:
    def __init__(self, number, name, teachers, students):
        self.number = number
        self.name = name
        self.teachers = teachers  # list of Teacher objects
        self.students = students  # how many students take this course

# Represents a department containing multiple courses
class Department:
    def __init__(self, name, courses):
        self.name = name
        self.courses = courses

# Data Setup

# Define available rooms with capacities
rooms = [Room("R1", 25), Room("R2", 45), Room("R3", 35)]

# Define available meeting times
times = [
    MeetingTime("MT1", "MWF 9:00-10:00"),
    MeetingTime("MT2", "MWF 10:00-11:00"),
    MeetingTime("MT3", "TTH 9:00-10:30"),
    MeetingTime("MT4", "TTH 10:30-12:00"),
]

# Define teachers (global teacher list)
teachers = [
    Teacher("T1", "MR.ROY"),
    Teacher("T2", "MR.SEN"),
    Teacher("T3", "MR.GUPTA"),
    Teacher("T4", "MR.GIRI"),
]

# Define courses and specify which teachers can teach them + number of students
c1 = Course("C1","101",[teachers[0],teachers[1]],25)
c2 = Course("C2","102",[teachers[0],teachers[1],teachers[2]],35)
c3 = Course("C3","103",[teachers[0],teachers[1]],25)
c4 = Course("C4","104",[teachers[2],teachers[3]],30)
c5 = Course("C5","105",[teachers[3]],35)
c6 = Course("C6","106",[teachers[0],teachers[2]],45)
c7 = Course("C7","107",[teachers[1],teachers[3]],45)

# Define departments with courses inside them
departments = [
    Department("MATH",[c1,c3]),
    Department("BEE",[c2,c4,c5]),
    Department("CHEM",[c6,c7]),
]

# List of all courses
courses = [c1,c2,c3,c4,c5,c6,c7]

# Map teacher objects to their index (needed for constraints)
teacher_index = {t: idx for idx, t in enumerate(teachers)}

# OR-Tools Model

# Create constraint programming model
model = cp_model.CpModel()

# Number of items
num_courses = len(courses)
num_times = len(times)
num_rooms = len(rooms)
num_teachers = len(teachers)

# Decision variables:
# Each course gets assigned a time, room, and teacher
course_time = [model.NewIntVar(0, num_times-1, f"time_{i}") for i in range(num_courses)]
course_room = [model.NewIntVar(0, num_rooms-1, f"room_{i}") for i in range(num_courses)]
course_teacher = [model.NewIntVar(0, num_teachers-1, f"teacher_{i}") for i in range(num_courses)]

# Constraints

# (1) Room capacity constraint
room_capacities = [r.capacity for r in rooms]
min_capacity = min(room_capacities)
max_capacity = max(room_capacities)

for i, course in enumerate(courses):
    # Variable to hold the capacity of chosen room
    room_capacity_var = model.NewIntVar(min_capacity, max_capacity, f"room_capacity_{i}")
    # Link chosen room index to its actual capacity
    model.AddElement(course_room[i], room_capacities, room_capacity_var)
    # Ensure room has enough seats for all students
    model.Add(room_capacity_var >= course.students)

# (2) Teacher assignment constraint
# Only allowed teachers can be assigned to a given course
for i, course in enumerate(courses):
    allowed_indices = [teacher_index[t] for t in course.teachers]
    allowed_tuples = [[idx] for idx in allowed_indices]  # OR-Tools expects tuples
    model.AddAllowedAssignments([course_teacher[i]], allowed_tuples)

# (3) No two courses in the same room at the same time
for i in range(num_courses):
    for j in range(i+1, num_courses):
        diff_time = model.NewBoolVar(f"diff_time_{i}_{j}")
        diff_room = model.NewBoolVar(f"diff_room_{i}_{j}")

        # True if times differ
        model.Add(course_time[i] != course_time[j]).OnlyEnforceIf(diff_time)
        model.Add(course_time[i] == course_time[j]).OnlyEnforceIf(diff_time.Not())

        # True if rooms differ
        model.Add(course_room[i] != course_room[j]).OnlyEnforceIf(diff_room)
        model.Add(course_room[i] == course_room[j]).OnlyEnforceIf(diff_room.Not())

        # At least one must differ (no complete clash)
        model.AddBoolOr([diff_time, diff_room])

# (4) A teacher cannot teach two courses at the same time
for i in range(num_courses):
    for j in range(i+1, num_courses):
        same_teacher = model.NewBoolVar(f"same_teacher_{i}_{j}")

        # same_teacher = True if teachers are the same
        model.Add(course_teacher[i] == course_teacher[j]).OnlyEnforceIf(same_teacher)
        model.Add(course_teacher[i] != course_teacher[j]).OnlyEnforceIf(same_teacher.Not())

        # If same teacher, then courses must be at different times
        model.Add(course_time[i] != course_time[j]).OnlyEnforceIf(same_teacher)

# Solve

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10.0  # prevent long solving times

status = solver.Solve(model)

# Display Results

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    table = PrettyTable(["Course","Dept","Room","Teacher","Time"])
    for i, course in enumerate(courses):
        assigned_time = times[solver.Value(course_time[i])]
        assigned_room = rooms[solver.Value(course_room[i])]
        assigned_teacher = teachers[solver.Value(course_teacher[i])]

        # Find department name that this course belongs to
        dept = next((d.name for d in departments if course in d.courses), "Unknown")

        # Add to output table
        table.add_row([
            course.name,dept,
            f"{assigned_room.number} ({assigned_room.capacity})",
            f"{assigned_teacher.name} ({assigned_teacher.id})",
            f"{assigned_time.time} ({assigned_time.id})"
        ])
    print(table)
else:
    print("No feasible timetable found!")
