# Import the Flask tool from the flask package we installed
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import datetime

# Create our web application instance
app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# This line tells our app where to find the database file. 
# We are using SQLite, which is a simple file-based database.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
# This creates the database object that we will use to interact with our database. 
db = SQLAlchemy(app)

#--- DATABASE MODEL ---
# Card Model: Represents a single credit card 
class Card(db.Model): 
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each card
    name = db.Column(db.String(50), nullable=False)  # Name of the card
    benefits = db.relationship('Benefit', backref='card', lazy=True)  # Relationship to benefits

# Benefit Model: Represents a benefit associated with a credit card
class Benefit(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each benefit
    description = db.Column(db.String(200), nullable=False)  # Description of the benefit
    value = db.Column(db.Float, nullable=False)  # Monetary value of the benefit
    frequency = db.Column(db.String(50), nullable=False)  # How often the benefit is received
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)  # Foreign key to Card

# BonusCategory Model: Represents a bonus category for a credit card
class BonusCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each bonus category
    category_name = db.Column(db.String(100), nullable=False)  # Name of the bonus category
    multiplier = db.Column(db.Float, nullable=False)  # Multiplier for the bonus category
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)  # Foreign key to Card

# This "decorator" creates a URL route. It's a signpost.
# It says "If someone visits the homepage ('/'), run the function below."
@app.route('/')
def hello_world():
    # This function runs and returns some HTML text to the browser.
    return '<h1>HELLO MI STINKY</h1>'