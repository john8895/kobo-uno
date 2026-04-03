"""Tests for ai.py — AI opponent logic."""

import unittest
from card import Card, CardType, Color, Deck
from game import GameState
from ai import AIPlayer


class TestAIChoosePlay(unittest.TestCase):

    def _make_game(self, hand, top_card=None, current_color=None):
        g = GameState()
        g.num_players = 2
        g.current_player = 1
        g.direction = 1
        top = top_card or Card(Color.RED, CardType.NUMBER, 5)
        g.discard_pile = [top]
        g.current_color = current_color or top.color
        g.deck = Deck()
        g.deck.shuffle()
        g.hands = [
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,  # player 0
            hand,  # AI = player 1
        ]
        return g

    def test_no_playable_returns_none(self):
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.BLUE, CardType.NUMBER, 3),
            Card(Color.GREEN, CardType.NUMBER, 7),
        ])
        result = ai.choose_play(g)
        self.assertIsNone(result)

    def test_prefers_action_over_number(self):
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.RED, CardType.NUMBER, 3),  # idx 0
            Card(Color.RED, CardType.SKIP),        # idx 1
        ])
        idx, color = ai.choose_play(g)
        self.assertEqual(idx, 1)
        self.assertIsNone(color)

    def test_prefers_number_over_wild(self):
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.WILD, CardType.WILD),        # idx 0
            Card(Color.RED, CardType.NUMBER, 3),    # idx 1
        ])
        idx, color = ai.choose_play(g)
        self.assertEqual(idx, 1)
        self.assertIsNone(color)

    def test_prefers_wild_over_wild_draw_four(self):
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.WILD, CardType.WILD_DRAW_FOUR),  # idx 0
            Card(Color.WILD, CardType.WILD),             # idx 1
        ], top_card=Card(Color.BLUE, CardType.NUMBER, 3))
        idx, color = ai.choose_play(g)
        self.assertEqual(idx, 1)
        self.assertIsNotNone(color)

    def test_wild_chooses_most_common_color(self):
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.WILD, CardType.WILD),           # idx 0
            Card(Color.GREEN, CardType.NUMBER, 1),     # idx 1
            Card(Color.GREEN, CardType.NUMBER, 2),     # idx 2
            Card(Color.BLUE, CardType.NUMBER, 3),      # idx 3
        ], top_card=Card(Color.BLUE, CardType.NUMBER, 8))
        idx, color = ai.choose_play(g)
        # Should pick number card first (blue 3 matches color, or green doesn't)
        # Current color is BLUE, so blue 3 at idx 3 matches
        self.assertEqual(idx, 3)

    def test_wild_color_choice(self):
        """When only wild cards are playable, choose most common hand color."""
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.WILD, CardType.WILD),           # idx 0
            Card(Color.GREEN, CardType.NUMBER, 1),     # idx 1
            Card(Color.GREEN, CardType.NUMBER, 2),     # idx 2
            Card(Color.YELLOW, CardType.NUMBER, 3),    # idx 3
        ], top_card=Card(Color.BLUE, CardType.NUMBER, 8),
           current_color=Color.BLUE)
        # No blue cards in hand, only wild is playable
        # Actually green 1, green 2, yellow 3 don't match blue or 8
        # Only wild is playable
        idx, color = ai.choose_play(g)
        self.assertEqual(idx, 0)
        self.assertEqual(color, Color.GREEN)  # 2 green > 1 yellow

    def test_prefers_skip_over_draw_two(self):
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.RED, CardType.DRAW_TWO),  # idx 0
            Card(Color.RED, CardType.SKIP),       # idx 1
        ])
        idx, _ = ai.choose_play(g)
        self.assertEqual(idx, 1)

    def test_color_match_preference_in_numbers(self):
        """Prefer number cards matching current color."""
        ai = AIPlayer(1)
        g = self._make_game([
            Card(Color.BLUE, CardType.NUMBER, 5),  # idx 0: matches number
            Card(Color.RED, CardType.NUMBER, 3),    # idx 1: matches color
        ])
        idx, _ = ai.choose_play(g)
        self.assertEqual(idx, 1)  # prefer color match


class TestAIChallenge(unittest.TestCase):

    def test_challenge_with_few_cards(self):
        ai = AIPlayer(1)
        g = GameState()
        g.hands = [[], [Card(Color.RED, CardType.NUMBER, 1)] * 2]
        self.assertTrue(ai.should_challenge(g))

    def test_no_challenge_with_many_cards(self):
        ai = AIPlayer(1)
        g = GameState()
        g.hands = [[], [Card(Color.RED, CardType.NUMBER, 1)] * 5]
        self.assertFalse(ai.should_challenge(g))


class TestAIChooseColor(unittest.TestCase):

    def test_default_color_when_no_colored_cards(self):
        ai = AIPlayer(1)
        hand = [Card(Color.WILD, CardType.WILD), Card(Color.WILD, CardType.WILD_DRAW_FOUR)]
        color = ai._choose_color(hand, 0)
        self.assertEqual(color, Color.RED)

    def test_picks_most_common(self):
        ai = AIPlayer(1)
        hand = [
            Card(Color.WILD, CardType.WILD),
            Card(Color.BLUE, CardType.NUMBER, 1),
            Card(Color.BLUE, CardType.NUMBER, 2),
            Card(Color.RED, CardType.NUMBER, 3),
        ]
        color = ai._choose_color(hand, 0)
        self.assertEqual(color, Color.BLUE)


if __name__ == "__main__":
    unittest.main()
