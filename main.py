from flask import Flask, render_template, session, flash, redirect, request, jsonify, url_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from setup_db import User, WishlistItem, Base, engine
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from rapidfuzz import fuzz, process
from functools import wraps
from flask import make_response
from flask import session, redirect, url_for

#from setup_db import User, ToDo, Base 
# IGDB COMMUNICATION SETUP




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


AUTH_TOKEN = data['access_token']




# WEBSITE INITIATION




engine = create_engine('sqlite:///user_info.db')

Session = sessionmaker(bind=engine)
db_session = Session()



#__IGDB COMMUNICATION FUNCTIONS__



def igdb_query(query_string):
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }

    response = requests.post(url, headers=headers, data=query_string)

    if response.status_code != 200:
        print(f"IGDB query error: {response.status_code} - {response.text}")
        return []

    return response.json()

#IGDB Data Fetch

def igdb_fetch(endpoint):
    url = f'https://api.igdb.com/v4/{endpoint}'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {AUTH_TOKEN}'
    }
    body = 'fields id, name; limit 500;'

    response = requests.post(url, headers=headers, data=body)
    if response.status_code != 200:
        print(f"IGDB fetch error for {endpoint}: {response.status_code} - {response.text}")
        return []
    return response.json()


#Fetch Game Details


def fetch_game_details(game_ids):
    if not game_ids:
        return []

    chunked = [game_ids[i:i + 50] for i in range(0, len(game_ids), 50)]
    all_games = []

    for chunk in chunked:
        ids_str = ','.join(str(i) for i in chunk)
        games = igdb_query(f'''
            fields id, name, summary, aggregated_rating, cover.url, genres, platforms;
            where id = ({ids_str});
            limit 50;
        ''')
        all_games.extend(games)

    return all_games






# GAME DATA FETCH FUNCTIONS

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

# GAME NAME SEARCH FILTRATION
def fuzzy_filter(games, user_input, threshold=60):
    user_input = user_input.lower()
    game_names = {game['name']: game['id'] for game in games if 'name' in game}

    matches = process.extract(user_input, game_names.keys(), scorer=fuzz.partial_ratio, score_cutoff=threshold, limit=15)
    return [(match, game_names[match]) for match, score, _ in matches]



# APP ROUTES

def nocache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return no_cache_view

@app.route('/')
def home():
    return render_template('index.html')


#__GENERAL ROUTES__


#Login // Logout Route

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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


#Signup Route


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


#Homepage Route


@app.route('/homepage')
@nocache
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


#__WISHLIST ROUTES__


#Wishlist Addition Logic


@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']
    game_id = request.form.get('game_id')

    existing_item = db_session.query(WishlistItem).filter_by(user_id=user_id, game_id=game_id).first()
    if existing_item:
        return jsonify({'status': 'already in wishlist', 'game_id': game_id})

    new_item = WishlistItem(user_id=user_id, game_id=game_id)
    db_session.add(new_item)
    db_session.commit()

    return jsonify({'status': 'success', 'game_id': game_id})



#Wishlist Route


@app.route('/wishlist')
@nocache
def wishlist():
    if 'user_id' not in session:
        flash("Please log in to view your wishlist.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    wishlist_items = db_session.query(WishlistItem).filter_by(user_id=user_id).all()
    game_ids = [item.game_id for item in wishlist_items]

    games = fetch_game_details(game_ids)

    return render_template('wishlist.html', games=games)

@app.route('/game/<int:game_id>')
def game_titlepage(game_id):
    game_data = igdb_query(f'''
        fields name, summary, cover.url;
        where id = {game_id};
        limit 1;
    ''')

    if not game_data:
        flash("Game not found.", "danger")
        return redirect(url_for('recc_generator'))

    game = game_data[0]
    return render_template('game_titlepage.html', game=game)

@app.route('/remove_from_wishlist', methods=['POST'])
def remove_from_wishlist():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    game_id = request.form.get("game_id")
    if not game_id:
        return "Missing game ID", 400

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return redirect(url_for("login"))

    # Find the wishlist entry matching user and game
    wishlist_entry = db_session.query(WishlistItem).filter_by(user_id=user.id, game_id=game_id).first()
    if not wishlist_entry:
        return "Game not in wishlist", 404

    db_session.delete(wishlist_entry)
    db_session.commit()

    return redirect(url_for("wishlist"))

#__RECCOMENDATION ALGORITHMS__


#Recomendations Display Page


@app.route('/recommendations')
@nocache
def recommendations():
    if 'recommended_game_ids' not in session:
        flash("No recommendations to display. Please generate them first.", "warning")
        return redirect('/recc_generator')

    recommended_ids = session['recommended_game_ids']
    recommended_games = fetch_game_details(recommended_ids)

    return render_template('recommendations.html', games=recommended_games)




#Recomendation Generator


@app.route('/recc_generator', methods=['GET', 'POST'])
@nocache
def recc_generator():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')

    themes = igdb_fetch('themes')
    game_modes = igdb_fetch('game_modes')
    player_perspectives = igdb_fetch('player_perspectives')
    genres = igdb_fetch('genres')
    keywords_data = igdb_fetch('keywords')
    developers = igdb_fetch('companies')
    platforms = igdb_fetch('platforms')

    if request.method == 'POST':
        favourite_game_ids = [id.strip() for id in request.form.get('favourite_games', '').split(',') if id.strip()]
        preferred_genres = request.form.getlist('genres')
        selected_keywords = request.form.getlist('keywords')
        preferred_devs = request.form.getlist('devs')
        platforms_selected = request.form.getlist('platform')
        selected_themes = request.form.getlist('themes')
        selected_modes = request.form.getlist('game_modes')
        selected_perspectives = request.form.getlist('player_perspectives')

        if not favourite_game_ids or not preferred_genres:
            flash("Please enter at least one favourite game and select at least one genre.", "danger")
            return render_template('recc_generator.html',
                                   genres=genres,
                                   keywords=keywords_data,
                                   developers=developers,
                                   platforms=platforms,
                                   themes=themes,
                                   game_modes=game_modes,
                                   player_perspectives=player_perspectives)

        filters = []
        if preferred_genres:
            filters.append(f"genres = ({','.join(preferred_genres)})")
        if selected_keywords:
            filters.append(f"keywords = ({','.join(selected_keywords)})")
        if preferred_devs:
            filters.append(f"involved_companies.company = ({','.join(preferred_devs)})")
        if platforms_selected:
            filters.append(f"platforms = ({','.join(platforms_selected)})")
        if selected_themes:
            filters.append(f"themes = ({','.join(selected_themes)})")
        if selected_modes:
            filters.append(f"game_modes = ({','.join(selected_modes)})")
        if selected_perspectives:
            filters.append(f"player_perspectives = ({','.join(selected_perspectives)})")
        filters.append("aggregated_rating >= 50")

        final_query = f'''
            fields name, aggregated_rating, genres, platforms, summary, cover.url, id;
            where {" & ".join(filters)};
            sort aggregated_rating desc;
            limit 50;
        '''

        print("Final IGDB query:", final_query)

        recommended_games = igdb_query(final_query)
        print("Recommended games:", recommended_games)

        if not recommended_games:
            flash("No games found matching your filters. Try relaxing some options.", "warning")
            return render_template('recc_generator.html',
                                   genres=genres,
                                   keywords=keywords_data,
                                   developers=developers,
                                   platforms=platforms,
                                   themes=themes,
                                   game_modes=game_modes,
                                   player_perspectives=player_perspectives)

        session['recommended_game_ids'] = [game['id'] for game in recommended_games]

        return render_template('recommendations.html', games=recommended_games)

    return render_template('recc_generator.html',
                           genres=genres,
                           keywords=keywords_data,
                           developers=developers,
                           platforms=platforms,
                           themes=themes,
                           game_modes=game_modes,
                           player_perspectives=player_perspectives)


#___________________________________________________________________

if __name__ == '__main__':
    app.run(debug=True)
