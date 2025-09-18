#!/usr/bin/env python3
"""
Database Interaction Examples
This file shows you how to interact with your SQLite database using Python.
Think of this as a tutorial for working with your database!
"""

# Import our Flask app and database models
from app import app, db, Card, Benefit, BonusCategory

def main():
    """
    Main function that demonstrates different database operations.
    We use app.app_context() because Flask needs to know we're working within the app.
    """

    with app.app_context():
        print("=== Credit Card Database Tutorial ===\n")

        # Example 1: Get all cards
        print("1. Getting all credit cards:")
        cards = Card.query.all()
        for card in cards:
            print(f"   - {card.name} (ID: {card.id})")
        print()

        # Example 2: Get a specific card by ID
        print("2. Getting a specific card (ID: 1):")
        card = Card.query.get(1)
        if card:
            print(f"   Found: {card.name}")
        else:
            print("   Card not found!")
        print()

        # Example 3: Get benefits for a specific card
        print("3. Getting benefits for the first card:")
        if card:
            benefits = Benefit.query.filter_by(card_id=card.id).all()
            print(f"   Benefits for {card.name}:")
            for benefit in benefits:
                print(f"      • {benefit.description}")
                print(f"        Value: {benefit.value}x, {benefit.frequency}")
        print()

        # Example 4: Search for cards by name
        print("4. Searching for cards with 'Chase' in the name:")
        chase_cards = Card.query.filter(Card.name.like('%Chase%')).all()
        for card in chase_cards:
            print(f"   - {card.name}")
        print()

        # Example 5: Get cards with high-value benefits
        print("5. Finding benefits with 3x or higher value:")
        high_value_benefits = Benefit.query.filter(Benefit.value >= 3.0).all()
        for benefit in high_value_benefits:
            card = Card.query.get(benefit.card_id)
            print(f"   - {benefit.description} ({card.name})")
        print()

        # Example 6: Count total cards and benefits
        print("6. Database statistics:")
        card_count = Card.query.count()
        benefit_count = Benefit.query.count()
        category_count = BonusCategory.query.count()
        print(f"   Total Cards: {card_count}")
        print(f"   Total Benefits: {benefit_count}")
        print(f"   Total Bonus Categories: {category_count}")
        print()

        # Example 7: Add a new card (uncomment to try)
        print("7. Adding a new card (commented out - uncomment to try):")
        print("   # new_card = Card(name='Citi Double Cash')")
        print("   # db.session.add(new_card)")
        print("   # db.session.commit()")
        print("   # print(f'Added new card: {new_card.name}')")
        print()

        # Uncomment these lines to actually add a new card:
        # new_card = Card(name="Citi Double Cash")
        # db.session.add(new_card)
        # db.session.commit()
        # print(f"Added new card: {new_card.name}")

        # Example 8: Complex query - cards with dining benefits
        print("8. Finding cards that have dining benefits:")
        dining_benefits = Benefit.query.filter(
            Benefit.description.like('%dining%')
        ).all()

        dining_card_ids = [benefit.card_id for benefit in dining_benefits]
        dining_cards = Card.query.filter(Card.id.in_(dining_card_ids)).all()

        for card in dining_cards:
            print(f"   - {card.name}")
        print()

        print("=== Tutorial Complete! ===")
        print("You now know how to:")
        print("• Query all records with .query.all()")
        print("• Get specific records with .query.get(id)")
        print("• Filter records with .query.filter()")
        print("• Search with patterns using .like('%text%')")
        print("• Count records with .query.count()")
        print("• Add new records with .add() and .commit()")

if __name__ == "__main__":
    main()