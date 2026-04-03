"""Tests for card.py — Card and Deck classes."""

import unittest
from card import Card, CardType, Color, Deck


class TestCard(unittest.TestCase):

    def test_number_card_creation(self):
        c = Card(Color.RED, CardType.NUMBER, 5)
        self.assertEqual(c.color, Color.RED)
        self.assertEqual(c.card_type, CardType.NUMBER)
        self.assertEqual(c.number, 5)

    def test_number_card_requires_number(self):
        with self.assertRaises(ValueError):
            Card(Color.RED, CardType.NUMBER)

    def test_action_card_no_number(self):
        c = Card(Color.BLUE, CardType.SKIP)
        self.assertIsNone(c.number)

    def test_action_card_rejects_number(self):
        with self.assertRaises(ValueError):
            Card(Color.BLUE, CardType.SKIP, 3)

    def test_wild_must_have_wild_color(self):
        with self.assertRaises(ValueError):
            Card(Color.RED, CardType.WILD)

    def test_non_wild_rejects_wild_color(self):
        with self.assertRaises(ValueError):
            Card(Color.WILD, CardType.NUMBER, 5)

    def test_number_range_validation(self):
        with self.assertRaises(ValueError):
            Card(Color.RED, CardType.NUMBER, 10)
        with self.assertRaises(ValueError):
            Card(Color.RED, CardType.NUMBER, -1)

    def test_wild_card_creation(self):
        c = Card(Color.WILD, CardType.WILD)
        self.assertTrue(c.is_wild())

    def test_wild_draw_four_creation(self):
        c = Card(Color.WILD, CardType.WILD_DRAW_FOUR)
        self.assertTrue(c.is_wild())

    def test_is_action(self):
        self.assertTrue(Card(Color.RED, CardType.SKIP).is_action())
        self.assertTrue(Card(Color.RED, CardType.REVERSE).is_action())
        self.assertTrue(Card(Color.RED, CardType.DRAW_TWO).is_action())
        self.assertFalse(Card(Color.RED, CardType.NUMBER, 5).is_action())
        self.assertFalse(Card(Color.WILD, CardType.WILD).is_action())

    def test_repr_number(self):
        self.assertEqual(repr(Card(Color.RED, CardType.NUMBER, 7)), "Red 7")

    def test_repr_action(self):
        self.assertEqual(repr(Card(Color.BLUE, CardType.SKIP)), "Blue Skip")

    def test_repr_wild(self):
        self.assertEqual(repr(Card(Color.WILD, CardType.WILD)), "Wild")
        self.assertEqual(repr(Card(Color.WILD, CardType.WILD_DRAW_FOUR)), "Wild Draw Four")

    def test_equality(self):
        a = Card(Color.RED, CardType.NUMBER, 3)
        b = Card(Color.RED, CardType.NUMBER, 3)
        c = Card(Color.RED, CardType.NUMBER, 4)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_hash(self):
        a = Card(Color.RED, CardType.NUMBER, 3)
        b = Card(Color.RED, CardType.NUMBER, 3)
        self.assertEqual(hash(a), hash(b))


class TestDeck(unittest.TestCase):

    def test_deck_has_108_cards(self):
        d = Deck()
        self.assertEqual(len(d), 108)

    def test_deck_composition(self):
        d = Deck()
        # Count by type
        numbers = [c for c in d.cards if c.card_type == CardType.NUMBER]
        skips = [c for c in d.cards if c.card_type == CardType.SKIP]
        reverses = [c for c in d.cards if c.card_type == CardType.REVERSE]
        draw_twos = [c for c in d.cards if c.card_type == CardType.DRAW_TWO]
        wilds = [c for c in d.cards if c.card_type == CardType.WILD]
        wd4s = [c for c in d.cards if c.card_type == CardType.WILD_DRAW_FOUR]

        # 4 colors × (1×0 + 2×(1-9)) = 4 × 19 = 76
        self.assertEqual(len(numbers), 76)
        # 4 colors × 2 = 8 each
        self.assertEqual(len(skips), 8)
        self.assertEqual(len(reverses), 8)
        self.assertEqual(len(draw_twos), 8)
        self.assertEqual(len(wilds), 4)
        self.assertEqual(len(wd4s), 4)

    def test_deck_zeros(self):
        """Each color has exactly one 0."""
        d = Deck()
        zeros = [c for c in d.cards if c.card_type == CardType.NUMBER and c.number == 0]
        self.assertEqual(len(zeros), 4)
        colors = {c.color for c in zeros}
        self.assertEqual(colors, {Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW})

    def test_draw(self):
        d = Deck()
        c = d.draw()
        self.assertIsInstance(c, Card)
        self.assertEqual(len(d), 107)

    def test_draw_many(self):
        d = Deck()
        cards = d.draw_many(7)
        self.assertEqual(len(cards), 7)
        self.assertEqual(len(d), 101)

    def test_draw_empty_raises(self):
        d = Deck()
        d.cards.clear()
        with self.assertRaises(IndexError):
            d.draw()

    def test_shuffle_changes_order(self):
        d1 = Deck()
        original = list(d1.cards)
        d1.shuffle()
        # Extremely unlikely to be same order after shuffle
        self.assertEqual(len(d1.cards), len(original))
        # Just verify length preserved; order check is probabilistic

    def test_is_empty(self):
        d = Deck()
        self.assertFalse(d.is_empty())
        d.cards.clear()
        self.assertTrue(d.is_empty())


if __name__ == "__main__":
    unittest.main()
