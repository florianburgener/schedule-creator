import math

import utils
from models import DataStorage, SemesterSchedule, with_storage


def printnoln(*args) -> None:
    """Calls the print function without line break."""
    print(*args, end="")


def print_divider(c: str = "-") -> None:
    """Displays a divider.

    Args:
        c (str, optional): The character used for the divider.. Defaults to "-".
    """
    print(c * (len(DataStorage().slots) * 2 + 11))


@with_storage
def print_variables_matrix_header(storage: DataStorage) -> None:
    """Displays the variables matrix header.

    Args:
        storage (DataStorage): This parameter is automatically injected.
    """
    print_divider()
    slot_count_per_day = utils.get_slot_count_per_day()

    # First row.
    printnoln("| ")
    for i in range(len(storage.slots)):
        slot_weekday = storage.slots[i].weekday
        printnoln(f"{slot_weekday} ")

        if (i + 1) % slot_count_per_day == 0:
            printnoln("| ")
    print("<= Jour de la semaine")

    # Second row.
    printnoln("| ")
    for i in range(len(storage.slots)):
        # WARNING: this line will not work correctly with different slot data.
        printnoln(f"{((i % slot_count_per_day) % 9) + 1} ")

        if (i + 1) % slot_count_per_day == 0:
            printnoln("| ")
    print("<= Créneau horaire")

    print_divider()


@with_storage
def print_variables_matrix(semester_schedule: SemesterSchedule, storage: DataStorage) -> None:
    """Displays the variables matrix.

    Args:
        semester_schedule (SemesterSchedule): The semester schedule.
        storage (DataStorage): This parameter is automatically injected.
    """
    print_variables_matrix_header()
    slot_count_per_day = utils.get_slot_count_per_day()

    for i in range(len(semester_schedule.variables_matrix)):
        printnoln("| ")

        for j in range(len(semester_schedule.variables_matrix[0])):
            if math.isclose(semester_schedule.variables_matrix[i][j].varValue, 0):
                if storage.slots[j].is_lunch_break:
                    printnoln("  ")
                else:
                    printnoln("· ")
            else:
                printnoln("🞮 ")

            if (j + 1) % slot_count_per_day == 0:
                printnoln("| ")

        class_ = semester_schedule.semester.classes[i]

        check_slot_count = sum(semester_schedule.variables_matrix[i][j].varValue for j in range(len(semester_schedule.variables_matrix[0]))) == class_.slot_count
        check_slot_count_str = "✅" if check_slot_count else "❌"
        class_id_str = str(class_.id).ljust(2)
        class_slot_count = class_.slot_count
        class_name = class_.name
        group_name = class_.group_name
        formatted_group_name = f"[{group_name}] " if group_name else ""
        printnoln(f"-- {check_slot_count_str} #{class_id_str} [{class_slot_count} h] {formatted_group_name}{class_name}")

        sorted_teachers = sorted(x.last_name for x in class_.teachers)
        print(" (%s)" % ", ".join(sorted_teachers))

    print_divider()


def print_class_schedules(semester_schedule: SemesterSchedule) -> None:
    """Displays the class schedules.

    Args:
        semester_schedule (SemesterSchedule): The semester schedule.
    """
    for class_schedule in semester_schedule.get_class_schedules():
        print(class_schedule)


@with_storage
def print_teachers_preferences(storage: DataStorage) -> None:
    """Displays the teacher preferences.

    Args:
        storage (DataStorage): This parameter is automatically injected.
    """
    print_variables_matrix_header()
    sorted_teachers = sorted(storage.teachers.values(), key=lambda x: x.last_name)
    slot_count_per_day = utils.get_slot_count_per_day()

    for teacher in sorted_teachers:
        printnoln("| ")

        for i, slot_preference in enumerate(teacher.slot_preferences):
            if slot_preference is None:
                printnoln("  ")
            elif slot_preference == 0:
                printnoln("· ")
            else:
                printnoln(f"{slot_preference} ")

            if (i + 1) % slot_count_per_day == 0:
                printnoln("| ")

        print("--", teacher.last_name, teacher.first_name)

    print_divider()

    print("5 = Forte préférence")
    print("4 = Idéalement oui")
    print("· = Neutre")
    print("3 = De préférence pas")
    print("2 = Si pas possible autrement")
    print("1 = Pas disponible")


def print_results(semester_schedules: SemesterSchedule) -> None:
    """Displays the results.

    Args:
        semester_schedules (SemesterSchedule): The semester schedules.
    """
    for semester_schedule in semester_schedules:
        print_divider("*")
        print(semester_schedule.semester.name)
        print_divider("*")
        print()

        print_variables_matrix(semester_schedule)

        print_class_schedules(semester_schedule)
        print()

    print_divider("*")

    print("\nPréférences des professeurs:")
    print_teachers_preferences()
