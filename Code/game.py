""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Battleship Game Engine
Supports 4 difficulty levels, each using a progressively smarter strategy.

Handles board state, ship, placement, and shot logic.

@author Jackson McIntyre & Nicolas Serrano
@date March 26, 2026
@version 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""



import random

BOARD_SIZE = 10

SHIPS = {
    "Carrier":    5,
    "Battleship": 4,
    "Cruiser":    3,
    "Submarine":  3,
    "Destroyer":  2,
}

# Cell states
EMPTY = "."
SHIP  = "S"
HIT   = "X"
MISS  = "O"


class Ship:
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.cells = []  # list of (row, col) tuples
        self.hits = set()

    def place(self, cells):
        self.cells = cells
        self.hits = set()

    def receive_hit(self, row, col):
        self.hits.add((row, col))

    def is_sunk(self):
        return len(self.hits) == self.size

    def __repr__(self):
        return f"Ship({self.name}, size={self.size}, sunk={self.is_sunk()})"


class Board:
    def __init__(self):
        self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ships = []

    def in_bounds(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def can_place(self, cells):
        """Check if all cells are in bounds and unoccupied."""
        for r, c in cells:
            if not self.in_bounds(r, c):
                return False
            if self.grid[r][c] != EMPTY:
                return False
        return True

    def place_ship(self, ship, row, col, horizontal=True):
        """
        Place a ship on the board.
        Returns True if successful, False if placement is invalid.
        """
        if horizontal:
            cells = [(row, col + i) for i in range(ship.size)]
        else:
            cells = [(row + i, col) for i in range(ship.size)]

        if not self.can_place(cells):
            return False

        ship.place(cells)
        for r, c in cells:
            self.grid[r][c] = SHIP
        self.ships.append(ship)
        return True

    def place_ships_randomly(self):
        """Place all standard ships in random valid positions."""
        self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ships = []

        for name, size in SHIPS.items():
            ship = Ship(name, size)
            placed = False
            while not placed:
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.randint(0, BOARD_SIZE - 1)
                    col = random.randint(0, BOARD_SIZE - size)
                else:
                    row = random.randint(0, BOARD_SIZE - size)
                    col = random.randint(0, BOARD_SIZE - 1)
                placed = self.place_ship(ship, row, col, horizontal)

    def receive_shot(self, row, col):
        """
        Process an incoming shot at (row, col).
        Returns: "hit", "miss", "already_shot", or "sunk:<ship_name>"
        """
        if not self.in_bounds(row, col):
            raise ValueError(f"Shot ({row}, {col}) is out of bounds.")

        cell = self.grid[row][col]

        if cell in (HIT, MISS):
            return "already_shot"

        if cell == SHIP:
            self.grid[row][col] = HIT
            for ship in self.ships:
                if (row, col) in ship.cells:
                    ship.receive_hit(row, col)
                    if ship.is_sunk():
                        return f"sunk:{ship.name}"
            return "hit"

        # cell == EMPTY
        self.grid[row][col] = MISS
        return "miss"

    def all_ships_sunk(self):
        return all(ship.is_sunk() for ship in self.ships)

    def display(self, hide_ships=False):
        """
        Print the board. Set hide_ships=True to show opponent's view
        (ships hidden, only hits and misses visible).
        """
        col_labels = "  " + " ".join(str(i) for i in range(BOARD_SIZE))
        print(col_labels)
        for r, row in enumerate(self.grid):
            cells = []
            for cell in row:
                if hide_ships and cell == SHIP:
                    cells.append(EMPTY)
                else:
                    cells.append(cell)
            print(f"{r} " + " ".join(cells))

    def get_display_rows(self, hide_ships=False):
        """Return board rows as a list of strings (for side-by-side rendering)."""
        rows = []
        for r, row in enumerate(self.grid):
            cells = []
            for cell in row:
                if hide_ships and cell == SHIP:
                    cells.append(EMPTY)
                else:
                    cells.append(cell)
            rows.append(f"{r} " + " ".join(cells))
        return rows


def display_both_boards(player_board, ai_board):
    """Display the player's board and the opponent's board side by side."""
    header     = "  " + " ".join(str(i) for i in range(BOARD_SIZE))
    gap = "      "

    print(f"  YOUR BOARD{gap}        OPPONENT'S BOARD")
    print(f"{header}{gap}  {header}")

    player_rows = player_board.get_display_rows(hide_ships=False)
    ai_rows     = ai_board.get_display_rows(hide_ships=True)

    for p_row, a_row in zip(player_rows, ai_rows):
        print(f"{p_row}{gap}  {a_row}")


class Game:
    def __init__(self):
        self.player_board = Board()
        self.ai_board = Board()
        self.turn = 0  # 0 = player, 1 = AI
        self.game_over = False
        self.winner = None

    def setup(self, ai_agent):
        """Set up both boards. Player places manually or randomly."""
        self.ai_agent = ai_agent

        # Place player ships randomly for now
        self.player_board.place_ships_randomly()

        # Place AI ships randomly
        self.ai_board.place_ships_randomly()
        self.ai_agent.set_board(self.ai_board)

    def player_shoot(self, row, col):
        """Process a player shot against the AI board."""
        result = self.ai_board.receive_shot(row, col)
        if self.ai_board.all_ships_sunk():
            self.game_over = True
            self.winner = "player"
        return result

    def ai_shoot(self):
        """Let the AI agent pick and fire a shot at the player board."""
        row, col = self.ai_agent.choose_shot(self.player_board)
        result = self.player_board.receive_shot(row, col)
        self.ai_agent.record_result(row, col, result)
        if self.player_board.all_ships_sunk():
            self.game_over = True
            self.winner = "ai"
        return row, col, result


if __name__ == "__main__":
    player_board = Board()
    ai_board = Board()
    player_board.place_ships_randomly()
    ai_board.place_ships_randomly()

    all_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)]
    for r, c in random.sample(all_cells, 15):
        player_board.receive_shot(r, c)
    for r, c in random.sample(all_cells, 15):
        ai_board.receive_shot(r, c)

    print("=== Game State ===")
    display_both_boards(player_board, ai_board)