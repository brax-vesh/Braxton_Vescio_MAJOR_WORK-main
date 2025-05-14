from flask import Flask, render_template, session, flash, redirect, request, url_for
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import requests
# from setup_db import User, ToDo, Base 

app = Flask(__name__)

app.secret_key = "sneaky"
#I would replace this with a random key / string in production...

# Connecting to the Database
engine = create_engine('sqlite:///userdata.db')

Session = sessionmaker(bind=engine)
db_session = Session()

# Base.metadata.create_all(engine)

# CODE FOR PAGES

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Add logic to verify user credentials
        # Example: user = db_session.query(User).filter_by(username=username).first()
        # if user and user.check_password(password):
        #     session['user_id'] = user.id
        #     flash('Login successful!', 'success')
        #     return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Add logic to create a new user
        # Example: new_user = User(username=username)
        # new_user.set_password(password)
        # db_session.add(new_user)
        # db_session.commit()
        # flash('Account created successfully!', 'success')
        # return redirect(url_for('login'))
        flash('Signup failed. Try again.', 'danger')
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)