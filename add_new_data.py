#!/usr/bin/env python3
"""
Add New Data Script
This script shows you how to add new cards and benefits to your existing database.
You can customize this script to add whatever data you want!
"""

from app import app, db, Card, Benefit, BonusCategory

def add_custom_cards():
    """
    Add your own custom credit cards to the database.
    Change this function to add whatever cards you want!
    """
    with app.app_context():
        print("🃏 Adding custom credit cards...")

        # Example 1: Add a new card
        wells_fargo = Card(name="Wells Fargo Active Cash")
        db.session.add(wells_fargo)
        db.session.commit()  # Save the card so we get an ID

        # Add benefits for Wells Fargo card
        wells_cash = Benefit(
            description="2% cash back on all purchases",
            value=2.0,
            frequency="Per purchase",
            card_id=wells_fargo.id
        )
        db.session.add(wells_cash)

        # Example 2: Add another card
        discover_it = Card(name="Discover it Student")
        db.session.add(discover_it)
        db.session.commit()

        # Add benefits for Discover card
        discover_rotating = Benefit(
            description="5% cash back on rotating categories",
            value=5.0,
            frequency="Quarterly",
            card_id=discover_it.id
        )

        discover_everything = Benefit(
            description="1% cash back on everything else",
            value=1.0,
            frequency="Per purchase",
            card_id=discover_it.id
        )

        db.session.add(discover_rotating)
        db.session.add(discover_everything)

        # Add bonus categories for Discover
        discover_gas = BonusCategory(
            category_name="Gas Stations",
            multiplier=5.0,
            card_id=discover_it.id
        )

        discover_restaurants = BonusCategory(
            category_name="Restaurants",
            multiplier=5.0,
            card_id=discover_it.id
        )

        db.session.add(discover_gas)
        db.session.add(discover_restaurants)

        # Save everything
        db.session.commit()

        print(f"✅ Added {wells_fargo.name}")
        print(f"✅ Added {discover_it.name}")
        print("🎉 Custom cards added successfully!")

def add_benefit_to_existing_card():
    """
    Add a new benefit to a card that already exists.
    """
    with app.app_context():
        print("🔧 Adding benefit to existing card...")

        # Find an existing card (let's use the first one)
        existing_card = Card.query.first()

        if existing_card:
            new_benefit = Benefit(
                description="No foreign transaction fees",
                value=0.0,  # This benefit saves money rather than earning points
                frequency="Always",
                card_id=existing_card.id
            )

            db.session.add(new_benefit)
            db.session.commit()

            print(f"✅ Added new benefit to {existing_card.name}")
        else:
            print("❌ No existing cards found!")

def show_all_data():
    """
    Display all the data in your database.
    """
    with app.app_context():
        print("\n📊 Current Database Contents:")
        print("=" * 40)

        cards = Card.query.all()
        for card in cards:
            print(f"\n🃏 {card.name} (ID: {card.id})")

            benefits = Benefit.query.filter_by(card_id=card.id).all()
            if benefits:
                print("   Benefits:")
                for benefit in benefits:
                    print(f"   • {benefit.description} ({benefit.value}x)")

            categories = BonusCategory.query.filter_by(card_id=card.id).all()
            if categories:
                print("   Bonus Categories:")
                for category in categories:
                    print(f"   • {category.category_name}: {category.multiplier}x")

def main():
    print("=== Add New Data Tool ===")
    print("This tool helps you add new cards and benefits to your database.")
    print()

    while True:
        print("\nWhat would you like to do?")
        print("1. Add custom cards (Wells Fargo + Discover)")
        print("2. Add benefit to existing card")
        print("3. Show all current data")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            add_custom_cards()
        elif choice == "2":
            add_benefit_to_existing_card()
        elif choice == "3":
            show_all_data()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()