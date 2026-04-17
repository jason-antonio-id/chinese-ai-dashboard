suppliers = [
    {
        "name": "Dongguan Metals",
        "location": "Guangdong",
        "order_volume": 150000,
        "late_deliveries": 2,
        "quality_complaints": 1
    },
    {
        "name": "Shanghai Plastics",
        "location": "Shanghai",
        "order_volume": 80000,
        "late_deliveries": 5,
        "quality_complaints": 3
    },
    {
        "name": "Beijing Electronics",
        "location": "Beijing",
        "order_volume": 250000,
        "late_deliveries": 0,
        "quality_complaints": 0
    },
    {
        "name": "Wuhan Textiles",
        "location": "Hubei",
        "order_volume": 45000,
        "late_deliveries": 7,
        "quality_complaints": 4
    }
]
action_map = {
    "LOW RISK": "Continue partnership",
    "MEDIUM RISK": "Monitor closely",
    "HIGH RISK": "Consider alternative suppliers"
}
def calculate_risk(volume, late_deliveries, quality_complaints):
    score = 0
    if volume > 100000:
        score = score -1
    if volume < 50000:
        score = score +1
    if late_deliveries > 3:
        score = score +2
    if quality_complaints > 2:
        score = score +2
    return score
def get_risk_level(score):
    if score <= 0:
        return "LOW RISK"
    elif score <= 2:
        return "MEDIUM RISK"
    else:
        return "HIGH RISK"
for supplier in suppliers:
    risk_score = calculate_risk(supplier["order_volume"], supplier["late_deliveries"], supplier["quality_complaints"])
    risk_level = get_risk_level(risk_score)
    action = action_map[risk_level]
    print(f"Supplier: {supplier['name']}")
    print(f"Location: {supplier['location']}")
    print(f"Order Volume: {supplier['order_volume']}")
    print(f"Late Deliveries: {supplier['late_deliveries']}")
    print(f"Quality Complaints: {supplier['quality_complaints']}")
    print(f"Risk Level: {risk_level}")
    print(f"Recommended Action: {action}")
    print()
