# Google Sheets Setup Guide

This guide explains exactly how to structure your Google Sheets to work with your Credit Card Tracker dashboard.

## 📋 Required Sheet Structure

Your Google Sheet must have exactly **5 tabs** with specific column headers:

### Tab 1: "Cards" (Master Card List)
This contains all possible credit cards and their basic information.

**Columns:**
- **Column A**: `Issuer` (e.g., "Chase", "American Express", "Capital One")
- **Column B**: `Card Name` (e.g., "Sapphire Reserve", "Gold Card", "VentureX")
- **Column C**: `Brand Class` (e.g., "Premium", "Gold", "Travel", "Cash Back")

**Example:**
```
A1: Issuer          B1: Card Name           C1: Brand Class
A2: Chase           B2: Sapphire Reserve    C2: Premium
A3: American Express B3: Gold Card          C3: Gold
A4: Capital One     B4: VentureX           C4: Premium
```

**How card names are formed:** The app combines Issuer + Card Name = "Chase Sapphire Reserve"

---

### Tab 2: "SignupBonuses" (Signup Bonuses)
These appear under **"Sign-up Bonuses"** in the LEFT column of your dashboard.

**Columns:**
- **Column A**: `Card Name` (full name: "Chase Sapphire Reserve")
- **Column B**: `Bonus Amount` (e.g., "60,000 points", "200 cash back")
- **Column C**: `Description` (e.g., "Spend $4,000 in first 3 months")
- **Column D**: `Required Spend` (numeric, e.g., "4000")
- **Column E**: `Deadline Months` (numeric, e.g., "3")

**Example:**
```
A1: Card Name              B1: Bonus Amount    C1: Description                      D1: Required Spend  E1: Deadline Months
A2: Chase Sapphire Reserve B2: 60,000 points   C2: Spend $4,000 in first 3 months  D2: 4000           E2: 3
A3: American Express Gold  B3: 90,000 points   C3: Spend $4,000 in first 6 months  D3: 4000           E3: 6
```

---

### Tab 3: "SpendingBonuses" (Threshold Bonuses)
These appear under **"Threshold Bonuses"** in the LEFT column of your dashboard.

**Columns:**
- **Column A**: `Card Name` (full name: "Chase Sapphire Reserve")
- **Column B**: `Bonus Amount` (e.g., "5,000 points", "Free Night Award")
- **Column C**: `Description` (e.g., "Earn after spending $15,000 annually")
- **Column D**: `Required Spend` (numeric, e.g., "15000")
- **Column E**: `Frequency` (e.g., "annual", "monthly")

**Example:**
```
A1: Card Name              B1: Bonus Amount        C1: Description                        D1: Required Spend  E1: Frequency
A2: Chase Sapphire Reserve B2: 5,000 points        C2: Earn after spending $15,000       D2: 15000          E2: annual
A3: World of Hyatt         B3: Free Night Award    C3: Anniversary bonus                 D3: 0              E3: annual
```

---

### Tab 4: "Multipliers" (Points Multipliers)
These are **ONLY shown when clicking into individual cards**, NOT on the dashboard.

**Columns:**
- **Column A**: `Card Name` (full name: "Chase Sapphire Reserve")
- **Column B**: `Category` (e.g., "Travel", "Dining", "Gas")
- **Column C**: `Multiplier` (numeric, e.g., "3", "2", "1.5")
- **Column D**: `Description` (e.g., "3x points on travel purchases")

**Example:**
```
A1: Card Name              B1: Category  C1: Multiplier  D1: Description
A2: Chase Sapphire Reserve B2: Travel    C2: 3          D2: 3x points on travel purchases
A3: Chase Sapphire Reserve B3: Dining    C3: 3          D3: 3x points on dining
```

---

### Tab 5: "Credits" (Statement Credits)
These appear in the **RIGHT column** of your dashboard, organized by frequency.

**Columns:**
- **Column A**: `Card Name` (full name: "Chase Sapphire Reserve")
- **Column B**: `Benefit Name` (e.g., "Travel Credit", "Uber Credit")
- **Column C**: `Credit Amount` (numeric, e.g., "300", "120")
- **Column D**: `Description` (e.g., "Annual travel credit")
- **Column E**: `Frequency` (IMPORTANT: must match dashboard sections)
- **Column F**: `Category` (optional, e.g., "Travel", "Transportation")

**Critical Frequency Values:**
- `annual` → appears under **"Recurring - Annual"**
- `semiannual` → appears under **"Recurring - Semi-Annual"**
- `quarterly` → appears under **"Recurring - Quarterly"**
- `monthly` → appears under **"Recurring - Monthly"**
- `onetime` → appears under **"One-Time"**

**Example:**
```
A1: Card Name              B1: Benefit Name  C1: Credit Amount  D1: Description           E1: Frequency   F1: Category
A2: Chase Sapphire Reserve B2: Travel Credit C2: 300           D2: Annual travel credit  E2: annual      F2: Travel
A3: American Express Gold  B3: Uber Credit   C3: 120           D3: Monthly Uber credits  E3: monthly     F3: Transportation
```

## 🎯 Data Flow Summary

**Dashboard Left Column:**
- **Sign-up Bonuses** ← Tab 2: "SignupBonuses"
- **Threshold Bonuses** ← Tab 3: "SpendingBonuses"

**Dashboard Right Column:**
- **Recurring - Annual** ← Tab 5: "Credits" where frequency = "annual"
- **Recurring - Semi-Annual** ← Tab 5: "Credits" where frequency = "semiannual"
- **Recurring - Quarterly** ← Tab 5: "Credits" where frequency = "quarterly"
- **Recurring - Monthly** ← Tab 5: "Credits" where frequency = "monthly"
- **One-Time** ← Tab 5: "Credits" where frequency = "onetime"

**Card Details Only:**
- **Points Multipliers** ← Tab 4: "Multipliers" (not shown on dashboard)

## ⚠️ Important Notes

1. **Card names must be consistent** across all tabs (use full name: "Issuer Card Name")
2. **Frequency values are case-sensitive** - use lowercase exactly as shown
3. **Numeric columns** (Required Spend, Credit Amount, Multiplier) should contain only numbers
4. **First row** of each tab must contain the exact column headers shown above
5. **Multipliers tab** data only appears when clicking into individual cards, never on the dashboard

## 🧪 Testing Your Setup

1. Add a test card to all 5 tabs
2. Click "Add New Card" in your app
3. Select the test card from the dropdown
4. Verify the preview shows correct issuer and type
5. Add the card and check that bonuses appear in the correct dashboard sections
6. Click into the card details to verify multipliers appear there