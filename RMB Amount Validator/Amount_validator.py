def validate_rmb_amount(value):
    """
    Handle Chinese currency formats:
    - "5000" -> 5000.0
    - "5000元" -> 5000.0  
    - "5000.50元" -> 5000.5
    - "5,000元" -> 5000.0
    - "1.5万" -> 15000.0
    - "1.5万元" -> 15000.0
    - "¥5000" -> 5000.0
    
    Returns: float if valid, 0.0 if invalid
    """
    def is_valid_amount(amount_value):
        try:
            amount = float(amount_value)
            if amount <= 0:
                return False
        except ValueError:
            return False
        return True
    
    try:
        # Clean the input
        value = str(value).strip()
        
        # Handle "万元" (ten thousand yuan)
        if "万元" in value:
            value = value.replace("万元", "").replace(",", "")
            amount = float(value) * 10000
            return amount if amount > 0 else 0.0
        
        # Handle "万" (ten thousand)
        elif "万" in value:
            value = value.replace("万", "").replace(",", "")
            amount = float(value) * 10000
            return amount if amount > 0 else 0.0
        
        # Handle "元" (yuan)
        elif "元" in value:
            value = value.replace("元", "").replace(",", "")
            amount = float(value)
            return amount if amount > 0 else 0.0
        
        # Handle "¥" symbol
        elif value.startswith("¥"):
            value = value[1:].replace(",", "")
            amount = float(value)
            return amount if amount > 0 else 0.0
        
        # Handle regular numbers
        else:
            # Remove commas
            value = value.replace(",", "")
            amount = float(value)
            return amount if amount > 0 else 0.0
            
    except (ValueError, AttributeError):
        return 0.0

# Test cases
print(validate_rmb_amount("5000"))      # Should print: 5000.0
print(validate_rmb_amount("5000元"))    # Should print: 5000.0
print(validate_rmb_amount("1.5万"))     # Should print: 15000.0
print(validate_rmb_amount("1.5万元"))   # Should print: 15000.0
print(validate_rmb_amount("¥5000"))     # Should print: 5000.0
print(validate_rmb_amount("5,000"))     # Should print: 5000.0
print(validate_rmb_amount("5,000元"))   # Should print: 5000.0
print(validate_rmb_amount("invalid"))   # Should print: 0.0
print(validate_rmb_amount("0元"))       # Should print: 0.0
print(validate_rmb_amount("-100"))      # Should print: 0.0