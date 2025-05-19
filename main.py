from flask import Flask, render_template, session, flash, redirect, request, url_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from setup_db import User, Base  # Add Base to imports
from werkzeug.security import check_password_hash, generate_password_hash
# from setup_db import User, ToDo, Base 

app = Flask(__name__)

app.secret_key = "sneaky"
#I would replace this with a random key / string in production...

# Connecting to the Database
engine = create_engine('sqlite:///user_info.db')

Session = sessionmaker(bind=engine)
db_session = Session()

# Base.metadata.create_all(engine) 

# CODE FOR PAGES

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

        # Check if username already exists
        existing_user = db_session.query(User).filter_by(username=username).first()
        if (existing_user):
            flash('Username already exists', 'danger')
            return redirect('/signup')

        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect('/signup')

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db_session.add(new_user)
        db_session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect('/login')
    
    return render_template('signup.html')
    
@app.route('/homepage')
def homepage():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    
    return render_template('homepage.html')

@app.route('/recc_generator')
def recc_generator():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    
    # Add recommendation logic here
    return render_template('recc_generator.html')

@app.route('/wishlist')
def wishlist():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect('/login')
    
    # You might want to fetch wishlist items from database here
    return render_template('wishlist.html')

if __name__ == '__main__':
    app.run(debug=True