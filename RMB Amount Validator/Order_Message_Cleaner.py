def clean_order_message(message):
    """
    Combine all validators to clean a complete order message:
    
    Input: "订单金额5000元，日期2024年1月15日，电话13912345678"
    Output: {
        "amount": 5000.0,
        "date": "2024-01-15", 
        "phone": "13912345678",
        "is_valid": True
    }
    
    If any field invalid, mark is_valid as False and return what's valid
    """
    from Amount_validator import validate_rmb_amount
    from Chinese_Date_Validator import validate_chinese_date
    from Chinese_Phone_Validator import validate_chinese_phone
    # Initialize result dictionary
    result = {
        "amount": 0.0,
        "date": "no date",
        "phone": "",
        "is_valid": True
    }
    
    # Split message into parts
    parts = message.split("，")
    for part in parts:
        part = part.strip()
        if part.startswith("订单金额"):
            amount_str = part.replace("订单金额", "").strip()
            result["amount"] = validate_rmb_amount(amount_str)
            if result["amount"] == 0.0:
                result["is_valid"] = False
        elif part.startswith("日期"):
            date_str = part.replace("日期", "").strip()
            result["date"] = validate_chinese_date(date_str)
            if result["date"] == "no date":
                result["is_valid"] = False
        elif part.startswith("电话"):
            phone_str = part.replace("电话", "").strip()
            if validate_chinese_phone(phone_str):
                result["phone"] = phone_str
            else:
                result["is_valid"] = False
    return result
    pass

# Test case
test_message = "订单金额5000元，日期2024年1月15日，电话13912345678"
print("\n" + str(clean_order_message(test_message)))
#