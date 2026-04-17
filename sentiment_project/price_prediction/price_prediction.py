import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv("products.csv")

le = LabelEncoder()
df['category_encoded'] = le.fit_transform(df['category'])

X = df[["category_encoded", "rating", "num_reviews", "brand_tier"]]
y = df["price"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor()
model.fit(X_train, y_train)

print("Model trained successfully!")

def predict_price(category, rating, num_reviews, brand_tier):
    category_encoded = le.transform([category])[0]
    prediction = model.predict([[category_encoded, rating, num_reviews, brand_tier]])
    return round(prediction[0], 2)

print("\n===== Price Predictions =====")
print(f"Phone, rating 4.5, 1000 reviews, premium brand → ¥{predict_price('phone', 4.5, 1000, 3)}")
print(f"Clothing, rating 3.8, 200 reviews, budget brand → ¥{predict_price('clothing', 3.8, 200, 1)}")
print(f"Food, rating 4.9, 2000 reviews, mid brand → ¥{predict_price('food', 4.9, 2000, 2)}")
print("=============================")