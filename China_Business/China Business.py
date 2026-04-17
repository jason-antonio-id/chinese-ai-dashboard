import csv

def calculate_customer_score(total_spent, orders, last_order_days):
    score = 0
    if total_spent > 100000:
        score += 3
    elif total_spent > 50000:
        score += 2
    elif total_spent < 20000:
        score -= 1
    
    if orders > 20:
        score += 2
    elif orders > 10:
        score += 1
    
    if last_order_days > 60:
        score -= 2
    elif last_order_days > 30:
        score -= 1
    
    return score

def get_customer_segment(score):
    if score >= 5:
        return "VIP"
    elif score >= 2:
        return "STANDARD"
    elif score >= 0:
        return "GROWTH"
    else:
        return "AT RISK"

action_map = {
    "VIP": "Personal outreach + exclusive offers",
    "STANDARD": "Email newsletter + loyalty program",
    "GROWTH": "Engagement campaign + discount codes",
    "AT RISK": "Win-back call + special deals"
}

import os

# Change to the directory where this script is located
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Read CSV
with open('customers.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    customers = list(reader)

# Count segments for summary
vip_count = 0
standard_count = 0
growth_count = 0
at_risk_count = 0

# Process and write results
with open('customer_segments.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['name', 'score', 'segment', 'action'])
    
    # FOR LOOP MUST BE INDENTED INSIDE 'with' BLOCK
    for customer in customers:
        # Convert strings to numbers (CSV reads everything as text)
        total_spent = int(customer["total_spent"])
        orders = int(customer["orders"])
        last_order_days = int(customer["last_order_days"])
        
        score = calculate_customer_score(total_spent, orders, last_order_days)
        segment = get_customer_segment(score)
        action = action_map[segment]
        
        # Write to CSV
        writer.writerow([customer["name"], score, segment, action])
        
        # Print to screen
        print(f"Customer: {customer['name']}")
        print(f"  Score: {score}")
        print(f"  Segment: {segment}")
        print(f"  Action: {action}")
        print()
        
        # Count for summary
        if segment == "VIP":
            vip_count += 1
        elif segment == "STANDARD":
            standard_count += 1
        elif segment == "GROWTH":
            growth_count += 1
        else:
            at_risk_count += 1

# Print summary
total = len(customers)
print("=" * 40)
print(f"SUMMARY: Processed {total} customers")
print(f"  VIP: {vip_count}")
print(f"  STANDARD: {standard_count}")
print(f"  GROWTH: {growth_count}")
print(f"  AT RISK: {at_risk_count}")
print(f"Output saved to: customer_segments.csv")


