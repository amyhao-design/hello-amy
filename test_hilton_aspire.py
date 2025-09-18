from app import app, db, Card, MultiplierBenefit, CreditBenefit

def test_hilton_aspire():
    with app.app_context():
        hilton_aspire = Card.query.filter_by(name="Hilton Honors Aspire").first()
        if hilton_aspire:
            print(f"🃏 {hilton_aspire.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=hilton_aspire.id).all()
            credits = CreditBenefit.query.filter_by(card_id=hilton_aspire.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (premium hotel co-brand)")
            print(f"   💳 {len(credits)} credit benefits")

            print("   Multipliers:")
            for multiplier in multipliers:
                print(f"      • {multiplier.multiplier}x {multiplier.category}")

            print("   Credits:")
            for credit in credits:
                if credit.credit_amount > 0:
                    print(f"      • ${credit.credit_amount:.0f} ({credit.frequency})")
                else:
                    print(f"      • Hotel/Status Benefit ({credit.frequency})")
        else:
            print("❌ Hilton Honors Aspire not found!")

if __name__ == "__main__":
    test_hilton_aspire()