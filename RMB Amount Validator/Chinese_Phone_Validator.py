def validate_chinese_phone(value):
    """
    Validate Chinese phone numbers:
    - "+8613912345678" -> True
    - "13912345678" -> True
    - "139 1234 5678" -> True
    - "139-1234-5678" -> True
    - "123456" -> False
    
    Returns: True if valid Chinese phone number, False otherwise
    """
    def is_valid_phone(phone_value):
        import re
        
        # Remove spaces and dashes
        phone_value = phone_value.replace(" ", "").replace("-", "")
        
        # Define regex for Chinese phone numbers
        pattern = r"^(\+86)?1[3-9]\d{9}$"
        
        return bool(re.match(pattern, phone_value))
    try:
        value = str(value).strip()
        return is_valid_phone(value)
    except ValueError:
        return False
    
    pass

# Test cases
print(validate_chinese_phone("+8613912345678"))  # Should print: True
print(validate_chinese_phone("13912345678"))     # Should print: True
print(validate_chinese_phone("139 1234 5678"))   # Should print: True
print(validate_chinese_phone("123456"))          # Should print: False