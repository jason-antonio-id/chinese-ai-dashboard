from snownlp import SnowNLP
import pandas as pd

df = pd.read_csv('review.csv')

results = []
positive_count = 0 
negative_count = 0
neutral_count = 0

for review in df['review']:
    s = SnowNLP(review)
    score = s.sentiments

    if score > 0.6:
        label = ("Positive Review")
        recommendation = ("Keep it up")
        positive_count = positive_count + 1
    elif score < 0.4:
        label = ("Negative Review")
        recommendation = ("Needs Improvement")
        negative_count = negative_count + 1
    else:
        label = ("Neutral Review")
        recommendation = ("Could be better")
        neutral_count = neutral_count + 1

    results.append({
        "review": review,
        "label": label,
        "recommendation": recommendation,
        "score" : round (score, 2),
    })

df_results = pd.DataFrame(results)

summary = pd.DataFrame([{
    "review" : "SUMMARY",
    "label" : f"Positive: {positive_count}, Negative: {negative_count}, Neutral: {neutral_count}",
    "recommendation":"", 
    "score": ""
}])

final = pd.concat ([df_results, summary], ignore_index=True)
final.to_csv("sentiment_analysis_results.csv", index=False)

print("===== Sentiment Report =====")
print("Total reviews:", len(df))
print("Positive:", positive_count)
print("Negative:", negative_count)
print("Neutral:", neutral_count)
print("============================")
print("Done! Sentiment analysis results saved to 'sentiment_analysis_results.csv'.")