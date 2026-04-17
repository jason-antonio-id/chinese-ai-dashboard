import pandas as pd

df = pd.read_csv ("ratings.csv")

table = df.pivot_table(index = "user", columns = "product", values = "rating")

correlation = table.T.corr()

def recommend(user):
    similar_users = correlation [user].dropna(). sort_values (ascending = False)
    similar_users = similar_users.drop(user)

    already_bought = table.loc[user].dropna().index.tolist()

    recommendations = []
    for similar_user in similar_users.index:
        similar_user_products = table.loc[similar_user].dropna().index.tolist()
        for product in similar_user_products:
            if product not in already_bought and product not in recommendations :
                recommendations.append(product)

    return recommendations

print ("Recommendations for Bob :", recommend ("Bob"))
print ("Recommendations for Charlie", recommend ("Charlie"))
print ("Recommendations for Alice", recommend ("Alice"))