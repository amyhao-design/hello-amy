from app import app, db, Card, MultiplierBenefit, CreditBenefit

def test_us_bank_cash_back():
    with app.app_context():
        us_bank_cash_back = Card.query.filter_by(name="U.S. Bank Cash Back").first()
        if us_bank_cash_back:
            print(f"🃏 {us_bank_cash_back.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=us_bank_cash_back.id).all()
            credits = CreditBenefit.query.filter_by(card_id=us_bank_cash_back.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (Apple Pay promotion)")
            print(f"   💳 {len(credits)} credit benefits")

            print("   Multipliers:")
            for multiplier in multipliers:
                print(f"      • {multiplier.multiplier}% {multiplier.category}")
                print(f"        {multiplier.description}")

            if credits:
                print("   Credits:")
                for credit in credits:
                    if credit.credit_amount > 0:
                        print(f"      • ${credit.credit_amount:.0f} ({credit.frequency})")
                    else:
                        print(f"      • {credit.description}")
            else:
                print("   Credits: None (focused on Apple Pay promotion)")
        else:
            print("❌ U.S. Bank Cash Back not found!")

if __name__ == "__main__":
    test_us_bank_cash_back()