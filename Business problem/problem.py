def is_valid_amount(value):
    try:
        amount = float(value)
        if amount <= 0:
            return False
    except ValueError:
        return False
    return True

print ("testing amount validation:")   
print(is_valid_amount("5000"))      # True?
print(is_valid_amount("0"))         # True or False? You decide
print(is_valid_amount("-100"))      # False?
print(is_valid_amount("INVALID"))   # False?
print(is_valid_amount(""))          # False?

def clean_amount_value(value):
    
    if is_valid_amount(value):
        return float(value)
    else:
        return 0.0
    
print("\nTesting clean_amount_value:")
print(clean_amount_value("5000"))      # Should be 5000.0
print(clean_amount_value("0"))         # Should be 0.0 (invalid, return default)
print(clean_amount_value("-100"))       # Should be 0.0
print(clean_amount_value("INVALID"))  # Should be 0.0
print(clean_amount_value(""))           # Should be 0.0

from datetime import datetime

def clean_date_value(value):
    if value.strip() == "":
        return "no date"
    else:
        try:
            # Attempt to parse the date
            datetime.strptime(value.strip(), "%Y-%m-%d")
            return value.strip()
        except ValueError:
            return "no date"
        
print("\nTesting clean_date_value:")
print (clean_date_value("2024-01-15"))  # Should be "2024-01-15"
print (clean_date_value("March, 18 2024"))  # Should be "no date" (invalid format)
print (clean_date_value(""))              # Should be "no date"
