from flask import Flask, request
from snownlp import SnowNLP

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])  # SINGLE ROUTE = Railway happy
def index():
    if request.method == 'POST':
        review = request.form["review"]
        s = SnowNLP(review)
        score = s.sentiments

        if score > 0.6:
            label = "Positive 😊"
            color = "#d4edda"
            emoji = "🎉"
        elif score < 0.4:
            label = "Negative 😞"
            color = "#f8d7da"
            emoji = "⚠️"
        else:
            label = "Neutral 😐"
            color = "#fff3cd"
            emoji = "➡️"

        return '''
<!DOCTYPE html>
<html>
<head><title>Result - Sentiment Analyzer</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 500px; width: 90%; text-align: center; }
.result { background: ''' + color + '''; padding: 30px; border-radius: 15px; margin: 20px 0; }
.emoji { font-size: 50px; margin-bottom: 20px; }
.score { font-size: 48px; font-weight: bold; color: #333; margin: 20px 0; }
a { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 12px; display: inline-block; margin-top: 20px; }
</style>
</head>
<body>
<div class="container">
<h1>''' + emoji + ''' Result</h1>
<div class="result">
<div class="emoji">''' + emoji + '''</div>
<h2>''' + label + '''</h2>
<div class="score">''' + str(round(score, 2)) + '''</div>
<p><strong>Review:</strong><br>''' + review + '''</p>
</div>
<a href="/">← Analyze Another</a>
</div>
</body>
</html>'''

    return '''
<!DOCTYPE html>
<html>
<head>
<title>🇨🇳 Chinese Sentiment Analyzer</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); max-width: 500px; width: 90%; text-align: center; }
h1 { color: #333; margin-bottom: 10px; font-size: 28px; }
.subtitle { color: #666; margin-bottom: 30px; font-size: 16px; }
input { width: 100%; padding: 18px; font-size: 16px; border: 2px solid #e1e5e9; border-radius: 12px; margin-bottom: 20px; transition: all 0.3s; }
input:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 18px 40px; font-size: 16px; border: none; border-radius: 12px; cursor: pointer; transition: transform 0.2s; }
button:hover { transform: translateY(-2px); }
.contact { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 12px; font-size: 14px; color: #666; }
</style>
</head>
<body>
<div class="container">
<h1>🇨🇳 Sentiment Analyzer</h1>
<p class="subtitle">Analyze Taobao/Shopee reviews instantly</p>
<form method="POST">
<input type="text" name="review" placeholder="输入中文评论... (e.g. 这个手机电池很棒！)" required>
<button type="submit">🔍 Analyze Now</button>
</form>
<div class="contact">
<p>Built for Chinese businesses | WhatsApp: +62852-6455-2796 | WeChat: wxid_pxnd52vvyqtx22</p>
</div>
</div>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True)