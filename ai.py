"""AI opponent logic for UNO game."""

from collections import Counter
from typing import Optional, Tuple

from card import Card, CardType, Color
from game import GameState


class AIPlayer:
    """Simple AI that follows a priority-based strategy.

    Strategy:
    1. Play action cards first (Skip > Reverse > Draw Two)
    2. Play number cards matching color/number
    3. Play Wild cards as last resort
    4. Wild: choose the color with most remaining cards in hand
    5. Draw if nothing is playable
    """

    def __init__(self, player_index: int):
        self.player_index = player_index

    def choose_play(self, game: GameState) -> Optional[Tuple[int, Optional[Color]]]:
        """Decide which card to play.

        Returns (card_index, chosen_color) or None to draw.
        """
        hand = game.get_hand(self.player_index)
        playable = game.playable_cards(self.player_index)

        if not playable:
            return None

        # Categorize playable cards
        action_indices = []
        number_indices = []
        wild_indices = []
        wild_draw_four_indices = []

        for idx in playable:
            card = hand[idx]
            if card.card_type == CardType.WILD_DRAW_FOUR:
                wild_draw_four_indices.append(idx)
            elif card.card_type == CardType.WILD:
                wild_indices.append(idx)
            elif card.is_action():
                action_indices.append(idx)
            else:
                number_indices.append(idx)

        # Priority: action > number > wild > wild draw four
        chosen_idx: Optional[int] = None

        if action_indices:
            # Prefer Skip > Draw Two > Reverse
            priority = {CardType.SKIP: 0, CardType.DRAW_TWO: 1, CardType.REVERSE: 2}
            action_indices.sort(key=lambda i: priority.get(hand[i].card_type, 99))
            chosen_idx = action_indices[0]
        elif number_indices:
            # Prefer cards matching current color
            color_match = [i for i in number_indices
                           if hand[i].color == game.current_color]
            chosen_idx = color_match[0] if color_match else number_indices[0]
        elif wild_indices:
            chosen_idx = wild_indices[0]
        elif wild_draw_four_indices:
            chosen_idx = wild_draw_four_indices[0]

        if chosen_idx is None:
            return None

        card = hand[chosen_idx]
        chosen_color = None
        if card.is_wild():
            chosen_color = self._choose_color(hand, chosen_idx)

        return (chosen_idx, chosen_color)

    def should_challenge(self, game: GameState) -> bool:
        """Decide whether to challenge a Wild Draw Four.

        Simple heuristic: challenge if we have few cards (aggressive play).
        """
        hand_size = game.hand_size(self.player_index)
        return hand_size <= 3

    def _choose_color(self, hand: list, exclude_index: int) -> Color:
        """Choose the color with the most cards in remaining hand."""
        color_counts: Counter = Counter()
        for i, card in enumerate(hand):
            if i == exclude_index:
                continue
            if card.color != Color.WILD:
                color_counts[card.color] += 1

        if not color_counts:
            return Color.RED  # default if no colored cards remain

        return color_counts.most_common(1)[0][0]
