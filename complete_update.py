#!/usr/bin/env python3
"""
Complete Database Update Script: Replace ALL database data with source of truth
This script processes the complete source of truth table and updates everything
"""

import sqlite3
from datetime import datetime

def parse_source_data():
    """Parse the complete source of truth data"""
    # This is the complete data from your table
    raw_data = """Chase Sapphire Reserve,Points Multiplier,Travel,Points on Chase Travel (flights, hotels, rental cars, cruises, activities, tours),8x,N/A,Per dollar spent
Chase Sapphire Reserve,Points Multiplier,Travel,Points on travel booked directly with airline or hotel,4x,N/A,Per dollar spent
Chase Sapphire Reserve,Points Multiplier,Dining,Points on dining at restaurants worldwide (including eligible delivery),3x,N/A,Per dollar spent
Chase Sapphire Reserve,Points Multiplier,Travel,Bonus points on eligible Lyft rides,4x,N/A,Per dollar spent
Chase Sapphire Reserve,Points Multiplier,Fitness,Bonus points on eligible Peloton hardware and accessories (up to 50,000 total points),10x,N/A,Per dollar spent
Chase Sapphire Reserve,Credit,Recurring - Annual,Travel credit for travel purchases,$300,N/A,Annually
Chase Sapphire Reserve,Credit,Recurring - Annual,Credit for prepaid bookings with Chase Travel for The Edit properties,$500,N/A,Annually
Chase Sapphire Reserve,Credit,Recurring - Annual,Credit for prepaid Chase Travel hotel bookings (specific hotel groups),$250,Prepaid hotel stay,Annually
Chase Sapphire Reserve,Credit,Recurring - Annual,Dashpass membership,$120,N/A,Annually
Chase Sapphire Reserve,Credit,Recurring - Annual,Statement credit towards Peloton membership,$120,N/A,Annually
Chase Sapphire Reserve,Credit,Recurring - Semi-Annually,Statement credits for dining at Sapphire Reserve Exclusive Tables program restaurants,$150,N/A,Semi-Annually
Chase Sapphire Reserve,Credit,Recurring - Semi-Annually,Statement credits for purchases on StubHub and viagogo.com,$150,N/A,Semi-Annually
Chase Sapphire Reserve,Credit,Recurring - Monthly,DoorDash credit ($5 for restaurants, two $10 promotions for groceries/retail),$25,N/A,Monthly
Chase Sapphire Reserve,Credit,Recurring - Monthly,Lyft credit,$10,N/A,Monthly
Chase Sapphire Reserve,Credit,Recurring - Other,Subscription to AppleTV and AppleMusic,Complimentary,N/A,Ongoing
Chase Sapphire Reserve,Credit,One-Time,Reimbursement for Global Entry, TSA Precheck, or NEXUS,$120,N/A,Every 4 years
Chase Sapphire Reserve,Bonus,Spending Bonus,Southwest Airlines credit,$500,$75,000,Annually
Chase Sapphire Reserve,Bonus,Spending Bonus,Shops at Chase credit,$250,$75,000,Annually
American Express Gold Card,Points Multiplier,Dining,Points on restaurants worldwide (plus takeout and delivery in the U.S.),4x,Up to $50,000/year,Per dollar spent
American Express Gold Card,Points Multiplier,Groceries,Points on groceries at U.S. supermarkets,4x,Up to $25,000/year,Per dollar spent
American Express Gold Card,Points Multiplier,Travel,Points on flights booked directly with airlines or on AmexTravel.com,3x,N/A,Per dollar spent
American Express Gold Card,Points Multiplier,Travel,Points on prepaid hotels and other eligible travel through AmexTravel.com,2x,N/A,Per dollar spent
American Express Gold Card,Credit,Recurring - Annual,Resy restaurant credit,$100,N/A,Annually
American Express Gold Card,Credit,Recurring - Monthly,Uber Cash for orders and rides in the U.S.,$10,N/A,Monthly
American Express Gold Card,Credit,Recurring - Monthly,Statement credits for Dunkin' Donuts,$7,N/A,Monthly
American Express Gold Card,Credit,Recurring - Monthly,Statement credits for Grubhub, The Cheesecake Factory, Goldbelly, Wine.com, Five Guys,$10,N/A,Monthly
Capital One VentureX,Points Multiplier,Travel,Miles on hotels and rental cars booked through Capital One Travel,10x,N/A,Per dollar spent
Capital One VentureX,Points Multiplier,Travel,Miles on flights and vacation rentals booked through Capital One Travel,5x,N/A,Per dollar spent
Capital One VentureX,Points Multiplier,General,Miles on all other purchases,2x,N/A,Per dollar spent
Capital One VentureX,Credit,Recurring - Annual,Travel credit for bookings through Capital One Travel,$300,N/A,Annually
Capital One VentureX,Credit,One-Time,Global Entry or TSA PreCheck credit,$120,N/A,Every 4 years
Capital One VentureX,Bonus,Spending Bonus,Anniversary miles,10,000 miles,N/A,Annually
Capital One VentureX,Bonus,Sign-Up Bonus,Welcome bonus,75,000 miles,$4,000 in 3 months,One-Time
Chase United Quest,Points Multiplier,Travel,Miles on United flights,8x,N/A,Per dollar spent
Chase United Quest,Points Multiplier,Travel,Miles on all other eligible United purchases,3x,N/A,Per dollar spent
Chase United Quest,Points Multiplier,Travel,Miles on prepaid hotel stays through Renowned Hotels and resorts,5x,N/A,Per dollar spent
Chase United Quest,Points Multiplier,Travel,Miles on all other travel,2x,N/A,Per dollar spent
Chase United Quest,Points Multiplier,Dining,Miles on dining (including eligible delivery services),2x,N/A,Per dollar spent
Chase United Quest,Points Multiplier,Entertainment,Miles on select streaming services,2x,N/A,Per dollar spent
Chase United Quest,Points Multiplier,General,Miles on all other purchases,1x,N/A,Per dollar spent
Chase United Quest,Bonus,Sign-Up Bonus,Bonus miles and United Premier qualifying points,70,000 miles + 1,000 PQP,$4,000 in 3 months,One-Time
Chase United Quest,Credit,Recurring - Annual,United travel credit,$200,N/A,Annually
Chase United Quest,Credit,Recurring - Annual,Credits on prepaid hotel stays via Renowned Hotels and Resorts,$150,N/A,Annually
Chase United Quest,Credit,Recurring - Annual,Credits on rideshare purchases,$100,N/A,Annually
Chase United Quest,Credit,Recurring - Annual,United travel credits for Avis or Budget car rentals,$80,N/A,Annually
Chase United Quest,Credit,Recurring - Annual,Instacart credits,$180,N/A,Annually
Chase United Quest,Credit,Recurring - Annual,Credits on flights purchased directly through JSX,$150,N/A,Annually
Chase United Quest,Bonus,Spending Bonus,Premier qualifying point (PQP) earning rate (up to 18,000 PQP/year),1 PQP per $20,N/A,Per dollar spent
Chase United Quest,Bonus,Spending Bonus,Anniversary award flight discount,10,000 miles,N/A,Annually
Chase United Quest,Bonus,Spending Bonus,Award flight discount,10,000 miles,$20,000,Annually
Chase United Quest,Bonus,Spending Bonus,Global Economy Plus® seat upgrades,2 upgrades,$40,000,Annually
Chase United Quest,Credit,Recurring - Other,Free first and second checked bags for cardmember and companion,Up to $360 per roundtrip,N/A,Per flight
Chase Freedom Unlimited,Points Multiplier,General,Cash back on every purchase,1.50%,N/A,Per dollar spent
Chase Freedom Unlimited,Points Multiplier,Travel,Cash back on travel booked through Chase Travel,5%,N/A,Per dollar spent
Chase Freedom Unlimited,Points Multiplier,Dining,Cash back on dining,3%,N/A,Per dollar spent
Chase Freedom Unlimited,Points Multiplier,Health,Cash back in drugstores,3%,N/A,Per dollar spent
World of Hyatt,Points Multiplier,Travel,Points on qualifying purchases at Hyatt hotels and resorts,9x,N/A,Per dollar spent
World of Hyatt,Points Multiplier,Dining,Points on dining, airline tickets, gym memberships, local transit,2x,N/A,Per dollar spent
World of Hyatt,Points Multiplier,General,Points on all other purchases,1x,N/A,Per dollar spent
World of Hyatt,Bonus,Spending Bonus,Free night at Category 1-4 Hyatt hotel,1 Free Night,N/A,Annually
World of Hyatt,Bonus,Spending Bonus,Second free night at Category 1-4 Hyatt hotel,1 Free Night,$15,000,Annually
World of Hyatt,Bonus,Spending Bonus,Tier-qualifying night credits,2 credits,$5,000,Per threshold
Venmo Cash Back,Points Multiplier,General,Cash back on top spend category,3%,N/A,Per dollar spent
Venmo Cash Back,Points Multiplier,General,Cash back on second top spend category,2%,N/A,Per dollar spent
Venmo Cash Back,Points Multiplier,General,Cash back on all other eligible purchases,1%,N/A,Per dollar spent
Marriott Bonvoy Boundless,Points Multiplier,Travel,Points on hotels participating in Marriott Bonvoy,17x,N/A,Per dollar spent
Marriott Bonvoy Boundless,Points Multiplier,General,Points on gas stations, grocery stores, and dining,3x,First $6,000/year,Per dollar spent
Marriott Bonvoy Boundless,Points Multiplier,General,Points on all other purchases,2x,N/A,Per dollar spent
Marriott Bonvoy Boundless,Bonus,Sign-Up Bonus,Free night awards,3 Free Nights,$3,000 in 3 months,One-Time
Marriott Bonvoy Boundless,Bonus,Spending Bonus,Free night award,1 Free Night,N/A,Annually
Marriott Bonvoy Boundless,Bonus,Spending Bonus,Elite night credit,1 credit,$5,000,Per threshold
Marriott Bonvoy Boundless,Bonus,Spending Bonus,Gold status,Gold Status,$35,000,Annually
Hilton Honors Surpass,Points Multiplier,Travel,Bonus Points on purchases at Hilton portfolio hotels/resorts,12x,N/A,Per dollar spent
Hilton Honors Surpass,Points Multiplier,General,Bonus Points at U.S. restaurants, U.S. gas stations, U.S. supermarkets,6x,N/A,Per dollar spent
Hilton Honors Surpass,Points Multiplier,Retail,Bonus Points on U.S. online retail purchases,4x,N/A,Per dollar spent
Hilton Honors Surpass,Points Multiplier,General,Bonus Points on all other eligible purchases,3x,N/A,Per dollar spent
Hilton Honors Surpass,Bonus,Sign-Up Bonus,Bonus points,130,000 points,$3,000 in 6 months,One-Time
Hilton Honors Surpass,Bonus,Spending Bonus,Upgrade to Diamond Status,Diamond Status,$40,000,Annually
Hilton Honors Surpass,Bonus,Spending Bonus,Free night award,1 Free Night,$15,000,Annually
Hilton Honors Surpass,Credit,Recurring - Quarterly,Statement credits for purchases made directly with a Hilton property,$50,N/A,Quarterly
Hilton Honors Aspire,Points Multiplier,Travel,Bonus Points on purchases at Hilton portfolio hotels/resorts,14x,N/A,Per dollar spent
Hilton Honors Aspire,Points Multiplier,Travel,Bonus Points on flights, select car rentals, and U.S. restaurants,7x,N/A,Per dollar spent
Hilton Honors Aspire,Points Multiplier,General,Bonus Points on all other eligible purchases,3x,N/A,Per dollar spent
Hilton Honors Aspire,Bonus,Sign-Up Bonus,Bonus points,150,000 points,$6,000 in 6 months,One-Time
Hilton Honors Aspire,Bonus,Spending Bonus,Additional Free Night Reward,1 Free Night,$30,000,Annually
Hilton Honors Aspire,Bonus,Spending Bonus,Additional Free Night Reward,1 Free Night,$60,000,Annually
Hilton Honors Aspire,Credit,Recurring - Semi-Annually,Statement credits for purchases made directly with participating Hilton Resorts,$200,N/A,Semi-Annually
Hilton Honors Aspire,Credit,Recurring - Quarterly,Statement credits on flight purchases,$50,N/A,Quarterly
Hilton Honors Aspire,Credit,Recurring - Annual,Statement credits for a CLEAR plus membership,$209,N/A,Annually
Hilton Honors Aspire,Credit,Recurring - Other,Resort credit at Waldorf Astoria and Conrad Hotels,$100,2-night minimum stay,Per stay
Atmos Rewards Ascent,Points Multiplier,Travel,Points for eligible purchases on Alaska Airlines, Hawaiian Airlines, dining, foreign purchases,3x,N/A,Per dollar spent
Atmos Rewards Ascent,Points Multiplier,General,Points on all other purchases,1x,N/A,Per dollar spent
Atmos Rewards Ascent,Bonus,Sign-Up Bonus,Bonus points and Global Companion Award,100,000 points + 25,000 point award,$6,000 in 90 days,One-Time
Atmos Rewards Ascent,Bonus,Spending Bonus,Rewards bonus with eligible Bank of America account,10%,N/A,Ongoing
Atmos Rewards Ascent,Bonus,Spending Bonus,Anniversary status points,10,000 points,N/A,Annually
Atmos Rewards Ascent,Bonus,Spending Bonus,Status point earning rate,1 status point per $2,N/A,Per dollar spent
Atmos Rewards Ascent,Credit,One-Time,Airport Security Credit (TSA PreCheck® or Global Entry),$120,N/A,Every 4 years
U.S. Bank Cash Back,Points Multiplier,General,Cash back on all Apple Pay purchases,4.5x,N/A,Through Dec 2025
Hilton Honors American Express Card,Points Multiplier,Travel,Points on Hotels & Resorts in the Hilton portfolio,7x,N/A,Per dollar spent
Hilton Honors American Express Card,Points Multiplier,Dining,Points on dining,5x,N/A,Per dollar spent
Hilton Honors American Express Card,Points Multiplier,Groceries,Points on groceries,5x,N/A,Per dollar spent
Hilton Honors American Express Card,Points Multiplier,Gas,Points on gas,5x,N/A,Per dollar spent
Hilton Honors American Express Card,Points Multiplier,General,Points for all other purchases,3x,N/A,Per dollar spent
Hilton Honors American Express Card,Bonus,Sign-Up Bonus,Hilton Honors Bonus Points,80,000 points,$2,000 in 6 months,One-Time
American Express Platinum,Credit,Recurring - Quarterly,Lululemon credit at U.S. stores and online,$75,N/A,Quarterly
American Express Platinum,Credit,Recurring - Quarterly,U.S. Resy Restaurants credit,$100,N/A,Quarterly
American Express Platinum,Credit,Recurring - Monthly,Credit for Paramount+, YouTube Premium and YouTube TV,$25,N/A,Monthly
American Express Platinum,Credit,Recurring - Annual,Oura Ring credit (hardware only),$200,N/A,Annually
American Express Platinum,Credit,Recurring - Annual,Uber One membership credit,$120,N/A,Annually
American Express Platinum,Credit,Recurring - Semi-Annually,Hotel credit,$300,N/A,Semi-Annually
American Express Platinum,Credit,Recurring - Annual,CLEAR membership credit,$209,N/A,Annually
American Express Platinum,Credit,Recurring - Annual,Airline fee credit with selected airline,$200,N/A,Annually
American Express Platinum,Credit,Recurring - Annual,Equinox credit,$300,N/A,Annually
American Express Platinum,Credit,One-Time,Global Entry/TSA PreCheck credit,$120 / $85,N/A,Every 4-4.5 years
American Express Platinum,Credit,Recurring - Annual,Saks credit,$100,N/A,Annually
American Express Platinum,Credit,Recurring - Annual,Uber Cash,$200,N/A,Annually
American Express Platinum,Credit,Recurring - Annual,Walmart+ membership credit,$155,N/A,Annually"""

    # Parse the data
    cards_data = {}
    for line in raw_data.strip().split('\n'):
        parts = line.split(',')
        if len(parts) >= 7:
            card_name = parts[0]
            benefit_category = parts[1]
            sub_category = parts[2]
            description = parts[3]
            value_rate = parts[4]
            spending_req = parts[5]
            frequency = parts[6]

            if card_name not in cards_data:
                cards_data[card_name] = {"multipliers": [], "credits": [], "bonuses": []}

            if benefit_category == "Points Multiplier":
                # Extract multiplier value
                if 'x' in value_rate:
                    multiplier = float(value_rate.replace('x', ''))
                elif '%' in value_rate:
                    multiplier = float(value_rate.replace('%', ''))
                else:
                    multiplier = 1.0

                cards_data[card_name]["multipliers"].append({
                    "category": sub_category,
                    "multiplier": multiplier,
                    "description": description
                })

            elif benefit_category == "Credit":
                # Extract dollar amount
                amount = 0.0
                if '$' in value_rate:
                    try:
                        amount_str = value_rate.replace('$', '').replace(',', '').split()[0]
                        if '/' in amount_str:  # Handle "$120 / $85" format
                            amount_str = amount_str.split('/')[0].strip()
                        amount = float(amount_str)
                    except:
                        amount = 0.0

                # Map frequency
                freq_map = {
                    "Recurring - Annual": "annual",
                    "Recurring - Semi-Annually": "semi-annual",
                    "Recurring - Quarterly": "quarterly",
                    "Recurring - Monthly": "monthly",
                    "Recurring - Other": "other",
                    "One-Time": "onetime"
                }
                freq = freq_map.get(sub_category, "annual")

                cards_data[card_name]["credits"].append({
                    "name": description.split()[0] + " Credit" if not description.endswith("Credit") and not description.endswith("credit") else description,
                    "amount": amount,
                    "frequency": freq,
                    "description": description
                })

            elif benefit_category == "Bonus":
                # Extract bonus amount and spending requirement
                required_spend = 0.0
                if spending_req and spending_req != "N/A":
                    try:
                        required_spend = float(spending_req.replace('$', '').replace(',', ''))
                    except:
                        required_spend = 0.0

                cards_data[card_name]["bonuses"].append({
                    "category": sub_category,
                    "amount": value_rate,
                    "description": description,
                    "required_spend": required_spend
                })

    return cards_data

def update_database_complete():
    """Update database with complete source of truth data"""
    print("=== COMPLETE DATABASE UPDATE ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Clean existing data
    cursor.execute("DELETE FROM spending_bonus")
    cursor.execute("DELETE FROM credit_benefit2")
    cursor.execute("DELETE FROM signup_bonus")

    # Update card name
    cursor.execute("UPDATE card_enhanced SET name = 'American Express Gold Card' WHERE name = 'American Express Gold'")

    print("Cleaned existing data")

    # Get card IDs
    cursor.execute("SELECT id, name FROM card_enhanced")
    cards = {name: card_id for card_id, name in cursor.fetchall()}

    # Parse source data
    source_data = parse_source_data()

    # Add all data
    for card_name, data in source_data.items():
        if card_name not in cards:
            print(f"Warning: Card '{card_name}' not found in database")
            continue

        card_id = cards[card_name]

        # Add multipliers
        for mult in data["multipliers"]:
            cursor.execute("""
                INSERT INTO spending_bonus
                (card_id, category, multiplier, description, cap_amount, current_spend, reset_date, bonus_type, is_active)
                VALUES (?, ?, ?, ?, 0, 0, '2025-12-31', 'ongoing', 1)
            """, (card_id, mult["category"], mult["multiplier"], mult["description"]))

        # Add credits
        for credit in data["credits"]:
            reset_date = None
            if credit["frequency"] in ["annual", "semi-annual", "quarterly", "monthly"]:
                reset_date = "2025-12-01"

            cursor.execute("""
                INSERT INTO credit_benefit2
                (card_id, benefit_name, credit_amount, description, frequency, reset_date, has_progress, current_amount)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """, (card_id, credit["name"], credit["amount"], credit["description"], credit["frequency"], reset_date))

        # Add bonuses
        for bonus in data["bonuses"]:
            cursor.execute("""
                INSERT INTO signup_bonus
                (card_id, bonus_amount, description, required_spend, current_spend, deadline, status, created_date)
                VALUES (?, ?, ?, ?, 0, '2025-12-31', 'not-started', ?)
            """, (card_id, bonus["amount"], bonus["description"], bonus["required_spend"], datetime.now().isoformat()))

        print(f"Updated {card_name}: {len(data['multipliers'])} multipliers, {len(data['credits'])} credits, {len(data['bonuses'])} bonuses")

    conn.commit()
    conn.close()

    print("\n=== UPDATE COMPLETE ===")
    print("All cards updated with source of truth data!")

if __name__ == "__main__":
    update_database_complete()