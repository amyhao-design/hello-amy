#!/usr/bin/env python3
"""
Convert CSV files back to JSON format for the card tracker
Run this after editing the CSV files in Excel

This matches the Google Sheets structure exactly:
1. Cards.csv (Issuer, Card Name, Brand Class)
2. SignupBonuses.csv (signup bonuses for left column)
3. SpendingBonuses.csv (threshold bonuses for left column)
4. Multipliers.csv (points multipliers for card details only)
5. Credits.csv (credits for right column by frequency)
"""

import csv
import json

def csv_to_json():
    """Convert all 5 CSV files to a single JSON database file"""

    # Initialize the data structure
    data = {
        "cards": [],
        "signup_bonuses": [],
        "threshold_bonuses": [],
        "multipliers": [],
        "credits": []
    }

    # Read Cards.csv with user's improved structure (card_name, issuer)
    try:
        with open('Cards.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Form full card name as "issuer + card_name"
                full_card_name = f"{row['issuer']} {row['card_name']}".strip()
                card_data = {
                    'card_name': full_card_name,
                    'issuer': row['issuer'],
                    'card_base_name': row['card_name']
                }
                data["cards"].append(card_data)
        print("✅ Loaded cards from Cards.csv")
    except FileNotFoundError:
        print("❌ Cards.csv not found")

    # Read SignupBonuses.csv with user's improved structure
    try:
        with open('SignupBonuses.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up required_spend (remove $ and commas)
                required_spend_str = str(row['required_spend']).replace('$', '').replace(',', '')
                bonus_data = {
                    'card_name': row['card_name'],
                    'bonus_amount': row['bonus_amount'],
                    'required_spend': int(required_spend_str) if required_spend_str.isdigit() else 0,
                    'deadline_months': int(row['deadline_months']) if row['deadline_months'] else 0
                }
                data["signup_bonuses"].append(bonus_data)
        print("✅ Loaded signup bonuses from SignupBonuses.csv")
    except FileNotFoundError:
        print("❌ SignupBonuses.csv not found")

    # Read SpendingBonuses.csv (threshold bonuses) with new bonus_type field
    try:
        with open('SpendingBonuses.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up required_spend (remove $ and commas)
                required_spend_str = str(row['required_spend']).replace('$', '').replace(',', '')
                bonus_data = {
                    'card_name': row['card_name'],
                    'bonus_type': row.get('bonus_type', 'threshold'),  # New field
                    'bonus_amount': row['bonus_amount'],
                    'description': row['description'],
                    'required_spend': int(required_spend_str) if required_spend_str.isdigit() else 0,
                    'frequency': row['frequency']
                }
                data["threshold_bonuses"].append(bonus_data)
        print("✅ Loaded threshold bonuses from SpendingBonuses.csv")
    except FileNotFoundError:
        print("ℹ️  SpendingBonuses.csv not found (that's okay)")

    # Read Multipliers.csv with new cap fields
    try:
        with open('Multipliers.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                multiplier_data = {
                    'card_name': row['card_name'],
                    'category': row['category'],
                    'multiplier': float(row['multiplier']) if row['multiplier'] else 1.0,
                    'description': row['description'],
                    'cap_amount': int(row.get('cap_amount', 0)) if row.get('cap_amount', '0').isdigit() else 0,  # New field
                    'cap_frequency': row.get('cap_frequency', 'N/A')  # New field
                }
                data["multipliers"].append(multiplier_data)
        print("✅ Loaded multipliers from Multipliers.csv")
    except FileNotFoundError:
        print("ℹ️  Multipliers.csv not found (that's okay)")

    # Read Credits.csv with support for new frequencies like every_4_years
    try:
        with open('Credits.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                credit_data = {
                    'card_name': row['card_name'],
                    'benefit_name': row['benefit_name'],
                    'credit_amount': int(row['credit_amount']) if row['credit_amount'] else 0,
                    'description': row['description'],
                    'frequency': row['frequency'].lower(),  # Support every_4_years, etc.
                    'category': row['category']
                }
                data["credits"].append(credit_data)
        print("✅ Loaded credits from Credits.csv")
    except FileNotFoundError:
        print("❌ Credits.csv not found")

    # Write to JSON file
    with open('master_cards_database.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("🎉 Successfully created master_cards_database.json")
    print(f"   - {len(data['cards'])} cards")
    print(f"   - {len(data['signup_bonuses'])} signup bonuses")
    print(f"   - {len(data['threshold_bonuses'])} threshold bonuses")
    print(f"   - {len(data['multipliers'])} multipliers")
    print(f"   - {len(data['credits'])} credits")

    # Create a mapping of short names to full names for consistency
    name_mapping = {}
    for card in data['cards']:
        name_mapping[card['card_base_name']] = card['card_name']

    # Update all references in other files to use full card names
    for bonus in data['signup_bonuses']:
        if bonus['card_name'] in name_mapping:
            bonus['card_name'] = name_mapping[bonus['card_name']]

    for bonus in data['threshold_bonuses']:
        if bonus['card_name'] in name_mapping:
            bonus['card_name'] = name_mapping[bonus['card_name']]

    for multiplier in data['multipliers']:
        if multiplier['card_name'] in name_mapping:
            multiplier['card_name'] = name_mapping[multiplier['card_name']]

    for credit in data['credits']:
        if credit['card_name'] in name_mapping:
            credit['card_name'] = name_mapping[credit['card_name']]

    # Show how card names are formed
    print("\n📋 Card names formed:")
    for card in data['cards'][:5]:  # Show first 5
        print(f"   - {card['card_name']} (from '{card['issuer']}' + '{card['card_base_name']}')")

    print("\n🔗 Name mapping applied:")
    for short_name, full_name in list(name_mapping.items())[:5]:
        print(f"   - '{short_name}' → '{full_name}'")

if __name__ == "__main__":
    csv_to_json()