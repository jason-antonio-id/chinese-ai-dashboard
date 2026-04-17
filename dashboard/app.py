from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import io
import jieba
from snownlp import SnowNLP
import os
from sklearn.tree import DecisionTreeClassifier
from datetime import datetime
import re

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

from flask import send_from_directory

@app.route('/api/sentiment', methods=['POST'])
def api_sentiment():
    from snownlp import SnowNLP
    data = request.json
    review = data.get('review', '')
    if not review:
        return {'error': 'No review provided'}, 400
    
    s = SnowNLP(review)
    score = s.sentiments
    if score > 0.6:
        label = "Positive 😊"
        emoji = "🎉"
    elif score < 0.4:
        label = "Negative 😞"
        emoji = "⚠️"
    else:
        label = "Neutral 😐"
        emoji = "➡️"
    
    return {
        'success': True,
        'score': round(score, 2),
        'label': label,
        'emoji': emoji,
        'review': review
    }

df_global = None

product_words = ['手机', '屏幕', '电池', '拍照', '充电', '续航', '运行', '速度', '外壳', '内存', '音质', '摄像头', '处理器', '系统', '显示屏']

def count_product_words(text):
    words = jieba.lcut(str(text))
    return sum(1 for word in words if word in product_words)

def detect_fake(word_count, sentiment, product_word_count):
    if word_count <= 2: return 1
    if word_count <= 4 and sentiment > 0.9: return 1
    if word_count <= 6 and sentiment > 0.95 and product_word_count == 0: return 1
    if sentiment < 0.3: return 0
    return 0

@app.route('/fake-detector', methods=['GET', 'POST'])
def fake_detector():
    global df_global
    if request.method == 'POST':
        file = request.files.get('csv_file')
        reviews_text = request.form.get('reviews_text', '').strip()
        
        if file and file.filename:
            try:
                df = pd.read_csv(file)
                if 'review' not in df.columns:
                    return render_template('fake_detector.html', error="CSV must have 'review' column")
            except Exception as e:
                return render_template('fake_detector.html', error=f"CSV read error: {str(e)}")
        else:
            if not reviews_text:
                return render_template('fake_detector.html', error="Upload CSV or paste reviews")
            lines = [line.strip() for line in reviews_text.split('\n') if line.strip()]
            df = pd.DataFrame({'review': lines})
        
        if df.empty:
            return render_template('fake_detector.html', error="No valid reviews found")
        
        try:
            df['word_count'] = df['review'].apply(lambda x: len(jieba.lcut(str(x))))
            df['sentiment'] = df['review'].apply(lambda x: SnowNLP(str(x)).sentiments)
            df['product_words'] = df['review'].apply(count_product_words)
            df['fake'] = df.apply(lambda row: detect_fake(row['word_count'], row['sentiment'], row['product_words']), axis=1)
            df['label'] = df['fake'].apply(lambda x: '🚨 假评论' if x==1 else '✅ 真实评论')
            df['risk'] = df['fake'].apply(lambda x: '高风险' if x==1 else '正常')
        except Exception as e:
            return render_template('fake_detector.html', error=f"Analysis error: {str(e)}")
        
        df_global = df
        accuracy = None
        if 'is_fake' in df.columns:
            accuracy = (df['is_fake'] == df['fake']).mean()
        
        table_html = df.to_html(index=False, classes='table table-striped table-hover table-3d', escape=False, 
                               columns=['review', 'word_count', 'sentiment', 'product_words', 'label', 'risk'],
                               table_id='resultsTable')
        
        download_btn = '<a href="/download" class="btn-3d"><i class="fas fa-download mr-2"></i>📥 Download Report</a>'
        
        return render_template('fake_detector.html', 
                              results=True,
                              summary_count=len(df),
                              fake_count=int((df['fake']==1).sum()),
                              accuracy=f"{accuracy:.1%}" if accuracy else "N/A",
                              table=table_html,
                              download_btn=download_btn,
                              error='')
    
    return render_template('fake_detector.html', results=False, error='')

@app.route('/download')
def download():
    global df_global
    if df_global is not None and not df_global.empty:
        csv_buffer = io.StringIO()
        df_global.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_content = csv_buffer.getvalue()
        return send_file(io.BytesIO(csv_content.encode('utf-8-sig')), 
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name='fake_review_report.csv')
    return redirect(url_for('fake_detector'))

# Stub routes for other tools
customer_df = pd.read_csv('data/customer_sample.csv')
X = customer_df[["months_active", "total_purchases", "total_spent", "days_since_last_purchase"]]
y = customer_df["churned"]

churn_model = DecisionTreeClassifier()
churn_model.fit(X, y)

@app.route('/churn', methods=['GET', 'POST'])
def churn():
    if request.method == 'POST':
        months_active = float(request.form["months_active"])
        total_purchases = float(request.form["total_purchases"])
        total_spent = float(request.form["total_spent"])
        days_since_last_purchase = float(request.form["days_since_last_purchase"])
        
        new_customer = [[months_active, total_purchases, total_spent, days_since_last_purchase]]
        prediction = churn_model.predict(new_customer)[0]
        
        return render_template('churn.html', prediction=int(prediction),
                              months_active=int(months_active),
                              total_purchases=int(total_purchases),
                              total_spent=int(total_spent),
                              days_since_last_purchase=int(days_since_last_purchase))
    
    return render_template('churn.html')

ratings_df = pd.read_csv('data/ratings_sample.csv')
table = ratings_df.pivot_table(index="user", columns="product", values="rating", fill_value=0)
correlation = table.T.corr()

def recommend(user):
    if user not in correlation.index:
        return ['No data']
    similar_users = correlation[user].dropna().sort_values(ascending=False).iloc[1:4]
    already_bought = table.loc[user].dropna().index.tolist()
    recs = []
    for sim_user in similar_users.index:
        for product in table.loc[sim_user].dropna().index:
            if product not in already_bought and product not in recs:
                recs.append(product)
                if len(recs) >= 5:
                    break
    return recs or ['No recommendations']

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    users = ratings_df['user'].unique().tolist()
    recommendations = []
    user = ''
    if request.method == 'POST':
        user = request.form["user"]
        recommendations = recommend(user)
    return render_template('recommend.html', users=users, recommendations=recommendations, user=user)

@app.route('/forecast')
def forecast():
    return '<h1>Sales Forecasting (Coming Soon)</h1><a href="/">Back</a>'

def validate_rmb_amount(value):
    def is_valid_amount(amount_value):
        try:
            amount = float(amount_value)
            if amount <= 0:
                return False
        except ValueError:
            return False
        return True
    
    try:
        value = str(value).strip()
        
        if "万元" in value:
            value = value.replace("万元", "").replace(",", "")
            amount = float(value) * 10000
            return amount if is_valid_amount(value) else 0.0
        
        elif "万" in value:
            value = value.replace("万", "").replace(",", "")
            amount = float(value) * 10000
            return amount if is_valid_amount(value) else 0.0
        
        elif "元" in value:
            value = value.replace("元", "").replace(",", "")
            amount = float(value)
            return amount if is_valid_amount(value) else 0.0
        
        elif value.startswith("¥"):
            value = value[1:].replace(",", "")
            amount = float(value)
            return amount if is_valid_amount(value) else 0.0
        
        else:
            value = value.replace(",", "")
            amount = float(value)
            return amount if is_valid_amount(value) else 0.0
            
    except (ValueError, AttributeError):
        return 0.0

def validate_chinese_date(value):
    value = str(value).strip()
    
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

def validate_chinese_phone(value):
    def is_valid_phone(phone_value):
        phone_value = phone_value.replace(" ", "").replace("-", "")
        pattern = r"^(\+86)?1[3-9]\d{9}$"
        return bool(re.match(pattern, phone_value))
    try:
        value = str(value).strip()
        if is_valid_phone(value):
            return value.replace(" ", "").replace("-", "")
        return ""
    except:
        return ""

@app.route('/rmb-tools', methods=['GET', 'POST'])
def rmb_tools():
    amount_result = amount_valid = date_result = date_valid = phone_result = phone_clean = phone_valid = None
    if request.method == 'POST':
        tool = request.form["tool"]
        input_val = request.form["input"]
        
        if tool == "amount":
            amount_result = validate_rmb_amount(input_val)
            amount_valid = amount_result > 0
        elif tool == "date":
            date_result = validate_chinese_date(input_val)
            date_valid = date_result != "no date"
        elif tool == "phone":
            phone_clean = validate_chinese_phone(input_val)
            phone_valid = bool(phone_clean)
    
    return render_template('rmb_tools.html', 
                          amount_result=amount_result, amount_valid=amount_valid,
                          date_result=date_result, date_valid=date_valid,
                          phone_result=phone_result, phone_clean=phone_clean, phone_valid=phone_valid)

def clean_order_message(message):
    result = {
        "amount": 0.0,
        "date": "no date",
        "phone": "",
        "is_valid": True
    }
    
    parts = message.split("，")
    for part in parts:
        part = part.strip()
        if part.startswith("订单金额"):
            amount_str = part.replace("订单金额", "").strip()
            result["amount"] = validate_rmb_amount(amount_str)
            if result["amount"] == 0.0:
                result["is_valid"] = False
        elif part.startswith("日期"):
            date_str = part.replace("日期", "").strip()
            result["date"] = validate_chinese_date(date_str)
            if result["date"] == "no date":
                result["is_valid"] = False
        elif part.startswith("电话"):
            phone_str = part.replace("电话", "").strip()
            result["phone"] = validate_chinese_phone(phone_str)
            if not result["phone"]:
                result["is_valid"] = False
    return result

@app.route('/rmb-order-cleaner', methods=['GET', 'POST'])
def rmb_order_cleaner():
    result = None
    message = ""
    if request.method == 'POST':
        message = request.form["message"]
        result = clean_order_message(message)
        return render_template('rmb_order_cleaner.html', result=result, message=message)
    
    return render_template('rmb_order_cleaner.html')

def generate_report_summary(df):
    if df.empty:
        return pd.DataFrame()
    summary = pd.DataFrame({
        'Metric': ['Total Orders', 'Valid Orders', 'Total Amount', 'Avg Amount'],
        'Value': [len(df), len(df[df['is_valid'] == True]), df[df['is_valid'] == True]['amount'].sum(), df[df['is_valid'] == True]['amount'].mean()]
    })
    return summary

excel_df_global = None

@app.route('/excel-report', methods=['GET', 'POST'])
def excel_report():
    global excel_df_global
    if request.method == 'POST':
        file = request.files['csv_file']
        df = pd.read_csv(file)
        excel_df_global = df
        summary = generate_report_summary(df)
        table_html = summary.to_html(index=False, classes='table-3d', escape=False)
        return render_template('excel_report.html', summary=True, summary_table=table_html)
    return render_template('excel_report.html')

@app.route('/excel-download')
def excel_download():
    global excel_df_global
    if excel_df_global is not None:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            excel_df_global.to_excel(writer, sheet_name='Orders', index=False)
            summary = generate_report_summary(excel_df_global)
            summary.to_excel(writer, sheet_name='Summary', index=False)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='business_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return redirect(url_for('excel_report'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

