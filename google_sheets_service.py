"""
Google Sheets Service for Credit Card Tracker
Handles all Google Sheets API interactions for fetching card data
"""

import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsService:
    def __init__(self, credentials_file='google-credentials.json', spreadsheet_id=None):
        """
        Initialize Google Sheets service

        Args:
            credentials_file: Path to the service account JSON file
            spreadsheet_id: ID of the Google Sheet (from the URL)
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Google Sheets API service"""
        try:
            # Define the scope for Google Sheets API
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

            # Load credentials from the service account file
            if os.path.exists(self.credentials_file):
                credentials = Credentials.from_service_account_file(
                    self.credentials_file, scopes=SCOPES
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                print("✅ Google Sheets service initialized successfully")
            else:
                print(f"❌ Credentials file not found: {self.credentials_file}")
                print("Please make sure you've downloaded the service account JSON file")

        except Exception as e:
            print(f"❌ Error initializing Google Sheets service: {e}")

    def set_spreadsheet_id(self, spreadsheet_id):
        """Set the spreadsheet ID to work with"""
        self.spreadsheet_id = spreadsheet_id

    def read_sheet_data(self, sheet_name, range_name="A:Z"):
        """
        Read data from a specific sheet

        Args:
            sheet_name: Name of the sheet tab (e.g., 'Cards', 'SignupBonuses')
            range_name: Range to read (default: all columns A-Z)

        Returns:
            List of rows with data
        """
        if not self.service or not self.spreadsheet_id:
            return []

        try:
            # Call the Sheets API
            sheet_range = f"{sheet_name}!{range_name}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range
            ).execute()

            values = result.get('values', [])

            if not values:
                print(f"No data found in {sheet_name}")
                return []

            return values

        except HttpError as error:
            print(f"❌ Error reading sheet {sheet_name}: {error}")
            return []

    def get_available_cards(self):
        """
        Get list of all available credit cards from the Cards sheet
        Card names are formed by combining issuer + card name

        Returns:
            List of dictionaries with card information
        """
        data = self.read_sheet_data('Cards')
        if not data:
            return []

        # First row contains headers
        headers = data[0]
        cards = []

        for row in data[1:]:  # Skip header row
            if len(row) >= 2:  # Need at least issuer and card name
                # Form full card name as "Issuer Card Name"
                issuer = row[0] if len(row) > 0 else ''
                card_name = row[1] if len(row) > 1 else ''
                full_card_name = f"{issuer} {card_name}".strip()

                if full_card_name:
                    card = {
                        'card_name': full_card_name,
                        'issuer': issuer,
                        'card_base_name': card_name,
                        'brand_class': row[2] if len(row) > 2 else ''
                    }
                    cards.append(card)

        return cards

    def get_card_signup_bonuses(self, card_name):
        """
        Get signup bonuses for a specific card

        Args:
            card_name: Name of the credit card

        Returns:
            List of signup bonus dictionaries
        """
        data = self.read_sheet_data('SignupBonuses')
        if not data:
            return []

        headers = data[0]
        bonuses = []

        for row in data[1:]:
            if row and row[0] == card_name:  # Match card name in first column
                bonus = {}
                for i, header in enumerate(headers):
                    bonus[header.lower().replace(' ', '_')] = row[i] if i < len(row) else ''
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
        data = self.read_sheet_data('SpendingBonuses')
        if not data:
            return []

        headers = data[0]
        bonuses = []

        for row in data[1:]:
            if row and row[0] == card_name:
                bonus = {}
                for i, header in enumerate(headers):
                    bonus[header.lower().replace(' ', '_')] = row[i] if i < len(row) else ''
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
        data = self.read_sheet_data('Multipliers')
        if not data:
            return []

        headers = data[0]
        multipliers = []

        for row in data[1:]:
            if row and row[0] == card_name:
                multiplier = {}
                for i, header in enumerate(headers):
                    multiplier[header.lower().replace(' ', '_')] = row[i] if i < len(row) else ''
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
        data = self.read_sheet_data('CreditBenefits')
        if not data:
            return []

        headers = data[0]
        benefits = []

        for row in data[1:]:
            if row and row[0] == card_name:
                benefit = {}
                for i, header in enumerate(headers):
                    benefit[header.lower().replace(' ', '_')] = row[i] if i < len(row) else ''
                benefits.append(benefit)

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
def test_sheets_service():
    """Test function to verify Google Sheets integration"""
    service = GoogleSheetsService()

    # You'll need to set your actual spreadsheet ID here
    # service.set_spreadsheet_id('your-spreadsheet-id-here')

    # Test getting available cards
    cards = service.get_available_cards()
    print(f"Found {len(cards)} available cards")

    if cards:
        # Test getting complete data for first card
        first_card = cards[0]['card_name']
        complete_data = service.get_complete_card_data(first_card)
        print(f"Complete data for {first_card}:")
        print(json.dumps(complete_data, indent=2))


if __name__ == "__main__":
    test_sheets_service()