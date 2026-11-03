
from datetime import datetime, date, timedelta, timezone
from getpass import getpass

PH_TIMEZONE = timezone(timedelta(hours=8))

appointments = []
next_appointment_id = 1

teachers = [
    ["T1", "Ms. Roxanne Tagam", "rope", "roxanne123"],
    ["T2", "Ms. Jeanne Avila", "jeli", "jeanne123"],
    ["T3", "Ms. Nathaly Mabanto", "nath", "nathaly123"]
]

time_slots = [
    "8:00 AM",
    "10:00 AM",
    "1:00 PM",
    "4:00 PM"
]

ID, NAME, STUDENT_ID, TEACHER_ID, DATE, TIME, PURPOSE, STATUS = range(8)


def shorten(text, limit=25):
    text = str(text)
    if len(text) > limit:
        return text[:limit - 3] + "..."
    return text


def print_table(headers, rows):
    widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    line = "+" + "+".join("-" * (w + 2) for w in widths)

    line += "+"

    def format_row(cells):
        return "| " + " | ".join(
            str(cell).ljust(widths[i]) for i, cell in enumerate(cells)
        ) + " |"

    print(line)
    print(format_row(headers))
    print(line)

    for row in rows:
        print(format_row(row))

    print(line)


def sort_key(appointment):
    return (appointment[DATE], time_slots.index(appointment[TIME]))


def get_teacher_name(teacher_id):
    for teacher in teachers:
        if teacher[0] == teacher_id:
            return teacher[1]

    return "Unknown"


def show_student_table(items):
    rows = [
        [a[ID], get_teacher_name(a[TEACHER_ID]), a[DATE], a[TIME],
         shorten(a[PURPOSE]), a[STATUS]]
        for a in sorted(items, key=sort_key)
    ]

    print_table(
        ["ID", "Teacher", "Date", "Time", "Purpose", "Status"],
        rows
    )


def show_teacher_table(items):
    rows = [
        [a[ID], a[NAME], a[STUDENT_ID], a[DATE], a[TIME],
         shorten(a[PURPOSE]), a[STATUS]]
        for a in sorted(items, key=sort_key)
    ]

    print_table(
        ["ID", "Student", "Student ID", "Date", "Time", "Purpose", "Status"],
        rows
    )


def main_menu():
    print()
    print("===== APPOINTMENT SCHEDULER =====")
    print("[1] Teacher")
    print("[2] Student")
    print("[3] Exit")


def teacher_login():
    while True:
        print()
        print("===== TEACHER LOGIN =====")
        print("(Leave username blank to go back)")

        username = input("Username: ").strip()

        if username == "":
            return

        password = input("Password: ")

        for teacher in teachers:
            if teacher[2] == username and teacher[3] == password:
                print()
                print("Login successful!")
                print("Welcome,", teacher[1])

                teacher_menu(teacher)
                return

        print("Invalid username or password.")
        print("Please try again.")


def teacher_menu(teacher):
    while True:
        print()
        print(teacher[1], "- Teacher")
        print("[1] View appointments")
        print("[2] Approve appointment")
        print("[3] Cancel appointment")
        print("[4] Log out")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            view_teacher_appointments(teacher)

        elif choice == "2":
            approve_appointment(teacher)

        elif choice == "3":
            cancel_appointment(teacher)

        elif choice == "4":
            print("Logging out...")
            break

        else:
            print("Invalid choice.")


def student_menu():
    while True:
        print()
        print("Student - Menu")
        print("[1] Add appointment")
        print("[2] View status of appointment")
        print("[3] Edit appointment")
        print("[4] Back")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            book_appointment()

        elif choice == "2":
            view_student_appointments()

        elif choice == "3":
            edit_appointment()

        elif choice == "4":
            break

        else:
            print("Invalid choice.")


def get_valid_student_name():
    while True:
        name = input("Enter your name: ").strip()

        if name and all(c.isalpha() or c.isspace() for c in name):
            return " ".join(name.split()).title()

        print("Invalid name.")
        print("Please enter letters and spaces only.")


def get_valid_student_id():
    while True:
        student_id = input("Enter your student ID: ").strip()

        if (
            len(student_id) == 14
            and student_id[2] == "-"
            and student_id[7] == "-"
            and student_id[:2].isdigit()
            and student_id[3:7].isdigit()
            and student_id[8:14].isdigit()
        ):
            return student_id

        print("Invalid student ID.")
        print("Please use the format 00-0000-000000.")


def get_valid_date():
    while True:
        date_input = input("Enter date (YYYY-MM-DD): ").strip()

        if (
            len(date_input) != 10
            or date_input[4] != "-"
            or date_input[7] != "-"
        ):
            print("Invalid date.")
            print("Please use the format YYYY-MM-DD.")
            continue

        try:
            selected_date = datetime.strptime(
                date_input, "%Y-%m-%d"
            ).date()

        except ValueError:
            print("Invalid date.")
            print("Please use the format YYYY-MM-DD.")
            continue

        current_year = datetime.now(PH_TIMEZONE).year

        if selected_date.year != current_year:
            print(
                f"Invalid year. Please enter a date in "
                f"{current_year} only."
            )
            continue

        return date_input


def time_available(
    teacher_id, selected_date, selected_time, ignore_id=None
):
    for appointment in appointments:
        if (
            appointment[TEACHER_ID] == teacher_id
            and appointment[DATE] == selected_date
            and appointment[TIME] == selected_time
            and appointment[STATUS] != "Cancelled"
            and (ignore_id is None or appointment[ID] != ignore_id)
        ):
            return False

    return True


def student_is_busy(
    student_id, selected_date, selected_time, ignore_id=None
):
    for appointment in appointments:
        if (
            appointment[STUDENT_ID] == student_id
            and appointment[DATE] == selected_date
            and appointment[TIME] == selected_time
            and appointment[STATUS] != "Cancelled"
            and (ignore_id is None or appointment[ID] != ignore_id)
        ):
            return True

    return False


def slot_has_passed(selected_date, slot):
    now = datetime.now(PH_TIMEZONE)

    if selected_date != now.date().isoformat():
        return False

    slot_time = datetime.strptime(slot, "%I:%M %p").time()
    current_time = now.time().replace(tzinfo=None)

    return slot_time <= current_time


def get_valid_time(
    selected_date, teacher_id, student_id, ignore_id=None
):
    open_slots = [
        slot for slot in time_slots
        if time_available(
            teacher_id, selected_date, slot, ignore_id
        )
        and not student_is_busy(
            student_id, selected_date, slot, ignore_id
        )
    ]

    if not open_slots:
        print()
        print("No time slots are available on that date.")
        print("Please try another date.")
        return None

    print()
    print("Available Time Slots:")

    for i, slot in enumerate(open_slots, start=1):
        print(f"[{i}] {slot}")

    while True:
        choice = input("Choose a time slot: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(open_slots):
            return open_slots[int(choice) - 1]

        print("Invalid choice.")
        print("Please choose one of the available time slots.")


def id_belongs_to_other_name(student_id, name):
    for appointment in appointments:
        if (
            appointment[STUDENT_ID] == student_id
            and appointment[NAME].lower() != name.lower()
        ):
            return True

    return False


def book_appointment():
    global next_appointment_id

    print()
    print("--- ADD APPOINTMENT ---")

    name = get_valid_student_name()
    student_id = get_valid_student_id()

    if id_belongs_to_other_name(student_id, name):
        print()
        print("This student ID is already registered under a different name.")
        return

    print()
    print("Available Teachers:")
    print_table(
        ["ID", "Teacher"],
        [[t[0], t[1]] for t in teachers]
    )

    selected_teacher = None

    while selected_teacher is None:
        teacher_id = input("Enter teacher ID: ").strip().upper()

        for teacher in teachers:
            if teacher[0] == teacher_id:
                selected_teacher = teacher
                break

        if selected_teacher is None:
            print("Teacher ID not found.")
            print("Please enter one of the teacher IDs above (e.g. T1).")

    date_selected = get_valid_date()

    time_selected = get_valid_time(
        date_selected, selected_teacher[0], student_id
    )

    if time_selected is None:
        return

    purpose = input("Enter purpose: ").strip()

    if not purpose:
        print("Please complete all appointment details.")
        return

    appointment_id = next_appointment_id
    next_appointment_id += 1

    appointments.append([
        appointment_id,
        name,
        student_id,
        selected_teacher[0],
        date_selected,
        time_selected,
        purpose,
        "Pending"
    ])

    print()
    print("Appointment added successfully!")
    print_table(
        ["ID", "Teacher", "Date", "Time", "Status"],
        [[appointment_id, selected_teacher[1], date_selected,
          time_selected, "Pending"]]
    )


def view_student_appointments():
    print()
    print("--- VIEW STATUS OF APPOINTMENT ---")

    student_id = get_valid_student_id()

    mine = [
        a for a in appointments if a[STUDENT_ID] == student_id
    ]

    if not mine:
        print("No appointments found.")
        return

    print()
    print("Student:", mine[0][NAME])
    show_student_table(mine)


def edit_appointment():
    print()
    print("--- EDIT APPOINTMENT ---")

    student_id = get_valid_student_id()

    pending = [
        a for a in appointments
        if a[STUDENT_ID] == student_id and a[STATUS] == "Pending"
    ]

    if not pending:
        print("No pending appointment found.")
        return

    print()
    print("Your pending appointments:")
    show_student_table(pending)

    chosen = input("Enter the appointment ID to edit: ").strip()

    if not chosen.isdigit():
        print("Please enter a valid number.")
        return

    chosen = int(chosen)
    selected = None

    for appointment in pending:
        if appointment[ID] == chosen:
            selected = appointment
            break

    if selected is None:
        print("That is not one of your pending appointments.")
        return

    print()
    print("Enter the new details.")

    new_date = get_valid_date()
    new_time = get_valid_time(
        new_date, selected[TEACHER_ID], student_id, selected[ID]
    )

    if new_time is None:
        return

    new_purpose = input(
        f"Enter new purpose (leave blank to keep "
        f"'{selected[PURPOSE]}'): "
    ).strip()

    if not new_purpose:
        new_purpose = selected[PURPOSE]

    selected[DATE] = new_date
    selected[TIME] = new_time
    selected[PURPOSE] = new_purpose

    print()
    print("Appointment updated successfully.")
    show_student_table([selected])


def view_teacher_appointments(teacher):
    print()
    print("--- MY APPOINTMENTS ---")

    mine = [
        a for a in appointments if a[TEACHER_ID] == teacher[0]
    ]

    if not mine:
        print("You have no appointments.")
        return

    show_teacher_table(mine)


def approve_appointment(teacher):
    print()
    print("--- APPROVE APPOINTMENT ---")

    pending = [
        a for a in appointments
        if a[TEACHER_ID] == teacher[0] and a[STATUS] == "Pending"
    ]

    if not pending:
        print("You have no pending appointments.")
        return

    show_teacher_table(pending)

    appointment_id = input("Enter appointment ID: ").strip()

    if not appointment_id.isdigit():
        print("Please enter a valid number.")
        return

    appointment_id = int(appointment_id)

    for appointment in pending:
        if appointment[ID] == appointment_id:
            appointment[STATUS] = "Approved"
            print()
            print("Appointment approved successfully.")
            return

    print("That is not one of your pending appointments.")


def cancel_appointment(teacher):
    print()
    print("--- CANCEL APPOINTMENT ---")

    active = [
        a for a in appointments
        if a[TEACHER_ID] == teacher[0]
        and a[STATUS] != "Cancelled"
    ]

    if not active:
        print("You have no appointments to cancel.")
        return

    show_teacher_table(active)

    appointment_id = input("Enter appointment ID: ").strip()

    if not appointment_id.isdigit():
        print("Please enter a valid number.")
        return

    appointment_id = int(appointment_id)

    for appointment in active:
        if appointment[ID] == appointment_id:
            print()
            print("Are you sure you want to cancel?")
            print("[1] Confirm")
            print("[2] Cancel")

            confirm = input("Choose an option: ").strip()

            if confirm == "1":
                appointment[STATUS] = "Cancelled"
                print("Appointment cancelled successfully.")
            elif confirm == "2":
                print("Cancellation aborted. Appointment unchanged.")
            else:
                print("Invalid choice. No changes made.")

            return

    print("That is not one of your active appointments.")


def main():
    while True:
        main_menu()

        choice = input("Choose an option: ").strip()

        if choice == "1":
            teacher_login()

        elif choice == "2":
            student_menu()

        elif choice == "3":
            print()
            print("Thank you for using the system!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
