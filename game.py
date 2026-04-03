"""Game state management, play validation, and special card effects."""

from typing import List, Optional, Tuple

from card import Card, CardType, Color, Deck


class GameState:
    """Manages the full state of an UNO game."""

    def __init__(self, num_initial_cards: int = 7,
                 enable_challenge: bool = True):
        self.deck = Deck()
        self.deck.shuffle()
        self.discard_pile: List[Card] = []
        self.current_color: Optional[Color] = None
        self.direction: int = 1  # 1 = clockwise, -1 = counter-clockwise
        self.hands: List[List[Card]] = []
        self.current_player: int = 0
        self.num_players: int = 0
        self.num_initial_cards = num_initial_cards
        self.enable_challenge = enable_challenge
        self.winner: Optional[int] = None
        self._pending_draw: int = 0  # cards next player must draw
        self._skip_next: bool = False
        # Track last played card for Wild Draw Four challenge
        self._last_wild_draw_four_player: Optional[int] = None
        self._last_wild_draw_four_hand_snapshot: Optional[List[Card]] = None
        self._last_wild_draw_four_color: Optional[Color] = None  # color before WD4

    def setup(self, num_players: int = 2) -> None:
        """Deal initial hands and flip first discard card."""
        self.num_players = num_players
        self.hands = []
        for _ in range(num_players):
            self.hands.append(self.deck.draw_many(self.num_initial_cards))

        # Flip the first card onto discard pile
        # If it's a Wild Draw Four, reshuffle it back and try again
        while True:
            first_card = self.deck.draw()
            if first_card.card_type == CardType.WILD_DRAW_FOUR:
                self.deck.cards.insert(0, first_card)
                self.deck.shuffle()
                continue
            self.discard_pile.append(first_card)
            break

        # Set current color
        if first_card.is_wild():
            # Wild card as first: current player chooses color (default Red)
            self.current_color = Color.RED
        else:
            self.current_color = first_card.color

        # Apply first card effects
        if first_card.card_type == CardType.SKIP:
            self._skip_next = True
        elif first_card.card_type == CardType.REVERSE:
            if num_players == 2:
                self._skip_next = True
            else:
                self.direction *= -1
        elif first_card.card_type == CardType.DRAW_TWO:
            self._pending_draw = 2
            self._skip_next = True

    def top_card(self) -> Card:
        return self.discard_pile[-1]

    def get_hand(self, player: int) -> List[Card]:
        return self.hands[player]

    def can_play(self, card: Card) -> bool:
        """Check if a card can be legally played on the current discard."""
        if card.card_type == CardType.WILD:
            return True
        if card.card_type == CardType.WILD_DRAW_FOUR:
            return True
        if card.color == self.current_color:
            return True
        top = self.top_card()
        if card.card_type == CardType.NUMBER and top.card_type == CardType.NUMBER:
            if card.number == top.number:
                return True
        if card.card_type != CardType.NUMBER and top.card_type == card.card_type:
            return True
        return False

    def playable_cards(self, player: int) -> List[int]:
        """Return indices of playable cards in a player's hand."""
        return [i for i, c in enumerate(self.hands[player]) if self.can_play(c)]

    def has_matching_color(self, player: int) -> bool:
        """Check if player has a card matching current color (for WD4 challenge)."""
        return any(c.color == self.current_color
                   for c in self.hands[player]
                   if not c.is_wild())

    def play_card(self, player: int, card_index: int,
                  chosen_color: Optional[Color] = None) -> str:
        """Play a card from the player's hand. Returns description of effect."""
        if player != self.current_player:
            raise ValueError("Not this player's turn")

        card = self.hands[player][card_index]
        if not self.can_play(card):
            raise ValueError(f"Cannot play {card}")

        if card.is_wild() and chosen_color is None:
            raise ValueError("Must choose a color for wild cards")
        if card.is_wild() and chosen_color == Color.WILD:
            raise ValueError("Cannot choose WILD as color")

        # Save color before WD4 changes it (for challenge)
        color_before_play = self.current_color

        # Remove from hand
        self.hands[player].pop(card_index)
        self.discard_pile.append(card)

        # Check win
        if len(self.hands[player]) == 0:
            self.winner = player
            return f"Player {player} wins!"

        # Set color
        if card.is_wild():
            self.current_color = chosen_color
        else:
            self.current_color = card.color

        # Apply effects
        effect = self._apply_card_effect(card, player, color_before_play)

        # Advance turn
        self._advance_turn()

        return effect

    def draw_card(self, player: int) -> Card:
        """Player draws a card from the deck."""
        if player != self.current_player:
            raise ValueError("Not this player's turn")
        self._refill_deck_if_needed()
        card = self.deck.draw()
        self.hands[player].append(card)
        return card

    def pass_turn(self, player: int) -> None:
        """Player passes after drawing."""
        if player != self.current_player:
            raise ValueError("Not this player's turn")
        self._advance_turn()

    def execute_pending_effects(self) -> int:
        """Execute any pending draw/skip effects at start of turn.

        Returns number of cards drawn (0 if no pending draw).
        """
        drawn = 0
        if self._pending_draw > 0:
            self._refill_deck_if_needed()
            for _ in range(self._pending_draw):
                if self.deck.is_empty():
                    self._refill_deck_if_needed()
                    if self.deck.is_empty():
                        break
                card = self.deck.draw()
                self.hands[self.current_player].append(card)
                drawn += 1
            self._pending_draw = 0

        if self._skip_next:
            self._skip_next = False
            self._advance_turn()

        return drawn

    def challenge_wild_draw_four(self, challenger: int) -> Tuple[bool, int]:
        """Challenge a Wild Draw Four play.

        Returns (challenge_succeeded, cards_drawn_by_loser).
        The challenger is the current player who was targeted by WD4.
        """
        if not self.enable_challenge:
            raise ValueError("Challenge is disabled")
        if self._last_wild_draw_four_player is None:
            raise ValueError("No Wild Draw Four to challenge")

        wd4_player = self._last_wild_draw_four_player
        snapshot = self._last_wild_draw_four_hand_snapshot
        original_color = self._last_wild_draw_four_color

        # Challenge succeeds if the WD4 player had a matching color card
        # (matching the color that was active BEFORE the WD4 was played)
        had_matching = any(c.color == original_color
                          for c in snapshot
                          if not c.is_wild())

        # Clear challenge state
        self._last_wild_draw_four_player = None
        self._last_wild_draw_four_hand_snapshot = None
        self._last_wild_draw_four_color = None

        if had_matching:
            # Challenge succeeded: WD4 player draws 4
            self._refill_deck_if_needed()
            cards_drawn = 0
            for _ in range(4):
                if self.deck.is_empty():
                    self._refill_deck_if_needed()
                    if self.deck.is_empty():
                        break
                self.hands[wd4_player].append(self.deck.draw())
                cards_drawn += 1
            self._pending_draw = 0
            self._skip_next = False
            return (True, cards_drawn)
        else:
            # Challenge failed: challenger draws 6 (4 + 2 penalty)
            self._refill_deck_if_needed()
            cards_drawn = 0
            for _ in range(6):
                if self.deck.is_empty():
                    self._refill_deck_if_needed()
                    if self.deck.is_empty():
                        break
                self.hands[challenger].append(self.deck.draw())
                cards_drawn += 1
            self._pending_draw = 0
            self._skip_next = True
            return (False, cards_drawn)

    def _apply_card_effect(self, card: Card, player: int,
                            color_before_play: Optional[Color] = None) -> str:
        if card.card_type == CardType.SKIP:
            self._skip_next = True
            return "Next player is skipped!"
        elif card.card_type == CardType.REVERSE:
            self.direction *= -1
            if self.num_players == 2:
                self._skip_next = True
            return "Direction reversed!"
        elif card.card_type == CardType.DRAW_TWO:
            self._pending_draw = 2
            self._skip_next = True
            return "Next player draws 2 and is skipped!"
        elif card.card_type == CardType.WILD:
            return f"Color changed to {self.current_color.value}!"
        elif card.card_type == CardType.WILD_DRAW_FOUR:
            self._pending_draw = 4
            self._skip_next = True
            # Save state for challenge
            self._last_wild_draw_four_player = player
            snapshot = list(self.hands[player])
            self._last_wild_draw_four_hand_snapshot = snapshot
            self._last_wild_draw_four_color = color_before_play
            return f"Next player draws 4! Color changed to {self.current_color.value}!"
        else:
            return ""

    def _advance_turn(self) -> None:
        self.current_player = (self.current_player + self.direction) % self.num_players

    def _refill_deck_if_needed(self) -> None:
        """Reshuffle discard pile into deck when deck is empty."""
        if not self.deck.is_empty():
            return
        if len(self.discard_pile) <= 1:
            return
        top = self.discard_pile.pop()
        self.deck.cards = self.discard_pile
        self.discard_pile = [top]
        self.deck.shuffle()

    def is_over(self) -> bool:
        return self.winner is not None

    def hand_size(self, player: int) -> int:
        return len(self.hands[player])

    def is_uno(self, player: int) -> bool:
        return len(self.hands[player]) == 1
