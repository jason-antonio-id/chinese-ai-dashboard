def validate_chinese_date(value):
    """
    Handle Chinese date formats:
    - "2024-01-15" -> "2024-01-15"
    - "2024年1月15日" -> "2024-01-15"
    - "2024年01月15日" -> "2024-01-15"
    - "2024.01.15" -> "2024-01-15"
    - "15/01/2024" -> "2024-01-15" (convert from DD/MM/YYYY)
    
    Returns: standardized date string "YYYY-MM-DD" or "no date" if invalid
    """
    from datetime import datetime
    
    value = str(value).strip()
    
    # Try multiple date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y年%m月%d日",
        "%Y.%m.%d",
        "%d/%m/%Y"
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(value, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return "no date"


# Test cases
print(validate_chinese_date("2024-01-15"))      # Should print: 2024-01-15
print(validate_chinese_date("2024年1月15日"))   # Should print: 2024-01-15
print(validate_chinese_date("2024年01月15日"))  # Should print: 2024-01-15
print(validate_chinese_date("invalid"))         # Should print: no date