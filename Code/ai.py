""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Super Intelligent and Smart Battleship AI Agent (SISBAI)
Supports 4 difficulty levels, each using a progressively smarter strategy.

Difficulty 1 - Random:        Shoot random unexplored cells.
Difficulty 2 - Hunt & Target: Random until a hit, then systematically finish the ship.
Difficulty 3 - Parity:        Use checkerboard spacing based on smallest remaining ship size.
Difficulty 4 - Heatmap:       Build a probability density map and target the hottest cell.

@author Jackson McIntyre & Nicolas Serrano
@date March 26, 2026
@version 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

import random
from game import BOARD_SIZE, SHIPS


class AIAgent:
    def __init__(self, difficulty=1):
        '''
        Create a new AI agent with the selected difficulty level
        '''
        if difficulty not in (1, 2, 3, 4):
            raise ValueError("Difficulty must be 1, 2, 3, or 4.")
        self.difficulty = difficulty
        self.reset()

    def reset(self):
        """
        Reset all internal state for a new game.
        Agent stores every shot it's fired, which shots were hits and misses, hunt/target mode state, and remaining ship sizes for smarter search strats
        """
        self.shots_fired = set()
        self.hits = set()
        self.misses = set()

        #Hunt & Target (difficulty 2+)
        #Hunt - broadly searches for a new ship
        #Target - focus around a known hit to finish off that ship
        self.mode = "hunt"          # "hunt" or "target"
        self.target_queue = []      # cells to probe around a hit

        #Difficulty 3 uses remaining ships sizes to improve search spacing. Tracks which ship sizes are still alive on the opponent's board.
        self.remaining_ship_sizes = sorted(SHIPS.values())  # [2, 3, 3, 4, 5]

        #Refernce to this AI's own board, assigned via Game.setup
        self._board = None

    def set_board(self, board):
        """Give the agent a reference to its OWN board (not the opponent's). This is NOT the opponents board."""
        self._board = board

#PUBLIC INTERFACE

    def choose_shot(self, opponent_board):
        '''
        Choose and return the next shot as a (row, col) tuple.
        The strategy used depends on the difficulty.
        '''

        
        if self.difficulty == 1:
            return self._random_shot()
        elif self.difficulty == 2:
            return self._hunt_and_target_shot()
        elif self.difficulty == 3:
            return self._parity_shot()
        else:
            return self._heatmap_shot(opponent_board)

    def record_result(self, row, col, result):
        '''
        Record the outcome of a shot after the game engine evaluates it.
        Updates the AI memory to future decisions are smarter.
        '''
        
        self.shots_fired.add((row, col))

        #Handle misses
        if result == "miss":
            self.misses.add((row, col))
            if self.difficulty >= 2:
                #If this cell was still waiting in the target queue, remove it bc we know it's not useful
                if (row, col) in self.target_queue:
                    self.target_queue.remove((row, col))
                
                #If there are no more target canadites left, go back to hunt mode
                if not self.target_queue:
                    self.mode = "hunt"

        #Handle hit or sunk results
        elif result == "hit" or result.startswith("sunk:"):
            self.hits.add((row, col))

            #If a ship was sunk, remove its size from the remaining list
            if result.startswith("sunk:"):
                ship_name = result.split(":")[1]
                sunk_size = SHIPS[ship_name]
                if sunk_size in self.remaining_ship_sizes:
                    self.remaining_ship_sizes.remove(sunk_size)

                if self.difficulty >= 2:
                    #Once a ship is sunk, stop targeting around it and return to hunt mode
                    self.target_queue = []
                    self.mode = "hunt"
            else:
                #A hit that did not sink a ship means we should continue targeting nearby cells to try and finish it.
                if self.difficulty >= 2:
                    self._enqueue_neighbors(row, col)
                    self.mode = "target"


    def _random_shot(self):
        '''
        Choose a completely random cell from all the cells not fired at yet.
        '''
        candidates = self._unseen_cells()
        return random.choice(candidates)

    def _hunt_and_target_shot(self):
        '''
        If the AI is currently targeting a ship and has queued cells to try, fire at the next target cell.
        Otherwise, switch back to hunt mode and pick a random unseen cell.
        '''
        if self.mode == "target" and self.target_queue:
            return self.target_queue.pop(0)
        #No useful target cell remain, go back to general hunting
        self.mode = "hunt"
        return self._random_shot()

    def _enqueue_neighbors(self, row, col):
        '''
        Add neighboring cells around a hit into the target queue. 

        If multiple hits suggest the ship lies horizontally or vertically, prioritize that direction. Else, consider all orthoginal neighbors
        '''
        #Try to infer ship orientiation from known hits
        axis = self._detect_axis()

        if axis == "horizontal":
            #If the ships looks like its horizontal, only search left and right
            candidates = [(row, col - 1), (row, col + 1)]
        elif axis == "vertical":
            #If the ship looks like its vertical, only search up and down
            candidates = [(row - 1, col), (row + 1, col)]
        else:
            #No clear direction yet, so try all orthogonal neighbors
            candidates = [(row - 1, col), (row + 1, col),
                          (row, col - 1), (row, col + 1)]

        #Only add valid, unseen cells that are not already queued   
        for r, c in candidates:
            if (self._in_bounds(r, c)
                    and (r, c) not in self.shots_fired
                    and (r, c) not in self.target_queue):
                self.target_queue.append((r, c))

    def _detect_axis(self):
        '''
        Try to determine whether current hits line up horizontally or vertically

        Return horizontal if all current hits share the same row.
        Return vertical if all current hits share the same col.
        Return None if neither are clear.
        '''
        if len(self.hits) < 2:
            return None
        rows = {r for r, c in self.hits}
        cols = {c for r, c in self.hits}
        if len(rows) == 1:
            return "horizontal"
        if len(cols) == 1:
            return "vertical"
        return None

    #CHECKERBOARD/PARITY

    def _parity_shot(self):
        '''
        Difficulty 3 strat

        Use hunt and target when actively chasing a ship, otherwise apply parity spacing so AI
        only check cells that could contain the smallest remaining ship.
        '''
        #If we alr have a hit to follow up on, continue targeting first
        if self.mode == "target" and self.target_queue:
            return self.target_queue.pop(0)

        #Use the smallest remaining ship size to define the search spacing
        spacing = min(self.remaining_ship_sizes) if self.remaining_ship_sizes else 1

        candidates = [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if (r + c) % spacing == 0 and (r, c) not in self.shots_fired
        ]

        if candidates:
            return random.choice(candidates)

        #If no parity cells left, fall back to any unseen cells
        return self._random_shot()

    #PROBABILITY HEATMAP

    def _heatmap_shot(self, opponent_board):
        '''
        Uses hunt and target when a ship is partially found. Otherwise, builds a heatmap
        that shows which cells are part of the largest number of valid remaining ship placements, 
        then fires at the cell with the highest score
        '''
        #If already chasing a ship, continue with that first
        if self.mode == "target" and self.target_queue:
            return self.target_queue.pop(0)

        heatmap = self._build_heatmap(opponent_board)

        #Find the highest scoring unseen cell(s)
        best_score = -1
        best_cells = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) in self.shots_fired:
                    continue
                score = heatmap[r][c]
                if score > best_score:
                    best_score = score
                    best_cells = [(r, c)]
                elif score == best_score:
                    best_cells.append((r, c))

        #Break ties randomly so can't predict behavior
        return random.choice(best_cells)

    def _build_heatmap(self, opponent_board):
        '''
        Build probability heatmap for all remaining ship sizes.

        For each unsunk ship, try placing it in every valid horizontal and vertical location. Every cell
        covered by a valid placement gets its score increased.
        '''
        heatmap = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

        for size in self.remaining_ship_sizes:
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    #Try horizontal placement
                    if c + size <= BOARD_SIZE:
                        cells = [(r, c + i) for i in range(size)]
                        if self._placement_valid(cells):
                            for pr, pc in cells:
                                heatmap[pr][pc] += 1

                    #Try vertical placement
                    if r + size <= BOARD_SIZE:
                        cells = [(r + i, c) for i in range(size)]
                        if self._placement_valid(cells):
                            for pr, pc in cells:
                                heatmap[pr][pc] += 1

        return heatmap

    def _placement_valid(self, cells):
        '''
        Check whether a hypothetical ship placement is consistent with what the AI already knows.

        Invalid if overlaps a known miss or overlaps a previously fired cell that was not a hit.
        Else, valid.
        '''
        for r, c in cells:
            if (r, c) in self.misses:
                return False
            if (r, c) in self.shots_fired and (r, c) not in self.hits:
                return False
        return True

    #HELPERS

    def _unseen_cells(self):
        '''
        Return a list of all board cells that have not yet been fired at yet.
        '''
        return [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if (r, c) not in self.shots_fired
        ]

    def _in_bounds(self, row, col):
        '''
        Return True if (row, col) lies inside board boundaries
        '''
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def display_heatmap(self, opponent_board):
        '''
        Print the current heatmap to console
        '''
        heatmap = self._build_heatmap(opponent_board)
        max_val = max(heatmap[r][c] for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))

        #Print col labels
        print("  " + "  ".join(str(i) for i in range(BOARD_SIZE)))

        #Print each row of the heatmap
        for r in range(BOARD_SIZE):
            row_str = f"{r} "
            for c in range(BOARD_SIZE):
                if (r, c) in self.hits:
                    row_str += " X " #Known hit
                elif (r, c) in self.misses:
                    row_str += " . " #Known miss
                else:
                    row_str += f"{heatmap[r][c]:2} " #Probability score
            print(row_str)