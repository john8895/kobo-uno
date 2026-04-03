"""CLI entry point for UNO game. I/O only — no game logic here."""

import sys
from typing import Optional

from card import Color, CardType
from game import GameState
from ai import AIPlayer


def display_state(game: GameState, player: int) -> None:
    """Display current game state to the human player."""
    print("\n" + "=" * 50)
    print(f"  Current color: {game.current_color.value}")
    print(f"  Top card: {game.top_card()}")
    print(f"  AI hand size: {game.hand_size(1)}")
    if game.is_uno(1):
        print("  *** AI calls UNO! ***")
    print(f"  Deck remaining: {len(game.deck)}")
    print("-" * 50)
    hand = game.get_hand(player)
    print("  Your hand:")
    for i, card in enumerate(hand):
        playable = game.can_play(card)
        marker = " *" if playable else ""
        print(f"    [{i}] {card}{marker}")
    if game.is_uno(player):
        print("  *** UNO! ***")
    print("=" * 50)


def choose_color_input() -> Color:
    """Prompt user to choose a color for wild cards."""
    colors = {"r": Color.RED, "b": Color.BLUE, "g": Color.GREEN, "y": Color.YELLOW}
    while True:
        choice = input("  Choose color (R/B/G/Y): ").strip().lower()
        if choice in colors:
            return colors[choice]
        print("  Invalid choice. Enter R, B, G, or Y.")


def prompt_challenge() -> bool:
    """Ask if the player wants to challenge a Wild Draw Four."""
    while True:
        choice = input("  Challenge Wild Draw Four? (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("  Enter y or n.")


def human_turn(game: GameState) -> None:
    """Handle a human player's turn (player 0)."""
    player = 0

    # Execute pending effects (draw 2/4, skip)
    drawn = game.execute_pending_effects()
    if drawn > 0:
        print(f"\n  You drew {drawn} card(s) and your turn is skipped.")
        return
    if game.current_player != player:
        # Was skipped
        return

    display_state(game, player)
    playable = game.playable_cards(player)

    while True:
        if playable:
            action = input("  Play card index or (d)raw: ").strip().lower()
        else:
            print("  No playable cards.")
            action = input("  Press Enter to draw: ").strip().lower()
            if action == "" or action == "d":
                action = "d"

        if action == "d":
            card = game.draw_card(player)
            print(f"  Drew: {card}")
            if game.can_play(card):
                play_it = input("  Play it? (y/n): ").strip().lower()
                if play_it in ("y", "yes"):
                    idx = len(game.get_hand(player)) - 1
                    chosen_color = None
                    if card.is_wild():
                        chosen_color = choose_color_input()
                    effect = game.play_card(player, idx, chosen_color)
                    print(f"  {effect}")
                    return
            game.pass_turn(player)
            return

        try:
            idx = int(action)
        except ValueError:
            print("  Invalid input.")
            continue

        hand = game.get_hand(player)
        if idx < 0 or idx >= len(hand):
            print("  Index out of range.")
            continue

        if idx not in playable:
            print("  That card can't be played.")
            continue

        card = hand[idx]
        chosen_color = None
        if card.is_wild():
            chosen_color = choose_color_input()

        effect = game.play_card(player, idx, chosen_color)
        print(f"  {effect}")
        return


def ai_turn(game: GameState, ai: AIPlayer) -> None:
    """Handle AI player's turn."""
    player = ai.player_index

    # Check for Wild Draw Four challenge opportunity
    if (game.enable_challenge
            and game._last_wild_draw_four_player is not None
            and game._last_wild_draw_four_player != player):
        if ai.should_challenge(game):
            print("\n  AI challenges the Wild Draw Four!")
            success, drawn = game.challenge_wild_draw_four(player)
            if success:
                print(f"  Challenge succeeded! Player 0 draws {drawn} cards.")
            else:
                print(f"  Challenge failed! AI draws {drawn} cards.")
            return

    # Execute pending effects
    drawn = game.execute_pending_effects()
    if drawn > 0:
        print(f"\n  AI drew {drawn} card(s) and is skipped.")
        return
    if game.current_player != player:
        return

    print(f"\n  AI's turn... (hand size: {game.hand_size(player)})")

    play = ai.choose_play(game)
    if play is None:
        card = game.draw_card(player)
        print(f"  AI draws a card.")
        if game.can_play(card):
            idx = len(game.get_hand(player)) - 1
            chosen_color = ai._choose_color(game.get_hand(player), idx) if card.is_wild() else None
            effect = game.play_card(player, idx, chosen_color)
            print(f"  AI plays: {card} — {effect}")
        else:
            game.pass_turn(player)
            print("  AI passes.")
    else:
        idx, chosen_color = play
        card = game.get_hand(player)[idx]
        effect = game.play_card(player, idx, chosen_color)
        print(f"  AI plays: {card} — {effect}")

    if game.is_uno(player):
        print("  *** AI calls UNO! ***")


def main() -> None:
    """Main game loop."""
    print("=" * 50)
    print("         UNO — Player vs AI")
    print("=" * 50)

    challenge_flag = "--no-challenge" not in sys.argv
    game = GameState(enable_challenge=challenge_flag)
    game.setup(num_players=2)
    ai = AIPlayer(player_index=1)

    while not game.is_over():
        if game.current_player == 0:
            human_turn(game)
        else:
            ai_turn(game, ai)

    print("\n" + "=" * 50)
    if game.winner == 0:
        print("  Congratulations! You win!")
    else:
        print("  AI wins! Better luck next time.")
    print("=" * 50)


if __name__ == "__main__":
    main()
