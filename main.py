from flask import Flask, render_template, session, flash, redirect, request, jsonify, url_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from setup_db import User, Base  # Add Base to imports
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from rapidfuzz import fuzz, process
#from setup_db import User, ToDo, Base 

app = Flask(__name__)

app.secret_key = "mimicveil"

CLIENT_ID = 'ampfnnafsc0jkx9eo7xhfuts116t7k'
CLIENT_SECRET = '51jusdnsznz30mbrabgn1flz7u8xw1'
AUTH_TOKEN = None

url = 'https://id.twitch.tv/oauth2/token'
params = {
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'client_credentials'
}

response = requests.post(url, params=params)
data = response.json()

#this saves my IGDB auth token globally once i get it.
AUTH_TOKEN = data['access_token']

#connecting to the Database
engine = create_engine('sqlite:///user_info.db')

Session = sessionmaker(bind=engine)
db_session = Session()

# Base.metadata.create_all(engine) (CREATES DATABASE EVERY TIME THE SERVER STARTS) 
def fetch_games(query):
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }
    body = f'''search "{query}"; fields name, id; limit 500;'''
    response = requests.post(url, headers=headers, data=body)

    if response.status_code != 200:
        print(f"Search error: {response.status_code} - {response.text}")
        return []

    return response.json()

# Fuzzy filter results
def fuzzy_filter(games, user_input, threshold=60):
    user_input = user_input.lower()
    game_names = {game['name']: game['id'] for game in games if 'name' in game}

    matches = process.extract(user_input, game_names.keys(), scorer=fuzz.partial_ratio, score_cutoff=threshold, limit=15)
    return [(match, game_names[match]) for match, score, _ in matches]

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db_session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect('/homepage')
        else:
            flash("Invalid username or password", "danger")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect('/signup')
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect('/signup')
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db_session.add(new_user)
        db_session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/homepage')
def homepage():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    return render_template('homepage.html')

@app.route('/search_games')
def search_games_api():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    games = fetch_games(query)
    filtered = fuzzy_filter(games, query)
    return jsonify([{"id": game_id, "name": name} for name, game_id in filtered])

# Rec generator
@app.route('/recc_generator', methods=['GET', 'POST'])
def recc_generator():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')

    if request.method == 'POST':
        favourite_game_ids = request.form.get('favourite_games', '').split(',')
        print("Selected Favourite Games:", favourite_game_ids)
        # TODO: Add rec logic using these game IDs

        return render_template('recommendations.html', favourite_games=favourite_game_ids)

    return render_template('recc_generator.html')

@app.route('/wishlist')
def wishlist():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    #Tfetch wishlist items from DB
    return render_template('wishlist.html')

# --- Run app ---

if __name__ == '__main__':
    app.run(debug=True)
