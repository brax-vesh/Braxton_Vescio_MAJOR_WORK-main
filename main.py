from flask import Flask, render_template, session, flash, redirect, request, url_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from setup_db import User, Base  # Add Base to imports
from werkzeug.security import check_password_hash, generate_password_hash
import requests
#from setup_db import User, ToDo, Base 

app = Flask(__name__)

app.secret_key = "mimicveil"

CLIENT_ID = ''
CLIENT_SECRET = ''
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
            print("Login successful!", "info")
            return redirect('/homepage')
        else:
            print("Invalid username or password", "danger")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        #check if username exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if (existing_user):
            flash('Username already exists', 'danger')
            return redirect('/signup')

        #check that passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect('/signup')

        #create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db_session.add(new_user)
        db_session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect('/login')
    
    return render_template('signup.html')
    
@app.route('/homepage')
def homepage():
    #check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    
    return render_template('homepage.html')

def igdb_fetch(endpoint):
    url = f'https://api.igdb.com/v4/{endpoint}'
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {AUTH_TOKEN}',
    }
    data = 'fields id,name; limit 50;'
    response = requests.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print(f"⚠️ IGDB ERROR [{endpoint}]: {response.status_code} - {response.text}")
        return []

    return response.json()

@app.route('/recc_generator', methods=['GET', 'POST'])
def recc_generator():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')

    genres = igdb_fetch('genres')
    games = igdb_fetch('games')
    developers = igdb_fetch('companies')
    platforms = igdb_fetch('platforms')
    age_ratings = igdb_fetch('age_ratings')  #optional not sure whether i'll leave it

    print("GENRES:", genres)
    print("GAMES:", games)
    print("DEVS:", developers)
    print("PLATFORMS:", platforms)
    print("RATINGS:", age_ratings)

    if request.method == 'POST':
        favourite_games = request.form.getlist('favourite_games')
        preffered_genres = request.form.getlist('genres')
        key_words = request.form.getlist('keywords') #artstyle etc...
        preffered_devs = request.form.getlist('devs') # optional
        platform = request.form.getlist('platform') #optional
        rating = request.form.getlist('rating') #optional

        #reccomendation logic will go here

        art_genre_recommended_games = []
        similarity_reccomended_games = []

        
        return render_template('recommendations.html',                   
            favourite_games=favourite_games,
            preffered_genres=preffered_genres,
            preffered_devs=preffered_devs,
            platform=platform,
            rating=rating)

    return render_template('recc_generator.html',
        genres=genres,
        games=games,
        developers=developers,
        platforms=platforms,
        ratings=age_ratings)


@app.route('/wishlist')
def wishlist():
    #check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    
    #will get wishlist items from database
    return render_template('wishlist.html')

if __name__ == '__main__':
    app.run(debug=True)
