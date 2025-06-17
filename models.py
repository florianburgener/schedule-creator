from __future__ import annotations

import math
from typing import List

from pulp import LpAffineExpression, LpProblem, LpVariable

import constants


class Singleton(type):
    """Singleton is a metaclass for making a class a Singleton."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Semester:
    """Represents a semester with its classes."""

    def __init__(self, id: int, name: str) -> None:
        """Creates a new instance of the Semester class.

        Args:
            id (int): The semester ID.
            name (str): The semester name.
        """
        self.id = id
        self.name = name
        self.classes: List[Class_] = []

    def init_groups(self) -> None:
        """Initializes the groups."""
        groups = {1: Group(1, "")}
        identifiers = {"": 1}
        id = 2

        for class_ in self.classes:
            if not class_.group_name in identifiers:
                identifiers[class_.group_name] = id
                groups[id] = Group(id, class_.group_name)
                id += 1

            groups[identifiers[class_.group_name]].classes.append(class_)

        self.groups = list(groups.values())
        self.groups = [self.groups[0]] + sorted(self.groups[1:], key=lambda x: x.name)

    def sort_classes(self) -> None:
        """Sorts the classes."""
        self.classes = []

        for group in self.groups:
            group.sort_classes()
            self.classes += group.classes

    def common_group(self) -> Group:
        """Gets the group containing the common class list.

        Returns:
            Group: The group containing the common class list.
        """
        return self.groups[0]

    def non_common_groups(self) -> List[Group]:
        """Gets the groups that do not contain the list of common classes.

        Returns:
            List[Group]: The groups that do not contain the list of common classes.
        """
        return self.groups[1:]


class Class_:
    """Represents a class."""

    def __init__(self, id: int, name: str, group_name: str, slot_count: int, teachers: List[Teacher]) -> None:
        """Creates a new instance of the Class_ class.

        Args:
            id (int): The class ID.
            name (str): The class name.
            group_name (str): The name of the group to which the class belongs.
            slot_count (int): The number of time slots the class lasts.
            teachers (List[Teacher]): The list of teachers.
        """
        self.id = id
        self.name = name
        self.group_name = group_name
        self.slot_count = slot_count
        self.teachers = teachers

    def contains_teacher(self, teacher: Teacher) -> bool:
        """Checks if the teacher teaches this class.

        Args:
            teacher (Teacher): The teacher.

        Returns:
            bool: True, if the teacher teaches this class otherwise False.
        """
        return teacher.id in [x.id for x in self.teachers]


class Group:
    """Represents a group."""

    def __init__(self, id: int, name: str) -> None:
        """Creates a new instance of the Group class.

        Args:
            id (int): The group ID.
            name (str): The group name.
        """
        self.id = id
        self.name = name
        self.classes: List[Class_] = []

    def sort_classes(self):
        """Sorts the classes."""
        self.classes.sort(key=lambda x: x.name)


class Teacher:
    """Represents a teacher."""

    def __init__(self, id: int, last_name: str, first_name: str, slot_preferences: List[int]) -> None:
        """Creates a new instance of the Teacher class.

        Args:
            id (int): The teacher ID.
            last_name (str): The teacher last name.
            first_name (str): The teacher first name.
            slot_preferences (List[int]): The list of teachers time slot preferences.
        """
        self.id = id
        self.last_name = last_name
        self.first_name = first_name
        self.slot_preferences = slot_preferences


class Slot:
    """Represents a time slot."""

    def __init__(self, id: int, weekday: int, start_time: str, end_time: str, is_lunch_break: bool, is_evening: bool) -> None:
        """Creates a new instance of the Slot class.

        Args:
            id (int): The slot ID.
            weekday (int): The day of the week of the time slot.
            start_time (str): The time slot start time.
            end_time (str): The time slot end time.
            is_lunch_break (bool): Is this time slot on the lunch break?
            is_evening (bool): Is this time slot in the evening?
        """
        self.id = id
        self.weekday = weekday
        self.start_time = start_time
        self.end_time = end_time
        self.is_lunch_break = is_lunch_break
        self.is_evening = is_evening


class DataStorage(metaclass=Singleton):
    """Represents the data storage. This class is a Singleton."""

    def __init__(self) -> None:
        """Creates a new instance of the DataStorage class."""
        self.teachers = parsing.load_teachers()
        self.classes_by_semester = parsing.load_classes()
        self.slots = parsing.load_slots()

        for semester_data in self.classes_by_semester:
            for class_ in semester_data.classes:
                class_teachers = []

                for teacher_id in class_.teachers:
                    class_teachers.append(self.teachers[teacher_id])

                class_.teachers = class_teachers


def with_storage(func):
    def wrapper(*args, **kwargs):
        storage = DataStorage()
        return func(*args, storage, **kwargs)

    return wrapper


class SemesterSchedule:
    """Represents a semester schedule."""

    @with_storage
    def __init__(self, semester: Semester, storage: DataStorage) -> None:
        """Creates a new instance of the SemesterSchedule class.

        Args:
            semester (Semester): The semester for which a schedule will be calculated.
            storage (DataStorage): This parameter is automatically injected.
        """
        self.semester = semester
        self.variables_matrix = self._create_variables_matrix(len(self.semester.classes), len(storage.slots))

    def _create_variables_matrix(self, m: int, n: int) -> List[List[LpVariable]]:
        """Creates the variables matrix.

        Args:
            m (int): The number of rows.
            n (int): The number of columns.

        Returns:
            List[List[LpVariable]]: The variables matrix
        """
        variables = []

        for i in range(m):
            variables.append([])

            for j in range(n):
                variables[-1].append(utils.create_binary_variable(f"{self.semester.id}_X_{i},{j}"))

        return variables

    def _get_objective_function_unallocated_class_slots(self) -> LpAffineExpression:
        """Minimizes the number of unallocated class slots.

        Returns:
            LpAffineExpression: A fragment of the objective function.
        """
        objective_function = 0

        for i in range(len(self.variables_matrix)):
            for j in range(len(self.variables_matrix[0])):
                objective_function += self.variables_matrix[i][j]

        objective_function = -objective_function
        return objective_function

    def _get_objective_function_teachers_slot_preferences(self) -> LpAffineExpression:
        """Takes teachers' preferences into account.

        Returns:
            LpAffineExpression: A fragment of the objective function.
        """
        objective_function = 0
        preference_coefficients = [
            constants.COEFFICIENT_PREFERENCE_NEUTRAL,
            constants.COEFFICIENT_PREFERENCE_NOT_AVAILABLE,
            constants.COEFFICIENT_PREFERENCE_IF_NOT_OTHERWISE_POSSIBLE,
            constants.COEFFICIENT_PREFERENCE_PREFERABLY_NOT,
            constants.COEFFICIENT_PREFERENCE_IDEALLY_YES,
            constants.COEFFICIENT_PREFERENCE_STRONG_PREFERENCE,
        ]

        for i in range(len(self.variables_matrix)):
            for teacher in self.semester.classes[i].teachers:
                for j, slot_preference in enumerate(teacher.slot_preferences):
                    if slot_preference is None:
                        continue

                    variable = self.variables_matrix[i][j]
                    coefficient = preference_coefficients[slot_preference]
                    class_slot_count = self.semester.classes[i].slot_count

                    objective_function += variable * coefficient / class_slot_count

        return objective_function

    def _get_objective_function_penalize_first_hour(self) -> LpAffineExpression:
        """Penalizes the first hour of each day.

        Returns:
            LpAffineExpression: A fragment of the objective function.
        """
        objective_function = 0
        slot_count_per_day = utils.get_slot_count_per_day()

        for i in range(len(self.variables_matrix)):
            for j in range(constants.NUMBER_OF_CLASS_DAYS):
                variable = self.variables_matrix[i][j * slot_count_per_day]
                coefficient = constants.COEFFICIENT_SLOT_PENALTY_FIRST_HOUR
                class_slot_count = self.semester.classes[i].slot_count

                objective_function += variable * coefficient / class_slot_count

        return objective_function

    @with_storage
    def _get_objective_function_penalize_lunch_break(self, storage: DataStorage) -> LpAffineExpression:
        """Penalizes the lunch break hour.

        Args:
            storage (DataStorage): This parameter is automatically injected.

        Returns:
            LpAffineExpression: A fragment of the objective function.
        """
        objective_function = 0

        for i in range(len(self.variables_matrix)):
            for j in range(len(self.variables_matrix[0])):
                if storage.slots[j].is_lunch_break:
                    variable = self.variables_matrix[i][j]
                    coefficient = constants.COEFFICIENT_SLOT_PENALTY_LUNCH_BREAK
                    class_slot_count = self.semester.classes[i].slot_count

                    objective_function += variable * coefficient / class_slot_count

        return objective_function

    @with_storage
    def _get_objective_function_penalize_evening_hours(self, storage: DataStorage) -> LpAffineExpression:
        """Penalizes the evening hours.

        Args:
            storage (DataStorage): This parameter is automatically injected.

        Returns:
            LpAffineExpression: A fragment of the objective function.
        """
        objective_function = 0

        for i in range(len(self.variables_matrix)):
            for j in range(len(self.variables_matrix[0])):
                if storage.slots[j].is_evening:
                    variable = self.variables_matrix[i][j]
                    coefficient = constants.COEFFICIENT_SLOT_PENALTY_EVENING_HOURS
                    class_slot_count = self.semester.classes[i].slot_count

                    objective_function += variable * coefficient / class_slot_count

        return objective_function

    def _set_constraints_match_class_slot_count(self, model: LpProblem) -> None:
        """The sum of each row must equal the number of time slots of the class.

        Args:
            model (LpProblem): The PuLP model.
        """
        for i in range(len(self.variables_matrix)):
            x = 0

            for j in range(len(self.variables_matrix[0])):
                x += self.variables_matrix[i][j]

            model += x == self.semester.classes[i].slot_count

    def _set_constraints_consecutive_slots(self, model: LpProblem) -> None:
        """Force the time slots of each class to be consecutive.

        Args:
            model (LpProblem): The PuLP model.
        """
        slot_count_per_day = utils.get_slot_count_per_day()

        for i in range(len(self.variables_matrix)):
            class_slot_count = self.semester.classes[i].slot_count
            Z = 0

            for j in range(len(self.variables_matrix[0]) - class_slot_count + 1):
                if j % slot_count_per_day > slot_count_per_day - class_slot_count:
                    # Prevents having a class that starts in the evening and ends the next day at the beginning of the day.
                    continue

                x = 0

                for k in range(j, j + class_slot_count):
                    x += self.variables_matrix[i][k]

                z = utils.create_binary_variable(f"{self.semester.id}_Z_{i},{j},{k}")

                model += z <= x / class_slot_count
                model += z >= x - class_slot_count + 1
                Z += z

            model += Z == 1

    def _set_constraints_class_limits_per_slot(self, model: LpProblem) -> None:
        """Each slot can have a maximum of 1 common class or at least 1 group class.

        Args:
            model (LpProblem): The PuLP model.
        """
        for i in range(len(self.variables_matrix[0])):
            common_class_variables = 0
            common_group = self.semester.common_group()

            for j in range(len(common_group.classes)):
                common_class_variables += self.variables_matrix[j][i]

            non_common_groups = self.semester.non_common_groups()

            if not non_common_groups:
                model += common_class_variables <= 1
                continue

            offset = len(common_group.classes)

            for group in non_common_groups:
                group_class_variables = 0

                for j in range(len(group.classes)):
                    group_class_variables += self.variables_matrix[offset + j][i]

                model += common_class_variables + group_class_variables <= 1
                offset += len(group.classes)

    def get_objective_function(self) -> LpAffineExpression:
        """Gets the objective function.

        Returns:
            LpAffineExpression: The objective function for the semester.
        """
        objective_function = 0

        for func in [
            self._get_objective_function_unallocated_class_slots,
            self._get_objective_function_teachers_slot_preferences,
            self._get_objective_function_penalize_first_hour,
            self._get_objective_function_penalize_lunch_break,
            self._get_objective_function_penalize_evening_hours,
        ]:
            objective_function += func()

        return objective_function

    def set_constraints(self, model: LpProblem) -> None:
        """Sets the constraints.

        Args:
            model (LpProblem): The PuLP model.
        """
        for func in [
            self._set_constraints_match_class_slot_count,
            self._set_constraints_consecutive_slots,
            self._set_constraints_class_limits_per_slot,
        ]:
            func(model)

    @with_storage
    def get_class_schedules(self, storage: DataStorage) -> List[ClassSchedule]:
        """Gets the list of class schedules.

        Args:
            storage (DataStorage): This parameter is automatically injected.

        Returns:
            List[ClassSchedule]: The list of class schedules.
        """
        class_schedules = []

        for i in range(len(self.semester.classes)):
            slot_count = 0
            is_previous_variable_true = False

            for j in range(len(storage.slots)):
                is_variable_true = not math.isclose(self.variables_matrix[i][j].varValue, 0)

                if is_variable_true:
                    slot_count += 1

                class_ = self.semester.classes[i]

                if is_previous_variable_true and not is_variable_true:
                    class_schedules.append(ClassSchedule(class_, j - 1, slot_count))
                    slot_count = 0
                elif is_variable_true and j == len(storage.slots) - 1:
                    class_schedules.append(ClassSchedule(class_, len(storage.slots) - 1, slot_count))

                is_previous_variable_true = is_variable_true

        class_schedules.sort(key=lambda x: x.start_slot.id)
        return class_schedules


class ClassSchedule:
    """Represents a class schedule."""

    @with_storage
    def __init__(self, class_: Class_, end_slot_index: int, slot_count: int, storage: DataStorage) -> None:
        """Creates a new instance of the ClassSchedule class.

        Args:
            class_ (Class_): The semester for which a schedule will be calculated.
            end_slot_index (int): The time slot for the last hour of the class.
            slot_count (int): The number of time slots the class lasts.
            storage (DataStorage): This parameter is automatically injected.
        """
        self.class_ = class_
        self.start_slot = storage.slots[end_slot_index - slot_count + 1]
        self.end_slot = storage.slots[end_slot_index]

    def __str__(self):
        """Implementation of str for the class."""
        group_name = self.class_.group_name
        formatted_group_name = f"[{group_name}] " if group_name else ""

        weekdays = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        formatted_weekday = weekdays[self.start_slot.weekday - 1].ljust(len(max(weekdays, key=len)))

        start_time_end_time = f"{self.start_slot.start_time} - {self.end_slot.end_time}"
        formatted_classs_slot_count = f"{self.class_.slot_count} heures"

        return f"{formatted_weekday}   {start_time_end_time}   {formatted_classs_slot_count}   {formatted_group_name}{self.class_.name}"


import parsing
import utils
