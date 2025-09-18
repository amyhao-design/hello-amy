#!/usr/bin/env python3
"""
Fix Data Issues Script: Address all the identified problems
1. Fix sign-up bonus vs other bonus categorization
2. Fix $0 credit amounts
3. Fix 'Credit Credit' naming issues
4. Improve credit descriptions
"""

import sqlite3
import re
from datetime import datetime

def fix_signup_bonus_categorization():
    """Move threshold-based bonuses to a different category"""
    print("=== FIXING SIGNUP BONUS CATEGORIZATION ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # First, let's see what we have in signup_bonus that should be "other bonuses"
    cursor.execute("SELECT * FROM signup_bonus")
    bonuses = cursor.fetchall()

    # Categories that should be "other bonuses" (threshold-based, no time limit)
    other_bonus_keywords = [
        'Anniversary', 'Premier qualifying', 'Status', 'Elite', 'Free night',
        'Tier-qualifying', 'Award flight discount', 'seat upgrades', 'Gold status',
        'Diamond Status', 'Additional Free Night'
    ]

    # Time-limited sign-up bonuses (keep these as signup bonuses)
    signup_keywords = [
        'Spend $', 'in 3 months', 'in 6 months', 'in 90 days', 'Welcome bonus',
        'Sign-Up Bonus', 'Bonus points', 'Hilton Honors Bonus Points'
    ]

    # Create a new table for "other bonuses" if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS other_bonus (
            id INTEGER PRIMARY KEY,
            card_id INTEGER,
            bonus_type TEXT,
            bonus_amount TEXT,
            description TEXT,
            required_spend REAL,
            frequency TEXT,
            created_date TEXT,
            FOREIGN KEY (card_id) REFERENCES card_enhanced (id)
        )
    """)

    bonuses_to_move = []
    for bonus in bonuses:
        description = bonus[2] + " " + bonus[3]  # bonus_amount + description

        # Check if this should be moved to "other bonuses"
        is_other_bonus = any(keyword in description for keyword in other_bonus_keywords)
        is_signup_bonus = any(keyword in description for keyword in signup_keywords)

        if is_other_bonus and not is_signup_bonus:
            bonuses_to_move.append(bonus)

    # Move the bonuses
    for bonus in bonuses_to_move:
        # Insert into other_bonus table
        cursor.execute("""
            INSERT INTO other_bonus
            (card_id, bonus_type, bonus_amount, description, required_spend, frequency, created_date)
            VALUES (?, 'threshold', ?, ?, ?, 'ongoing', ?)
        """, (bonus[1], bonus[2], bonus[3], bonus[4], datetime.now().isoformat()))

        # Remove from signup_bonus table
        cursor.execute("DELETE FROM signup_bonus WHERE id = ?", (bonus[0],))
        print(f"Moved to other bonuses: {bonus[2]} - {bonus[3]}")

    conn.commit()
    conn.close()

def fix_credit_amounts():
    """Fix $0 credit amounts by parsing the description"""
    print("\n=== FIXING CREDIT AMOUNTS ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Get all credits with $0 amount
    cursor.execute("SELECT * FROM credit_benefit2 WHERE credit_amount = 0")
    zero_credits = cursor.fetchall()

    for credit in zero_credits:
        credit_id, card_id, benefit_name, category, amount, description, frequency, reset_date, has_progress, required_amount, current_amount = credit

        # Try to extract dollar amount from description
        dollar_match = re.search(r'\$(\d+(?:,\d{3})*)', description)
        if dollar_match:
            new_amount = float(dollar_match.group(1).replace(',', ''))
            cursor.execute("UPDATE credit_benefit2 SET credit_amount = ? WHERE id = ?", (new_amount, credit_id))
            print(f"Updated credit amount: {description} -> ${new_amount}")
        else:
            # Special cases
            if 'DoorDash' in description and '$5 for restaurants' in description:
                cursor.execute("UPDATE credit_benefit2 SET credit_amount = ? WHERE id = ?", (25.0, credit_id))
                print(f"Updated DoorDash credit: {description} -> $25")
            elif 'Grubhub' in description:
                cursor.execute("UPDATE credit_benefit2 SET credit_amount = ? WHERE id = ?", (10.0, credit_id))
                print(f"Updated Grubhub credit: {description} -> $10")

    conn.commit()
    conn.close()

def fix_credit_names():
    """Fix 'Credit Credit' naming and improve descriptions"""
    print("\n=== FIXING CREDIT NAMES ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Get all credits with bad names
    cursor.execute("SELECT * FROM credit_benefit2")
    credits = cursor.fetchall()

    for credit in credits:
        credit_id, card_id, benefit_name, category, amount, description, frequency, reset_date, has_progress, required_amount, current_amount = credit

        new_name = benefit_name

        # Fix "Credit Credit" issues
        if benefit_name == "Credit Credit" or benefit_name.endswith(" Credit Credit"):
            # Extract the actual service/benefit name from description
            desc_lower = description.lower()

            if 'paramount' in desc_lower:
                new_name = "Paramount+ Credit"
            elif 'chase travel' in desc_lower and 'edit' in desc_lower:
                new_name = "Chase Travel Edit Credit"
            elif 'hotel' in desc_lower and 'chase travel' in desc_lower:
                new_name = "Chase Travel Hotel Credit"
            elif 'rideshare' in desc_lower:
                new_name = "Rideshare Credit"
            elif 'avis' in desc_lower or 'budget' in desc_lower:
                new_name = "Car Rental Credit"
            elif 'jsx' in desc_lower:
                new_name = "JSX Flight Credit"
            elif 'renowned hotels' in desc_lower:
                new_name = "Renowned Hotels Credit"
            elif 'youtube' in desc_lower:
                new_name = "Digital Entertainment Credit"
            else:
                # Generic fix - take first meaningful word
                words = description.split()
                if len(words) > 0:
                    first_word = words[0].replace('Credit', '').replace('for', '').strip()
                    if first_word and first_word not in ['Up', 'Statement', 'credits']:
                        new_name = f"{first_word} Credit"

        # Fix other naming issues
        elif 'Statement Credit' in benefit_name:
            desc_lower = description.lower()
            if 'dunkin' in desc_lower:
                new_name = "Dunkin' Credit"
            elif 'grubhub' in desc_lower:
                new_name = "Food Credit"
            elif 'hilton' in desc_lower:
                new_name = "Hilton Property Credit"
            elif 'flight' in desc_lower:
                new_name = "Flight Credit"
            elif 'clear' in desc_lower:
                new_name = "CLEAR Credit"
            elif 'resort' in desc_lower:
                new_name = "Resort Credit"

        # Update if we changed the name
        if new_name != benefit_name:
            cursor.execute("UPDATE credit_benefit2 SET benefit_name = ? WHERE id = ?", (new_name, credit_id))
            print(f"Updated credit name: '{benefit_name}' -> '{new_name}'")

    conn.commit()
    conn.close()

def remove_low_multipliers_from_homepage():
    """Mark base multipliers (1x, 1.5x) as not active for homepage display"""
    print("\n=== HIDING BASE MULTIPLIERS FROM HOMEPAGE ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Update spending bonuses with multipliers <= 1.5 to not show on homepage
    cursor.execute("""
        UPDATE spending_bonus
        SET is_active = 0
        WHERE multiplier <= 1.5 AND category = 'General'
    """)

    # Also hide some redundant travel multipliers (keep only the highest ones)
    cursor.execute("""
        UPDATE spending_bonus
        SET is_active = 0
        WHERE multiplier <= 2.0 AND category = 'Travel'
        AND card_id IN (
            SELECT card_id FROM spending_bonus
            WHERE category = 'Travel' AND multiplier > 2.0
        )
    """)

    print("Hidden base multipliers from homepage display")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_signup_bonus_categorization()
    fix_credit_amounts()
    fix_credit_names()
    remove_low_multipliers_from_homepage()
    print("\n=== ALL FIXES COMPLETE ===")
    print("Database issues have been resolved!")