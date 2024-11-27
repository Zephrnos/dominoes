
# In our group there are 3 people
# Ethan Fischer
# Tristan Adams
# Salmann Shire


import random
import time
from threading import Thread, Lock

# Constants for the game
MAX_DOMINO_VALUE = 7  # Maximum number for a domino piece

class Randomizer:
    def __init__(self):
        random.seed(time.time())

    def shuffle(self, items):
        random.shuffle(items)
        return items

class DominoTable:
    def __init__(self):
        self.played_pieces = []
        self.lock = Lock()

    def display(self):
        with self.lock:
            print("\nDominoes on the table: ", end="")
            for piece in self.played_pieces:
                print(f"[{piece[0]}|{piece[1]}]", end=" ")
            print("")

    def add_piece(self, piece, at_tail):
        with self.lock:
            piece = list(piece)
            if not self.played_pieces:
                self.played_pieces.append(piece)
            elif at_tail:
                if piece[0] == self.played_pieces[-1][1]:
                    self.played_pieces.append(piece)
                else:
                    piece.reverse()
                    self.played_pieces.append(piece)
            else:
                if piece[1] == self.played_pieces[0][0]:
                    self.played_pieces.insert(0, piece)
                else:
                    piece.reverse()
                    self.played_pieces.insert(0, piece)

    def get_ends(self):
        with self.lock:
            if not self.played_pieces:
                return None, None
            return self.played_pieces[0][0], self.played_pieces[-1][1]

class DominoSet:
    def __init__(self):
        self.all_pieces = [(i, j) for i in range(MAX_DOMINO_VALUE) for j in range(i, MAX_DOMINO_VALUE)]
        self.available_pieces = []
        self.lock = Lock()

    def initialize(self):
        self.available_pieces = self.all_pieces.copy()

    def draw_piece(self):
        with self.lock:
            if self.available_pieces:
                return self.available_pieces.pop(0)
            return None

class Player(Thread):
    def __init__(self, name, table, domino_set, controller):
        super().__init__()
        self.name = name
        self.hand = []
        self.table = table
        self.domino_set = domino_set
        self.controller = controller  # Reference to the GameController
        self.can_play = False  # Signal for this player's turn
        self.winner = False
        self.no_moves = False

    def draw_pieces(self, num_pieces):
        for _ in range(num_pieces):
            piece = self.domino_set.draw_piece()
            if piece:
                self.hand.append(piece)

    def has_matching_piece(self, head, tail):
        return any(head in piece or tail in piece for piece in self.hand)

    def play_piece(self, index):
        if 0 <= index < len(self.hand):
            return self.hand.pop(index)
        return None

    def run(self):
        while not self.controller.game_over:  # Check if the game is over
            with self.controller.game_lock:
                if not self.can_play:
                    continue  # Wait for the turn signal

                head, tail = self.table.get_ends()
                print(f"\n{self.name}'s turn. Your hand:")

                # Display the player's hand as a numbered list
                for i, piece in enumerate(self.hand, start=1):
                    print(f"{i}: [{piece[0]}|{piece[1]}]")

                if self.has_matching_piece(head, tail):
                    while True:
                        try:
                            # Ask the player to select a domino by index
                            index_input = int(input(f"{self.name}, select a domino to play by its number (1-{len(self.hand)}): ")) - 1
                            if index_input < 0 or index_input >= len(self.hand):
                                print("Invalid selection. Please choose a valid number.")
                                continue

                            selected_piece = self.hand[index_input]
                            at_tail = input("Play at the head (h) or tail (t)? (h/t): ").strip().lower() == 't'

                            # Validate and play the selected piece
                            if at_tail and (selected_piece[0] == tail or selected_piece[1] == tail):
                                played_piece = self.play_piece(index_input)
                                self.table.add_piece(played_piece, at_tail=True)
                                break
                            elif not at_tail and (selected_piece[0] == head or selected_piece[1] == head):
                                played_piece = self.play_piece(index_input)
                                self.table.add_piece(played_piece, at_tail=False)
                                break
                            else:
                                print("Invalid move. The selected domino does not match the table ends.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")
                else:
                    if self.domino_set.available_pieces:
                        print(f"{self.name} cannot play. Drawing a piece...")
                        self.draw_pieces(1)
                    else:
                        print(f"{self.name} cannot play and no pieces are available to draw.")
                        self.no_moves = True

                # Check if the player has won
                if not self.hand:
                    self.winner = True
                    print(f"{self.name} wins!")
                    self.controller.game_over = True  # Set the game_over flag
                    return

                # Display the table after this player's turn
                self.table.display()

                # End this player's turn
                self.can_play = False

class GameController:
    def __init__(self):
        self.randomizer = Randomizer()
        self.table = DominoTable()
        self.domino_set = DominoSet()
        self.game_lock = Lock()
        self.game_over = False  # Shared state to track if the game is over

    def setup_game(self):
        # Initialize and shuffle the dominoes
        self.domino_set.initialize()
        self.domino_set.available_pieces = self.randomizer.shuffle(self.domino_set.available_pieces)

        # Create players and deal pieces
        self.player1 = Player("Player 1", self.table, self.domino_set, self)
        self.player2 = Player("Player 2", self.table, self.domino_set, self)

        self.player1.draw_pieces(10)
        self.player2.draw_pieces(10)

        # Start player threads
        self.player1.start()
        self.player2.start()

        # Place the first piece on the table
        first_piece = self.domino_set.draw_piece()
        self.table.add_piece(first_piece, at_tail=True)
        self.table.display()

    def start_game(self):
        current_player = self.player1 if random.choice([True, False]) else self.player2
        print(f"{current_player.name} goes first!")

        no_move_count = 0

        while not self.game_over:  # Check if the game is over
            with self.game_lock:
                # Signal the current player to play
                current_player.can_play = True

            # Wait for the player's turn to finish
            while current_player.can_play and not self.game_over:
                time.sleep(0.1)

            # Check for a winner
            if current_player.winner:
                print(f"The winner is {current_player.name}!")

                # Identify and print the loser's hand
                loser = self.player1 if current_player == self.player2 else self.player2
                print(f"The loser's hand: {', '.join(f'[{piece[0]}|{piece[1]}]' for piece in loser.hand)}")
                self.table.display()
                self.game_over = True  # Set the game_over flag
                break

            # Check for stalemate
            if current_player.no_moves:
                no_move_count += 1
            else:
                no_move_count = 0

            if no_move_count >= 2:
                print("Stalemate! No more moves can be made by either player.")
                self.game_over = True  # Set the game_over flag
                break

            # Switch turns
            current_player = self.player2 if current_player == self.player1 else self.player1

        # Wait for threads to finish
        self.player1.join()
        self.player2.join()

if __name__ == "__main__":
    controller = GameController()
    controller.setup_game()
    controller.start_game()