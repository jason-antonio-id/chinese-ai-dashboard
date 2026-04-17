import csv
from datetime import datetime

# Copy your existing validation functions here
def validate_rmb_amount(value):
    """Your existing RMB validator"""
    try:
        value = str(value).strip()
        
        # Handle "万元"
        if "万元" in value:
            value = value.replace("万元", "").replace(",", "")
            amount = float(value) * 10000
            return amount if amount > 0 else 0.0
        
        # Handle "万"
        elif "万" in value:
            value = value.replace("万", "").replace(",", "")
            amount = float(value) * 10000
            return amount if amount > 0 else 0.0
        
        # Handle "元"
        elif "元" in value:
            value = value.replace("元", "").replace(",", "")
            amount = float(value)
            return amount if amount > 0 else 0.0
        
        # Handle "¥"
        elif value.startswith("¥"):
            value = value[1:].replace(",", "")
            amount = float(value)
            return amount if amount > 0 else 0.0
        
        # Handle regular numbers
        else:
            value = value.replace(",", "")
            amount = float(value)
            return amount if amount > 0 else 0.0
            
    except (ValueError, AttributeError):
        return 0.0

def validate_chinese_date(value):
    """Your existing date validator"""
    value = str(value).strip()
    
    # Handle YYYY-MM-DD format
    if "-" in value:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            return "no date"
    
    # Handle Chinese format
    elif "年" in value and "月" in value and "日" in value:
        try:
            # Extract year
            year = value.split("年")[0]
            rest = value.split("年")[1]
            
            # Extract month
            month = rest.split("月")[0]
            
            # Extract day
            day = rest.split("月")[1].split("日")[0]
            
            # Format with leading zeros
            return f"{year}-{int(month):02d}-{int(day):02d}"
        except (ValueError, IndexError):
            return "no date"
    
    return "no date"

def validate_chinese_phone(value):
    """Your existing phone validator"""
    import re
    value = str(value).strip()
    
    # Remove spaces and dashes
    value = value.replace(" ", "").replace("-", "")
    
    # Check if it's a Chinese phone number
    pattern = r'^(?:\+86)?1[3-9]\d{9}$'
    
    if re.match(pattern, value):
        # Remove +86 if present
        if value.startswith("+86"):
            value = value[3:]
        return True
    return False

def clean_order_message(message):
    """Your existing order cleaner"""
    result = {
        "amount": 0.0,
        "date": "no date",
        "phone": "",
        "is_valid": True
    }
    
    # Extract amount
    if "金额" in message:
        after_amount = message.split("金额")[1]
        
        if "，" in after_amount:
            amount_str = after_amount.split("，")[0]
        elif "," in after_amount:
            amount_str = after_amount.split(",")[0]
        else:
            amount_str = after_amount
        
        cleaned_amount = validate_rmb_amount(amount_str)
        result["amount"] = cleaned_amount
        
        if cleaned_amount == 0.0 and amount_str.strip() != "0":
            result["is_valid"] = False
    
    # Extract date
    if "日期" in message:
        after_date = message.split("日期")[1]
        
        if "，" in after_date:
            date_str = after_date.split("，")[0]
        elif "," in after_date:
            date_str = after_date.split(",")[0]
        else:
            date_str = after_date
        
        cleaned_date = validate_chinese_date(date_str)
        result["date"] = cleaned_date
        
        if cleaned_date == "no date":
            result["is_valid"] = False
    
    # Extract phone
    if "电话" in message:
        after_phone = message.split("电话")[1]
        
        if "，" in after_phone:
            phone_str = after_phone.split("，")[0]
        elif "," in after_phone:
            phone_str = after_phone.split(",")[0]
        else:
            phone_str = after_phone
        
        if validate_chinese_phone(phone_str):
            result["phone"] = phone_str
        else:
            result["phone"] = "invalid"
            result["is_valid"] = False
    
    return result

# NEW CODE FOR FILE HANDLING
def process_orders_from_csv(filename):
    """
    Read orders from CSV file and clean each one
    
    Args:
        filename: Path to CSV file
    
    Returns:
        Dictionary with all orders and statistics
    """
    orders = []
    errors = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # Read CSV file
            csv_reader = csv.DictReader(file)
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (row 1 is header)
                try:
                    # Get the order text
                    order_text = row.get('order_text', '')
                    
                    if not order_text:
                        errors.append(f"Row {row_num}: Empty order text")
                        continue
                    
                    # Clean the order
                    cleaned = clean_order_message(order_text)
                    
                    # Add row number to track it
                    cleaned['row_number'] = row_num
                    cleaned['original_text'] = order_text
                    
                    orders.append(cleaned)
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
        
        # Calculate statistics
        total_orders = len(orders)
        valid_orders = sum(1 for o in orders if o['is_valid'])
        total_amount = sum(o['amount'] for o in orders)
        invalid_amount = sum(1 for o in orders if o['amount'] == 0.0 and o['original_text'] != "0")
        
        return {
            'orders': orders,
            'errors': errors,
            'stats': {
                'total_orders': total_orders,
                'valid_orders': valid_orders,
                'invalid_orders': total_orders - valid_orders,
                'total_amount': total_amount,
                'invalid_amount_count': invalid_amount
            }
        }
    
    except FileNotFoundError:
        return {
            'orders': [],
            'errors': [f"File not found: {filename}"],
            'stats': {
                'total_orders': 0,
                'valid_orders': 0,
                'invalid_orders': 0,
                'total_amount': 0,
                'invalid_amount_count': 0
            }
        }

def print_report(results):
    """Print a nice report of the processing results"""
    print("\n" + "="*50)
    print("ORDER PROCESSING REPORT")
    print("="*50)
    
    stats = results['stats']
    print(f"\n📊 STATISTICS:")
    print(f"   Total orders: {stats['total_orders']}")
    print(f"   ✅ Valid orders: {stats['valid_orders']}")
    print(f"   ❌ Invalid orders: {stats['invalid_orders']}")
    print(f"   💰 Total amount: ¥{stats['total_amount']:,.2f}")
    
    if results['errors']:
        print(f"\n⚠️  ERRORS FOUND ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n📋 DETAILED ORDERS:")
    for order in results['orders']:
        status = "✅" if order['is_valid'] else "❌"
        print(f"\n   {status} Row {order['row_number']}:")
        print(f"      Amount: ¥{order['amount']:,.2f}")
        print(f"      Date: {order['date']}")
        print(f"      Phone: {order['phone']}")
        if not order['is_valid']:
            print(f"      Original: {order['original_text'][:50]}...")
    
    print("\n" + "="*50)

def save_cleaned_orders(results, output_filename):
    """Save cleaned orders to a new CSV file"""
    orders = results['orders']
    
    with open(output_filename, 'w', encoding='utf-8', newline='') as file:
        fieldnames = ['row_number', 'original_text', 'amount', 'date', 'phone', 'is_valid']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        for order in orders:
            writer.writerow({
                'row_number': order['row_number'],
                'original_text': order['original_text'],
                'amount': order['amount'],
                'date': order['date'],
                'phone': order['phone'],
                'is_valid': order['is_valid']
            })
    
    print(f"\n✅ Cleaned orders saved to: {output_filename}")

# Main execution
if __name__ == "__main__":
    # Process the orders file
    filename = "orders.csv"
    
    print(f"Processing file: {filename}")
    print("Loading and cleaning orders...")
    
    # Process the orders
    results = process_orders_from_csv(filename)
    
    # Print report
    print_report(results)
    
    # Save cleaned orders to new file
    save_cleaned_orders(results, "cleaned_orders.csv")

