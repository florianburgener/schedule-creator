import csv
from typing import Dict, List

import utils
from models import Class_, Semester, Slot, Teacher


def load_teachers() -> Dict[int, List[Teacher]]:
    """Loads teacher data.

    Returns:
        Dict[int, List[Teacher]]: The list of teachers.
    """
    data = {}

    with open("./data/Teachers.csv", "r") as f:
        reader = csv.reader(f, delimiter=";")

        for row in reader:
            slot_preferences = []

            # WARNING: If the storage of teacher preferences changes, this code will no longer work.
            for i, x in enumerate(row[3:]):
                x = int(x)

                if i % 3 == 0:
                    slot_preferences += [x] * 4 + [None]
                elif i % 3 == 1:
                    slot_preferences += [x] * 4
                else:
                    slot_preferences += [x] * 6

            item = Teacher(
                id=int(row[0]),
                last_name=row[1],
                first_name=row[2],
                slot_preferences=slot_preferences,
            )
            data[item.id] = item

    return data


def load_classes() -> List[Semester]:
    """Loads class data.

    Returns:
        List[Semester]: The list of classes by semester.
    """
    semesters = {}

    with open("./data/Classes.csv", "r") as f:
        reader = csv.reader(f, delimiter=";")

        identifiers = {}
        id = 1

        for row in reader:
            semester_name = row[2]

            if not semester_name in identifiers:
                identifiers[semester_name] = id
                semesters[id] = Semester(id, semester_name)
                id += 1

            class_ = Class_(
                id=int(row[0]),
                name=row[1],
                group_name=row[3],
                slot_count=int(row[4]),
                teachers=eval(row[5]),
            )
            semesters[identifiers[semester_name]].classes.append(class_)

    semesters = list(semesters.values())

    for semester in semesters:
        semester.init_groups()
        semester.sort_classes()

    return semesters


def load_slots() -> List[Slot]:
    """Loads slot data.

    Returns:
        List[Slot]: The list of slots.
    """
    data = []

    with open("./data/Slots.csv", "r") as f:
        reader = csv.reader(f, delimiter=";")
        rows = [x for x in reader]
        slot_count_per_day = utils.get_slot_count_per_day_(len(rows))

        for i, row in enumerate(rows):
            item = Slot(
                id=int(row[0]),
                weekday=int(row[2]),
                start_time=row[3],
                end_time=row[4],
                # The lunch break must always be the 5th hour of the day.
                is_lunch_break=i % slot_count_per_day == 4,
                # Evening hours should always start from the 10th hour of the day.
                is_evening=i % slot_count_per_day >= 9,
            )
            data.append(item)

    return data
