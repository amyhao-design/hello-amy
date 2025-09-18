#!/usr/bin/env python3
"""
Categorize bonuses correctly: Time-limited sign-up bonuses vs ongoing threshold bonuses
"""

import sqlite3
from datetime import datetime

def categorize_bonuses():
    """Analyze and properly categorize all bonuses"""
    print("=== CATEGORIZING BONUSES ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Get current signup bonuses with card names
    cursor.execute("""
        SELECT s.id, s.card_id, s.bonus_amount, s.description, s.required_spend, s.deadline, c.name
        FROM signup_bonus s
        JOIN card_enhanced c ON s.card_id = c.id
    """)
    current_signup_bonuses = cursor.fetchall()

    print("CURRENT SIGNUP BONUSES TO CATEGORIZE:")
    for bonus in current_signup_bonuses:
        bonus_id, card_id, amount, description, required_spend, deadline, card_name = bonus
        print(f"- {card_name}: {amount} - {description} (required_spend: ${required_spend})")

    print("\n" + "="*80)
    print("CATEGORIZATION ANALYSIS:")
    print("="*80)

    # Based on source of truth data, here's the correct categorization:

    # TRUE SIGN-UP BONUSES (time-limited with specific spend requirements in months)
    true_signup_bonuses = [
        # From source data: "Welcome bonus,75,000 miles,$4,000 in 3 months,One-Time"
        ("Capital One VentureX", "75", "Welcome bonus", 4000.0),
        # From source data: "Bonus points,130,000 points,$3,000 in 6 months,One-Time"
        ("Hilton Honors Surpass", "130", "Bonus points", 3000.0),
        # From source data: "Bonus points,150,000 points,$6,000 in 6 months,One-Time"
        ("Hilton Honors Aspire", "150", "Bonus points", 6000.0),
        # From source data: "Bonus points and Global Companion Award,100,000 points + 25,000 point award,$6,000 in 90 days,One-Time"
        ("Atmos Rewards Ascent", "100", "Bonus points and Global Companion Award", 6000.0),
        # From source data: "Hilton Honors Bonus Points,80,000 points,$2,000 in 6 months,One-Time"
        ("Hilton Honors American Express Card", "80", "Hilton Honors Bonus Points", 2000.0),
    ]

    # THRESHOLD BONUSES (ongoing spending thresholds, not time-limited)
    threshold_bonuses = [
        # Chase Sapphire Reserve: These are SPENDING BONUSES requiring $75k annual spend, not sign-up bonuses
        ("Chase Sapphire Reserve", "$500", "Southwest Airlines credit", 75000.0),
        ("Chase Sapphire Reserve", "$250", "Shops at Chase credit", 75000.0),
        # World of Hyatt: Second free night requires $15k spend - this is ongoing threshold
        ("World of Hyatt", "1 Free Night", "Second free night at Category 1-4 Hyatt hotel", 15000.0),
        # Atmos: 10% bonus is ongoing with eligible account, not time-limited
        ("Atmos Rewards Ascent", "10%", "Rewards bonus with eligible Bank of America account", 0.0),
    ]

    # Update sign-up bonuses with correct spend requirements and descriptions
    for card_name, amount, description, required_spend in true_signup_bonuses:
        cursor.execute("""
            UPDATE signup_bonus
            SET required_spend = ?,
                bonus_amount = ?,
                description = ?
            WHERE card_id = (SELECT id FROM card_enhanced WHERE name = ?)
            AND bonus_amount LIKE ?
        """, (required_spend, amount, description, card_name, f"%{amount.split()[0]}%"))

        if cursor.rowcount > 0:
            print(f"✅ SIGN-UP BONUS: {card_name} - {amount} ({description}) - ${required_spend:,.0f} required")

    # Move threshold bonuses to other_bonus table
    bonuses_to_move = []
    for card_name, amount, description, required_spend in threshold_bonuses:
        cursor.execute("""
            SELECT id FROM signup_bonus
            WHERE card_id = (SELECT id FROM card_enhanced WHERE name = ?)
            AND (bonus_amount LIKE ? OR description LIKE ?)
        """, (card_name, f"%{amount}%", f"%{description}%"))

        bonus_records = cursor.fetchall()
        for (bonus_id,) in bonus_records:
            bonuses_to_move.append(bonus_id)

            # Insert into other_bonus
            cursor.execute("""
                INSERT INTO other_bonus
                (card_id, bonus_type, bonus_amount, description, required_spend, frequency, created_date)
                VALUES (
                    (SELECT id FROM card_enhanced WHERE name = ?),
                    'threshold',
                    ?,
                    ?,
                    ?,
                    'ongoing',
                    ?
                )
            """, (card_name, amount, description, required_spend, datetime.now().isoformat()))

            print(f"📊 THRESHOLD BONUS: {card_name} - {amount} ({description}) - ${required_spend:,.0f} threshold")

    # Remove moved bonuses from signup_bonus table
    for bonus_id in bonuses_to_move:
        cursor.execute("DELETE FROM signup_bonus WHERE id = ?", (bonus_id,))

    print(f"\nMoved {len(bonuses_to_move)} bonuses from sign-up to threshold category")

    conn.commit()
    conn.close()

    print("\n" + "="*80)
    print("FINAL CATEGORIZATION SUMMARY:")
    print("="*80)
    print("\n🎯 SIGN-UP BONUSES (Time-limited with specific spend requirements):")
    print("- Capital One VentureX: 75,000 miles for $4,000 in 3 months")
    print("- Hilton Honors Surpass: 130,000 points for $3,000 in 6 months")
    print("- Hilton Honors Aspire: 150,000 points for $6,000 in 6 months")
    print("- Atmos Rewards Ascent: 100,000 points + 25,000 point award for $6,000 in 90 days")
    print("- Hilton Honors Amex: 80,000 points for $2,000 in 6 months")

    print("\n📊 THRESHOLD BONUSES (Ongoing spending thresholds, no time limit):")
    print("- Chase Sapphire Reserve: $500 Southwest credit after $75,000 annual spend")
    print("- Chase Sapphire Reserve: $250 Shops at Chase credit after $75,000 annual spend")
    print("- World of Hyatt: Second free night after $15,000 annual spend")
    print("- Atmos Rewards Ascent: 10% rewards bonus (ongoing with eligible Bank of America account)")

if __name__ == "__main__":
    categorize_bonuses()
    print("\n=== BONUS CATEGORIZATION COMPLETE ===")