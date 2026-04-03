"""Tests for game.py — GameState, play validation, and special card effects."""

import unittest
from card import Card, CardType, Color, Deck
from game import GameState


class TestGameSetup(unittest.TestCase):

    def test_setup_deals_correct_hands(self):
        g = GameState()
        g.setup(2)
        self.assertEqual(len(g.hands), 2)
        self.assertEqual(len(g.hands[0]), 7)
        self.assertEqual(len(g.hands[1]), 7)

    def test_setup_has_discard_pile(self):
        g = GameState()
        g.setup(2)
        self.assertEqual(len(g.discard_pile), 1)
        self.assertIsNotNone(g.current_color)
        self.assertNotEqual(g.current_color, Color.WILD)

    def test_setup_first_card_not_wild_draw_four(self):
        """First discard card should never be Wild Draw Four."""
        for _ in range(50):
            g = GameState()
            g.setup(2)
            self.assertNotEqual(g.top_card().card_type, CardType.WILD_DRAW_FOUR)

    def test_deck_size_after_setup(self):
        g = GameState()
        g.setup(2)
        # 108 - 14 dealt - 1 discard = 93
        self.assertEqual(len(g.deck) + len(g.discard_pile) +
                         sum(len(h) for h in g.hands), 108)


class TestCanPlay(unittest.TestCase):

    def _make_game(self, top_card, current_color=None):
        g = GameState()
        g.num_players = 2
        g.hands = [[], []]
        g.discard_pile = [top_card]
        g.current_color = current_color or top_card.color
        return g

    def test_matching_color(self):
        g = self._make_game(Card(Color.RED, CardType.NUMBER, 5))
        self.assertTrue(g.can_play(Card(Color.RED, CardType.NUMBER, 3)))

    def test_matching_number(self):
        g = self._make_game(Card(Color.RED, CardType.NUMBER, 5))
        self.assertTrue(g.can_play(Card(Color.BLUE, CardType.NUMBER, 5)))

    def test_no_match(self):
        g = self._make_game(Card(Color.RED, CardType.NUMBER, 5))
        self.assertFalse(g.can_play(Card(Color.BLUE, CardType.NUMBER, 3)))

    def test_matching_action_type(self):
        g = self._make_game(Card(Color.RED, CardType.SKIP))
        self.assertTrue(g.can_play(Card(Color.BLUE, CardType.SKIP)))

    def test_wild_always_playable(self):
        g = self._make_game(Card(Color.RED, CardType.NUMBER, 5))
        self.assertTrue(g.can_play(Card(Color.WILD, CardType.WILD)))

    def test_wild_draw_four_always_playable(self):
        g = self._make_game(Card(Color.RED, CardType.NUMBER, 5))
        self.assertTrue(g.can_play(Card(Color.WILD, CardType.WILD_DRAW_FOUR)))

    def test_color_match_uses_current_color_not_card_color(self):
        """After a wild, current_color may differ from top card color."""
        g = self._make_game(Card(Color.WILD, CardType.WILD), current_color=Color.BLUE)
        self.assertTrue(g.can_play(Card(Color.BLUE, CardType.NUMBER, 1)))
        self.assertFalse(g.can_play(Card(Color.RED, CardType.NUMBER, 1)))


class TestPlayCard(unittest.TestCase):

    def _make_game_with_hands(self):
        g = GameState()
        g.num_players = 2
        g.current_player = 0
        g.direction = 1
        g.discard_pile = [Card(Color.RED, CardType.NUMBER, 5)]
        g.current_color = Color.RED
        g.deck = Deck()
        g.deck.shuffle()
        return g

    def test_play_number_card(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.RED, CardType.NUMBER, 3)],
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
        ]
        result = g.play_card(0, 0, None)
        self.assertIn("wins", result)
        self.assertEqual(g.winner, 0)

    def test_play_wrong_turn_raises(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.RED, CardType.NUMBER, 3)] * 3,
            [Card(Color.RED, CardType.NUMBER, 1)] * 3,
        ]
        with self.assertRaises(ValueError):
            g.play_card(1, 0, None)

    def test_play_illegal_card_raises(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.BLUE, CardType.NUMBER, 3)] * 3,
            [Card(Color.RED, CardType.NUMBER, 1)] * 3,
        ]
        with self.assertRaises(ValueError):
            g.play_card(0, 0, None)

    def test_play_wild_requires_color(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.WILD, CardType.WILD)] * 2,
            [Card(Color.RED, CardType.NUMBER, 1)] * 3,
        ]
        with self.assertRaises(ValueError):
            g.play_card(0, 0, None)

    def test_play_wild_sets_color(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.WILD, CardType.WILD)] * 2,
            [Card(Color.RED, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, Color.GREEN)
        self.assertEqual(g.current_color, Color.GREEN)

    def test_play_wild_rejects_wild_color(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.WILD, CardType.WILD)] * 2,
            [Card(Color.RED, CardType.NUMBER, 1)] * 3,
        ]
        with self.assertRaises(ValueError):
            g.play_card(0, 0, Color.WILD)

    def test_turn_advances(self):
        g = self._make_game_with_hands()
        g.hands = [
            [Card(Color.RED, CardType.NUMBER, 3)] * 3,
            [Card(Color.RED, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, None)
        self.assertEqual(g.current_player, 1)


class TestSpecialCards(unittest.TestCase):

    def _make_game(self):
        g = GameState()
        g.num_players = 2
        g.current_player = 0
        g.direction = 1
        g.discard_pile = [Card(Color.RED, CardType.NUMBER, 5)]
        g.current_color = Color.RED
        g.deck = Deck()
        g.deck.shuffle()
        return g

    def test_skip_effect(self):
        g = self._make_game()
        g.hands = [
            [Card(Color.RED, CardType.SKIP)] * 2,
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, None)
        # Skip sets _skip_next, then advances turn to 1
        # execute_pending_effects on player 1's turn will skip them
        self.assertEqual(g.current_player, 1)
        drawn = g.execute_pending_effects()
        self.assertEqual(drawn, 0)
        # After skip, turn goes back to 0
        self.assertEqual(g.current_player, 0)

    def test_reverse_in_2_player(self):
        """In 2-player, reverse acts like skip."""
        g = self._make_game()
        g.hands = [
            [Card(Color.RED, CardType.REVERSE)] * 2,
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, None)
        self.assertEqual(g.current_player, 1)
        g.execute_pending_effects()
        # Should skip back to 0
        self.assertEqual(g.current_player, 0)

    def test_draw_two_effect(self):
        g = self._make_game()
        g.hands = [
            [Card(Color.RED, CardType.DRAW_TWO)] * 2,
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, None)
        self.assertEqual(g.current_player, 1)
        initial_hand = len(g.hands[1])
        drawn = g.execute_pending_effects()
        self.assertEqual(drawn, 2)
        self.assertEqual(len(g.hands[1]), initial_hand + 2)
        # Also skipped
        self.assertEqual(g.current_player, 0)

    def test_wild_draw_four_effect(self):
        g = self._make_game()
        g.hands = [
            [Card(Color.WILD, CardType.WILD_DRAW_FOUR)] * 2,
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, Color.BLUE)
        self.assertEqual(g.current_player, 1)
        initial_hand = len(g.hands[1])
        drawn = g.execute_pending_effects()
        self.assertEqual(drawn, 4)
        self.assertEqual(len(g.hands[1]), initial_hand + 4)
        self.assertEqual(g.current_player, 0)


class TestChallenge(unittest.TestCase):

    def _make_game_for_challenge(self, player0_had_matching: bool):
        g = GameState(enable_challenge=True)
        g.num_players = 2
        g.current_player = 0
        g.direction = 1
        g.discard_pile = [Card(Color.RED, CardType.NUMBER, 5)]
        g.current_color = Color.RED
        g.deck = Deck()
        g.deck.shuffle()

        if player0_had_matching:
            # Player 0 has a red card + WD4
            g.hands = [
                [Card(Color.RED, CardType.NUMBER, 3),
                 Card(Color.WILD, CardType.WILD_DRAW_FOUR)],
                [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
            ]
        else:
            # Player 0 has no matching color + WD4
            g.hands = [
                [Card(Color.BLUE, CardType.NUMBER, 3),
                 Card(Color.WILD, CardType.WILD_DRAW_FOUR)],
                [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
            ]

        # Play the WD4
        g.play_card(0, 1, Color.BLUE)
        return g

    def test_challenge_success(self):
        """Challenge succeeds when WD4 player had matching color."""
        g = self._make_game_for_challenge(player0_had_matching=True)
        # Player 1 challenges
        success, drawn = g.challenge_wild_draw_four(1)
        self.assertTrue(success)
        self.assertEqual(drawn, 4)
        # Player 0 got 4 extra cards (had 1 remaining + 4 drawn)
        self.assertEqual(len(g.hands[0]), 5)

    def test_challenge_failure(self):
        """Challenge fails when WD4 player had no matching color."""
        g = self._make_game_for_challenge(player0_had_matching=False)
        initial_p1 = len(g.hands[1])
        success, drawn = g.challenge_wild_draw_four(1)
        self.assertFalse(success)
        self.assertEqual(drawn, 6)
        self.assertEqual(len(g.hands[1]), initial_p1 + 6)

    def test_challenge_disabled(self):
        g = GameState(enable_challenge=False)
        g.num_players = 2
        g.current_player = 0
        g.direction = 1
        g.discard_pile = [Card(Color.RED, CardType.NUMBER, 5)]
        g.current_color = Color.RED
        g.deck = Deck()
        g.deck.shuffle()
        g.hands = [
            [Card(Color.WILD, CardType.WILD_DRAW_FOUR)] * 2,
            [Card(Color.BLUE, CardType.NUMBER, 1)] * 3,
        ]
        g.play_card(0, 0, Color.BLUE)
        with self.assertRaises(ValueError):
            g.challenge_wild_draw_four(1)


class TestDrawAndPass(unittest.TestCase):

    def test_draw_card(self):
        g = GameState()
        g.setup(2)
        player = g.current_player
        initial = len(g.hands[player])
        g.draw_card(player)
        self.assertEqual(len(g.hands[player]), initial + 1)

    def test_pass_turn(self):
        g = GameState()
        g.setup(2)
        g.current_player = 0
        # Clear any pending effects first
        g._skip_next = False
        g._pending_draw = 0
        g.draw_card(0)
        g.pass_turn(0)
        self.assertEqual(g.current_player, 1)

    def test_deck_refill(self):
        """When deck runs out, discard pile is reshuffled into deck."""
        g = GameState()
        g.num_players = 2
        g.current_player = 0
        g.direction = 1
        g.hands = [[Card(Color.RED, CardType.NUMBER, 1)] * 3,
                    [Card(Color.BLUE, CardType.NUMBER, 2)] * 3]
        g.discard_pile = [Card(Color.RED, CardType.NUMBER, i) for i in range(1, 8)]
        g.current_color = Color.RED
        g.deck = Deck()
        g.deck.cards.clear()  # Empty deck

        card = g.draw_card(0)
        # Deck was refilled from discard pile
        self.assertIsInstance(card, Card)
        # Discard pile should only have the top card
        self.assertEqual(len(g.discard_pile), 1)


class TestPlayableCards(unittest.TestCase):

    def test_playable_cards(self):
        g = GameState()
        g.num_players = 2
        g.discard_pile = [Card(Color.RED, CardType.NUMBER, 5)]
        g.current_color = Color.RED
        g.hands = [
            [Card(Color.RED, CardType.NUMBER, 3),   # playable (color)
             Card(Color.BLUE, CardType.NUMBER, 5),   # playable (number)
             Card(Color.BLUE, CardType.NUMBER, 3),   # not playable
             Card(Color.WILD, CardType.WILD)],        # playable (wild)
            [],
        ]
        playable = g.playable_cards(0)
        self.assertEqual(playable, [0, 1, 3])


class TestUnoStatus(unittest.TestCase):

    def test_is_uno(self):
        g = GameState()
        g.hands = [[Card(Color.RED, CardType.NUMBER, 1)]]
        self.assertTrue(g.is_uno(0))

    def test_not_uno(self):
        g = GameState()
        g.hands = [[Card(Color.RED, CardType.NUMBER, 1)] * 2]
        self.assertFalse(g.is_uno(0))


if __name__ == "__main__":
    unittest.main()
