#!/usr/bin/env python3
"""
Fix remaining "Statement Credit" naming issues to be more descriptive
"""

import sqlite3

def fix_statement_credits():
    """Fix all vague 'Statement Credit' names to be more descriptive"""
    print("=== FIXING STATEMENT CREDIT NAMING ISSUES ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Get all credits with "Statement Credit" in the name
    cursor.execute("SELECT * FROM credit_benefit2 WHERE benefit_name LIKE '%Statement Credit%'")
    statement_credits = cursor.fetchall()

    for credit in statement_credits:
        credit_id, card_id, benefit_name, category, amount, description, frequency, reset_date, has_progress, required_amount, current_amount = credit

        new_name = benefit_name
        desc_lower = description.lower()

        print(f"Fixing: '{benefit_name}' - '{description}'")

        # Specific fixes based on description content
        if 'peloton' in desc_lower:
            new_name = "Peloton Credit"
        elif 'dunkin' in desc_lower:
            new_name = "Dunkin' Credit"
        elif 'grubhub' in desc_lower or 'cheesecake factory' in desc_lower or 'goldbelly' in desc_lower or 'wine.com' in desc_lower or 'five guys' in desc_lower:
            new_name = "Food Credit"
        elif 'dining' in desc_lower and 'sapphire' in desc_lower:
            new_name = "Exclusive Dining Credit"
        elif 'stubhub' in desc_lower or 'viagogo' in desc_lower:
            new_name = "Entertainment Credit"
        elif 'hilton' in desc_lower and 'property' in desc_lower:
            new_name = "Hilton Property Credit"
        elif 'hilton' in desc_lower and 'resort' in desc_lower:
            new_name = "Hilton Resort Credit"
        elif 'flight' in desc_lower:
            new_name = "Flight Credit"
        elif 'clear' in desc_lower:
            new_name = "CLEAR Credit"
        elif 'resort' in desc_lower and ('waldorf' in desc_lower or 'conrad' in desc_lower):
            new_name = "Resort Credit"
        else:
            # Try to extract the main service from the description
            words = description.split()
            for i, word in enumerate(words):
                if word.lower() in ['for', 'towards', 'on', 'at', 'with']:
                    # Look for the service name after these prepositions
                    if i + 1 < len(words):
                        service_word = words[i + 1]
                        # Clean up common words
                        service_word = service_word.replace(',', '').replace('.', '').strip()
                        if service_word.lower() not in ['purchases', 'made', 'directly', 'a', 'the', 'membership']:
                            new_name = f"{service_word.title()} Credit"
                            break

        # Clean up the name
        new_name = new_name.replace('Statement Credit', 'Credit').replace('credits', 'Credit')

        # Update if we changed the name
        if new_name != benefit_name:
            cursor.execute("UPDATE credit_benefit2 SET benefit_name = ? WHERE id = ?", (new_name, credit_id))
            print(f"  → Updated to: '{new_name}'")
        else:
            print(f"  → No change needed")

    # Also check for any other vague patterns and fix them
    additional_fixes = [
        ("Statement credit towards Peloton membership", "Peloton Credit"),
        ("Statement credits for dining at Sapphire Reserve Exclusive Tables program restaurants", "Exclusive Dining Credit"),
        ("Statement credits for purchases on StubHub and viagogo.com", "Entertainment Credit"),
        ("Statement credits for Dunkin' Donuts", "Dunkin' Credit"),
        ("Statement credits for Grubhub, The Cheesecake Factory, Goldbelly, Wine.com, Five Guys", "Food Credit"),
        ("Statement credits for purchases made directly with a Hilton property", "Hilton Property Credit"),
        ("Statement credits for purchases made directly with participating Hilton Resorts", "Hilton Resort Credit"),
        ("Statement credits on flight purchases", "Flight Credit"),
        ("Statement credits for a CLEAR plus membership", "CLEAR Credit"),
    ]

    for description_pattern, new_name in additional_fixes:
        cursor.execute("UPDATE credit_benefit2 SET benefit_name = ? WHERE description LIKE ?", (new_name, f"%{description_pattern}%"))
        if cursor.rowcount > 0:
            print(f"Updated {cursor.rowcount} credits from description pattern to '{new_name}'")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_statement_credits()
    print("\n=== STATEMENT CREDIT NAMING FIXES COMPLETE ===")