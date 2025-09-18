#!/usr/bin/env python3
"""
Test New Benefits Structure
This script verifies our new MultiplierBenefit and CreditBenefit models are working.
"""

from app import app, db, Card, MultiplierBenefit, CreditBenefit

def test_new_benefits():
    with app.app_context():
        print("=== Testing New Benefits Structure ===\n")

        # Test Chase Sapphire Reserve
        csr = Card.query.filter_by(name="Chase Sapphire Reserve").first()
        if csr:
            print(f"🃏 {csr.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=csr.id).all()
            credits = CreditBenefit.query.filter_by(card_id=csr.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits")
            print(f"   💳 {len(credits)} credit benefits")

        # Test American Express Gold
        amex_gold = Card.query.filter_by(name="American Express Gold").first()
        if amex_gold:
            print(f"\n🃏 {amex_gold.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=amex_gold.id).all()
            credits = CreditBenefit.query.filter_by(card_id=amex_gold.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits")
            print(f"   💳 {len(credits)} credit benefits")
        else:
            print("❌ American Express Gold not found!")

        # Test Capital One VentureX
        venturex = Card.query.filter_by(name="Capital One VentureX").first()
        if venturex:
            print(f"\n🃏 {venturex.name}")

            # Test Multiplier Benefits
            multipliers = MultiplierBenefit.query.filter_by(card_id=venturex.id).all()
            print(f"\n🎯 Earning Multipliers ({len(multipliers)} found):")
            for multiplier in multipliers:
                print(f"   • {multiplier.multiplier}x {multiplier.category}")
                print(f"     {multiplier.description}")

            # Test Credit Benefits
            credits = CreditBenefit.query.filter_by(card_id=venturex.id).all()
            print(f"\n💳 Credits & Benefits ({len(credits)} found):")
            for credit in credits:
                if credit.credit_amount > 0:
                    print(f"   • ${credit.credit_amount:.0f} ({credit.frequency})")
                else:
                    print(f"   • Miles/Bonus ({credit.frequency})")
                print(f"     {credit.description}")

        else:
            print("❌ Capital One VentureX not found!")

        # Test Chase United Quest
        united_quest = Card.query.filter_by(name="Chase United Quest").first()
        if united_quest:
            print(f"\n🃏 {united_quest.name}")

            # Test Multiplier Benefits
            multipliers = MultiplierBenefit.query.filter_by(card_id=united_quest.id).all()
            print(f"\n🎯 Earning Multipliers ({len(multipliers)} found):")
            for multiplier in multipliers:
                print(f"   • {multiplier.multiplier}x {multiplier.category}")
                print(f"     {multiplier.description}")

            # Test Credit Benefits
            credits = CreditBenefit.query.filter_by(card_id=united_quest.id).all()
            print(f"\n💳 Credits & Benefits ({len(credits)} found):")
            for credit in credits:
                if credit.credit_amount > 0:
                    print(f"   • ${credit.credit_amount:.0f} ({credit.frequency})")
                else:
                    if "PQP" in credit.frequency:
                        print(f"   • PQP Benefit ({credit.frequency})")
                    else:
                        print(f"   • Miles/Bonus ({credit.frequency})")
                print(f"     {credit.description}")

        else:
            print("❌ Chase United Quest not found!")

        # Test Chase Freedom Unlimited (simpler card)
        freedom_unlimited = Card.query.filter_by(name="Chase Freedom Unlimited").first()
        if freedom_unlimited:
            print(f"\n🃏 {freedom_unlimited.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=freedom_unlimited.id).all()
            credits = CreditBenefit.query.filter_by(card_id=freedom_unlimited.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (cash back card)")
            print(f"   💳 {len(credits)} credit benefits")

            # Show the multipliers since it's a simple card
            for multiplier in multipliers:
                print(f"      • {multiplier.multiplier}% {multiplier.category}")
        else:
            print("❌ Chase Freedom Unlimited not found!")

        # Test World of Hyatt (hotel co-brand card)
        world_of_hyatt = Card.query.filter_by(name="World of Hyatt").first()
        if world_of_hyatt:
            print(f"\n🃏 {world_of_hyatt.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=world_of_hyatt.id).all()
            credits = CreditBenefit.query.filter_by(card_id=world_of_hyatt.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (hotel co-brand)")
            print(f"   💳 {len(credits)} credit benefits")

            # Show the multipliers and benefits for this hotel card
            for multiplier in multipliers:
                print(f"      • {multiplier.multiplier}x {multiplier.category}")

            for credit in credits:
                print(f"      • Hotel/Status Benefit ({credit.frequency})")
        else:
            print("❌ World of Hyatt not found!")

        # Test Venmo Cash Back (automatic category cash back card)
        venmo_cash_back = Card.query.filter_by(name="Venmo Cash Back").first()
        if venmo_cash_back:
            print(f"\n🃏 {venmo_cash_back.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=venmo_cash_back.id).all()
            credits = CreditBenefit.query.filter_by(card_id=venmo_cash_back.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (automatic category cash back)")
            print(f"   💳 {len(credits)} credit benefits")

            # Show the multipliers for this automatic category card
            for multiplier in multipliers:
                print(f"      • {multiplier.multiplier}% {multiplier.category}")
        else:
            print("❌ Venmo Cash Back not found!")

        # Test Marriott Bonvoy Boundless (hotel co-brand card)
        marriott_boundless = Card.query.filter_by(name="Marriott Bonvoy Boundless").first()
        if marriott_boundless:
            print(f"\n🃏 {marriott_boundless.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=marriott_boundless.id).all()
            credits = CreditBenefit.query.filter_by(card_id=marriott_boundless.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (hotel co-brand)")
            print(f"   💳 {len(credits)} credit benefits")

            # Show key highlights for this hotel card
            for multiplier in multipliers:
                if "17x" in multiplier.description:
                    print(f"      • 17x Marriott Bonvoy Hotels (highest multiplier!)")
                else:
                    print(f"      • {multiplier.multiplier}x {multiplier.category}")

            for credit in credits:
                if "signup" in credit.frequency:
                    print(f"      • Welcome Bonus: 3 free nights")
                elif "anniversary" in credit.frequency:
                    print(f"      • Annual free night")
                else:
                    print(f"      • Status/Elite Benefit ({credit.frequency})")
        else:
            print("❌ Marriott Bonvoy Boundless not found!")

        # Test all cards summary
        print(f"\n📊 Database Summary:")
        total_cards = Card.query.count()
        total_multipliers = MultiplierBenefit.query.count()
        total_credits = CreditBenefit.query.count()

        print(f"   Total Cards: {total_cards}")
        print(f"   Total Multiplier Benefits: {total_multipliers}")
        print(f"   Total Credit Benefits: {total_credits}")

        # Show cards with benefits vs without
        cards_with_multipliers = MultiplierBenefit.query.with_entities(MultiplierBenefit.card_id).distinct().count()
        cards_with_credits = CreditBenefit.query.with_entities(CreditBenefit.card_id).distinct().count()
        print(f"   Cards with multiplier benefits: {cards_with_multipliers}")
        print(f"   Cards with credit benefits: {cards_with_credits}")

if __name__ == "__main__":
    test_new_benefits()