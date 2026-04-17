import pandas as pd
from prophet import Prophet

df = pd.read_csv("sales.csv")

model = Prophet ()
model.fit(df)

future = model.make_future_dataframe(periods=3, freq = "MS")
forecast = model.predict(future)

print ("===== Sales Forecast Report =====")
print ("Next 3 Months prediction :")
print("")
for index, row in forecast.tail(3).iterrows():
    print (f"{row['ds'].strftime('%B %Y')} → {round(row['yhat'])} items")