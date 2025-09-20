#!/usr/bin/env python3
from app import *

with app.app_context():
    # Test the new master database functions
    print('Testing master database functions:')
    print('=================================')

    signup_bonuses = get_master_signup_bonuses()
    print(f'Master signup bonuses: {len(signup_bonuses)}')
    for bonus in signup_bonuses[:3]:  # Show first 3
        print(f'  - {bonus["card_name"]}: {bonus["bonus_amount"]}')

    threshold_bonuses = get_master_threshold_bonuses()
    print(f'\nMaster threshold bonuses: {len(threshold_bonuses)}')
    for bonus in threshold_bonuses[:3]:  # Show first 3
        print(f'  - {bonus["card_name"]}: {bonus["bonus_amount"]}')

    annual_credits = get_master_credits_by_frequency('annual')
    print(f'\nMaster annual credits: {len(annual_credits)}')
    for credit in annual_credits[:3]:  # Show first 3
        print(f'  - {credit["card_name"]}: {credit["benefit_name"]} (${credit["credit_amount"]})')