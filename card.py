"""Card and Deck classes for UNO game."""

import random
from enum import Enum
from typing import List, Optional


class Color(Enum):
    RED = "Red"
    BLUE = "Blue"
    GREEN = "Green"
    YELLOW = "Yellow"
    WILD = "Wild"


class CardType(Enum):
    NUMBER = "Number"
    SKIP = "Skip"
    REVERSE = "Reverse"
    DRAW_TWO = "Draw Two"
    WILD = "Wild"
    WILD_DRAW_FOUR = "Wild Draw Four"


class Card:
    __slots__ = ("color", "card_type", "number")

    def __init__(self, color: Color, card_type: CardType, number: Optional[int] = None):
        if card_type == CardType.NUMBER and number is None:
            raise ValueError("Number cards must have a number value")
        if card_type != CardType.NUMBER and number is not None:
            raise ValueError("Non-number cards cannot have a number value")
        if card_type in (CardType.WILD, CardType.WILD_DRAW_FOUR) and color != Color.WILD:
            raise ValueError("Wild cards must have WILD color")
        if card_type not in (CardType.WILD, CardType.WILD_DRAW_FOUR) and color == Color.WILD:
            raise ValueError("Non-wild cards cannot have WILD color")
        if number is not None and not (0 <= number <= 9):
            raise ValueError("Number must be between 0 and 9")

        self.color = color
        self.card_type = card_type
        self.number = number

    def is_wild(self) -> bool:
        return self.card_type in (CardType.WILD, CardType.WILD_DRAW_FOUR)

    def is_action(self) -> bool:
        return self.card_type in (CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO)

    def __repr__(self) -> str:
        if self.card_type == CardType.NUMBER:
            return f"{self.color.value} {self.number}"
        if self.is_wild():
            return self.card_type.value
        return f"{self.color.value} {self.card_type.value}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return (self.color == other.color
                and self.card_type == other.card_type
                and self.number == other.number)

    def __hash__(self) -> int:
        return hash((self.color, self.card_type, self.number))


class Deck:
    """Standard 108-card UNO deck."""

    def __init__(self):
        self.cards: List[Card] = []
        self._build()

    def _build(self) -> None:
        colors = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
        for color in colors:
            # One 0 per color
            self.cards.append(Card(color, CardType.NUMBER, 0))
            # Two each of 1-9
            for num in range(1, 10):
                self.cards.append(Card(color, CardType.NUMBER, num))
                self.cards.append(Card(color, CardType.NUMBER, num))
            # Two each of action cards
            for action in (CardType.SKIP, CardType.REVERSE, CardType.DRAW_TWO):
                self.cards.append(Card(color, action))
                self.cards.append(Card(color, action))
        # Wild cards
        for _ in range(4):
            self.cards.append(Card(Color.WILD, CardType.WILD))
            self.cards.append(Card(Color.WILD, CardType.WILD_DRAW_FOUR))

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            raise IndexError("Cannot draw from empty deck")
        return self.cards.pop()

    def draw_many(self, count: int) -> List[Card]:
        drawn = []
        for _ in range(count):
            drawn.append(self.draw())
        return drawn

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def __len__(self) -> int:
        return len(self.cards)
