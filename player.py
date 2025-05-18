import random

# This is a dictionary that contains words categorized by difficulty levels.
WORDS = {
    "easy":   ["Cat", "Dog", "Ship", "Book", "Tree"],
    "medium": ["BasTion", "FuChsia", "JaCkAl", "Mother", "BiTcoiN"],
    "hard":   ["Associate", "Vortex", "Zephyr", "Quixotic", "Obfuscate"]
}
# This is the default difficulty level for the game.
DEFAULT_DIFFICULTY = "medium"
# This is the amount of points awarded for each difficulty level.
POINTS_MAPPING = {"easy": 2, "medium": 5, "hard": 10}
PENALTY_MAPPING = {"easy": 1, "medium": 2, "hard": 3}

# This is the player class. It contains methods and attributes that define the player's state and behavior in the game.
class Player:
    # Sets the default difficulty level and initializes the player's attributes.
    def __init__(self, username):
        self.username            = username
        self.difficulty          = DEFAULT_DIFFICULTY
        self.points              = 0
        self.attempts            = 0
        self.hint                = ""
        self.correct_binary_code = ""
        self.random_word         = ""
    # This function sets the difficulty level for the game.
    def set_difficulty(self, difficulty):
        if difficulty in WORDS: # Check if the difficulty is valid
            self.difficulty = difficulty
    # This function function generates a random word based on the difficulty level and converts it to binary.
    def generate_binary_code(self):
        word   = random.choice(WORDS[self.difficulty]) # Select a random word based on the difficulty level
        binary = ' '.join(format(ord(c), '08b') for c in word) # This is the python function that actually is used to manually generate the binary code when the player clicks on generate
        self.correct_binary_code = binary
        self.random_word         = word
        return binary, word
    # This function increases the score when the player guesses the binary code correctly.
    def increase_score(self, pts):
        self.points += pts
    # This function decreases the score when the player makes an incorrect guess.
    def decrease_score(self, penalty):
        self.points -= penalty
    
    def add_attempt(self):
        self.attempts += 1

    def use_hint(self):
        self.hint and setattr(self, 'hint', self.hint)  # (no-op, hint is already tracked)

    def reset(self):
        self.points              = 0
        self.attempts            = 0
        self.hint                = ""
        self.correct_binary_code = ""
        self.random_word         = ""