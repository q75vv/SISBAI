from game import Board
from ai import AIAgent

# Set up a board and place ships
board = Board()
board.place_ships_randomly()

# Use difficulty 4 (heatmap AI)
agent = AIAgent(difficulty=4)
agent.set_board(board)

# Fire a few shots to make the heatmap interesting
for _ in range(20):
    row, col = agent.choose_shot(board)
    result = board.receive_shot(row, col)
    agent.record_result(row, col, result)

# Print the heatmap
print("=== Probability Heatmap ===")
agent.display_heatmap(board)