from game import Board
from ai import AIAgent

#Num games to simulate per difficulty level
games = 1000

for diff in [1, 2, 3, 4]:
    total = 0
    for _ in range(games):
        #Create fresh AI agent for each game
        agent = AIAgent(difficulty=diff)

        #Create a board and randomly place all 5 ships on it
        opponent = Board()
        opponent.place_ships_randomly()

        #Give the agent a reference to the board
        agent.set_board(opponent)

        shots = 0
        while not opponent.all_ships_sunk():
            #Ask AI to pick a cell to shoot
            row, col = agent.choose_shot(opponent)

            #Fire the shot and get result
            result = opponent.receive_shot(row, col)

            #Tell the agent what happened so it can update its internal state
            agent.record_result(row, col, result)
            shots += 1
        total += shots

    print(f"Difficulty {diff}: avg {total/games:.1f} shots to win over {games} games")