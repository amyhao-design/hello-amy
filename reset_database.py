#!/usr/bin/env python3
"""
Database Reset Script
This script clears ALL data from your database and lets you start fresh.
Be careful - this will delete everything!
"""

from app import app, db, Card, Benefit, BonusCategory

def clear_all_data():
    """
    Removes all data from the database.
    Think of it like emptying all the filing cabinets.
    """
    with app.app_context():
        print("⚠️  WARNING: This will delete ALL data from your database!")
        response = input("Are you sure you want to continue? (type 'yes' to confirm): ")

        if response.lower() != 'yes':
            print("❌ Operation cancelled. No data was deleted.")
            return False

        # Delete all records from each table
        print("🗑️  Deleting all bonus categories...")
        BonusCategory.query.delete()

        print("🗑️  Deleting all benefits...")
        Benefit.query.delete()

        print("🗑️  Deleting all cards...")
        Card.query.delete()

        # Save the changes
        db.session.commit()

        print("✅ All data has been cleared!")
        print("💡 You can now run your app to add fresh sample data.")
        return True

def main():
    print("=== Database Reset Tool ===")
    print("This tool will help you start fresh with your database.")
    print()

    clear_all_data()

if __name__ == "__main__":
    main()