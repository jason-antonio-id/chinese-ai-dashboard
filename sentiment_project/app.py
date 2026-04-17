from flask import Flask, request
from snownlp import SnowNLP

app = Flask(__name__)

@app.route("/")
def home():
    return '''
        <h1>Chinese Sentiment Analyzer</h1>
        <form method="POST" action="/analyze">
            <input type="text" name="review" placeholder="输入中文评论..." style="width:400px; padding:8px;">
            <button type="submit" style="padding:8px 16px;">Analyze</button>
        </form>
    '''

@app.route("/analyze", methods=["POST"])
def analyze():
    review = request.form["review"]
    s = SnowNLP(review)
    score = s.sentiments

    if score > 0.6:
        label = "Positive 😊"
    elif score < 0.4:
        label = "Negative 😞"
    else:
        label = "Neutral 😐"

    return f'''
        <h1>Result</h1>
        <p>Review: {review}</p>
        <p>Sentiment: {label}</p>
        <p>Score: {round(score, 2)}</p>
        <a href="/">Go back</a>
    '''

if __name__ == "__main__":
    app.run(debug=True)