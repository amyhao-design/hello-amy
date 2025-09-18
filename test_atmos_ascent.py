from app import app, db, Card, MultiplierBenefit, CreditBenefit

def test_atmos_ascent():
    with app.app_context():
        atmos_ascent = Card.query.filter_by(name="Atmos Rewards Ascent").first()
        if atmos_ascent:
            print(f"🃏 {atmos_ascent.name}")
            multipliers = MultiplierBenefit.query.filter_by(card_id=atmos_ascent.id).all()
            credits = CreditBenefit.query.filter_by(card_id=atmos_ascent.id).all()
            print(f"   🎯 {len(multipliers)} multiplier benefits (airline co-brand)")
            print(f"   💳 {len(credits)} credit benefits")

            print("   Multipliers:")
            for multiplier in multipliers:
                print(f"      • {multiplier.multiplier}x {multiplier.category}")

            print("   Credits:")
            for credit in credits:
                if credit.credit_amount > 0:
                    print(f"      • ${credit.credit_amount:.0f} ({credit.frequency})")
                else:
                    print(f"      • Status/Points Benefit ({credit.frequency})")
        else:
            print("❌ Atmos Rewards Ascent not found!")

if __name__ == "__main__":
    test_atmos_ascent()