# Import the Flask tool from the flask package we installed
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime
from dateutil.relativedelta import relativedelta
from threading import Thread
import time
import atexit

# Create our web application instance
app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# This line tells our app where to find the database file. 
# We are using SQLite, which is a simple file-based database.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
# This creates the database object that we will use to interact with our database.
db = SQLAlchemy(app)

# Custom Jinja2 filter to format dollar amounts without unnecessary decimals
@app.template_filter('currency')
def currency_filter(value):
    """Format currency values to remove unnecessary decimal places"""
    if value is None:
        return "$0"

    # Convert to float if it's a string
    if isinstance(value, str):
        # Remove any existing dollar signs and commas
        clean_value = value.replace('$', '').replace(',', '')
        try:
            value = float(clean_value)
        except ValueError:
            return value  # Return original if can't convert

    # Format as integer if it's a whole number, otherwise keep 2 decimal places
    if value == int(value):
        return f"${int(value):,}"
    else:
        formatted = f"${value:,.2f}"
        # Remove trailing zeros and decimal point if necessary
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return formatted

# Custom Jinja2 filter to format multipliers without unnecessary decimals
@app.template_filter('multiplier')
def multiplier_filter(value):
    """Format multiplier values to remove unnecessary decimal places"""
    if value is None:
        return "1x"
    
    # Convert to float if it's a string
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return str(value)  # Return original if can't convert
    
    # Format as integer if it's a whole number, otherwise keep 1 decimal place
    if value == int(value):
        return f"{int(value)}x"
    else:
        return f"{value:.1f}x"

#--- DATABASE MODEL ---
# Card Model: Represents a single credit card 
class Card(db.Model): 
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each card
    name = db.Column(db.String(50), nullable=False)  # Name of the card
    benefits = db.relationship('Benefit', backref='card', lazy=True)  # Relationship to benefits

# MultiplierBenefit Model: Represents earning multipliers (like 3x points on dining)
class MultiplierBenefit(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each multiplier benefit
    category = db.Column(db.String(100), nullable=False)  # Category like "Dining", "Travel", etc.
    description = db.Column(db.String(300), nullable=False)  # Full description of the multiplier
    multiplier = db.Column(db.Float, nullable=False)  # The multiplier value (3.0 for 3x points)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)  # Foreign key to Card

# CreditBenefit Model: Represents statement credits and reimbursements
class CreditBenefit(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each credit benefit
    description = db.Column(db.String(300), nullable=False)  # Description of the credit
    credit_amount = db.Column(db.Float, nullable=False)  # Dollar amount of the credit
    frequency = db.Column(db.String(100), nullable=False)  # How often you get this credit
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)  # Foreign key to Card

# Legacy Benefit Model: Keep for backward compatibility, but we'll use the new models
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

# Usage Model: Tracks when you actually use a benefit (like when you get a statement credit)
class Usage(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each usage record
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)  # Which card was used
    benefit_type = db.Column(db.String(50), nullable=False)  # "multiplier" or "credit"
    benefit_id = db.Column(db.Integer, nullable=False)  # ID of the specific benefit used
    amount = db.Column(db.Float, nullable=False)  # Amount earned or credited
    description = db.Column(db.String(200), nullable=False)  # What you used it for
    date_used = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)  # When you used it

class CreditStatus(db.Model):
    """Track the usage status of credits (annual, quarterly, monthly, one-time)"""
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(100), nullable=False)  # Name of the card
    credit_type = db.Column(db.String(20), nullable=False)  # annual, quarterly, monthly, onetime
    credit_identifier = db.Column(db.String(100), nullable=False)  # benefit_name or category
    status = db.Column(db.String(20), nullable=False, default='available')  # available, used
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    # Create a unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('card_name', 'credit_type', 'credit_identifier'),)

# === NEW FUNCTIONAL DATABASE MODELS ===

class SignupBonus(db.Model):
    """Track signup bonuses with progress and deadlines"""
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card_enhanced.id'), nullable=False)
    bonus_amount = db.Column(db.String(50), nullable=False)  # "60,000 points"
    description = db.Column(db.String(200), nullable=False)  # "Spend $4,000 in first 3 months"
    required_spend = db.Column(db.Float, nullable=False)  # 4000.0
    current_spend = db.Column(db.Float, default=0.0)  # Track progress
    deadline = db.Column(db.Date, nullable=True)  # When bonus expires
    status = db.Column(db.String(20), default='not-started')  # not-started, in-progress, completed
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @property
    def progress_percent(self):
        if self.required_spend == 0:
            return 0
        return min(100, int((self.current_spend / self.required_spend) * 100))

    @property
    def status_text(self):
        status_map = {
            'not-started': 'Not Started',
            'in-progress': 'In Progress',
            'completed': 'Completed'
        }
        return status_map.get(self.status, 'Unknown')

class SpendingBonus(db.Model):
    """Track ongoing spending bonuses with caps and progress"""
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card_enhanced.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # "Rotating Categories"
    multiplier = db.Column(db.Float, nullable=False)  # 5.0 for 5x
    description = db.Column(db.String(200), nullable=False)
    cap_amount = db.Column(db.Float, nullable=False)  # 1500.0 spending cap
    current_spend = db.Column(db.Float, default=0.0)
    reset_date = db.Column(db.Date, nullable=False)  # When the bonus resets
    bonus_type = db.Column(db.String(20), default='quarterly')  # quarterly, monthly, annual
    is_active = db.Column(db.Boolean, default=True)

    @property
    def progress_percent(self):
        if self.cap_amount == 0:
            return 0
        return min(100, int((self.current_spend / self.cap_amount) * 100))

    @property
    def status(self):
        if self.current_spend >= self.cap_amount:
            return 'completed'
        elif self.current_spend > 0:
            return 'in-progress'
        else:
            return 'not-started'

    @property
    def status_text(self):
        return self.status.replace('-', ' ').title()

class CreditBenefit2(db.Model):
    """Enhanced credit benefit tracking with reset cycles"""
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card_enhanced.id'), nullable=False)
    benefit_name = db.Column(db.String(100), nullable=False)  # "Travel Credit"
    category = db.Column(db.String(100), nullable=True)  # For categorized credits
    credit_amount = db.Column(db.Float, nullable=False)  # 300.0
    description = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # annual, quarterly, monthly, onetime
    reset_date = db.Column(db.Date, nullable=True)  # When it resets
    has_progress = db.Column(db.Boolean, default=False)  # Whether to show progress bar
    required_amount = db.Column(db.Float, nullable=True)  # If progress tracking needed
    current_amount = db.Column(db.Float, default=0.0)  # Current progress
    original_multiplier = db.Column(db.String(50), nullable=True)  # Original format like "1 night", "2 credits"
    from_spending_bonus = db.Column(db.Boolean, default=False)  # True if created from spending bonus completion
    spending_bonus_id = db.Column(db.Integer, nullable=True)  # Reference to original spending bonus for undo

    # Link to CreditStatus for usage tracking
    @property
    def credit_status(self):
        identifier = self.benefit_name if self.benefit_name else self.category
        status_record = CreditStatus.query.filter_by(
            card_name=self.card.name,
            credit_type=self.frequency,
            credit_identifier=identifier
        ).first()
        return status_record.status if status_record else 'available'

    @property
    def status_text(self):
        return 'Used' if self.credit_status == 'used' else 'Available'

    @property
    def progress_percent(self):
        if not self.has_progress or self.required_amount == 0:
            return 0
        return min(100, int((self.current_amount / self.required_amount) * 100))

# Other Bonus Model: For threshold-based bonuses (not time-limited sign-up bonuses)
class OtherBonus(db.Model):
    """Model for threshold-based bonuses like anniversary rewards, status bonuses, etc."""
    __tablename__ = 'other_bonus'
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('card_enhanced.id'), nullable=False)
    bonus_type = db.Column(db.String(50), nullable=False)  # 'threshold', 'anniversary', etc.
    bonus_amount = db.Column(db.String(100), nullable=False)  # '10,000 miles', 'Gold Status', etc.
    description = db.Column(db.String(200), nullable=False)
    required_spend = db.Column(db.Float, nullable=True)  # Spending threshold if applicable
    frequency = db.Column(db.String(20), nullable=False)  # 'annual', 'ongoing', etc.
    status = db.Column(db.String(20), default='pending')  # pending, completed, expired
    completed_date = db.Column(db.DateTime, nullable=True)  # When bonus was completed
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    @property
    def status_text(self):
        status_map = {
            'pending': 'Pending',
            'completed': 'Completed',
            'expired': 'Expired'
        }
        return status_map.get(self.status, 'Unknown')

# Update Card model to include missing fields
class CardEnhanced(db.Model):
    """Enhanced Card model with proper fields for UI"""
    __tablename__ = 'card_enhanced'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    last_four = db.Column(db.String(4), default='0000')
    issuer = db.Column(db.String(50), nullable=True)
    brand_class = db.Column(db.String(50), nullable=True)

    # Relationships
    signup_bonuses = db.relationship('SignupBonus', backref='card', lazy=True)
    spending_bonuses = db.relationship('SpendingBonus', backref='card', lazy=True)
    credit_benefits = db.relationship('CreditBenefit2', backref='card', lazy=True)
    other_bonuses = db.relationship('OtherBonus', backref='card', lazy=True)

    @property
    def total_benefits(self):
        return (len(self.signup_bonuses) +
                len(self.spending_bonuses) +
                len(self.credit_benefits) +
                len(self.other_bonuses))

# Function to initialize the database
def create_tables():
    """
    This function creates all the database tables based on our models.
    Think of it like building the filing cabinets before you can store files.
    """
    with app.app_context():  # This tells Flask we're working within the app
        db.create_all()  # Creates all tables defined in our models
        print("Database tables created successfully!")

# Function to add sample data
def add_sample_data():
    """
    This function adds some example credit cards and their benefits to our database.
    Think of it like putting sample files in our filing cabinets to test them out.
    """
    with app.app_context():
        # First, let's check if we already have data (to avoid duplicates)
        if Card.query.first():
            print("Sample data already exists!")
            return

        # Create your 12 credit cards
        chase_sapphire_reserve = Card(name="Chase Sapphire Reserve")
        chase_freedom_unlimited = Card(name="Chase Freedom Unlimited")
        amex_gold = Card(name="American Express Gold")
        capital_one_venturex = Card(name="Capital One VentureX")
        chase_united_quest = Card(name="Chase United Quest")
        world_of_hyatt = Card(name="World of Hyatt")
        venmo_cash_back = Card(name="Venmo Cash Back")
        marriott_bonvoy_boundless = Card(name="Marriott Bonvoy Boundless")
        hilton_honors_surpass = Card(name="Hilton Honors Surpass")
        hilton_honors_aspire = Card(name="Hilton Honors Aspire")
        atmos_rewards_ascent = Card(name="Atmos Rewards Ascent")
        us_bank_cash_back = Card(name="U.S. Bank Cash Back")

        # Add all the cards to our database session (like putting them in a shopping cart)
        cards_to_add = [
            chase_sapphire_reserve, chase_freedom_unlimited, amex_gold, capital_one_venturex,
            chase_united_quest, world_of_hyatt, venmo_cash_back, marriott_bonvoy_boundless,
            hilton_honors_surpass, hilton_honors_aspire, atmos_rewards_ascent, us_bank_cash_back
        ]

        for card in cards_to_add:
            db.session.add(card)

        # Save all the cards to the database (like checking out the shopping cart)
        db.session.commit()

        # CHASE SAPPHIRE RESERVE - Multiplier Benefits (Points Earning)
        csr_multipliers = [
            MultiplierBenefit(
                category="Chase Travel",
                description="8x points on Chase Travel for flights, hotels, rental cars, cruises, activities and tours",
                multiplier=8.0,
                card_id=chase_sapphire_reserve.id
            ),
            MultiplierBenefit(
                category="Direct Travel Booking",
                description="4x points on travel when you book directly with an airline or hotel",
                multiplier=4.0,
                card_id=chase_sapphire_reserve.id
            ),
            MultiplierBenefit(
                category="Dining",
                description="3x points on dining at restaurants worldwide, including eligible delivery",
                multiplier=3.0,
                card_id=chase_sapphire_reserve.id
            ),
            MultiplierBenefit(
                category="Lyft",
                description="4x bonus points on eligible Lyft rides",
                multiplier=4.0,
                card_id=chase_sapphire_reserve.id
            ),
            MultiplierBenefit(
                category="Peloton",
                description="10x bonus points on eligible Peloton hardware and accessories (cap of 50,000 total points)",
                multiplier=10.0,
                card_id=chase_sapphire_reserve.id
            )
        ]

        # Add all Chase Sapphire Reserve multiplier benefits
        for multiplier in csr_multipliers:
            db.session.add(multiplier)

        # CHASE SAPPHIRE RESERVE - Credit Benefits (Statement Credits & Reimbursements)
        csr_credits = [
            # Annual Credits
            CreditBenefit(
                description="Up to $300 annually towards travel purchases",
                credit_amount=300.0,
                frequency="Annual",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="Up to $500 annually for prepaid bookings made with Chase Travel for The Edit properties",
                credit_amount=500.0,
                frequency="Annual",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="$250 on prepaid Chase Travel hotel bookings for stays with IHG, Montage, Pendry, Omni, Virgin, Minor, and Pan Pacific Hotels",
                credit_amount=250.0,
                frequency="Annual",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="$150 in statement credits from January through June and again from July through December for dining at restaurants that are part of the Sapphire Reserve Exclusive Tables program",
                credit_amount=300.0,
                frequency="Annual (biannual payments)",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="$150 in statement credits from Jan 1 through June 30 and again from July 1 through December 31 for purchases on StubHub and viagogo.com",
                credit_amount=300.0,
                frequency="Annual (biannual payments)",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="$120 in annual statement credit towards Peloton membership",
                credit_amount=120.0,
                frequency="Annual",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="Complimentary $120 DashPass membership annually",
                credit_amount=120.0,
                frequency="Annual",
                card_id=chase_sapphire_reserve.id
            ),

            # Monthly Credits
            CreditBenefit(
                description="$25 per month to spend on DoorDash, including $5 monthly to spend on restaurant orders and two $10 promotions each month to save on groceries and retail orders",
                credit_amount=25.0,
                frequency="Monthly",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="$10 monthly Lyft credit",
                credit_amount=10.0,
                frequency="Monthly",
                card_id=chase_sapphire_reserve.id
            ),

            # Other Frequency Credits
            CreditBenefit(
                description="Up to $120 every four years as reimbursement for Global Entry, TSA PreCheck, or NEXUS",
                credit_amount=120.0,
                frequency="Every 4 years",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="After spending $75,000 on the card, get a $500 Southwest Airlines credit",
                credit_amount=500.0,
                frequency="After $75,000 spend",
                card_id=chase_sapphire_reserve.id
            ),
            CreditBenefit(
                description="After spending $75,000 on the card, $250 in Shops at Chase credit",
                credit_amount=250.0,
                frequency="After $75,000 spend",
                card_id=chase_sapphire_reserve.id
            ),

            # Ongoing Benefits (No Dollar Value)
            CreditBenefit(
                description="Complimentary subscription to AppleTV and AppleMusic",
                credit_amount=0.0,
                frequency="Ongoing benefit",
                card_id=chase_sapphire_reserve.id
            )
        ]

        # Add all Chase Sapphire Reserve credit benefits
        for credit in csr_credits:
            db.session.add(credit)

        # AMERICAN EXPRESS GOLD CARD - Multiplier Benefits (Points Earning)
        amex_gold_multipliers = [
            MultiplierBenefit(
                category="Restaurants",
                description="4x points on restaurants worldwide, plus takeout and delivery in the U.S., on up to $50,000 in purchases each year",
                multiplier=4.0,
                card_id=amex_gold.id
            ),
            MultiplierBenefit(
                category="Groceries",
                description="4x points on groceries at U.S. supermarkets, on up to $25,000 in purchases each year",
                multiplier=4.0,
                card_id=amex_gold.id
            ),
            MultiplierBenefit(
                category="Flights",
                description="3x points on flights booked directly with airlines or on AmexTravel.com",
                multiplier=3.0,
                card_id=amex_gold.id
            ),
            MultiplierBenefit(
                category="Prepaid Travel",
                description="2x points on prepaid hotels and other eligible travel – such as prepaid car rentals, vacation packages and cruises when you book through AmexTravel.com",
                multiplier=2.0,
                card_id=amex_gold.id
            )
        ]

        # Add all American Express Gold multiplier benefits
        for multiplier in amex_gold_multipliers:
            db.session.add(multiplier)

        # AMERICAN EXPRESS GOLD CARD - Credit Benefits (Statement Credits & Reimbursements)
        amex_gold_credits = [
            CreditBenefit(
                description="$10 in Uber Cash each month to use on orders and rides in the U.S. when you select an Amex Card for your transaction",
                credit_amount=10.0,
                frequency="Monthly",
                card_id=amex_gold.id
            ),
            CreditBenefit(
                description="$7 in monthly statement credits for Dunkin Donuts",
                credit_amount=7.0,
                frequency="Monthly",
                card_id=amex_gold.id
            ),
            CreditBenefit(
                description="Resy restaurants or make other eligible Resy purchases, you can get up to $100 back annually",
                credit_amount=100.0,
                frequency="Annual",
                card_id=amex_gold.id
            ),
            CreditBenefit(
                description="Earn up to $10 in statement credits monthly when you pay with the Gold Card at Grubhub, The Cheesecake Factory, Goldbelly, Wine.com, and Five Guys",
                credit_amount=10.0,
                frequency="Monthly",
                card_id=amex_gold.id
            )
        ]

        # Add all American Express Gold credit benefits
        for credit in amex_gold_credits:
            db.session.add(credit)

        # CAPITAL ONE VENTUREX - Multiplier Benefits (Miles Earning)
        venturex_multipliers = [
            MultiplierBenefit(
                category="Hotels & Rental Cars via Capital One Travel",
                description="10x miles on hotels and rental cars booked through Capital One Travel",
                multiplier=10.0,
                card_id=capital_one_venturex.id
            ),
            MultiplierBenefit(
                category="Flights & Vacation Rentals via Capital One Travel",
                description="5x miles on flights and vacation rentals booked through Capital One Travel",
                multiplier=5.0,
                card_id=capital_one_venturex.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="2x miles on all other purchases, every day",
                multiplier=2.0,
                card_id=capital_one_venturex.id
            )
        ]

        # Add all Capital One VentureX multiplier benefits
        for multiplier in venturex_multipliers:
            db.session.add(multiplier)

        # CAPITAL ONE VENTUREX - Credit Benefits (Statement Credits & Bonuses)
        venturex_credits = [
            CreditBenefit(
                description="$300 annual travel credit for bookings through Capital One Travel",
                credit_amount=300.0,
                frequency="Annual",
                card_id=capital_one_venturex.id
            ),
            CreditBenefit(
                description="$120 Global Entry or TSA PreCheck credit",
                credit_amount=120.0,
                frequency="Every 4 years",
                card_id=capital_one_venturex.id
            ),
            CreditBenefit(
                description="10,000 free miles every year for your card anniversary",
                credit_amount=0.0,
                frequency="Annual (anniversary)",
                card_id=capital_one_venturex.id
            ),
            CreditBenefit(
                description="75,000 miles welcome bonus when you spend $4,000 on purchases within the first 3 months from account opening",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=capital_one_venturex.id
            )
        ]

        # Add all Capital One VentureX credit benefits
        for credit in venturex_credits:
            db.session.add(credit)

        # CHASE UNITED QUEST - Multiplier Benefits (Miles Earning)
        united_quest_multipliers = [
            MultiplierBenefit(
                category="United Flights",
                description="8x miles on United flights",
                multiplier=8.0,
                card_id=chase_united_quest.id
            ),
            MultiplierBenefit(
                category="United Purchases",
                description="3x miles on all other eligible United purchases",
                multiplier=3.0,
                card_id=chase_united_quest.id
            ),
            MultiplierBenefit(
                category="Renowned Hotels via United",
                description="5x miles on hotel stays when prepaying through Renowned Hotels and resorts for United cardmembers",
                multiplier=5.0,
                card_id=chase_united_quest.id
            ),
            MultiplierBenefit(
                category="Travel",
                description="2x miles on all other travel including airfare, trains, local transit, cruise lines, hotels, car rentals, taxicabs, resorts, ride share services and tolls",
                multiplier=2.0,
                card_id=chase_united_quest.id
            ),
            MultiplierBenefit(
                category="Dining",
                description="2x miles on dining including eligible delivery services",
                multiplier=2.0,
                card_id=chase_united_quest.id
            ),
            MultiplierBenefit(
                category="Streaming Services",
                description="2x miles on select streaming services",
                multiplier=2.0,
                card_id=chase_united_quest.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="1x miles on all other purchases",
                multiplier=1.0,
                card_id=chase_united_quest.id
            )
        ]

        # Add all Chase United Quest multiplier benefits
        for multiplier in united_quest_multipliers:
            db.session.add(multiplier)

        # CHASE UNITED QUEST - Credit Benefits (Statement Credits & Bonuses)
        united_quest_credits = [
            CreditBenefit(
                description="$200 United travel credit - Receive after account opening and on each account anniversary",
                credit_amount=200.0,
                frequency="Annual",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="Up to $150 in credits annually on prepaid hotel stays purchased directly through Renowned Hotels and Resorts for United Cardmembers",
                credit_amount=150.0,
                frequency="Annual",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="Up to $100 in credits each calendar year on rideshare purchases when paying with your United Quest Card (enrollment required)",
                credit_amount=100.0,
                frequency="Annual",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="Up to $80 in United travel credits annually when you book Avis or Budget car rentals directly through cars.united.com",
                credit_amount=80.0,
                frequency="Annual",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="Up to $180 Instacart credits each calendar year for purchases made directly through Instacart",
                credit_amount=180.0,
                frequency="Annual",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="Up to $150 in credits annually on flights purchased directly through JSX",
                credit_amount=150.0,
                frequency="Annual",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="70,000 bonus miles and 1,000 United Premier qualifying points after you spend $4,000 on purchases within the first 3 months from account opening",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="10,000-mile discount starting with your first anniversary and every anniversary thereafter, to use toward an eligible award flight",
                credit_amount=0.0,
                frequency="Annual (anniversary)",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="10,000-mile award flight discount after spending $20,000 each calendar year to use toward an eligible award flight",
                credit_amount=0.0,
                frequency="Annual (after $20k spend)",
                card_id=chase_united_quest.id
            ),
            CreditBenefit(
                description="Earn 1 Premier qualifying point (PQP) for every $20 spent on purchases, up to 18,000 PQP per year",
                credit_amount=0.0,
                frequency="PQP benefit",
                card_id=chase_united_quest.id
            )
        ]

        # Add all Chase United Quest credit benefits
        for credit in united_quest_credits:
            db.session.add(credit)

        # CHASE FREEDOM UNLIMITED - Multiplier Benefits (Cash Back Earning)
        freedom_unlimited_multipliers = [
            MultiplierBenefit(
                category="Chase Travel",
                description="5% cash back on travel booked through Chase Travel",
                multiplier=5.0,
                card_id=chase_freedom_unlimited.id
            ),
            MultiplierBenefit(
                category="Dining",
                description="3% cash back on dining",
                multiplier=3.0,
                card_id=chase_freedom_unlimited.id
            ),
            MultiplierBenefit(
                category="Drugstores",
                description="3% cash back in drugstores",
                multiplier=3.0,
                card_id=chase_freedom_unlimited.id
            ),
            MultiplierBenefit(
                category="All Purchases",
                description="1.5% cash back on every purchase",
                multiplier=1.5,
                card_id=chase_freedom_unlimited.id
            )
        ]

        # Add all Chase Freedom Unlimited multiplier benefits
        for multiplier in freedom_unlimited_multipliers:
            db.session.add(multiplier)

        # Note: Chase Freedom Unlimited has no credit benefits - it's a pure cash back card

        # WORLD OF HYATT - Multiplier Benefits (Points Earning)
        world_of_hyatt_multipliers = [
            MultiplierBenefit(
                category="Hyatt Hotels & Resorts",
                description="9x on qualifying purchases at Hyatt hotels and resorts",
                multiplier=9.0,
                card_id=world_of_hyatt.id
            ),
            MultiplierBenefit(
                category="Dining, Airlines, Gym & Transit",
                description="2x on dining, airline tickets purchased directly from the airline, gym memberships, and local transit and commuting",
                multiplier=2.0,
                card_id=world_of_hyatt.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="1x on all other purchases",
                multiplier=1.0,
                card_id=world_of_hyatt.id
            )
        ]

        # Add all World of Hyatt multiplier benefits
        for multiplier in world_of_hyatt_multipliers:
            db.session.add(multiplier)

        # WORLD OF HYATT - Credit Benefits (Free Nights & Status Benefits)
        world_of_hyatt_credits = [
            CreditBenefit(
                description="1 Free night at any Category 1-4 Hyatt hotel or resort annually each year after cardmember anniversary",
                credit_amount=0.0,
                frequency="Annual (anniversary)",
                card_id=world_of_hyatt.id
            ),
            CreditBenefit(
                description="Second free night if you spend $15,000 in a calendar year",
                credit_amount=0.0,
                frequency="Annual (after $15k spend)",
                card_id=world_of_hyatt.id
            ),
            CreditBenefit(
                description="Earn 2 tier-qualifying night credits towards your next tier status every time you spend $5,000 on the card",
                credit_amount=0.0,
                frequency="Per $5k spend",
                card_id=world_of_hyatt.id
            )
        ]

        # Add all World of Hyatt credit benefits
        for credit in world_of_hyatt_credits:
            db.session.add(credit)

        # VENMO CASH BACK - Multiplier Benefits (Cash Back Earning)
        venmo_cash_back_multipliers = [
            MultiplierBenefit(
                category="Top Spend Category",
                description="3% cash back on your top spend category",
                multiplier=3.0,
                card_id=venmo_cash_back.id
            ),
            MultiplierBenefit(
                category="Second Highest Category",
                description="2% cash back on the next highest spend category",
                multiplier=2.0,
                card_id=venmo_cash_back.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="1% cash back on all other eligible purchases",
                multiplier=1.0,
                card_id=venmo_cash_back.id
            )
        ]

        # Add all Venmo Cash Back multiplier benefits
        for multiplier in venmo_cash_back_multipliers:
            db.session.add(multiplier)

        # Note: Venmo Cash Back has no credit benefits - it's a pure cash back card

        # MARRIOTT BONVOY BOUNDLESS - Multiplier Benefits (Points Earning)
        marriott_boundless_multipliers = [
            MultiplierBenefit(
                category="Marriott Bonvoy Hotels",
                description="17x on hotels participating in Marriott Bonvoy",
                multiplier=17.0,
                card_id=marriott_bonvoy_boundless.id
            ),
            MultiplierBenefit(
                category="Gas, Grocery & Dining",
                description="3x on the first $6,000 spent in combined purchases annually on gas stations, grocery stores, and dining",
                multiplier=3.0,
                card_id=marriott_bonvoy_boundless.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="2x points on all other purchases",
                multiplier=2.0,
                card_id=marriott_bonvoy_boundless.id
            )
        ]

        # Add all Marriott Bonvoy Boundless multiplier benefits
        for multiplier in marriott_boundless_multipliers:
            db.session.add(multiplier)

        # MARRIOTT BONVOY BOUNDLESS - Credit Benefits (Free Nights & Status Benefits)
        marriott_boundless_credits = [
            CreditBenefit(
                description="3 free night awards after spending $3,000 on eligible purchases within 3 months of account opening",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=marriott_bonvoy_boundless.id
            ),
            CreditBenefit(
                description="Free night award every year after your account anniversary, valid for one-night hotel stay",
                credit_amount=0.0,
                frequency="Annual (anniversary)",
                card_id=marriott_bonvoy_boundless.id
            ),
            CreditBenefit(
                description="1 Elite night credit for every $5,000 you spend",
                credit_amount=0.0,
                frequency="Per $5k spend",
                card_id=marriott_bonvoy_boundless.id
            ),
            CreditBenefit(
                description="Gold status when you spend $35,000 on purchases each calendar year",
                credit_amount=0.0,
                frequency="Annual (after $35k spend)",
                card_id=marriott_bonvoy_boundless.id
            )
        ]

        # Add all Marriott Bonvoy Boundless credit benefits
        for credit in marriott_boundless_credits:
            db.session.add(credit)

        # HILTON HONORS SURPASS - Multiplier Benefits (Points Earning)
        hilton_surpass_multipliers = [
            MultiplierBenefit(
                category="Hilton Hotels & Resorts",
                description="12x bonus points on purchases made directly with hotels or resorts within the Hilton portfolio",
                multiplier=12.0,
                card_id=hilton_honors_surpass.id
            ),
            MultiplierBenefit(
                category="U.S. Restaurants, Gas & Supermarkets",
                description="6x bonus points at U.S. restaurants, U.S. gas stations, and U.S. supermarkets",
                multiplier=6.0,
                card_id=hilton_honors_surpass.id
            ),
            MultiplierBenefit(
                category="U.S. Online Retail",
                description="4x bonus points on U.S. online retail purchases",
                multiplier=4.0,
                card_id=hilton_honors_surpass.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="3x bonus points on all other eligible purchases",
                multiplier=3.0,
                card_id=hilton_honors_surpass.id
            )
        ]

        # Add all Hilton Honors Surpass multiplier benefits
        for multiplier in hilton_surpass_multipliers:
            db.session.add(multiplier)

        # HILTON HONORS SURPASS - Credit Benefits (Statement Credits & Status Benefits)
        hilton_surpass_credits = [
            CreditBenefit(
                description="130,000 bonus points after you spend $3,000 in eligible purchases on the card within your first 6 months of card membership",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=hilton_honors_surpass.id
            ),
            CreditBenefit(
                description="$50 in statement credits each quarter for purchases made directly with a property in the Hilton portfolio",
                credit_amount=50.0,
                frequency="Quarterly",
                card_id=hilton_honors_surpass.id
            ),
            CreditBenefit(
                description="One free night award after spending $15,000 in eligible purchases on your card in a calendar year",
                credit_amount=0.0,
                frequency="Annual (after $15k spend)",
                card_id=hilton_honors_surpass.id
            ),
            CreditBenefit(
                description="Upgrade to Diamond Status after spending $40,000 in eligible purchases on the card in a calendar year",
                credit_amount=0.0,
                frequency="Annual (after $40k spend)",
                card_id=hilton_honors_surpass.id
            )
        ]

        # Add all Hilton Honors Surpass credit benefits
        for credit in hilton_surpass_credits:
            db.session.add(credit)

        # HILTON HONORS ASPIRE - Multiplier Benefits (Points Earning)
        hilton_aspire_multipliers = [
            MultiplierBenefit(
                category="Hilton Hotels & Resorts",
                description="14x bonus points on purchases made directly with hotels and resorts within the Hilton portfolio",
                multiplier=14.0,
                card_id=hilton_honors_aspire.id
            ),
            MultiplierBenefit(
                category="Flights, Car Rentals & U.S. Restaurants",
                description="7x bonus points on flights booked directly with airlines or AmexTravel.com, car rentals booked directly from select companies, and at U.S. restaurants",
                multiplier=7.0,
                card_id=hilton_honors_aspire.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="3x bonus points on all other eligible purchases",
                multiplier=3.0,
                card_id=hilton_honors_aspire.id
            )
        ]

        # Add all Hilton Honors Aspire multiplier benefits
        for multiplier in hilton_aspire_multipliers:
            db.session.add(multiplier)

        # HILTON HONORS ASPIRE - Credit Benefits (Statement Credits & Hotel Benefits)
        hilton_aspire_credits = [
            CreditBenefit(
                description="150,000 bonus points after you spend $6,000 in eligible purchases on the card in your first 6 months of card membership",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=hilton_honors_aspire.id
            ),
            CreditBenefit(
                description="Up to $200 in statement credits semi-annually for eligible purchases made directly with participating Hilton Resorts",
                credit_amount=200.0,
                frequency="Semi-annually",
                card_id=hilton_honors_aspire.id
            ),
            CreditBenefit(
                description="$50 in statement credits each quarter on flight purchases made directly with an airline or through AmexTravel.com",
                credit_amount=50.0,
                frequency="Quarterly",
                card_id=hilton_honors_aspire.id
            ),
            CreditBenefit(
                description="$209 per calendar year in statement credits for a CLEAR plus membership",
                credit_amount=209.0,
                frequency="Annual",
                card_id=hilton_honors_aspire.id
            ),
            CreditBenefit(
                description="$100 resort credit for qualifying charges at Waldorf Astoria and Conrad Hotels when you book a 2 night minimum stay with your card",
                credit_amount=100.0,
                frequency="Per qualifying stay",
                card_id=hilton_honors_aspire.id
            ),
            CreditBenefit(
                description="Free Night Reward from Hilton after you spend $30,000 in purchases on your Card in a calendar year",
                credit_amount=0.0,
                frequency="Annual (after $30k spend)",
                card_id=hilton_honors_aspire.id
            ),
            CreditBenefit(
                description="Additional Free Night Reward from Hilton after you spend $60,000 in purchases on your Card in a calendar year",
                credit_amount=0.0,
                frequency="Annual (after $60k spend)",
                card_id=hilton_honors_aspire.id
            )
        ]

        # Add all Hilton Honors Aspire credit benefits
        for credit in hilton_aspire_credits:
            db.session.add(credit)

        # ATMOS REWARDS ASCENT - Multiplier Benefits (Points Earning)
        atmos_ascent_multipliers = [
            MultiplierBenefit(
                category="Alaska Airlines & Hawaiian Airlines",
                description="3x points for eligible purchases on Alaska Airlines and Hawaiian Airlines",
                multiplier=3.0,
                card_id=atmos_rewards_ascent.id
            ),
            MultiplierBenefit(
                category="Dining",
                description="3x points for eligible purchases on dining",
                multiplier=3.0,
                card_id=atmos_rewards_ascent.id
            ),
            MultiplierBenefit(
                category="Foreign Purchases",
                description="3x points for eligible foreign purchases",
                multiplier=3.0,
                card_id=atmos_rewards_ascent.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="1x points on all other purchases",
                multiplier=1.0,
                card_id=atmos_rewards_ascent.id
            )
        ]

        # Add all Atmos Rewards Ascent multiplier benefits
        for multiplier in atmos_ascent_multipliers:
            db.session.add(multiplier)

        # ATMOS REWARDS ASCENT - Credit Benefits (Statement Credits & Status Benefits)
        atmos_ascent_credits = [
            CreditBenefit(
                description="100,000 bonus points after spending $6,000 or more on purchases within the first 90 days after account opening",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=atmos_rewards_ascent.id
            ),
            CreditBenefit(
                description="25,000 point Global Companion Award after spending $6,000 or more on purchases within the first 90 days after account opening",
                credit_amount=0.0,
                frequency="One-time signup bonus",
                card_id=atmos_rewards_ascent.id
            ),
            CreditBenefit(
                description="Up to $120 Airport Security Credit every four years in connection with the TSA PreCheck or Global Entry trusted traveler programs",
                credit_amount=120.0,
                frequency="Every 4 years",
                card_id=atmos_rewards_ascent.id
            ),
            CreditBenefit(
                description="10% rewards bonus on all points earned from card purchases with an eligible Bank of America account",
                credit_amount=0.0,
                frequency="Per purchase (with BOA account)",
                card_id=atmos_rewards_ascent.id
            ),
            CreditBenefit(
                description="10,000 status points every year on your account anniversary",
                credit_amount=0.0,
                frequency="Annual (anniversary)",
                card_id=atmos_rewards_ascent.id
            ),
            CreditBenefit(
                description="Earn 1 status point for every $2 spent on purchases",
                credit_amount=0.0,
                frequency="Per purchase",
                card_id=atmos_rewards_ascent.id
            )
        ]

        # Add all Atmos Rewards Ascent credit benefits
        for credit in atmos_ascent_credits:
            db.session.add(credit)

        # U.S. BANK CASH BACK - Multiplier Benefits (Cash Back Earning)
        us_bank_cash_back_multipliers = [
            MultiplierBenefit(
                category="Apple Pay Purchases",
                description="4.5% cash back on all Apple Pay purchases through December 2025 (limited-time promotion)",
                multiplier=4.5,
                card_id=us_bank_cash_back.id
            )
        ]

        # Add all U.S. Bank Cash Back multiplier benefits
        for multiplier in us_bank_cash_back_multipliers:
            db.session.add(multiplier)

        # U.S. BANK CASH BACK - Credit Benefits (No additional credits specified)
        # This card appears to be focused on the Apple Pay promotion with no additional credit benefits
        us_bank_cash_back_credits = []

        # Add all U.S. Bank Cash Back credit benefits (none in this case)
        for credit in us_bank_cash_back_credits:
            db.session.add(credit)

        # Save everything to the database
        db.session.commit()
        print("Sample data added successfully!")
        print("Added 12 credit cards with detailed benefits for Chase Sapphire Reserve, American Express Gold, Capital One VentureX, Chase United Quest, Chase Freedom Unlimited, World of Hyatt, Venmo Cash Back, Marriott Bonvoy Boundless, Hilton Honors Surpass, Hilton Honors Aspire, Atmos Rewards Ascent, and U.S. Bank Cash Back!")

# --- DATABASE INTERACTION FUNCTIONS ---
# These functions help us read and write data to our database

def get_all_cards():
    """
    Gets all credit cards from the database.
    Think of it like opening the filing cabinet and getting all the card folders.
    """
    return Card.query.all()

def get_card_by_id(card_id):
    """
    Gets a specific card by its ID number.
    Like looking up a specific folder by its label number.
    """
    return Card.query.get(card_id)

def get_benefits_for_card(card_id):
    """
    Gets all benefits for a specific card.
    Like opening a card folder and listing all the benefit papers inside.
    """
    return Benefit.query.filter_by(card_id=card_id).all()

def add_new_card(card_name):
    """
    Adds a new credit card to the database.
    Like creating a new folder and putting it in the filing cabinet.
    """
    new_card = Card(name=card_name)
    db.session.add(new_card)
    db.session.commit()
    return new_card

def add_benefit_to_card(card_id, description, value, frequency):
    """
    Adds a new benefit to an existing card.
    Like putting a new benefit paper into a card's folder.
    """
    new_benefit = Benefit(
        description=description,
        value=value,
        frequency=frequency,
        card_id=card_id
    )
    db.session.add(new_benefit)
    db.session.commit()
    return new_benefit

# --- WEB ROUTES ---
# These are the web pages that users can visit

# This "decorator" creates a URL route. It's a signpost.
# It says "If someone visits the homepage ('/'), run the function below."
@app.route('/')
def dashboard():
    """
    Main dashboard with card wallet and progress tracking - NOW WITH REAL DATABASE!
    """
    # Use real enhanced cards or fallback to sample data
    if CardEnhanced.query.first():
        # NEW: Use real database data
        cards = get_real_cards()
        signup_bonuses = get_real_signup_bonuses()
        spending_bonuses = get_real_spending_bonuses()
        annual_credits = get_real_credits_by_frequency('annual')
        semiannual_credits = get_real_credits_by_frequency('semi-annual')
        quarterly_credits = get_real_credits_by_frequency('quarterly')
        monthly_credits = get_real_credits_by_frequency('monthly')
        onetime_credits = get_real_credits_by_frequency('onetime')

        # Get used credits for each frequency
        used_annual_credits = get_used_credits_by_frequency('annual')
        used_semiannual_credits = get_used_credits_by_frequency('semi-annual')
        used_quarterly_credits = get_used_credits_by_frequency('quarterly')
        used_monthly_credits = get_used_credits_by_frequency('monthly')
        used_onetime_credits = get_used_credits_by_frequency('onetime')
    else:
        # Fallback to sample data if enhanced data not available
        cards = get_all_cards()
        display_cards = []
        for card in cards:
            brand_class = get_card_brand_class(card.name)
            multiplier_count = MultiplierBenefit.query.filter_by(card_id=card.id).count()
            credit_count = CreditBenefit.query.filter_by(card_id=card.id).count()

            display_cards.append({
                'id': card.id,
                'name': card.name,
                'issuer': get_card_issuer(card.name),
                'brand_class': brand_class,
                'total_benefits': multiplier_count + credit_count,
                'last_four': '1234'
            })
        cards = display_cards

        signup_bonuses = get_sample_signup_bonuses()
        spending_bonuses = get_sample_spending_bonuses()
        annual_credits = get_sample_annual_credits()
        quarterly_credits = get_sample_quarterly_credits()
        monthly_credits = get_sample_monthly_credits()
        onetime_credits = get_sample_onetime_credits()

        # No used credits in sample data
        used_annual_credits = []
        used_semiannual_credits = []
        used_quarterly_credits = []
        used_monthly_credits = []
        used_onetime_credits = []

    return render_template('dashboard.html',
                         cards=cards,
                         signup_bonuses=signup_bonuses,
                         spending_bonuses=spending_bonuses,
                         annual_credits=annual_credits,
                         semiannual_credits=semiannual_credits,
                         quarterly_credits=quarterly_credits,
                         monthly_credits=monthly_credits,
                         onetime_credits=onetime_credits,
                         used_annual_credits=used_annual_credits,
                         used_semiannual_credits=used_semiannual_credits,
                         used_quarterly_credits=used_quarterly_credits,
                         used_monthly_credits=used_monthly_credits,
                         used_onetime_credits=used_onetime_credits)

@app.route('/cards')
def list_cards():
    """
    A page that shows just the card names in a simple list.
    Think of it like a table of contents for your filing cabinet.
    """
    cards = get_all_cards()
    html = '<h1>All Credit Cards</h1>'
    html += '<ul>'

    for card in cards:
        html += f'<li><a href="/card/{card.id}">{card.name}</a></li>'

    html += '</ul>'
    html += '<p><a href="/">Back to Home</a></p>'
    return html

@app.route('/card/<int:card_id>')
def show_card_details(card_id):
    """
    Shows detailed information about a specific card using the new UI.
    """
    card = get_card_by_id(card_id)

    if not card:
        return render_template('card_details.html',
                             card={'name': 'Card Not Found', 'issuer': '', 'total_benefits': 0},
                             multiplier_benefits=[],
                             credit_benefits=[])

    # Get multiplier benefits
    multiplier_benefits = MultiplierBenefit.query.filter_by(card_id=card_id).all()

    # Get credit benefits
    credit_benefits = CreditBenefit.query.filter_by(card_id=card_id).all()

    # Transform card data for display
    card_data = {
        'id': card.id,
        'name': card.name,
        'issuer': get_card_issuer(card.name),
        'total_benefits': len(multiplier_benefits) + len(credit_benefits)
    }

    return render_template('card_details.html',
                         card=card_data,
                         multiplier_benefits=multiplier_benefits,
                         credit_benefits=credit_benefits)

# === API ENDPOINTS (JSON Data Services) ===
# These endpoints return JSON data instead of HTML pages

@app.route('/api/cards', methods=['GET'])
def api_get_all_cards():
    """
    API Endpoint: Get all cards as JSON data
    Like asking "Give me a list of all my credit cards"
    Returns: JSON array of all cards with basic info
    """
    try:
        cards = Card.query.all()
        cards_data = []

        for card in cards:
            # Count benefits for each card
            multiplier_count = MultiplierBenefit.query.filter_by(card_id=card.id).count()
            credit_count = CreditBenefit.query.filter_by(card_id=card.id).count()

            card_info = {
                'id': card.id,
                'name': card.name,
                'multiplier_benefits_count': multiplier_count,
                'credit_benefits_count': credit_count,
                'total_benefits': multiplier_count + credit_count
            }
            cards_data.append(card_info)

        return jsonify({
            'success': True,
            'total_cards': len(cards_data),
            'cards': cards_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/benefits/<int:card_id>', methods=['GET'])
def api_get_card_benefits(card_id):
    """
    API Endpoint: Get all benefits for a specific card
    Like asking "What benefits does my Chase Sapphire Reserve have?"
    Returns: JSON object with multipliers and credits for the card
    """
    try:
        # Check if card exists
        card = Card.query.get(card_id)
        if not card:
            return jsonify({
                'success': False,
                'error': f'Card with ID {card_id} not found'
            }), 404

        # Get multiplier benefits
        multipliers = MultiplierBenefit.query.filter_by(card_id=card_id).all()
        multiplier_data = []
        for multiplier in multipliers:
            multiplier_data.append({
                'id': multiplier.id,
                'category': multiplier.category,
                'multiplier': multiplier.multiplier,
                'description': multiplier.description
            })

        # Get credit benefits
        credits = CreditBenefit.query.filter_by(card_id=card_id).all()
        credit_data = []
        for credit in credits:
            credit_data.append({
                'id': credit.id,
                'description': credit.description,
                'credit_amount': credit.credit_amount,
                'frequency': credit.frequency
            })

        return jsonify({
            'success': True,
            'card': {
                'id': card.id,
                'name': card.name
            },
            'multiplier_benefits': multiplier_data,
            'credit_benefits': credit_data,
            'total_benefits': len(multiplier_data) + len(credit_data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/usage', methods=['GET', 'POST'])
def api_usage():
    """
    API Endpoint: Track benefit usage
    GET: View all your benefit usage history
    POST: Record when you use a benefit (like getting a statement credit)
    """
    if request.method == 'GET':
        # GET: Return usage history
        try:
            usage_records = Usage.query.order_by(Usage.date_used.desc()).all()
            usage_data = []

            for usage in usage_records:
                # Get card name
                card = Card.query.get(usage.card_id)
                card_name = card.name if card else "Unknown Card"

                usage_info = {
                    'id': usage.id,
                    'card_id': usage.card_id,
                    'card_name': card_name,
                    'benefit_type': usage.benefit_type,
                    'benefit_id': usage.benefit_id,
                    'amount': usage.amount,
                    'description': usage.description,
                    'date_used': usage.date_used.isoformat()
                }
                usage_data.append(usage_info)

            return jsonify({
                'success': True,
                'total_usage_records': len(usage_data),
                'usage_history': usage_data
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    elif request.method == 'POST':
        # POST: Record new usage
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['card_id', 'benefit_type', 'benefit_id', 'amount', 'description']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }), 400

            # Check if card exists
            card = Card.query.get(data['card_id'])
            if not card:
                return jsonify({
                    'success': False,
                    'error': f'Card with ID {data["card_id"]} not found'
                }), 404

            # Create new usage record
            new_usage = Usage(
                card_id=data['card_id'],
                benefit_type=data['benefit_type'],
                benefit_id=data['benefit_id'],
                amount=float(data['amount']),
                description=data['description']
            )

            db.session.add(new_usage)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Usage recorded successfully',
                'usage_id': new_usage.id,
                'card_name': card.name
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/used-credits/<frequency>', methods=['GET'])
def get_used_credits_api(frequency):
    """
    API Endpoint: Get used credits for a specific frequency
    """
    try:
        # Map the frequency names to match existing function expectations
        frequency_map = {
            'semiannual': 'semi-annual',
            'onetime': 'onetime'
        }

        mapped_frequency = frequency_map.get(frequency, frequency)

        # Validate frequency
        valid_frequencies = ['annual', 'semi-annual', 'quarterly', 'monthly', 'onetime']
        if mapped_frequency not in valid_frequencies:
            return jsonify({
                'success': False,
                'error': 'Invalid frequency. Must be one of: annual, semiannual, quarterly, monthly, onetime'
            }), 400

        # Get used credits using existing function
        used_credits = get_used_credits_by_frequency(mapped_frequency)

        # Format the data for the frontend
        formatted_credits = []
        for credit in used_credits:
            formatted_credit = {
                'benefit_name': credit.get('benefit_name', ''),
                'card_name': credit.get('card_name', ''),
                'credit_amount': currency_filter(credit.get('credit_amount', 0)),
                'description': credit.get('description', ''),
                'has_progress': credit.get('has_progress', False),
                'progress_percent': credit.get('progress_percent', 0),
                'current_amount': currency_filter(credit.get('current_amount', 0)),
                'required_amount': currency_filter(credit.get('required_amount', 0)),
                'reset_date': credit.get('reset_date', '')
            }
            formatted_credits.append(formatted_credit)

        return jsonify({
            'success': True,
            'credits': formatted_credits,
            'count': len(formatted_credits)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === NEW INTERACTIVE ROUTES ===

@app.route('/add-card', methods=['POST'])
def add_card():
    """Add a new credit card"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('vendor') or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Card vendor and name are required'
            }), 400

        # Create full card name
        vendor = data['vendor']
        name = data['name']
        full_name = f"{vendor} {name}" if vendor != 'Other' else name

        # Check if card already exists
        existing_card = Card.query.filter_by(name=full_name).first()
        if existing_card:
            return jsonify({
                'success': False,
                'error': 'A card with this name already exists'
            }), 400

        # Create new card
        new_card = Card(
            name=full_name,
            last_four=data.get('last_four', '0000')
        )

        db.session.add(new_card)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Card added successfully',
            'card_id': new_card.id,
            'card_name': new_card.name
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/mark-credit-used', methods=['POST'])
def mark_credit_used():
    """Mark a credit as used"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['type', 'card_name', 'identifier']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        credit_type = data['type']
        card_name = data['card_name']
        identifier = data['identifier']

        # Check if credit status record exists
        credit_status = CreditStatus.query.filter_by(
            card_name=card_name,
            credit_type=credit_type,
            credit_identifier=identifier
        ).first()

        if credit_status:
            # Update existing record
            credit_status.status = 'used'
            credit_status.last_updated = datetime.datetime.utcnow()
        else:
            # Create new record and mark as used
            credit_status = CreditStatus(
                card_name=card_name,
                credit_type=credit_type,
                credit_identifier=identifier,
                status='used'
            )
            db.session.add(credit_status)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Credit {identifier} for {card_name} marked as used'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/mark-signup-bonus-complete', methods=['POST'])
def mark_signup_bonus_complete():
    """Mark a signup bonus as complete"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['card_name', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        card_name = data['card_name']
        description = data['description']

        # Find the card first
        card = CardEnhanced.query.filter_by(name=card_name).first()
        if not card:
            return jsonify({
                'success': False,
                'error': f'Card not found: {card_name}'
            }), 404

        # Find the signup bonus
        signup_bonus = SignupBonus.query.filter_by(
            card_id=card.id,
            description=description
        ).first()

        if not signup_bonus:
            return jsonify({
                'success': False,
                'error': f'Signup bonus not found for {card_name}'
            }), 404

        # Update the status to completed
        signup_bonus.status = 'completed'
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Signup bonus for {card_name} marked as complete'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/mark-spending-bonus-complete', methods=['POST'])
def mark_spending_bonus_complete():
    """Mark a spending bonus as complete and convert it to an annual credit"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['card_name', 'category', 'multiplier']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        card_name = data['card_name']
        category = data['category']
        multiplier = data['multiplier']

        # Find the card first
        card = CardEnhanced.query.filter_by(name=card_name).first()
        if not card:
            return jsonify({
                'success': False,
                'error': f'Card not found: {card_name}'
            }), 404

        # Find the spending bonus (from other_bonus table)
        spending_bonus = OtherBonus.query.filter_by(
            card_id=card.id,
            bonus_type='threshold',
            description=category,
            status='pending'
        ).first()

        if not spending_bonus:
            return jsonify({
                'success': False,
                'error': f'Spending bonus not found for {card_name}: {category}'
            }), 404

        # Update the spending bonus status to completed
        spending_bonus.status = 'completed'
        spending_bonus.completed_date = datetime.datetime.utcnow()

        # Create a new annual credit based on the spending bonus reward
        # Calculate expiry date: 1 year from completion date
        expiry_date = datetime.datetime.utcnow() + relativedelta(years=1)

        # Create the credit benefit
        credit_benefit = CreditBenefit2(
            card_id=card.id,
            benefit_name=f"{category} Reward",
            credit_amount=1,  # Set to 1 as placeholder, display will use original_multiplier
            description=f"Earned from completing: {category} ({card_name})",
            frequency='annual',
            reset_date=expiry_date.date(),
            has_progress=False,
            original_multiplier=multiplier,  # Store original format like "1 night", "2 credits"
            from_spending_bonus=True,  # Mark this as coming from spending bonus
            spending_bonus_id=spending_bonus.id  # Reference for undo functionality
        )

        # Save both changes
        db.session.add(credit_benefit)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Spending bonus for {card_name} marked as complete and {multiplier} added to annual credits (expires {expiry_date.strftime("%B %d, %Y")})'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/undo-bonus-completion', methods=['POST'])
def undo_bonus_completion():
    """Undo a spending bonus completion by removing the credit and restoring the original bonus"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['card_name', 'benefit_name', 'spending_bonus_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        card_name = data['card_name']
        benefit_name = data['benefit_name']
        spending_bonus_id = data['spending_bonus_id']

        # Find the card
        card = CardEnhanced.query.filter_by(name=card_name).first()
        if not card:
            return jsonify({
                'success': False,
                'error': f'Card not found: {card_name}'
            }), 404

        # Find the credit benefit that was created from spending bonus
        credit_benefit = CreditBenefit2.query.filter_by(
            card_id=card.id,
            benefit_name=benefit_name,
            from_spending_bonus=True,
            spending_bonus_id=spending_bonus_id
        ).first()

        if not credit_benefit:
            return jsonify({
                'success': False,
                'error': f'Credit benefit not found: {benefit_name} for {card_name}'
            }), 404

        # Find the completed spending bonus
        spending_bonus = OtherBonus.query.get(spending_bonus_id)
        if not spending_bonus:
            return jsonify({
                'success': False,
                'error': f'Original spending bonus not found (ID: {spending_bonus_id})'
            }), 404

        # Remove the credit benefit
        db.session.delete(credit_benefit)

        # Restore the spending bonus to pending status
        spending_bonus.status = 'pending'
        spending_bonus.completed_date = None

        # Commit all changes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully undone bonus completion for {card_name}. The spending bonus has been restored and the credit removed.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/reset-annual-spending-bonuses', methods=['POST'])
def manual_reset_annual_spending_bonuses():
    """Manual route to trigger annual spending bonus reset (for testing)"""
    try:
        reset_annual_spending_bonuses()
        return jsonify({
            'success': True,
            'message': 'Annual spending bonus reset completed successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/completed-bonuses', methods=['GET'])
def get_completed_bonuses():
    """Get all completed signup bonuses"""
    try:
        completed_bonuses = get_completed_signup_bonuses()

        return jsonify({
            'success': True,
            'bonuses': completed_bonuses
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/mark-signup-bonus-incomplete', methods=['POST'])
def mark_signup_bonus_incomplete():
    """Mark a signup bonus as incomplete (reverse from completed status)"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['card_name', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        card_name = data['card_name']
        description = data['description']

        # Find the card first
        card = CardEnhanced.query.filter_by(name=card_name).first()
        if not card:
            return jsonify({
                'success': False,
                'error': f'Card not found: {card_name}'
            }), 404

        # Find the signup bonus
        signup_bonus = SignupBonus.query.filter_by(
            card_id=card.id,
            description=description
        ).first()

        if not signup_bonus:
            return jsonify({
                'success': False,
                'error': f'Signup bonus not found for {card_name}'
            }), 404

        # Update the status back to in-progress or not-started
        # If they have some progress, mark as in-progress, otherwise not-started
        if signup_bonus.current_spend > 0:
            signup_bonus.status = 'in-progress'
        else:
            signup_bonus.status = 'not-started'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Signup bonus for {card_name} marked as incomplete'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/mark-credit-available', methods=['POST'])
def mark_credit_available():
    """Mark a credit as available (reverse from used status)"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['card_name', 'identifier']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        card_name = data['card_name']
        identifier = data['identifier']

        # Find the credit status record
        credit_status = CreditStatus.query.filter_by(
            card_name=card_name,
            credit_identifier=identifier
        ).first()

        if credit_status:
            # Update existing record to available
            credit_status.status = 'available'
            credit_status.last_updated = datetime.datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Credit {identifier} for {card_name} marked as available'
            }), 200
        else:
            # No record found - credit was already available
            return jsonify({
                'success': True,
                'message': f'Credit {identifier} for {card_name} was already available'
            }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === HELPER FUNCTIONS FOR NEW UI ===

def get_credit_status(card_name, credit_type, credit_identifier):
    """Get the current status of a credit from the database"""
    credit_status = CreditStatus.query.filter_by(
        card_name=card_name,
        credit_type=credit_type,
        credit_identifier=credit_identifier
    ).first()

    if credit_status:
        return credit_status.status
    else:
        return 'available'  # Default status if not found

def get_card_brand_class(card_name):
    """Get CSS class for card brand styling"""
    name_lower = card_name.lower()
    if 'chase' in name_lower:
        return 'chase'
    elif 'amex' in name_lower or 'american express' in name_lower:
        return 'amex'
    elif 'capital one' in name_lower:
        return 'capital-one'
    elif 'marriott' in name_lower:
        return 'marriott'
    elif 'hilton' in name_lower:
        return 'hilton'
    elif 'venmo' in name_lower:
        return 'venmo'
    elif 'hyatt' in name_lower:
        return 'hyatt'
    elif 'atmos' in name_lower:
        return 'atmos'
    elif 'u.s. bank' in name_lower:
        return 'us-bank'
    else:
        return 'default'

def get_card_issuer(card_name):
    """Get card issuer from card name"""
    name_lower = card_name.lower()
    if 'chase' in name_lower:
        return 'Chase'
    elif 'amex' in name_lower or 'american express' in name_lower:
        return 'American Express'
    elif 'capital one' in name_lower:
        return 'Capital One'
    elif 'marriott' in name_lower:
        return 'Chase'
    elif 'hilton' in name_lower:
        return 'American Express'
    elif 'venmo' in name_lower:
        return 'Synchrony'
    elif 'hyatt' in name_lower:
        return 'Chase'
    elif 'atmos' in name_lower:
        return 'Bank of America'
    elif 'u.s. bank' in name_lower:
        return 'U.S. Bank'
    else:
        return 'Unknown'

def get_sample_signup_bonuses():
    """Sample signup bonus data with progress tracking"""
    return [
        {
            'card_name': 'Chase Sapphire Reserve',
            'bonus_amount': '60,000 points',
            'description': 'Spend $4,000 in first 3 months',
            'required_spend': 4000,
            'current_spend': 2800,
            'progress_percent': 70,
            'deadline': 'March 15, 2025',
            'status': 'in-progress',
            'status_text': 'In Progress'
        },
        {
            'card_name': 'American Express Gold',
            'bonus_amount': '60,000 points',
            'description': 'Spend $4,000 in first 6 months',
            'required_spend': 4000,
            'current_spend': 4000,
            'progress_percent': 100,
            'deadline': 'Completed',
            'status': 'completed',
            'status_text': 'Completed'
        },
        {
            'card_name': 'Hilton Honors Aspire',
            'bonus_amount': '150,000 points',
            'description': 'Spend $6,000 in first 6 months',
            'required_spend': 6000,
            'current_spend': 750,
            'progress_percent': 12,
            'deadline': 'June 20, 2025',
            'status': 'available',
            'status_text': 'Available'
        }
    ]

def get_sample_monthly_bonuses():
    """Sample monthly bonus data"""
    return [
        {
            'card_name': 'Chase Freedom Flex',
            'category': 'Gas Stations',
            'multiplier': 5,
            'description': '5% cash back on gas, up to $1,500 quarterly',
            'monthly_cap': 500,
            'current_spend': 320,
            'progress_percent': 64,
            'reset_date': 'January 1, 2025',
            'status': 'in-progress',
            'status_text': 'Active'
        }
    ]

def get_sample_quarterly_bonuses():
    """Sample quarterly bonus data"""
    return [
        {
            'card_name': 'Hilton Honors Aspire',
            'category': 'Airline Credits',
            'multiplier': 'Credit',
            'description': '$50 quarterly airline incidental credit',
            'quarterly_cap': 50,
            'current_spend': 0,
            'progress_percent': 0,
            'reset_date': 'April 1, 2025',
            'status': 'available',
            'status_text': 'Available'
        },
        {
            'card_name': 'Chase Freedom',
            'category': 'Rotating Categories',
            'multiplier': 5,
            'description': '5% cash back on rotating categories, up to $1,500',
            'quarterly_cap': 1500,
            'current_spend': 890,
            'progress_percent': 59,
            'reset_date': 'April 1, 2025',
            'status': 'in-progress',
            'status_text': 'Active'
        }
    ]

def get_sample_annual_bonuses():
    """Sample annual bonus data"""
    return [
        {
            'card_name': 'Chase Sapphire Reserve',
            'benefit_name': 'Travel Credit',
            'credit_amount': 300,
            'description': '$300 annual travel credit',
            'required_amount': 300,
            'current_amount': 150,
            'progress_percent': 50,
            'reset_date': 'December 1, 2025',
            'has_progress': True,
            'status': 'in-progress',
            'status_text': 'Active'
        },
        {
            'card_name': 'World of Hyatt',
            'benefit_name': 'Free Night Award',
            'bonus_amount': '1 Free Night',
            'description': 'Annual free night certificate (up to 40,000 points)',
            'has_progress': False,
            'reset_date': 'Card Anniversary',
            'status': 'available',
            'status_text': 'Available'
        }
    ]

def get_sample_spending_bonuses():
    """Sample other spending bonuses data"""
    return [
        {
            'card_name': 'Chase Freedom',
            'category': 'Rotating Categories',
            'multiplier': 5,
            'description': '5% cash back on rotating categories, up to $1,500',
            'cap_amount': 1500,
            'current_spend': 890,
            'progress_percent': 59,
            'reset_date': 'April 1, 2025',
            'status': 'in-progress',
            'status_text': 'In Progress'
        },
        {
            'card_name': 'Discover it',
            'category': 'Gas Stations',
            'multiplier': 5,
            'description': '5% cash back on gas stations this quarter',
            'cap_amount': 1500,
            'current_spend': 320,
            'progress_percent': 21,
            'reset_date': 'April 1, 2025',
            'status': 'in-progress',
            'status_text': 'In Progress'
        }
    ]

def get_sample_annual_credits():
    """Sample annual credits data with dynamic status from database"""
    credits = [
        {
            'card_name': 'Chase Sapphire Reserve',
            'benefit_name': 'Travel Credit',
            'credit_amount': 300,
            'description': '$300 annual travel credit',
            'required_amount': 300,
            'current_amount': 150,
            'progress_percent': 50,
            'reset_date': 'December 1, 2025',
            'has_progress': True
        },
        {
            'card_name': 'Capital One VentureX',
            'benefit_name': 'Travel Credit',
            'credit_amount': 300,
            'description': '$300 annual travel credit for Capital One Travel',
            'required_amount': 300,
            'current_amount': 0,
            'progress_percent': 0,
            'reset_date': 'Card Anniversary',
            'has_progress': True
        }
    ]

    # Add dynamic status from database
    for credit in credits:
        status = get_credit_status(credit['card_name'], 'annual', credit['benefit_name'])
        credit['status'] = status
        credit['status_text'] = 'Used' if status == 'used' else 'Available'

    return credits

def get_sample_quarterly_credits():
    """Sample quarterly credits data with dynamic status from database"""
    credits = [
        {
            'card_name': 'Hilton Honors Aspire',
            'benefit_name': 'Airline Incidental Credit',
            'category': 'Airline Credits',
            'credit_amount': 50,
            'description': '$50 quarterly airline incidental credit',
            'reset_date': 'April 1, 2025'
        },
        {
            'card_name': 'American Express Platinum',
            'benefit_name': 'PayPal Credit',
            'category': 'Digital Credits',
            'credit_amount': 30,
            'description': '$30 quarterly PayPal credit',
            'reset_date': 'April 1, 2025'
        },
        {
            'card_name': 'American Express Gold',
            'benefit_name': 'Resy Restaurant Credit',
            'category': 'Dining Credits',
            'credit_amount': 25,
            'description': '$25 quarterly Resy restaurant credit',
            'reset_date': 'April 1, 2025'
        }
    ]

    # Add dynamic status from database
    for credit in credits:
        status = get_credit_status(credit['card_name'], 'quarterly', credit['benefit_name'])
        credit['status'] = status
        credit['status_text'] = 'Used' if status == 'used' else 'Available'

    return credits

def get_sample_monthly_credits():
    """Sample monthly credits data with dynamic status from database"""
    credits = [
        {
            'card_name': 'Chase United Quest',
            'benefit_name': 'Streaming Service Credit',
            'category': 'Streaming Credits',
            'credit_amount': 15,
            'description': '$15 monthly streaming service credit',
            'reset_date': 'January 1, 2025'
        }
    ]

    # Add dynamic status from database
    for credit in credits:
        status = get_credit_status(credit['card_name'], 'monthly', credit['benefit_name'])
        credit['status'] = status
        credit['status_text'] = 'Used' if status == 'used' else 'Available'

    return credits

def get_sample_onetime_credits():
    """Sample one-time credits data with dynamic status from database"""
    credits = [
        {
            'card_name': 'Capital One VentureX',
            'benefit_name': 'TSA PreCheck Credit',
            'credit_amount': 120,
            'description': '$120 Global Entry or TSA PreCheck credit (every 4 years)'
        },
        {
            'card_name': 'Chase Sapphire Reserve',
            'benefit_name': 'Global Entry Credit',
            'credit_amount': 100,
            'description': '$100 Global Entry credit (every 4 years)'
        }
    ]

    # Add dynamic status from database
    for credit in credits:
        status = get_credit_status(credit['card_name'], 'onetime', credit['benefit_name'])
        credit['status'] = status
        credit['status_text'] = 'Used' if status == 'used' else 'Available'

    return credits

# === REAL DATABASE FUNCTIONS ===

def initialize_enhanced_data():
    """Initialize the new enhanced database with sample data"""
    with app.app_context():
        # Check if we already have enhanced data
        if CardEnhanced.query.first():
            print("Enhanced data already exists!")
            return

        # Create all 12 enhanced cards with proper attributes
        cards_data = [
            {'name': 'Chase Sapphire Reserve', 'issuer': 'Chase', 'brand_class': 'chase', 'last_four': '5432'},
            {'name': 'American Express Gold', 'issuer': 'American Express', 'brand_class': 'amex', 'last_four': '1001'},
            {'name': 'Capital One VentureX', 'issuer': 'Capital One', 'brand_class': 'capital-one', 'last_four': '7890'},
            {'name': 'Chase United Quest', 'issuer': 'Chase', 'brand_class': 'chase', 'last_four': '2468'},
            {'name': 'Chase Freedom Unlimited', 'issuer': 'Chase', 'brand_class': 'chase', 'last_four': '1357'},
            {'name': 'World of Hyatt', 'issuer': 'Chase', 'brand_class': 'hyatt', 'last_four': '9753'},
            {'name': 'Venmo Cash Back', 'issuer': 'Synchrony', 'brand_class': 'venmo', 'last_four': '4682'},
            {'name': 'Marriott Bonvoy Boundless', 'issuer': 'Chase', 'brand_class': 'marriott', 'last_four': '7531'},
            {'name': 'Hilton Honors Surpass', 'issuer': 'American Express', 'brand_class': 'hilton', 'last_four': '8642'},
            {'name': 'Hilton Honors Aspire', 'issuer': 'American Express', 'brand_class': 'hilton', 'last_four': '9753'},
            {'name': 'Atmos Rewards Ascent', 'issuer': 'Bank of America', 'brand_class': 'atmos', 'last_four': '1592'},
            {'name': 'U.S. Bank Cash Back', 'issuer': 'U.S. Bank', 'brand_class': 'us-bank', 'last_four': '7410'},
        ]

        created_cards = []
        for card_data in cards_data:
            card = CardEnhanced(**card_data)
            db.session.add(card)
            created_cards.append(card)

        db.session.commit()

        # Add real signup bonuses from user's credit card data
        csr = next(c for c in created_cards if 'Sapphire' in c.name)
        amex_gold = next(c for c in created_cards if 'Gold' in c.name)
        venturex = next(c for c in created_cards if 'VentureX' in c.name)
        united = next(c for c in created_cards if 'United' in c.name)
        aspire = next(c for c in created_cards if 'Aspire' in c.name)
        boundless = next(c for c in created_cards if 'Boundless' in c.name)

        signup_bonuses = [
            SignupBonus(
                card_id=csr.id,
                bonus_amount='60,000 points',
                description='Spend $4,000 in first 3 months',
                required_spend=4000.0,
                current_spend=2800.0,
                deadline=datetime.date(2025, 3, 15),
                status='in-progress'
            ),
            SignupBonus(
                card_id=amex_gold.id,
                bonus_amount='90,000 points',
                description='Spend $4,000 in first 6 months',
                required_spend=4000.0,
                current_spend=4000.0,
                deadline=datetime.date(2025, 6, 1),
                status='completed'
            ),
            SignupBonus(
                card_id=venturex.id,
                bonus_amount='75,000 miles',
                description='Spend $4,000 in first 3 months',
                required_spend=4000.0,
                current_spend=1200.0,
                deadline=datetime.date(2025, 4, 10),
                status='in-progress'
            ),
            SignupBonus(
                card_id=united.id,
                bonus_amount='80,000 miles',
                description='Spend $5,000 in first 3 months',
                required_spend=5000.0,
                current_spend=800.0,
                deadline=datetime.date(2025, 3, 25),
                status='in-progress'
            ),
            SignupBonus(
                card_id=aspire.id,
                bonus_amount='150,000 points',
                description='Spend $4,000 in first 3 months',
                required_spend=4000.0,
                current_spend=750.0,
                deadline=datetime.date(2025, 6, 20),
                status='in-progress'
            ),
            SignupBonus(
                card_id=boundless.id,
                bonus_amount='100,000 points',
                description='Spend $5,000 in first 3 months',
                required_spend=5000.0,
                current_spend=0.0,
                deadline=datetime.date(2025, 5, 15),
                status='not-started'
            ),
        ]

        for bonus in signup_bonuses:
            db.session.add(bonus)

        # Add real spending bonuses (after $X spend) from user's credit card data
        freedom = next(c for c in created_cards if 'Freedom' in c.name)
        hyatt = next(c for c in created_cards if 'Hyatt' in c.name)
        venmo = next(c for c in created_cards if 'Venmo' in c.name)
        surpass = next(c for c in created_cards if 'Surpass' in c.name)
        atmos = next(c for c in created_cards if 'Atmos' in c.name)
        usbank = next(c for c in created_cards if 'U.S. Bank' in c.name)

        spending_bonuses = [
            SpendingBonus(
                card_id=csr.id,
                category='Hotels',
                multiplier=5.0,
                description='5x points on hotels after $600 spend',
                cap_amount=600.0,
                current_spend=450.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=amex_gold.id,
                category='Restaurants',
                multiplier=4.0,
                description='4x points on restaurants after $150 spend each quarter',
                cap_amount=150.0,
                current_spend=89.0,
                reset_date=datetime.date(2025, 3, 31),
                bonus_type='quarterly'
            ),
            SpendingBonus(
                card_id=venturex.id,
                category='Hotels',
                multiplier=10.0,
                description='10x miles on hotels after $2,000 spend',
                cap_amount=2000.0,
                current_spend=1200.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=united.id,
                category='Annual Spend',
                multiplier=1.0,
                description='5,000 bonus miles after $10,000 spend each year',
                cap_amount=10000.0,
                current_spend=3500.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=freedom.id,
                category='Travel',
                multiplier=5.0,
                description='5% back on travel after $600 spend each quarter',
                cap_amount=600.0,
                current_spend=200.0,
                reset_date=datetime.date(2025, 3, 31),
                bonus_type='quarterly'
            ),
            SpendingBonus(
                card_id=hyatt.id,
                category='Annual Spend',
                multiplier=1.0,
                description='5 bonus points after $5,000 spend each year',
                cap_amount=5000.0,
                current_spend=2100.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=venmo.id,
                category='Top Category',
                multiplier=3.0,
                description='3% on top spend category after $50,000 spend each year',
                cap_amount=50000.0,
                current_spend=15000.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=boundless.id,
                category='Elite Credits',
                multiplier=1.0,
                description='15 Elite Night Credits after $25,000 spend',
                cap_amount=25000.0,
                current_spend=8500.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=surpass.id,
                category='Annual Spend',
                multiplier=10.0,
                description='10x points after $40,000 spend each year',
                cap_amount=40000.0,
                current_spend=22000.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=aspire.id,
                category='Annual Spend',
                multiplier=10.0,
                description='10x points after $60,000 spend each year',
                cap_amount=60000.0,
                current_spend=35000.0,
                reset_date=datetime.date(2025, 12, 31),
                bonus_type='annual'
            ),
            SpendingBonus(
                card_id=atmos.id,
                category='Eligible Purchases',
                multiplier=5.0,
                description='5% back on eligible purchases after $2,500 spend each quarter',
                cap_amount=2500.0,
                current_spend=1800.0,
                reset_date=datetime.date(2025, 3, 31),
                bonus_type='quarterly'
            ),
            SpendingBonus(
                card_id=usbank.id,
                category='Travel',
                multiplier=5.0,
                description='5% back on travel after $2,500 spend each quarter',
                cap_amount=2500.0,
                current_spend=950.0,
                reset_date=datetime.date(2025, 3, 31),
                bonus_type='quarterly'
            ),
        ]

        for bonus in spending_bonuses:
            db.session.add(bonus)

        # Add real credit benefits from user's credit card data organized by frequency

        credit_benefits = [
            # ANNUAL CREDITS
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Travel Credit',
                credit_amount=300.0,
                description='$300 annual travel credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1),
                has_progress=True,
                required_amount=300.0,
                current_amount=150.0
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Chase Travel Edit Credit',
                credit_amount=500.0,
                description='$500 annual Chase Travel Edit credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Hotel Credit',
                credit_amount=250.0,
                description='$250 annual hotel credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Peloton Credit',
                credit_amount=120.0,
                description='$120 annual Peloton credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='DashPass',
                credit_amount=120.0,
                description='$120 annual DashPass membership',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=amex_gold.id,
                benefit_name='Resy Credit',
                credit_amount=100.0,
                description='$100 annual Resy credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=venturex.id,
                benefit_name='Travel Credit',
                credit_amount=300.0,
                description='$300 annual travel credit for Capital One Travel',
                frequency='annual',
                reset_date=datetime.date(2025, 8, 15),
                has_progress=True,
                required_amount=300.0,
                current_amount=75.0
            ),
            CreditBenefit2(
                card_id=venturex.id,
                benefit_name='Anniversary Miles',
                credit_amount=0.0,
                description='10,000 anniversary miles',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='United Travel Credit',
                credit_amount=200.0,
                description='$200 annual United travel credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='Renowned Hotels Credit',
                credit_amount=150.0,
                description='$150 annual Renowned Hotels credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='Rideshare Credit',
                credit_amount=100.0,
                description='$100 annual rideshare credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='Car Rental Credit',
                credit_amount=80.0,
                description='$80 annual car rental credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='Instacart Credit',
                credit_amount=180.0,
                description='$180 annual Instacart credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='JSX Credit',
                credit_amount=150.0,
                description='$150 annual JSX credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=united.id,
                benefit_name='Anniversary Discount',
                credit_amount=0.0,
                description='10,000-mile anniversary discount',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=hyatt.id,
                benefit_name='Free Night',
                credit_amount=0.0,
                description='Category 1-4 free night award',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=boundless.id,
                benefit_name='Free Night Award',
                credit_amount=0.0,
                description='Annual free night award',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=aspire.id,
                benefit_name='CLEAR Credit',
                credit_amount=209.0,
                description='$209 annual CLEAR credit',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=atmos.id,
                benefit_name='Anniversary Points',
                credit_amount=0.0,
                description='10,000 anniversary points',
                frequency='annual',
                reset_date=datetime.date(2025, 12, 1)
            ),

            # SEMI-ANNUAL CREDITS
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Dining Credit',
                credit_amount=300.0,
                description='$300 dining credit ($150 Jan-June, $150 July-Dec)',
                frequency='semi-annual',
                reset_date=datetime.date(2025, 6, 1)
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Entertainment Credit',
                credit_amount=300.0,
                description='$300 entertainment credit ($150 Jan-June, $150 July-Dec)',
                frequency='semi-annual',
                reset_date=datetime.date(2025, 6, 1)
            ),
            CreditBenefit2(
                card_id=aspire.id,
                benefit_name='Resort Credit',
                credit_amount=400.0,
                description='$400 resort credit ($200 semi-annually)',
                frequency='semi-annual',
                reset_date=datetime.date(2025, 6, 1)
            ),

            # QUARTERLY CREDITS
            CreditBenefit2(
                card_id=surpass.id,
                benefit_name='Hilton Credit',
                credit_amount=50.0,
                description='$50 quarterly Hilton credit',
                frequency='quarterly',
                reset_date=datetime.date(2025, 3, 31)
            ),
            CreditBenefit2(
                card_id=aspire.id,
                benefit_name='Airline Credit',
                credit_amount=50.0,
                description='$50 quarterly airline credit',
                frequency='quarterly',
                reset_date=datetime.date(2025, 3, 31)
            ),

            # MONTHLY CREDITS
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='DoorDash Credit',
                credit_amount=25.0,
                description='$25 monthly DoorDash credit',
                frequency='monthly',
                reset_date=datetime.date(2025, 2, 1)
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Lyft Credit',
                credit_amount=10.0,
                description='$10 monthly Lyft credit',
                frequency='monthly',
                reset_date=datetime.date(2025, 2, 1)
            ),
            CreditBenefit2(
                card_id=amex_gold.id,
                benefit_name='Uber Credit',
                credit_amount=10.0,
                description='$10 monthly Uber credit',
                frequency='monthly',
                reset_date=datetime.date(2025, 2, 1)
            ),
            CreditBenefit2(
                card_id=amex_gold.id,
                benefit_name='Dunkin Credit',
                credit_amount=7.0,
                description='$7 monthly Dunkin credit',
                frequency='monthly',
                reset_date=datetime.date(2025, 2, 1)
            ),
            CreditBenefit2(
                card_id=amex_gold.id,
                benefit_name='Food Credit',
                credit_amount=10.0,
                description='$10 monthly food credit',
                frequency='monthly',
                reset_date=datetime.date(2025, 2, 1)
            ),

            # ONE-TIME CREDITS
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='TSA PreCheck/Global Entry',
                credit_amount=120.0,
                description='$120 TSA PreCheck/Global Entry credit (every 4 years)',
                frequency='onetime'
            ),
            CreditBenefit2(
                card_id=csr.id,
                benefit_name='Apple Services',
                credit_amount=0.0,
                description='Ongoing Apple Services benefit',
                frequency='onetime'
            ),
            CreditBenefit2(
                card_id=venturex.id,
                benefit_name='TSA PreCheck/Global Entry',
                credit_amount=120.0,
                description='$120 TSA PreCheck/Global Entry credit (every 4 years)',
                frequency='onetime'
            ),
            CreditBenefit2(
                card_id=aspire.id,
                benefit_name='Waldorf/Conrad Credit',
                credit_amount=100.0,
                description='$100 Waldorf/Conrad credit per qualifying stay',
                frequency='onetime'
            ),
            CreditBenefit2(
                card_id=atmos.id,
                benefit_name='Airport Security Credit',
                credit_amount=120.0,
                description='$120 airport security credit (every 4 years)',
                frequency='onetime'
            ),
        ]

        for benefit in credit_benefits:
            db.session.add(benefit)

        db.session.commit()
        print("Enhanced sample data created successfully!")

def get_real_signup_bonuses():
    """Get signup bonuses from database (excluding completed ones)"""
    bonuses = SignupBonus.query.filter(SignupBonus.status != 'completed').all()
    result = [{
        'card_name': bonus.card.name,
        'bonus_amount': bonus.bonus_amount,
        'description': bonus.description,
        'required_spend': bonus.required_spend,
        'current_spend': bonus.current_spend,
        'progress_percent': bonus.progress_percent,
        'deadline': bonus.deadline.strftime('%B %d, %Y') if bonus.deadline else None,
        'status': bonus.status,
        'status_text': bonus.status_text
    } for bonus in bonuses]

    # Sort by bonus amount from highest to lowest
    def parse_bonus_amount(amount_str):
        """Parse bonus amount string to extract numeric value for sorting"""
        clean_str = str(amount_str).replace('$', '').replace(',', '').lower()
        # Extract just the numeric part by removing text like 'points', 'miles', etc.
        import re
        numbers = re.findall(r'\d+', clean_str)
        return float(numbers[0]) if numbers else 0.0
    
    return sorted(result, key=lambda x: parse_bonus_amount(x['bonus_amount']), reverse=True)

def get_completed_signup_bonuses():
    """Get completed signup bonuses from database"""
    bonuses = SignupBonus.query.filter(SignupBonus.status == 'completed').all()
    result = [{
        'card_name': bonus.card.name,
        'bonus_amount': bonus.bonus_amount,
        'description': bonus.description,
        'required_spend': bonus.required_spend,
        'current_spend': bonus.current_spend,
        'progress_percent': bonus.progress_percent,
        'deadline': bonus.deadline.strftime('%B %d, %Y') if bonus.deadline else None,
        'status': bonus.status,
        'status_text': bonus.status_text
    } for bonus in bonuses]

    # Sort by bonus amount from highest to lowest
    def parse_bonus_amount(amount_str):
        """Parse bonus amount string to extract numeric value for sorting"""
        clean_str = str(amount_str).replace('$', '').replace(',', '').lower()
        # Extract just the numeric part by removing text like 'points', 'miles', etc.
        import re
        numbers = re.findall(r'\d+', clean_str)
        return float(numbers[0]) if numbers else 0.0

    return sorted(result, key=lambda x: parse_bonus_amount(x['bonus_amount']), reverse=True)

def get_real_spending_bonuses():
    """Get threshold bonuses from database for homepage (replaces multipliers per user request)"""
    # Return threshold bonuses from other_bonus table for homepage - only pending ones
    bonuses = OtherBonus.query.filter_by(bonus_type='threshold', status='pending').all()
    result = []

    for bonus in bonuses:
        # Only show threshold bonuses with meaningful spending requirements
        if bonus.required_spend and bonus.required_spend > 0:
            # Format the bonus amount properly - no extra 'x' and handle points vs dollars
            bonus_amount = bonus.bonus_amount

            # If it contains 'points' or is just a number followed by text, don't add dollar sign
            if 'points' in bonus_amount.lower() or 'status' in bonus_amount.lower() or 'night' in bonus_amount.lower() or 'upgrade' in bonus_amount.lower() or 'credit' in bonus_amount.lower():
                formatted_amount = bonus_amount  # Keep as-is for points, status, nights, upgrades, credits
            elif bonus_amount.startswith('$'):
                formatted_amount = bonus_amount  # Already has dollar sign
            else:
                # Only add dollar sign if it's clearly a dollar amount (number only)
                try:
                    float(bonus_amount.replace(',', ''))
                    formatted_amount = f"${bonus_amount}"
                except ValueError:
                    formatted_amount = bonus_amount  # Keep as-is if can't parse as number

            bonus_data = {
                'card_name': bonus.card.name,
                'category': bonus.description,
                'multiplier': formatted_amount,  # This will NOT go through |multiplier filter
                'description': f"{bonus_amount} after ${bonus.required_spend:,.0f} annual spend",
                'cap_amount': bonus.required_spend,
                'current_spend': 0,  # Default to 0 for now
                'progress_percent': 0,  # Default to 0 for now
                'reset_date': 'December 31',  # Default annual reset
                'status': bonus.status,
                'status_text': bonus.status_text
            }
            result.append(bonus_data)

    return result

def get_real_credits_by_frequency(frequency):
    """Get available (non-used) credits by frequency from database"""
    credits = CreditBenefit2.query.filter_by(frequency=frequency).all()
    result = []

    for credit in credits:
        # Skip credits that are marked as 'used'
        if credit.credit_status == 'used':
            continue

        # Use original multiplier format for credits from spending bonuses
        display_amount = credit.original_multiplier if credit.original_multiplier else credit.credit_amount

        credit_data = {
            'card_name': credit.card.name,
            'credit_amount': display_amount,
            'description': credit.description,
            'status': credit.credit_status,
            'status_text': credit.status_text,
            'from_spending_bonus': getattr(credit, 'from_spending_bonus', False),
            'spending_bonus_id': getattr(credit, 'spending_bonus_id', None)
        }

        if credit.benefit_name:
            credit_data['benefit_name'] = credit.benefit_name
        if credit.category:
            credit_data['category'] = credit.category
        if credit.reset_date:
            credit_data['reset_date'] = credit.reset_date.strftime('%B %d, %Y')
        if credit.has_progress:
            credit_data['has_progress'] = True
            credit_data['required_amount'] = credit.required_amount
            credit_data['current_amount'] = credit.current_amount
            credit_data['progress_percent'] = credit.progress_percent

        result.append(credit_data)

    # Sort by credit amount from highest to lowest (handle non-numeric amounts like "1 night")
    def safe_sort_key(credit):
        try:
            amount_str = str(credit['credit_amount']).replace('$', '').replace(',', '')
            # Try to extract first number from the string
            import re
            numbers = re.findall(r'\d+', amount_str)
            return float(numbers[0]) if numbers else 0
        except:
            return 0

    return sorted(result, key=safe_sort_key, reverse=True)

def get_used_credits_by_frequency(frequency):
    """Get used credits by frequency from database"""
    credits = CreditBenefit2.query.filter_by(frequency=frequency).all()
    result = []

    for credit in credits:
        # Only include credits that are marked as 'used'
        if credit.credit_status != 'used':
            continue

        # Use original multiplier format for credits from spending bonuses
        display_amount = credit.original_multiplier if credit.original_multiplier else credit.credit_amount

        credit_data = {
            'card_name': credit.card.name,
            'credit_amount': display_amount,
            'description': credit.description,
            'status': credit.credit_status,
            'status_text': credit.status_text,
            'from_spending_bonus': getattr(credit, 'from_spending_bonus', False),
            'spending_bonus_id': getattr(credit, 'spending_bonus_id', None)
        }

        if credit.benefit_name:
            credit_data['benefit_name'] = credit.benefit_name
        if credit.category:
            credit_data['category'] = credit.category
        if credit.reset_date:
            credit_data['reset_date'] = credit.reset_date.strftime('%B %d, %Y')
        if credit.has_progress:
            credit_data['has_progress'] = True
            credit_data['required_amount'] = credit.required_amount
            credit_data['current_amount'] = credit.current_amount
            credit_data['progress_percent'] = credit.progress_percent

        result.append(credit_data)

    # Sort by credit amount from highest to lowest (handle non-numeric amounts like "1 night")
    def safe_sort_key(credit):
        try:
            amount_str = str(credit['credit_amount']).replace('$', '').replace(',', '')
            # Try to extract first number from the string
            import re
            numbers = re.findall(r'\d+', amount_str)
            return float(numbers[0]) if numbers else 0
        except:
            return 0

    return sorted(result, key=safe_sort_key, reverse=True)

def get_real_cards():
    """Get cards from enhanced database"""
    cards = CardEnhanced.query.all()
    return [{
        'id': card.id,
        'name': card.name,
        'issuer': card.issuer or get_card_issuer(card.name),
        'brand_class': card.brand_class or get_card_brand_class(card.name),
        'last_four': card.last_four,
        'total_benefits': card.total_benefits
    } for card in cards]

# === NEW UI ROUTES ===

@app.route('/card_enhanced/<int:card_id>')
def show_enhanced_card_details(card_id):
    """
    Shows detailed information about a specific CardEnhanced card with properly organized benefits.
    """
    # Get the enhanced card
    card = CardEnhanced.query.get(card_id)

    if not card:
        return render_template('card_details.html',
                             card={'name': 'Card Not Found', 'issuer': '', 'total_benefits': 0},
                             signup_bonuses=[],
                             spending_bonuses=[],
                             multiplier_benefits=[],
                             annual_credits=[],
                             semiannual_credits=[],
                             quarterly_credits=[],
                             monthly_credits=[],
                             onetime_credits=[])

    # Get all benefits for this card
    signup_bonuses = [{
        'bonus_amount': bonus.bonus_amount,
        'description': bonus.description,
        'required_spend': bonus.required_spend,
        'current_spend': bonus.current_spend,
        'progress_percent': bonus.progress_percent,
        'deadline': bonus.deadline.strftime('%B %d, %Y') if bonus.deadline else None,
        'status': bonus.status,
        'status_text': bonus.status_text
    } for bonus in card.signup_bonuses]

    spending_bonuses = [{
        'category': bonus.category,
        'multiplier': bonus.multiplier,
        'description': bonus.description,
        'cap_amount': bonus.cap_amount,
        'current_spend': bonus.current_spend,
        'progress_percent': bonus.progress_percent,
        'reset_date': bonus.reset_date.strftime('%B %d, %Y'),
        'status': bonus.status,
        'status_text': bonus.status_text
    } for bonus in card.spending_bonuses if bonus.is_active]

    # Get multiplier benefits from old Card model by matching name
    old_card = Card.query.filter_by(name=card.name).first()
    multiplier_benefits = []
    if old_card:
        multiplier_benefits = MultiplierBenefit.query.filter_by(card_id=old_card.id).all()

    # Organize credit benefits by frequency
    annual_credits = []
    semiannual_credits = []
    quarterly_credits = []
    monthly_credits = []
    onetime_credits = []
    
    for credit in card.credit_benefits:
        credit_data = {
            'benefit_name': credit.benefit_name,
            'credit_amount': credit.credit_amount,
            'description': credit.description,
            'status': credit.credit_status,
            'status_text': credit.status_text
        }
        
        if credit.reset_date:
            credit_data['reset_date'] = credit.reset_date.strftime('%B %d, %Y')
        if credit.has_progress:
            credit_data['has_progress'] = True
            credit_data['required_amount'] = credit.required_amount
            credit_data['current_amount'] = credit.current_amount
            credit_data['progress_percent'] = credit.progress_percent

        # Categorize by frequency
        if credit.frequency == 'annual':
            annual_credits.append(credit_data)
        elif credit.frequency == 'semi-annual':
            semiannual_credits.append(credit_data)
        elif credit.frequency == 'quarterly':
            quarterly_credits.append(credit_data)
        elif credit.frequency == 'monthly':
            monthly_credits.append(credit_data)
        elif credit.frequency == 'onetime':
            onetime_credits.append(credit_data)

    # Separate other bonuses into threshold bonuses and other bonuses
    threshold_bonuses = []
    other_bonuses = []

    for bonus in card.other_bonuses:
        bonus_data = {
            'bonus_type': bonus.bonus_type,
            'bonus_amount': bonus.bonus_amount,
            'description': bonus.description,
            'required_spend': bonus.required_spend,
            'frequency': bonus.frequency
        }

        # Threshold bonuses are spending-related with dollar thresholds
        if (bonus.required_spend and bonus.required_spend > 0) or 'credit' in bonus.description.lower() or 'spend' in bonus.description.lower():
            threshold_bonuses.append(bonus_data)
        else:
            other_bonuses.append(bonus_data)

    # Transform card data for display
    card_data = {
        'id': card.id,
        'name': card.name,
        'issuer': card.issuer,
        'total_benefits': card.total_benefits
    }

    return render_template('enhanced_card_details.html',
                         card=card_data,
                         signup_bonuses=signup_bonuses,
                         threshold_bonuses=threshold_bonuses,
                         spending_bonuses=spending_bonuses,
                         other_bonuses=other_bonuses,
                         multiplier_benefits=multiplier_benefits,
                         annual_credits=annual_credits,
                         semiannual_credits=semiannual_credits,
                         quarterly_credits=quarterly_credits,
                         monthly_credits=monthly_credits,
                         onetime_credits=onetime_credits)

@app.route('/purchase-helper')
def purchase_helper():
    """Purchase recommendation tool"""

    # Sample category quick reference
    quick_reference = [
        {'name': 'Dining', 'best_multiplier': 4, 'best_card': 'American Express Gold'},
        {'name': 'Travel', 'best_multiplier': 10, 'best_card': 'Capital One VentureX'},
        {'name': 'Gas', 'best_multiplier': 3, 'best_card': 'Marriott Bonvoy Boundless'},
        {'name': 'Grocery', 'best_multiplier': 4, 'best_card': 'American Express Gold'},
        {'name': 'Hotels', 'best_multiplier': 17, 'best_card': 'Marriott Bonvoy Boundless'},
        {'name': 'Foreign Purchases', 'best_multiplier': 3, 'best_card': 'Atmos Rewards Ascent'}
    ]

    return render_template('purchase_helper.html', quick_reference=quick_reference)

@app.route('/usage-history')
def usage_history():
    """Usage history page - you can implement this later"""
    return jsonify({"message": "Usage history page - coming soon!"})

@app.route('/api/reset-credits', methods=['POST'])
def manual_reset_credits():
    """Manual endpoint to trigger credit reset (for testing)"""
    try:
        reset_expired_credits()
        return jsonify({
            'success': True,
            'message': 'Credit reset check completed'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# === AUTOMATED CREDIT RESET FUNCTIONALITY ===

def parse_reset_date(reset_date_str):
    """Parse reset date string into datetime object"""
    if not reset_date_str:
        return None

    try:
        # Handle various date formats
        formats_to_try = [
            "%B %d, %Y",      # "December 31, 2025"
            "%b %d, %Y",      # "Dec 31, 2025"
            "%Y-%m-%d",       # "2025-12-31"
            "%m/%d/%Y",       # "12/31/2025"
        ]

        for format_str in formats_to_try:
            try:
                return datetime.datetime.strptime(reset_date_str, format_str).date()
            except ValueError:
                continue

        print(f"Warning: Could not parse reset date: {reset_date_str}")
        return None
    except Exception as e:
        print(f"Error parsing reset date {reset_date_str}: {e}")
        return None

def calculate_next_reset_date(current_reset_date, frequency):
    """Calculate the next reset date based on frequency"""
    if not current_reset_date:
        return None

    try:
        if frequency == 'monthly':
            return current_reset_date + relativedelta(months=1)
        elif frequency == 'quarterly':
            return current_reset_date + relativedelta(months=3)
        elif frequency == 'semi-annual':
            return current_reset_date + relativedelta(months=6)
        elif frequency == 'annual':
            return current_reset_date + relativedelta(years=1)
        else:
            # For onetime credits, don't reset
            return current_reset_date
    except Exception as e:
        print(f"Error calculating next reset date for {current_reset_date}, frequency {frequency}: {e}")
        return None

def format_reset_date(date_obj):
    """Format date object back to string format"""
    if not date_obj:
        return None
    try:
        return date_obj.strftime("%B %d, %Y")
    except Exception as e:
        print(f"Error formatting date {date_obj}: {e}")
        return None

def reset_expired_credits():
    """Reset credits that have passed their reset date"""
    today = datetime.date.today()
    reset_count = 0

    try:
        with app.app_context():
            # Get all credits from the database
            credits = CreditBenefit2.query.all()

            for credit in credits:
                if not credit.reset_date:
                    continue

                # Parse the current reset date
                current_reset_date = parse_reset_date(credit.reset_date)
                if not current_reset_date:
                    continue

                # Check if reset date has passed
                if current_reset_date < today:
                    print(f"Resetting credit: {credit.benefit_name} for {credit.card_name}")

                    # Reset used credits to available
                    used_credit_statuses = CreditStatus.query.filter_by(
                        card_name=credit.card_name,
                        credit_identifier=credit.benefit_name,
                        status='used'
                    ).all()

                    for status in used_credit_statuses:
                        status.status = 'available'
                        status.last_updated = datetime.datetime.utcnow()
                        print(f"  → Marked {credit.benefit_name} as available")

                    # Calculate new reset date (skip one-time credits)
                    if credit.frequency.lower() != 'onetime':
                        new_reset_date = calculate_next_reset_date(current_reset_date, credit.frequency.lower())
                        if new_reset_date:
                            credit.reset_date = format_reset_date(new_reset_date)
                            print(f"  → Updated reset date to {credit.reset_date}")

                    reset_count += 1

            if reset_count > 0:
                db.session.commit()
                print(f"Successfully reset {reset_count} credits")
            else:
                print("No credits needed resetting")

    except Exception as e:
        print(f"Error in reset_expired_credits: {e}")
        db.session.rollback()

def run_reset_scheduler():
    """Background thread to check for credit resets daily at midnight"""
    def scheduler_loop():
        while not getattr(scheduler_loop, 'stop', False):
            try:
                now = datetime.datetime.now()
                # Check if it's midnight (within a 1-minute window)
                if now.hour == 0 and now.minute == 0:
                    print(f"Running daily credit reset check at {now}")
                    reset_expired_credits()

                    # Also check for annual spending bonus reset on January 1st
                    check_annual_reset()

                    # Sleep for 60 seconds to avoid running multiple times in the same minute
                    time.sleep(60)
                else:
                    # Check every 30 seconds
                    time.sleep(30)
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying

    # Start the scheduler thread
    scheduler_thread = Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()

    # Register cleanup function
    def stop_scheduler():
        scheduler_loop.stop = True
    atexit.register(stop_scheduler)

    print("Credit reset scheduler started - will check daily at midnight")

def reset_annual_spending_bonuses():
    """
    Reset annual spending bonuses on January 1st.
    Creates new pending bonuses for any that were completed in the previous year.
    """
    try:
        with app.app_context():
            current_year = datetime.datetime.now().year

            # Find all completed spending bonuses from previous years
            completed_bonuses = OtherBonus.query.filter_by(
                bonus_type='threshold',
                status='completed'
            ).all()

            new_bonuses_created = 0

            for completed_bonus in completed_bonuses:
                # Check if we already have a pending bonus for this year for the same card/category
                existing_pending = OtherBonus.query.filter_by(
                    card_id=completed_bonus.card_id,
                    bonus_type='threshold',
                    description=completed_bonus.description,
                    status='pending'
                ).first()

                # Only create a new one if we don't already have a pending version
                if not existing_pending:
                    # Create a new pending bonus based on the completed one
                    new_bonus = OtherBonus(
                        card_id=completed_bonus.card_id,
                        bonus_type='threshold',
                        bonus_amount=completed_bonus.bonus_amount,
                        description=completed_bonus.description,
                        required_spend=completed_bonus.required_spend,
                        frequency=completed_bonus.frequency,
                        status='pending',
                        created_date=datetime.datetime.utcnow()
                    )

                    db.session.add(new_bonus)
                    new_bonuses_created += 1

            if new_bonuses_created > 0:
                db.session.commit()
                print(f"Annual reset: Created {new_bonuses_created} new spending bonuses for {current_year}")
            else:
                print(f"Annual reset: No new spending bonuses needed for {current_year}")

    except Exception as e:
        print(f"Error during annual spending bonus reset: {e}")
        db.session.rollback()

def check_annual_reset():
    """Check if it's January 1st and run annual reset if needed"""
    now = datetime.datetime.now()
    if now.month == 1 and now.day == 1:
        print("January 1st detected - running annual spending bonus reset")
        reset_annual_spending_bonuses()

# This special block runs only when we run this file directly
# (not when it's imported by another file)
if __name__ == '__main__':
    # First, create our database tables
    create_tables()

    # Add legacy sample data for compatibility
    add_sample_data()

    # Initialize enhanced database with real functional data
    initialize_enhanced_data()

    # Start the automated credit reset scheduler
    run_reset_scheduler()

    # Finally, start our web application in debug mode
    # Debug mode helps us see errors more clearly while learning
    app.run(debug=True, port=5002)
