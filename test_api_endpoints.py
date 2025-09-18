#!/usr/bin/env python3
"""
API Endpoints Test Script
This script tests all our new API endpoints to make sure they work correctly.
"""

import json
from app import app, db, Card, MultiplierBenefit, CreditBenefit, Usage

def test_api_endpoints():
    """Test all our API endpoints"""

    # Start the Flask app for testing
    print("🧪 Testing API Endpoints")
    print("=" * 40)

    with app.app_context():
        print("\n1️⃣ Testing /api/cards endpoint...")

        # Test the cards endpoint manually by calling the function
        from app import api_get_all_cards

        with app.test_client() as client:
            # Test 1: Get all cards
            response = client.get('/api/cards')
            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Success: Found {data['total_cards']} cards")
                print(f"   📋 First 3 cards:")
                for i, card in enumerate(data['cards'][:3]):
                    print(f"      {i+1}. {card['name']} - {card['total_benefits']} benefits")
            else:
                print(f"   ❌ Error: {response.get_json()}")

        print("\n2️⃣ Testing /api/benefits/<card_id> endpoint...")

        with app.test_client() as client:
            # Test 2: Get benefits for first card
            response = client.get('/api/benefits/1')
            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.get_json()
                card_name = data['card']['name']
                multipliers = len(data['multiplier_benefits'])
                credits = len(data['credit_benefits'])
                print(f"   ✅ Success: {card_name}")
                print(f"   🎯 Multiplier benefits: {multipliers}")
                print(f"   💳 Credit benefits: {credits}")

                # Show a sample multiplier
                if data['multiplier_benefits']:
                    sample = data['multiplier_benefits'][0]
                    print(f"   📝 Sample multiplier: {sample['multiplier']}x {sample['category']}")
            else:
                print(f"   ❌ Error: {response.get_json()}")

        print("\n3️⃣ Testing /api/usage endpoint (GET - view history)...")

        with app.test_client() as client:
            # Test 3: Get usage history (should be empty initially)
            response = client.get('/api/usage')
            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Success: Found {data['total_usage_records']} usage records")
                if data['total_usage_records'] == 0:
                    print("   📝 No usage records yet (expected for fresh database)")
            else:
                print(f"   ❌ Error: {response.get_json()}")

        print("\n4️⃣ Testing /api/usage endpoint (POST - record usage)...")

        with app.test_client() as client:
            # Test 4: Record a usage (like using a travel credit)
            usage_data = {
                'card_id': 1,  # First card (Chase Sapphire Reserve)
                'benefit_type': 'credit',
                'benefit_id': 1,
                'amount': 300.0,
                'description': 'Used $300 travel credit for hotel booking'
            }

            response = client.post('/api/usage',
                                   data=json.dumps(usage_data),
                                   content_type='application/json')
            print(f"   Status Code: {response.status_code}")

            if response.status_code == 201:
                data = response.get_json()
                print(f"   ✅ Success: {data['message']}")
                print(f"   🃏 Card: {data['card_name']}")
                print(f"   🆔 Usage ID: {data['usage_id']}")
            else:
                print(f"   ❌ Error: {response.get_json()}")

        print("\n5️⃣ Testing /api/usage endpoint (GET again - should show our record)...")

        with app.test_client() as client:
            # Test 5: Get usage history again (should show our new record)
            response = client.get('/api/usage')
            print(f"   Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Success: Found {data['total_usage_records']} usage records")
                if data['usage_history']:
                    latest = data['usage_history'][0]
                    print(f"   📝 Latest usage: ${latest['amount']} on {latest['card_name']}")
                    print(f"   📅 Date: {latest['date_used']}")
            else:
                print(f"   ❌ Error: {response.get_json()}")

        print("\n6️⃣ Testing error handling...")

        with app.test_client() as client:
            # Test 6: Try to get benefits for non-existent card
            response = client.get('/api/benefits/999')
            print(f"   Status Code: {response.status_code}")

            if response.status_code == 404:
                data = response.get_json()
                print(f"   ✅ Success: Properly handled non-existent card")
                print(f"   📝 Error message: {data['error']}")
            else:
                print(f"   ❌ Unexpected response: {response.get_json()}")

def print_usage_examples():
    """Show examples of how to use the API endpoints"""
    print("\n" + "=" * 60)
    print("📚 HOW TO USE YOUR NEW API ENDPOINTS")
    print("=" * 60)

    print("\n🔗 1. Get All Cards:")
    print("   curl http://localhost:5000/api/cards")
    print("   Returns: JSON list of all your credit cards with benefit counts")

    print("\n🔗 2. Get Benefits for a Specific Card:")
    print("   curl http://localhost:5000/api/benefits/1")
    print("   Returns: JSON object with all multipliers and credits for card ID 1")

    print("\n🔗 3. View Usage History:")
    print("   curl http://localhost:5000/api/usage")
    print("   Returns: JSON list of all times you've used benefits")

    print("\n🔗 4. Record Benefit Usage:")
    print("   curl -X POST http://localhost:5000/api/usage \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print("          \"card_id\": 1,")
    print("          \"benefit_type\": \"credit\",")
    print("          \"benefit_id\": 1,")
    print("          \"amount\": 300.0,")
    print("          \"description\": \"Used travel credit for hotel\"")
    print("        }'")
    print("   Returns: Confirmation that usage was recorded")

    print("\n💡 Pro Tips:")
    print("   • Use these endpoints in scripts to automate tracking")
    print("   • Build a mobile app that calls these endpoints")
    print("   • Create reports by analyzing the usage data")
    print("   • Set up alerts when you haven't used certain benefits")

if __name__ == "__main__":
    test_api_endpoints()
    print_usage_examples()
    print("\n🎉 API endpoint testing complete!")