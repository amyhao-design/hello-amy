"""
Local Cards Database Service for Credit Card Tracker
Handles loading card data from local JSON file instead of Google Sheets
"""

import json
import os


class LocalCardsService:
    def __init__(self, database_file='master_cards_database.json'):
        """
        Initialize local cards service

        Args:
            database_file: Path to the JSON database file
        """
        self.database_file = database_file
        self.data = self._load_database()

    def _load_database(self):
        """Load the master database from JSON file"""
        try:
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r') as f:
                    data = json.load(f)
                    print("✅ Local cards database loaded successfully")
                    return data
            else:
                print(f"❌ Database file not found: {self.database_file}")
                return {}
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return {}

    def get_available_cards(self):
        """
        Get list of all available credit cards

        Returns:
            List of dictionaries with card information
        """
        return self.data.get('cards', [])

    def get_card_signup_bonuses(self, card_name):
        """
        Get signup bonuses for a specific card

        Args:
            card_name: Name of the credit card

        Returns:
            List of signup bonus dictionaries
        """
        bonuses = []
        for bonus in self.data.get('signup_bonuses', []):
            if bonus.get('card_name') == card_name:
                bonuses.append(bonus)
        return bonuses

    def get_card_threshold_bonuses(self, card_name):
        """
        Get threshold bonuses (spending bonuses) for a specific card
        These map to "Threshold Bonuses" section on dashboard

        Args:
            card_name: Name of the credit card

        Returns:
            List of threshold bonus dictionaries
        """
        bonuses = []
        for bonus in self.data.get('threshold_bonuses', []):
            if bonus.get('card_name') == card_name:
                bonuses.append(bonus)
        return bonuses

    def get_card_multipliers(self, card_name):
        """
        Get multiplier bonuses for a specific card
        These are only shown in card details, NOT on dashboard

        Args:
            card_name: Name of the credit card

        Returns:
            List of multiplier dictionaries
        """
        multipliers = []
        for multiplier in self.data.get('multipliers', []):
            if multiplier.get('card_name') == card_name:
                multipliers.append(multiplier)
        return multipliers

    def get_card_credit_benefits(self, card_name):
        """
        Get credit benefits for a specific card

        Args:
            card_name: Name of the credit card

        Returns:
            List of credit benefit dictionaries
        """
        benefits = []
        for benefit in self.data.get('credits', []):
            if benefit.get('card_name') == card_name:
                # Convert to match expected format
                formatted_benefit = {
                    'card_name': benefit.get('card_name'),
                    'benefit_name': benefit.get('benefit_name'),
                    'credit_amount': benefit.get('credit_amount'),
                    'description': benefit.get('description'),
                    'frequency': benefit.get('frequency'),
                    'category': benefit.get('category', '')
                }
                benefits.append(formatted_benefit)
        return benefits

    def get_complete_card_data(self, card_name):
        """
        Get all data for a specific card (card info + all bonuses/benefits)
        Maps to dashboard structure correctly

        Args:
            card_name: Name of the credit card

        Returns:
            Dictionary with complete card data
        """
        # Get basic card info
        cards = self.get_available_cards()
        card_info = next((card for card in cards if card.get('card_name') == card_name), {})

        if not card_info:
            return None

        # Get all bonuses and benefits with correct mapping
        card_data = {
            'card_info': card_info,
            'signup_bonuses': self.get_card_signup_bonuses(card_name),
            'threshold_bonuses': self.get_card_threshold_bonuses(card_name),  # Maps to "Threshold Bonuses" on dashboard
            'credit_benefits': self.get_card_credit_benefits(card_name),
            'multipliers': self.get_card_multipliers(card_name)  # Only for card details, not dashboard
        }

        return card_data


# Example usage and testing function
def test_local_service():
    """Test function to verify local database integration"""
    service = LocalCardsService()

    # Test getting available cards
    cards = service.get_available_cards()
    print(f"Found {len(cards)} available cards:")
    for card in cards:
        print(f"  - {card['card_name']}")

    if cards:
        # Test getting complete data for first card
        first_card = cards[0]['card_name']
        complete_data = service.get_complete_card_data(first_card)
        print(f"\nComplete data for {first_card}:")
        print(f"  Sign-up bonuses: {len(complete_data['signup_bonuses'])}")
        print(f"  Threshold bonuses: {len(complete_data['threshold_bonuses'])}")
        print(f"  Credit benefits: {len(complete_data['credit_benefits'])}")
        print(f"  Multipliers: {len(complete_data['multipliers'])}")


if __name__ == "__main__":
    test_local_service()