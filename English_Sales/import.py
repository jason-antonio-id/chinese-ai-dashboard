import csv
import os

file_path = r'C:\Users\LENOVO\Desktop\Python\English_Sales\messy_sales.csv'

# Verify file exists first
if not os.path.exists(file_path):
    print("ERROR: File not found at", file_path)
    exit()

# Read CSV
with open(file_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print("Columns found:", reader.fieldnames)

# Clean data
clean_rows = []
for row in rows:
    # Fix empty amount
    amount = row['amount'] if row['amount'] else '0'
    
    # Fix date (simplified - just show what we have)
    date = row['date'] if row['date'] else 'no date'
    
    # Fix empty status
    status = row['status'] if row['status'] else 'unknown'
    
    clean_rows.append({
        'customer': row['customer'],
        'amount': amount,
        'date': date,
        'status': status
    })

# Save clean data
output_path = r'C:\Users\LENOVO\Desktop\Python\English_Sales\clean_sales.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['customer', 'amount', 'date', 'status'])
    writer.writeheader()
    writer.writerows(clean_rows)

print(f"\nCleaned {len(clean_rows)} rows")
print(f"Saved to: {output_path}")