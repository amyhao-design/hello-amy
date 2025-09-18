#!/usr/bin/env python3
"""
Add New Cards Script
This script adds the Hilton Honors American Express Card and American Express Platinum Card 
with all their benefits to the card tracker database.
"""

from app import (app, db, CardEnhanced, SignupBonus, MultiplierBenefit, 
                 CreditBenefit2, SpendingBonus)
import datetime

def add_hilton_honors_amex_card():
    """Add the Hilton Honors American Express Card"""
    with app.app_context():
        print("🏨 Adding Hilton Honors American Express Card...")
        
        # Check if card already exists
        existing_card = CardEnhanced.query.filter_by(name="Hilton Honors American Express Card").first()
        if existing_card:
            print("   ⚠️ Card already exists, updating instead...")
            hilton_honors_card = existing_card
        else:
            # Create the new card
            hilton_honors_card = CardEnhanced(
                name="Hilton Honors American Express Card",
                issuer="American Express",
                brand_class="hilton",
                last_four="0001"  # Placeholder
            )
            db.session.add(hilton_honors_card)
            db.session.commit()  # Commit to get the ID
        
        # Add signup bonus
        signup_bonus = SignupBonus(
            card_id=hilton_honors_card.id,
            bonus_amount="80,000 Hilton Honors Bonus Points",
            description="Spend $2,000 in purchases within your first 6 months of Card Membership",
            required_spend=2000.0,
            current_spend=0.0,
            deadline=datetime.date(2025, 8, 1),  # Example 6 months from now
            status='not-started'
        )
        db.session.add(signup_bonus)
        
        # Add multiplier benefits
        multiplier_benefits = [
            MultiplierBenefit(
                category="Hotels & Resorts",
                description="7x points on Hotels & Resorts for eligible purchases made directly with hotels and resorts in the Hilton portfolio",
                multiplier=7.0,
                card_id=hilton_honors_card.id
            ),
            MultiplierBenefit(
                category="Dining",
                description="5x points on dining",
                multiplier=5.0,
                card_id=hilton_honors_card.id
            ),
            MultiplierBenefit(
                category="Groceries",
                description="5x points on groceries",
                multiplier=5.0,
                card_id=hilton_honors_card.id
            ),
            MultiplierBenefit(
                category="Gas",
                description="5x points on gas",
                multiplier=5.0,
                card_id=hilton_honors_card.id
            ),
            MultiplierBenefit(
                category="All Other Purchases",
                description="3x points for all other purchases",
                multiplier=3.0,
                card_id=hilton_honors_card.id
            )
        ]
        
        for benefit in multiplier_benefits:
            db.session.add(benefit)
        
        db.session.commit()
        print(f"✅ Added Hilton Honors American Express Card with {len(multiplier_benefits)} multiplier benefits and 1 signup bonus")


def add_american_express_platinum_card():
    """Add the American Express Platinum Card"""
    with app.app_context():
        print("💎 Adding American Express Platinum Card...")
        
        # Check if card already exists
        existing_card = CardEnhanced.query.filter_by(name="American Express Platinum").first()
        if existing_card:
            print("   ⚠️ Card already exists, updating instead...")
            platinum_card = existing_card
        else:
            # Create the new card
            platinum_card = CardEnhanced(
                name="American Express Platinum",
                issuer="American Express",
                brand_class="amex",
                last_four="0002"  # Placeholder
            )
            db.session.add(platinum_card)
            db.session.commit()  # Commit to get the ID
        
        # Add quarterly credits
        quarterly_credits = [
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Lululemon Credit",
                credit_amount=75.0,
                description="Up to $75 quarterly Lululemon at U.S. stores (excluding outlets) and online",
                frequency="quarterly",
                reset_date=datetime.date(2025, 3, 31)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Resy Credit",
                credit_amount=100.0,
                description="Up to $100 quarterly for U.S. Resy restaurants",
                frequency="quarterly",
                reset_date=datetime.date(2025, 3, 31)
            )
        ]
        
        for credit in quarterly_credits:
            db.session.add(credit)
        
        # Add monthly credits
        monthly_credits = [
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Digital Entertainment Credit",
                credit_amount=25.0,
                description="Up to $25 monthly for Paramount+, YouTube Premium and YouTube TV",
                frequency="monthly",
                reset_date=datetime.date(2025, 2, 1)
            )
        ]
        
        for credit in monthly_credits:
            db.session.add(credit)
        
        # Add semi-annual credits
        semiannual_credits = [
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Hotel Credit",
                credit_amount=300.0,
                description="Up to $300 biannually (every six months) for hotel credit",
                frequency="semi-annual",
                reset_date=datetime.date(2025, 6, 1)
            )
        ]
        
        for credit in semiannual_credits:
            db.session.add(credit)
        
        # Add annual credits
        annual_credits = [
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Oura Ring Credit",
                credit_amount=200.0,
                description="Up to $200 annual Oura Ring (hardware only; not for memberships)",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="CLEAR Credit",
                credit_amount=209.0,
                description="Up to $209 annually for CLEAR membership",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Airline Credit",
                credit_amount=200.0,
                description="Airline (up to $200 in statement credits with selected airline)",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Equinox Credit",
                credit_amount=300.0,
                description="Equinox (up to $300 in Equinox credit per calendar year on Equinox gym and Equinox+ app memberships, subject to auto-renewal)",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Saks Credit",
                credit_amount=100.0,
                description="Saks (up to a $100 per calendar year)",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Uber Cash Credit",
                credit_amount=200.0,
                description="Uber Cash (up to $200 per calendar year, valid on Uber rides and Uber Eats orders in the U.S.; Amex Plat must first be added to your Uber account and you can then redeem with any Amex card)",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Walmart+ Credit",
                credit_amount=155.0,
                description="Walmart+ (up to a $155 statement credit per calendar year on one membership, subject to auto-renewal, Plus Up excluded.)",
                frequency="annual",
                reset_date=datetime.date(2025, 12, 1)
            )
        ]
        
        for credit in annual_credits:
            db.session.add(credit)
        
        # Add one-time credits
        onetime_credits = [
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Global Entry/TSA PreCheck Credit",
                credit_amount=120.0,
                description="Global Entry/TSA PreCheck ($120 statement credit for Global Entry every four years or an up to $85 fee credit for TSA PreCheck every 4½ years)",
                frequency="onetime"
            ),
            CreditBenefit2(
                card_id=platinum_card.id,
                benefit_name="Uber One Membership Credit",
                credit_amount=120.0,
                description="Up to $120 for Uber One membership (subject to auto-renewal)",
                frequency="onetime"
            )
        ]
        
        for credit in onetime_credits:
            db.session.add(credit)
        
        db.session.commit()
        
        total_credits = len(quarterly_credits) + len(monthly_credits) + len(semiannual_credits) + len(annual_credits) + len(onetime_credits)
        print(f"✅ Added American Express Platinum Card with {total_credits} credit benefits")
        print(f"   📊 Breakdown: {len(quarterly_credits)} quarterly, {len(monthly_credits)} monthly, {len(semiannual_credits)} semi-annual, {len(annual_credits)} annual, {len(onetime_credits)} one-time")


def show_new_cards():
    """Display the newly added cards and their benefits"""
    with app.app_context():
        print("\n📊 New Cards Added:")
        print("=" * 50)
        
        for card_name in ["Hilton Honors American Express Card", "American Express Platinum"]:
            card = CardEnhanced.query.filter_by(name=card_name).first()
            if card:
                print(f"\n🃏 {card.name} (ID: {card.id})")
                print(f"   Issuer: {card.issuer}")
                print(f"   Brand Class: {card.brand_class}")
                print(f"   Total Benefits: {card.total_benefits}")
                
                # Show signup bonuses
                signup_bonuses = SignupBonus.query.filter_by(card_id=card.id).all()
                if signup_bonuses:
                    print("   Signup Bonuses:")
                    for bonus in signup_bonuses:
                        print(f"   • {bonus.bonus_amount} - {bonus.description}")
                
                # Show multiplier benefits
                multipliers = MultiplierBenefit.query.filter_by(card_id=card.id).all()
                if multipliers:
                    print("   Multiplier Benefits:")
                    for mult in multipliers:
                        print(f"   • {mult.category}: {mult.multiplier}x - {mult.description}")
                
                # Show credit benefits by frequency
                for freq in ['quarterly', 'monthly', 'semi-annual', 'annual', 'onetime']:
                    credits = CreditBenefit2.query.filter_by(card_id=card.id, frequency=freq).all()
                    if credits:
                        freq_title = freq.replace('-', ' ').title()
                        print(f"   {freq_title} Credits:")
                        for credit in credits:
                            amount_str = f"${credit.credit_amount:.0f}" if credit.credit_amount > 0 else "N/A"
                            print(f"   • {credit.benefit_name}: {amount_str} - {credit.description}")


def main():
    """Main function to add both cards"""
    print("=== Add New Credit Cards Tool ===")
    print("Adding Hilton Honors American Express Card and American Express Platinum Card")
    print()
    
    try:
        # Add both cards
        add_hilton_honors_amex_card()
        add_american_express_platinum_card()
        
        # Show results
        show_new_cards()
        
        print("\n🎉 Successfully added both new cards to the database!")
        print("You can now run the app to see them in your card tracker dashboard.")
        
    except Exception as e:
        print(f"❌ Error adding cards: {str(e)}")
        print("Please check the error and try again.")


if __name__ == "__main__":
    main()