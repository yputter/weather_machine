from enum import StrEnum, auto
from dataclasses import dataclass
from typing import ClassVar, Deque, Self, TypeVar
import pandas as pd
import numpy as np
from collections import deque

"""
game state, tracks all players- and global states

How to do a transaction?

For instance, player wants first chemical.
cost is x
the player loses x vouchers, but gains the chenmical in return
the board loses chemical, doesnt necessarily gain the voucher (but if you do count it like that, you can keep track)
"""


class Color(StrEnum):
    YELLOW = auto()
    BLACK = auto()
    ORANGE = auto()
    PURPLE = auto()


class WeatherType(StrEnum):
    RAIN = auto()
    WIND = auto()
    SUN = auto()
    FOG = auto()
    SNOW = auto()


class ChemicalType(StrEnum):
    VERDINO = auto()
    MELGOTH = auto()
    DELUGIUM = auto()
    CALORIUM = auto()
    RADIEU = auto()


@dataclass
class Chemical:
    type: ChemicalType


@dataclass
class ChemicalSupply:
    chemicals: dict[ChemicalType, Deque[Chemical]]
    COST_CHEMICALS: ClassVar[list[int]] = [1, 1, 2, 2, 3]
    supply_vouchers: int = 0

    def get_cost_of_chemical(self, chemical_type: ChemicalType, acquire_from_board: bool):
        # TODO should've been np.inf when you trade 5 times, but acquire cost is 1?
        chemical_deck = self._get_chemical_row(chemical_type)
        try:
            return self.COST_CHEMICALS[-(len(chemical_deck) + (not acquire_from_board))]
        except IndexError:
            return np.inf

    def store_chemical(self, chemical: Chemical):
        self._get_chemical_row(chemical.type).appendleft()

    def retreive_chemical(self, chemical_type: ChemicalType) -> Chemical:
        return self._get_chemical_row(chemical_type).popleft()

    def _get_chemical_row(self, chemical_type: ChemicalType):
        return self.chemicals[chemical_type]


@dataclass
class Player:
    name: str
    chemicals: dict[ChemicalType, Deque[Chemical]]
    max_vouchers = 4
    supply_vouchers: float = 0

    def _get_chemical_row(self, chemical_type: ChemicalType):
        return self.chemicals[chemical_type]

    def store_chemical(self, chemical: Chemical):
        self._get_chemical_row(chemical.type).appendleft(chemical)

    def retreive_chemical(self, chemical_type: Chemical) -> Chemical:
        return self._get_chemical_row(chemical_type).popleft()

    def store_supply_vouchers(self, n: int):
        self.vouchers = min(self.vouchers + n, self.max_vouchers)

    def retreive_supply_vouchers(self, n: int):
        self.vouchers = self.vouchers - n

    def trade_chemical(self, chemical_type: ChemicalType, chemical_supply: ChemicalSupply, acquire_from_board: bool):
        from_object, to_object = [chemical_supply, self] if acquire_from_board else [self, chemical_supply]

        # voucher trade
        cost = chemical_supply.get_cost_of_chemical(chemical_type, acquire_from_board)
        is_trade_impossible = to_object.supply_vouchers - cost < 0
        if is_trade_impossible:
            print("trade not possible \n")
            return
        from_object.supply_vouchers += cost
        to_object.supply_vouchers -= cost

        # chemical trade
        chemical = from_object.retreive_chemical(chemical_type)
        to_object.store_chemical(chemical)
        print("trade done \n")


def show_chemical_type_info(player: Player, chemical_supply: ChemicalSupply):
    df = pd.DataFrame(
        {
            c: {
                "n_supply": len(chemical_supply.chemicals[c]),
                "n_player": len(player.chemicals[c]),
                "acquire": chemical_supply.get_cost_of_chemical(c, True),
                "return": chemical_supply.get_cost_of_chemical(c, False),
            }
            for c in ChemicalType
        }
    )
    print(f"chemical info \n")
    print(f"{df.T}\n")


T = TypeVar("T")


def prompt_user(query: str, options: dict[str, T]) -> T:
    option_chosen = None
    while option_chosen is None:
        x = input(f"{query} \nPress {options}\n")
        option_chosen = options.get(x)
        if option_chosen is None:
            print("Wrong input given")
    print(f"You've selected {option_chosen} \n")
    return option_chosen


def ask_which_chemical_type() -> ChemicalType:
    options = {str(i + 1): t.value for i, t in enumerate(ChemicalType)}
    query = "Which chemical do you want to trade?"
    return ChemicalType(prompt_user(query, options))


def ask_to_trade() -> bool:
    lookup = {
        "acquire from supply": True,
        "return to supply": False,
    }
    query = "How do you want to trade?"
    options = {str(i + 1): t for i, t in enumerate(lookup)}
    return lookup[prompt_user(query, options)]


def initialize_chemicals(n_chemicals_per_type: int):
    return {t: deque(Chemical(type=t) for i in range(n_chemicals_per_type)) for t in ChemicalType}


if __name__ == "__main__":
    chemical_supply = ChemicalSupply(chemicals=initialize_chemicals(5))
    player_1 = Player("player one", initialize_chemicals(0), supply_vouchers=9)
    player_2 = Player("player two", initialize_chemicals(0), supply_vouchers=9)
    players = [player_1, player_2]
    round = 1
    while round < 5:
        print(f"{round=}\n")
        for player in players:
            print(f"Playing as {player.name}\n")
            show_chemical_type_info(player, chemical_supply)
            chemical_type = ask_which_chemical_type()
            acquire_from_board = ask_to_trade()
            player.trade_chemical(chemical_type, chemical_supply, acquire_from_board)

        round += 1
