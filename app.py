import os
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from player import Player, WORDS, DEFAULT_DIFFICULTY, POINTS_MAPPING, PENALTY_MAPPING
import random

# Variable that defines the total number of rounds per game
MAX_ROUNDS = 5
# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key')


# A function that sets the default difficulty level and initializes the rounds for the game.
def initialize_rounds():
    """Pre-generate a sequence of (binary, word) for MAX_ROUNDS rounds and start at round 1."""
    p = get_player()
    pool = WORDS[p.difficulty]
    chosen = random.sample(pool, k=min(MAX_ROUNDS, len(pool)))
    # Create an empty list to store the rounds
    rounds = []
    # loop through the chosen words and convert them to binary. This pre-generates the rounds and words. The player can still manually generate the binary code because of the player.py logic.
    for word in chosen:
        binary = ' '.join(format(ord(c), '08b') for c in word)
        rounds.append((binary, word))

    session['rounds'] = rounds # Stores the word list of (binary, word) pairs in the session key 'rounds'.
    session['current_round'] = 1 # Sets the counter to start at round 1 under the key 'current_round'.

# A function that creates a new Player object and sets its attributes using the session data stored for the user.
def get_player():
    username = session.get('username')
    if not username:
        return None
    p = Player(username)
    p.difficulty = session.get('difficulty', DEFAULT_DIFFICULTY)
    p.points = session.get('points', 0)
    p.attempts = session.get('attempts', 0)
    p.hint = session.get('hint', "")
    p.correct_binary_code = session.get('correct_binary_code', "")
    p.random_word = session.get('random_word', "")
    return p

# A function that saves the Player object attributes back to the session and updates the session data for the user.
def save_player(p: Player):
    session['difficulty'] = p.difficulty
    session['points'] = p.points
    session['attempts'] = p.attempts
    session['hint'] = p.hint
    session['correct_binary_code'] = p.correct_binary_code
    session['random_word'] = p.random_word

# Flask framework route handlers that generate the web application and retrieves the username.
@app.route('/')
def index():
    return render_template('index.html', username_set=('username' in session))

# This is the flask route that sets the username for the player and initializes the game session.
# It clears any existing session data and sets the username, difficulty level, and other attributes.
# If the username is empty, it returns an error message.
# The function returns a JSON response with the username.
@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({"error": "Username cannot be empty"}), 400
    # clear any previous session data and set new user info
    session.clear()
    session['username'] = username
    session['difficulty'] = DEFAULT_DIFFICULTY
    session['points'] = 0
    session['attempts'] = 0
    session['hint'] = ""
    session['correct_binary_code'] = ""
    session['random_word'] = ""
    session['wrong_count'] = 0
    session['total_attempts'] = 0
    # redirect to index so browser picks up the session cookie
    return redirect(url_for('index'))

# This is the flask route that that connects set_difficulty function to the server.
@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    p = get_player()
    if not p: # If the player object is not found, it defaults to DEFAULT_DIFFICULTY.
        return jsonify({"error": "Player not found"}), 400 
    d = request.form.get('difficulty', DEFAULT_DIFFICULTY)
    if d in WORDS: # It retrieves the difficulty level from the form data and updates the player's difficulty attribute.
        p.difficulty = d
    save_player(p)
    return jsonify({"difficulty": p.difficulty})

# This is the flask route that generates a binary code for the current round of the game.
# It retrieves the player object and checks if the rounds have been initialized.
# If not, it initializes the rounds.
# It then retrieves the current round's binary code and word, updates the player's attributes,
# and returns a JSON response with the binary code, word, current round, total rounds, and points.
@app.route('/generate_binary_code', methods=['GET'])
def generate_binary_code_route():
    p = get_player()
    if not p:
        return jsonify({"error": "Player not found"}), 400
    # Check if rounds are initialized, if not, initialize them
    if 'rounds' not in session or session['current_round'] > MAX_ROUNDS:
        initialize_rounds()
    current = session['current_round']
    binary, word = session['rounds'][current - 1]
    p.correct_binary_code = binary
    p.random_word = word
    p.attempts = 0
    p.hint = ""
    save_player(p)
    return jsonify({
        'binary': binary,
        'word': word,
        'round': current,
        'total_rounds': MAX_ROUNDS,
        'points': p.points
    })

# This is the flask route that generates a preview of the binary code for the current round.
# It retrieves the player object and randomly selects a word from the WORDS dictionary based on the player's difficulty level.
# It then converts the word to binary, updates the player's attributes, and returns a JSON response with the binary code, word, points, current round, and total rounds.
@app.route('/preview', methods=['GET'])
def preview_binary_code():
    p = get_player()
    if not p:
        return jsonify({"error": "Player not found"}), 400
    word = random.choice(WORDS[p.difficulty])
    binary = ' '.join(format(ord(c), '08b') for c in word)
    p.correct_binary_code = binary
    p.random_word = word
    p.attempts = 0
    p.hint = ""
    save_player(p)
    return jsonify({
        'binary': binary,
        'word': word,
        'points': p.points,
        'round': session.get('current_round', 0),
        'total_rounds': MAX_ROUNDS
    })

# Finally, it saves the player's attributes and returns a JSON response with the feedback.
# This is the flask route that checks the player's guess against the correct word for the current round.
@app.route('/check_guess', methods=['POST'])

# This function retrieves the player object and checks if the current round exists in the session.
# If not, it initializes the current round to 1.
# It then retrieves the player's guess, correct word, and difficulty level.
# If the player has made 3 incorrect attempts, it provides a hint by revealing the first few letters of the correct word.
# It also tracks the number of wrong guesses and total attempts in the session.
# If the game is over (after the last round), it provides a summary of the game.
def check_guess():
    # Ensure current_round exists to avoid KeyError
    if 'current_round' not in session:
        session['current_round'] = 1
    # Get player object and check if it exists
    p = get_player()
    if not p:
        return jsonify({"error": "Player not found"}), 400
    guess = request.form.get('guess', '').strip().lower()
    correct_word = (p.random_word or "").lower()
    diff = p.difficulty
    # If the player has not made any attempts, it initializes the attempts to 0.
    wrong_count = session.get('wrong_count', 0)
    total_attempts = session.get('total_attempts', 0)
    # Sets the feedback dictionary to store the result of the guess.
    feedback = {
        'result': '',
        'points': p.points,
        'new_graffiti': False,
        'hint': p.hint,
        'round': session['current_round'],
        'total_rounds': MAX_ROUNDS,
        'game_over': False
    }
    # Checks if the guess is correct and 
    # If the guess is correct, it increases the score and sets the new binary flag to True.
    if guess == correct_word:
        p.increase_score(POINTS_MAPPING[diff])
        feedback['result'] = 'Correct!'
        feedback['new_graffiti'] = True
    # If the guess is incorrect, it decreases the score and adds a failed attempt.         
    else:
        p.add_attempt()
        p.decrease_score(PENALTY_MAPPING[diff])
        feedback['result'] = f"Incorrect. {p.attempts} failed attempts."
        # If the player has made 3 incorrect attempts, provide a hint.        
        if p.attempts >= 3:
            hlen = p.attempts - 3
            hint = correct_word[:hlen] if hlen <= len(correct_word) else correct_word
            p.hint = hint
            feedback['hint'] = hint
            # If the hint is the same as the correct word, it counts as a wrong guess because the user did not correctly guess. 
            # Then the program generates new binary code to guess. 
            if hint == correct_word:
                feedback['new_graffiti'] = True
                feedback['reveal_word'] = correct_word
                wrong_count += 1

    if feedback['new_graffiti']:
        # Track attempts and wrong guesses        
        total_attempts += p.attempts
        current = session['current_round']
        # Game over on last round        
        if current >= MAX_ROUNDS:
            feedback['game_over'] = True
            feedback['result'] += '  Game over!'
            feedback['summary'] = f"You made {total_attempts} total attempts and got {wrong_count} word(s) wrong."
        # Move to next round for next /generate_binary_code call            
        else:
            session['current_round'] = current + 1
        # Reset per-round            
        p.attempts = 0
        p.hint = ''
    # Update session data with the current round, wrong count, and total attempts
    session['wrong_count'] = wrong_count
    session['total_attempts'] = total_attempts
    save_player(p)
    feedback['points'] = p.points
    # If the game is over, it clears the session data and returns a summary of the game.
    return jsonify(feedback)

# This is the flask route and python function that handles the restart of the game.
# It retrieves the username and difficulty level from the session,
# clears the session data, and reinitializes the game with the same username and difficulty level.
# It resets the points, attempts, hint, and other attributes to their initial values.
# It also clears the rounds, current round, wrong count, and total attempts from the session.
# Finally, it returns a JSON response indicating that the game has been restarted.
@app.route('/restart', methods=['POST'])
def restart():
    username = session.get('username')
    difficulty = session.get('difficulty', DEFAULT_DIFFICULTY)
    session.clear()
    session['username'] = username
    session['difficulty'] = difficulty
    session['points'] = 0
    session['attempts'] = 0
    session['hint'] = ""
    session['correct_binary_code'] = ""
    session['random_word'] = ""
    session.pop('rounds', None)
    session.pop('current_round', None)
    session.pop('wrong_count', None)
    session.pop('total_attempts', None)
    return jsonify({"status": "restarted"})

# This is the flask route that resets the game session.
# It clears the session data and redirects the user to the index page.
# It resets the game state for the user and returns a redirect response to the index page.
@app.route('/reset', methods=['POST'])
def reset():
    session.clear()
    return redirect(url_for('index'))

# Ensures that the Flask application runs only if this script is executed directly from the app and no outside sources.
if __name__ == '__main__':
    app.run(debug=False)