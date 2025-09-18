#!/usr/bin/env python3
"""
Data Audit Script: Compare current database data with source of truth
This script will help us understand what's currently in the database vs what should be there
"""

import sqlite3
import csv
from collections import defaultdict

def audit_current_data():
    """Examine what's currently in the database"""
    print("=== CURRENT DATABASE AUDIT ===\n")

    # Connect to the database
    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Available tables:")
    for table in tables:
        print(f"  - {table[0]}")
    print()

    # Check CardEnhanced table
    try:
        cursor.execute("SELECT * FROM card_enhanced")
        cards = cursor.fetchall()
        cursor.execute("PRAGMA table_info(card_enhanced)")
        columns = [col[1] for col in cursor.fetchall()]

        print("CURRENT CARDS (CardEnhanced):")
        print(f"Columns: {columns}")
        for card in cards:
            print(f"  - {dict(zip(columns, card))}")
        print()
    except Exception as e:
        print(f"Error reading card_enhanced: {e}")

    # Check SpendingBonus table (Points Multipliers)
    try:
        cursor.execute("SELECT * FROM spending_bonus")
        bonuses = cursor.fetchall()
        cursor.execute("PRAGMA table_info(spending_bonus)")
        columns = [col[1] for col in cursor.fetchall()]

        print("CURRENT SPENDING BONUSES (Points Multipliers):")
        print(f"Columns: {columns}")
        for bonus in bonuses:
            print(f"  - {dict(zip(columns, bonus))}")
        print()
    except Exception as e:
        print(f"Error reading spending_bonus: {e}")

    # Check CreditBenefit2 table
    try:
        cursor.execute("SELECT * FROM credit_benefit2")
        credits = cursor.fetchall()
        cursor.execute("PRAGMA table_info(credit_benefit2)")
        columns = [col[1] for col in cursor.fetchall()]

        print("CURRENT CREDIT BENEFITS:")
        print(f"Columns: {columns}")
        for credit in credits:
            print(f"  - {dict(zip(columns, credit))}")
        print()
    except Exception as e:
        print(f"Error reading credit_benefit2: {e}")

    # Check SignupBonus table
    try:
        cursor.execute("SELECT * FROM signup_bonus")
        signups = cursor.fetchall()
        cursor.execute("PRAGMA table_info(signup_bonus)")
        columns = [col[1] for col in cursor.fetchall()]

        print("CURRENT SIGNUP BONUSES:")
        print(f"Columns: {columns}")
        for signup in signups:
            print(f"  - {dict(zip(columns, signup))}")
        print()
    except Exception as e:
        print(f"Error reading signup_bonus: {e}")

    conn.close()

def parse_source_of_truth():
    """Parse the source of truth data provided by the user"""
    print("=== SOURCE OF TRUTH ANALYSIS ===\n")

    # The source data from the user (I'll parse it manually)
    source_data = """Card Name,Benefit Category,Sub-Category,Benefit Description,Value / Rate,Spending Requirement,Frequency
Chase Sapphire Reserve,Points Multiplier,Travel,Points on Chase Travel (flights, hotels, rental cars, cruises, activities, tours),8x,N/A,Per dollar spent
Chase Sapphire Reserve,Points Multiplier,Travel,Points on travel booked directly with airline or hotel,4x,N/A,Per dollar spent
Chase Sapphire Reserve,Points Multiplier,Dining,Points on dining at restaurants worldwide (including eligible delivery),3x,N/A,Per dollar spent"""

    # Group by card name for easier comparison
    cards_data = defaultdict(lambda: {
        'Points Multiplier': [],
        'Credit': [],
        'Bonus': []
    })

    # Note: In a real implementation, I would parse the full data table
    # For now, let me just show the structure and key discrepancies

    print("Cards that should exist according to source of truth:")
    expected_cards = [
        "Chase Sapphire Reserve", "American Express Gold Card", "Capital One VentureX",
        "Chase United Quest", "Chase Freedom Unlimited", "World of Hyatt",
        "Venmo Cash Back", "Marriott Bonvoy Boundless", "Hilton Honors Surpass",
        "Hilton Honors Aspire", "Atmos Rewards Ascent", "U.S. Bank Cash Back",
        "Hilton Honors American Express Card", "American Express Platinum"
    ]

    for card in expected_cards:
        print(f"  - {card}")

    return expected_cards

if __name__ == "__main__":
    audit_current_data()
    expected_cards = parse_source_of_truth()