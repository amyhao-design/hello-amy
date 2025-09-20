"""
Master Database Functions - Data-Driven Backend
These functions make your entire app pull live data from the master database
instead of static database entries. Update your CSV files and the whole app updates!
"""

from local_cards_service import LocalCardsService

# Initialize the cards service
cards_service = LocalCardsService()

def get_active_card_names():
    """Get list of all active card names in user's wallet"""
    from app import CardEnhanced  # Import here to avoid circular import
    active_cards = CardEnhanced.query.filter_by(is_active=True).all()
    return [card.name for card in active_cards]

def get_master_signup_bonuses():
    """
    Get signup bonuses for ALL cards in user's wallet from master database
    This replaces get_real_signup_bonuses() to be completely data-driven
    """
    active_card_names = get_active_card_names()
    all_bonuses = []

    for card_name in active_card_names:
        # Get bonuses from master database for this card
        master_bonuses = cards_service.get_card_signup_bonuses(card_name)

        for bonus in master_bonuses:
            # Get user progress from database for this specific bonus
            from app import SignupBonus, CardEnhanced
            card = CardEnhanced.query.filter_by(name=card_name, is_active=True).first()
            existing_bonus = SignupBonus.query.filter_by(
                card_id=card.id if card else None
            ).first()

            # Merge master data with user progress
            bonus_data = {
                'card_name': card_name,
                'bonus_amount': bonus.get('bonus_amount', ''),
                'description': bonus.get('description', ''),
                'required_spend': bonus.get('required_spend', 0),
                'deadline_months': bonus.get('deadline_months', 0),
                # User progress data (if exists)
                'current_spend': existing_bonus.current_spend if existing_bonus else 0,
                'progress_percent': existing_bonus.progress_percent if existing_bonus else 0,
                'status': existing_bonus.status if existing_bonus else 'active',
                'status_text': existing_bonus.status_text if existing_bonus else 'Active',
                'deadline': existing_bonus.deadline if existing_bonus else None
            }

            # Only show non-completed bonuses
            if bonus_data['status'] != 'completed':
                all_bonuses.append(bonus_data)

    return sorted(all_bonuses, key=lambda x: x.get('required_spend', 0), reverse=True)

def get_master_threshold_bonuses():
    """
    Get threshold bonuses for ALL cards in user's wallet from master database
    This replaces get_real_spending_bonuses() to be completely data-driven
    """
    active_card_names = get_active_card_names()
    all_bonuses = []

    for card_name in active_card_names:
        # Get threshold bonuses from master database for this card
        master_bonuses = cards_service.get_card_threshold_bonuses(card_name)

        for bonus in master_bonuses:
            # Get user progress from database for this specific bonus
            from app import OtherBonus, CardEnhanced
            card = CardEnhanced.query.filter_by(name=card_name, is_active=True).first()
            existing_bonus = OtherBonus.query.filter_by(
                card_id=card.id if card else None
            ).first()

            # Merge master data with user progress
            bonus_data = {
                'card_name': card_name,
                'bonus_amount': bonus.get('bonus_amount', ''),
                'description': bonus.get('description', ''),
                'required_spend': bonus.get('required_spend', 0),
                'frequency': bonus.get('frequency', 'annual'),
                # User progress data (if exists)
                'current_spend': existing_bonus.current_spend if existing_bonus else 0,
                'progress_percent': existing_bonus.progress_percent if existing_bonus else 0,
                'status': existing_bonus.status if existing_bonus else 'active',
                'status_text': existing_bonus.status_text if existing_bonus else 'Active'
            }

            # Only show non-completed bonuses
            if bonus_data['status'] != 'completed':
                all_bonuses.append(bonus_data)

    return sorted(all_bonuses, key=lambda x: x.get('required_spend', 0), reverse=True)

def get_master_credits_by_frequency(frequency):
    """
    Get credits for ALL cards in user's wallet from master database by frequency
    This replaces get_real_credits_by_frequency() to be completely data-driven

    Args:
        frequency: 'annual', 'semi-annual', 'quarterly', 'monthly', 'onetime'
    """
    active_card_names = get_active_card_names()
    all_credits = []

    for card_name in active_card_names:
        # Get credits from master database for this card
        master_credits = cards_service.get_card_credit_benefits(card_name)

        for credit in master_credits:
            # Only include credits matching the requested frequency
            if credit.get('frequency', '').lower() == frequency.lower():
                # Get user usage data from database for this specific credit
                from app import CreditBenefit, CardEnhanced
                card = CardEnhanced.query.filter_by(name=card_name, is_active=True).first()
                existing_credit = CreditBenefit.query.filter_by(
                    card_id=card.id if card else None,
                    benefit_name=credit.get('benefit_name', '')
                ).first()

                # Merge master data with user usage
                credit_data = {
                    'card_name': card_name,
                    'benefit_name': credit.get('benefit_name', ''),
                    'credit_amount': credit.get('credit_amount', 0),
                    'description': credit.get('description', ''),
                    'frequency': credit.get('frequency', frequency),
                    'category': credit.get('category', ''),
                    # User usage data (if exists)
                    'amount_used': existing_credit.amount_used if existing_credit else 0,
                    'remaining_amount': existing_credit.remaining_amount if existing_credit else credit.get('credit_amount', 0),
                    'usage_percent': existing_credit.usage_percent if existing_credit else 0,
                    'last_reset': existing_credit.last_reset if existing_credit else None
                }

                all_credits.append(credit_data)

    # Sort by credit amount (highest first)
    return sorted(all_credits, key=lambda x: x.get('credit_amount', 0), reverse=True)

def get_master_multipliers_for_card(card_name):
    """
    Get multipliers for a specific card from master database
    Used for card detail pages
    """
    return cards_service.get_card_multipliers(card_name)

def get_master_card_data(card_name):
    """
    Get complete card data from master database
    Used for card detail pages
    """
    return cards_service.get_complete_card_data(card_name)

# Wrapper functions to maintain compatibility with existing code
def get_used_credits_by_frequency(frequency):
    """
    Get used credits by frequency - this pulls user usage data
    This function can stay as-is since it's about user behavior, not card definitions
    """
    from app import CreditBenefit

    # Get all used credits for the frequency
    used_credits = []
    credits = get_master_credits_by_frequency(frequency)

    for credit in credits:
        if credit['amount_used'] > 0:
            used_credits.append(credit)

    return used_credits