""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Battleship CLI
Run this file to play against the AI in your terminal.

@author Jackson McIntyre & Nicolas Serrano
@date March 26, 2026
@version 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import os
import time
from game import Board, Game, BOARD_SIZE, display_both_boards
from ai import AIAgent

# Define 4 different difficulties (Ai methods) that user can choose from
DIFFICULTIES = {
    1: ("Easy",   "Random shooting"), #Shoot random unexplored cells
    2: ("Medium", "Hunt & Target"), #Random until a hit, then systematically finish the ship
    3: ("Hard",   "Parity / Checkerboard"), #Use checkerboard spacing based on smallest remaining ship size
    4: ("Expert", "Probability Heatmap"),  #Build a probability density map and target the hottest cell
}

# Clear the terminal screen 
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# Print header
def print_banner():
    print("=" * 50)
    print("          ⚓  BATTLESHIP  ⚓")
    print("=" * 50)

# Prompt asking user to pick among the 4 difficulties
def pick_difficulty():
    print("\nSelect AI difficulty:\n")
    # Display each option to the console
    for key, (name, desc) in DIFFICULTIES.items():
        print(f"  [{key}] {name} — {desc}")
    print()
    # Loop until user proveides a valid answer (1-4)
    while True:
        choice = input("Enter 1–4: ").strip()
        # Return difficulty chosen if among options
        if choice in ("1", "2", "3", "4"):
            return int(choice)
        print("  Please enter a number between 1 and 4.")


def parse_shot(raw):
    """""""""""""""""""""""""""""""""""""""
    Parse player input into (row, col).
    Accepts formats: 'A5', 'a5', '3 7', '3,7'
    Returns (row, col) or raises ValueError.
    """""""""""""""""""""""""""""""""""""""""""""
    raw = raw.strip().replace(",", " ")

    # Letter-number format e.g. A5
    if raw and raw[0].isalpha():
        row = ord(raw[0].upper()) - ord('A')
        col = int(raw[1:]) - 1
        return row, col

    # Two numbers e.g. '3 7' or '37'
    parts = raw.split()
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    if len(parts) == 1 and len(raw) == 2:
        return int(raw[0]), int(raw[1])

    raise ValueError("Unrecognised format")


def get_player_shot(game):
    # Prompt the player for a valid shot coordinate.
    while True:
        try:
            # Ask user for shot coordenates
            raw = input("\nYour shot (row col): ").strip()
            if raw.lower() in ("q", "quit", "exit"):
                raise SystemExit
            row, col = parse_shot(raw)
            # Handle if coordenates out of bounds
            if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
                print(f"  Out of bounds. Row and col must be 0–{BOARD_SIZE-1}.")
                continue
            # Handle if coordenates were already picked before
            if (row, col) in game.player_agent_shots:
                print("  You already shot there. Try again.")
                continue
            return row, col
        # Dsiplay invalid input message 
        except (ValueError, IndexError):
            print("  Invalid input. Try something like '3 7' ")

# Function to display the result of the shoot from the AI
def format_result(result, shooter="AI"):
    if result == "miss":
        return f"{shooter} missed."
    elif result == "hit":
        return f"{shooter} scored a HIT!"
    elif result.startswith("sunk:"):
        ship = result.split(":")[1]
        return f"{shooter} SUNK the {ship}!"
    return result


def print_ship_status(board, label):
    print(f"\n  {label} ships:")
    for ship in board.ships:
        status = "SUNK" if ship.is_sunk() else f"{len(ship.hits)}/{ship.size} hit"
        marker = "✗" if ship.is_sunk() else "✓"
        print(f"    [{marker}] {ship.name:<12} {status}")


def play():
    # Clear console before printing the game
    clear()
    print_banner()
    # Request for difficulty and asign it to the agent
    difficulty = pick_difficulty()
    diff_name, diff_desc = DIFFICULTIES[difficulty]
    agent = AIAgent(difficulty=difficulty)

    # Initialize the game
    game = Game()
    game.player_agent_shots = set()  # track player's own shots
    game.setup(agent)

    # Print banner, difficulty and introductory message
    clear()
    print_banner()
    print(f"\n  Difficulty: {diff_name} — {diff_desc}")
    print("  Ships placed. Let's go!\n")
    print("  Controls: enter 'row col' (e.g. '0 4')  |  'q' to quit\n")
    time.sleep(1)

    last_player_result = ""
    last_ai_result = ""

    # Loop until the game ends
    while not game.game_over:
        # Clear console and print banner and difficulty again
        print_banner()
        print(f"\n  Difficulty: {diff_name} — {diff_desc}")

        # Show boards
        print()
        display_both_boards(game.player_board, game.ai_board)

        # Display ship status panels
        print_ship_status(game.player_board, "Your")
        print_ship_status(game.ai_board,     "Opponent's")

        # Last round recap
        if last_player_result or last_ai_result:
            print("\n" + "-" * 50)
            if last_player_result:
                print(f"  You:  {last_player_result}")
            if last_ai_result:
                print(f"  AI:   {last_ai_result}")
            print("-" * 50)

        # --- Player turn ---
        row, col = get_player_shot(game)
        game.player_agent_shots.add((row, col))
        result = game.player_shoot(row, col)
        last_player_result = format_result(result, "You")

        if game.game_over:
            break

        # --- AI turn ---
        ai_row, ai_col, ai_result = game.ai_shoot()
        last_ai_result = format_result(ai_result, "AI")

    """ Once game is over """
    # Clear console and print banner and boards
    clear()
    print_banner()
    print()
    display_both_boards(game.player_board, game.ai_board)
    print("\n" + "=" * 50)
    # Display message indicating winner
    if game.winner == "player":
        print("YOU WIN! All enemy ships sunk.")
    else:
        print("GAME OVER. The AI sunk all your ships.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        play()
    except (SystemExit, KeyboardInterrupt):
        print("\n  Game quit. Goodbye!\n")