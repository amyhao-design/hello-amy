#!/usr/bin/env python3
"""
Fix remaining "Credits Credit" naming issues
"""

import sqlite3

def fix_credits_naming():
    """Fix specific remaining credit naming issues"""
    print("=== FIXING REMAINING CREDITS NAMING ISSUES ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Get all credits that still have "Credits Credit" or similar issues
    cursor.execute("SELECT * FROM credit_benefit2 WHERE benefit_name LIKE '%Credits Credit%' OR benefit_name LIKE '%Credit Credit%'")
    bad_credits = cursor.fetchall()

    for credit in bad_credits:
        credit_id, card_id, benefit_name, category, amount, description, frequency, reset_date, has_progress, required_amount, current_amount = credit

        new_name = benefit_name
        desc_lower = description.lower()

        print(f"Fixing: '{benefit_name}' - '{description}'")

        # Specific fixes based on description content
        if 'renowned hotels' in desc_lower:
            new_name = "Renowned Hotels and Resorts Credit"
        elif 'jsx' in desc_lower:
            new_name = "JSX Flight Credit"
        elif 'rideshare' in desc_lower:
            new_name = "Rideshare Credit"
        elif 'avis' in desc_lower or 'budget' in desc_lower:
            new_name = "Car Rental Credit"
        elif 'hotel' in desc_lower and 'chase travel' in desc_lower:
            new_name = "Chase Travel Hotel Credit"
        elif 'chase travel' in desc_lower and 'edit' in desc_lower:
            new_name = "Chase Travel Edit Credit"
        elif 'prepaid' in desc_lower and 'hotel' in desc_lower:
            new_name = "Prepaid Hotel Credit"
        else:
            # Try to extract the key service/benefit name from the beginning of description
            words = description.split()
            if len(words) > 1:
                # Look for the main service name
                if words[0].lower() in ['credits', 'credit']:
                    if len(words) > 2 and words[1].lower() == 'on':
                        # "Credits on [service]" format
                        service_words = []
                        for word in words[2:]:
                            if word.lower() in ['via', 'through', 'at', 'for', 'with']:
                                break
                            service_words.append(word)
                        if service_words:
                            service_name = ' '.join(service_words[:3])  # Take first 3 words max
                            new_name = f"{service_name} Credit"
                    elif len(words) > 1:
                        # "Credits [service]" format
                        service_words = []
                        for word in words[1:]:
                            if word.lower() in ['via', 'through', 'at', 'for', 'with', 'purchases', 'made']:
                                break
                            service_words.append(word)
                        if service_words:
                            service_name = ' '.join(service_words[:3])  # Take first 3 words max
                            new_name = f"{service_name} Credit"

        # Clean up the name
        new_name = new_name.replace('Credits Credit', 'Credit').replace('Credit Credit', 'Credit')

        # Update if we changed the name
        if new_name != benefit_name:
            cursor.execute("UPDATE credit_benefit2 SET benefit_name = ? WHERE id = ?", (new_name, credit_id))
            print(f"  → Updated to: '{new_name}'")
        else:
            print(f"  → No change needed")

    # Also fix any remaining bad patterns
    patterns_to_fix = [
        ("Credits Credit", "Credit"),
        ("Credit Credit", "Credit"),
        ("Credits on flights purchased directly through JSX", "JSX Flight Credit"),
        ("Credits on prepaid hotel stays via Renowned Hotels and Resorts", "Renowned Hotels and Resorts Credit"),
        ("Credits on rideshare purchases", "Rideshare Credit"),
    ]

    for old_pattern, new_name in patterns_to_fix:
        cursor.execute("UPDATE credit_benefit2 SET benefit_name = ? WHERE description LIKE ?", (new_name, f"%{old_pattern}%"))
        if cursor.rowcount > 0:
            print(f"Updated {cursor.rowcount} credits from pattern '{old_pattern}' to '{new_name}'")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_credits_naming()
    print("\n=== CREDITS NAMING FIXES COMPLETE ===")