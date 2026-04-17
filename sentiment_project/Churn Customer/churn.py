import pandas as pd
from sklearn.tree import DecisionTreeClassifier

pd.set_option('display.max_rows', None)
df = pd.read_csv("customer.csv")

X = df[["months_active", "total_purchases", "total_spent", "days_since_last_purchase"]]
y = df["churned"]

model = DecisionTreeClassifier()
model.fit(X, y)

print ("Model trained successfully")

new_customer = [[24,50,3000,5]]
prediction = model.predict(new_customer)

if prediction == 1:
    print ("This customer will likely churn")
else:
    print ("This customer will likely stay!")