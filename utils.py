import pulp as PuLP
from pulp import LpVariable

import constants
from models import DataStorage, with_storage


def create_binary_variable(name: str) -> LpVariable:
    """Creates a PuLP binary variable.

    Args:
        name (str): The variable name.

    Returns:
        LpVariable: The variable.
    """
    return LpVariable(name, lowBound=0, upBound=1, cat=PuLP.const.LpInteger)


def get_slot_count_per_day_(slot_count: int = None) -> int:
    """Gets the number of slots per day.

    Args:
        slot_count (int, optional): The total number of slots.. Defaults to None.

    Returns:
        int: The number of slots per day.
    """
    return slot_count // constants.NUMBER_OF_CLASS_DAYS


@with_storage
def get_slot_count_per_day(storage: DataStorage) -> int:
    """Gets the number of slots per day.

    Args:
        storage (DataStorage): This parameter is automatically injected.

    Returns:
        int: The number of slots per day.
    """
    return get_slot_count_per_day_(len(storage.slots))
