#!/usr/bin/env python3
"""
Fix remaining $0 credit amounts that weren't caught by the first fix
"""

import sqlite3

def fix_remaining_zero_credits():
    """Fix specific credit amounts based on source data"""
    print("=== FIXING REMAINING $0 CREDITS ===\n")

    conn = sqlite3.connect('instance/test.db')
    cursor = conn.cursor()

    # Fix specific credits based on source data
    fixes = [
        ("Paramount+ Credit", 25.0),  # From source: $25 monthly
        ("DoorDash Credit", 25.0),   # From source: $25 monthly (confirmed)
        ("Reimbursement Credit", 120.0),  # Global Entry credit
        ("Subscription Credit", 0.0),  # Apple services are complimentary
        ("Free Credit", 360.0),  # Up to $360 per roundtrip for checked bags
    ]

    for credit_name_pattern, amount in fixes:
        cursor.execute("""
            UPDATE credit_benefit2
            SET credit_amount = ?
            WHERE benefit_name LIKE ? AND credit_amount = 0
        """, (amount, f"%{credit_name_pattern}%"))

        if cursor.rowcount > 0:
            print(f"Updated {cursor.rowcount} credits matching '{credit_name_pattern}' to ${amount}")

    # Fix any remaining credits by extracting from description
    cursor.execute("SELECT id, benefit_name, description FROM credit_benefit2 WHERE credit_amount = 0")
    zero_credits = cursor.fetchall()

    for credit_id, benefit_name, description in zero_credits:
        # Try to extract amounts from description
        import re
        dollar_match = re.search(r'\$(\d+)', description)
        if dollar_match:
            amount = float(dollar_match.group(1))
            cursor.execute("UPDATE credit_benefit2 SET credit_amount = ? WHERE id = ?", (amount, credit_id))
            print(f"Updated '{benefit_name}' to ${amount} based on description")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_remaining_zero_credits()
    print("\n=== CREDIT FIXES COMPLETE ===")