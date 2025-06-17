"""
Project : Schedule Creator
Version : 0.4.0
Date    : November 2023
"""
from typing import List

from pulp import *

import output
from models import DataStorage, SemesterSchedule, with_storage


@with_storage
def set_global_constraints(model: LpProblem, semester_schedules: List[SemesterSchedule], storage: DataStorage) -> None:
    """Sets the global constraints.

    Args:
        model (LpProblem): The PuLP model.
        semester_schedules (List[SemesterSchedule]): The list of semester schedules.
        storage (DataStorage): This parameter is automatically injected.
    """

    # Prevents a teacher from teaching 2 classes at the same time.
    for teacher in storage.teachers.values():
        for i in range(len(storage.slots)):
            x = 0

            for semester_schedule in semester_schedules:
                for j, class_ in enumerate(semester_schedule.semester.classes):
                    if class_.contains_teacher(teacher):
                        x += semester_schedule.variables_matrix[j][i]

            model += x <= 1


@with_storage
def main(storage: DataStorage) -> None:
    model = LpProblem("Schedule_Creator", LpMinimize)
    objective_function = 0

    semester_schedules = []

    for semester in storage.classes_by_semester:
        semester_schedule = SemesterSchedule(semester)

        objective_function += semester_schedule.get_objective_function()
        semester_schedule.set_constraints(model)

        semester_schedules.append(semester_schedule)

    set_global_constraints(model, semester_schedules)

    model += objective_function
    model.solve()

    if model.status != LpStatusOptimal:
        print("STOP")
        return

    print(f"{len(model.variables())} variables")
    print(f"{len(model.constraints)} constraints")
    print()

    output.print_results(semester_schedules)


if __name__ == "__main__":
    main()
