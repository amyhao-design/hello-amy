#!/usr/bin/env python3
"""
Test New Card Wallet UI
This script tests our new beautiful card wallet interface.
"""

from app import app, db

def test_new_ui():
    """Test the new UI functionality"""
    print("🎨 Testing New Card Wallet UI")
    print("=" * 40)

    with app.app_context():
        # Test the helper functions
        from app import get_card_brand_class, get_card_issuer
        from app import get_sample_signup_bonuses, get_sample_monthly_bonuses
        from app import get_sample_quarterly_bonuses, get_sample_annual_bonuses

        print("\n1️⃣ Testing Card Brand Classification...")
        test_cards = [
            "Chase Sapphire Reserve",
            "American Express Gold",
            "Capital One VentureX",
            "Hilton Honors Aspire",
            "Marriott Bonvoy Boundless"
        ]

        for card_name in test_cards:
            brand_class = get_card_brand_class(card_name)
            issuer = get_card_issuer(card_name)
            print(f"   • {card_name}")
            print(f"     Brand Class: {brand_class}")
            print(f"     Issuer: {issuer}")

        print("\n2️⃣ Testing Sample Data Generation...")
        signup_bonuses = get_sample_signup_bonuses()
        print(f"   ✅ Generated {len(signup_bonuses)} signup bonuses")

        monthly_bonuses = get_sample_monthly_bonuses()
        print(f"   ✅ Generated {len(monthly_bonuses)} monthly bonuses")

        quarterly_bonuses = get_sample_quarterly_bonuses()
        print(f"   ✅ Generated {len(quarterly_bonuses)} quarterly bonuses")

        annual_bonuses = get_sample_annual_bonuses()
        print(f"   ✅ Generated {len(annual_bonuses)} annual bonuses")

        print("\n3️⃣ Sample Progress Data Preview...")
        for bonus in signup_bonuses[:2]:  # Show first 2
            print(f"   📊 {bonus['card_name']}: {bonus['progress_percent']}% complete")
            print(f"      ${bonus['current_spend']} / ${bonus['required_spend']}")

    print("\n4️⃣ Testing Flask Routes...")
    with app.test_client() as client:
        # Test dashboard
        response = client.get('/')
        print(f"   Dashboard: Status {response.status_code}")

        # Test purchase helper
        response = client.get('/purchase-helper')
        print(f"   Purchase Helper: Status {response.status_code}")

    print("\n🎉 UI Testing Complete!")
    print("\n💡 To view the new UI:")
    print("   1. Start the Flask app: python3 app.py")
    print("   2. Open browser to: http://localhost:5000")
    print("   3. Enjoy your beautiful card wallet! 💳")

if __name__ == "__main__":
    test_new_ui()