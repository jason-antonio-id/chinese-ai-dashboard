# ==============================================================
# ENVIRONMENT — must be the very first thing that runs so that
# every os.getenv() call below picks up values from .env
# ==============================================================
import os
from dotenv import load_dotenv
load_dotenv()  # reads .env file into os.environ (safe no-op if file absent)

# ==============================================================
# STANDARD LIBRARY
# ==============================================================
import json
import re
import time
import threading
from datetime import datetime, timedelta
from functools import wraps, lru_cache
import Levenshtein  # pip install python-Levenshtein

# ==============================================================
# THIRD-PARTY — web framework & utilities
# ==============================================================
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

# ==============================================================
# THIRD-PARTY — ML / NLP / vision
# ==============================================================
import numpy as np
import pandas as pd
import pytesseract
import tensorflow as tf
from PIL import Image
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from snownlp import SnowNLP
import jieba
import jieba.analyse

# ==============================================================
# THIRD-PARTY — Firebase
# ==============================================================
import firebase_admin
from firebase_admin import credentials, auth, firestore

# ==============================================================
# FLASK APP
# ==============================================================
app = Flask(__name__)

# ==================== ENVIRONMENT / CONFIG ====================

# 1. Secret key — required; app refuses to start without it
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is not set. "
        "Add it to your .env file or deployment environment variables."
    )

# 2. Admin email — required
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
if not ADMIN_EMAIL:
    raise RuntimeError(
        "ADMIN_EMAIL is not set. "
        "Add it to your .env file or deployment environment variables."
    )

# 3. File upload settings
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "csv", "xlsx", "xls"}
UPLOAD_FOLDER = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB hard limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 4. Tesseract — path loaded from .env so it works on Windows AND Linux
pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_CMD", "/usr/bin/tesseract"
)

# ==================== FIREBASE INIT (FLEXIBLE FOR RENDER) ====================

# Load credentials from environment variable (for Render) or fallback to local file
cred_json = os.getenv("FIREBASE_CREDENTIALS")
if not cred_json:
    # Fallback to local file for development
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
    if not os.path.exists(firebase_cred_path):
        raise FileNotFoundError(
            f"Firebase credentials file not found at '{firebase_cred_path}'. "
            "Set FIREBASE_CREDENTIALS in your .env file (as JSON string) or provide the file."
        )
    cred = credentials.Certificate(firebase_cred_path)
else:
    # Parse the JSON string from the environment variable (Render deployment)
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)
db = firestore.client()

# ==================== TOKEN CACHING (SPEEDS UP LOGIN) ====================
_token_cache = {}
def verify_token_cached(id_token):
    """Cache decoded tokens for 5 minutes to avoid repeated Google API calls."""
    if id_token in _token_cache:
        decoded, expiry = _token_cache[id_token]
        if time.time() < expiry:
            return decoded
    decoded = auth.verify_id_token(id_token)
    _token_cache[id_token] = (decoded, time.time() + 300)
    return decoded

# ==================== ASYNC FIRESTORE WRITES ====================
def update_user_async(uid, email, name, is_admin):
    """Fire-and-forget background update for last_active and log."""
    def _update():
        try:
            user_ref = db.collection("users").document(uid)
            # Update last_active and ensure user doc exists with minimal fields
            user_ref.set({
                "last_active": firestore.SERVER_TIMESTAMP,
                "email": email,
                "name": name,
                "is_admin": is_admin,
                "uid": uid
            }, merge=True)
            log_activity("🔑", f"User logged in: {email}", email)
        except Exception as e:
            print(f"Async update failed: {e}")
    threading.Thread(target=_update).start()

# ==================== LAZY LOADED ML MODELS ====================
# All heavy models are now initialized to None and loaded on first use.
mobilenet_model = None
preprocess_input_fn = None
decode_predictions_fn = None

churn_scaler = None
churn_model = None

price_model = None
price_scaler = None
_category_map = None
_global_avg_price = None

fakereview_vectorizer = None
fakereview_model = None

# Churn features constant (needed even without model loaded)
_CHURN_FEATURES = ["months_active", "total_purchases", "total_spent", "days_since_last_purchase"]

# ==============================================================
# CHURN PREDICTION MODEL — lazy loader
# ==============================================================
def _get_churn_model():
    global churn_scaler, churn_model
    if churn_model is None:
        print("Loading Churn model...")
        _churn_bootstrap = pd.DataFrame({
            "months_active":            [12, 3, 8, 1, 24, 2, 6, 1, 18, 2],
            "total_purchases":          [25, 2, 15, 1, 50, 3, 10, 1, 35, 2],
            "total_spent":              [1500, 80, 900, 30, 3000, 100, 600, 20, 2100, 60],
            "days_since_last_purchase": [10, 120, 25, 200, 5, 150, 30, 180, 15, 160],
            "churned":                  [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        })
        churn_scaler = StandardScaler()
        _X_boot = churn_scaler.fit_transform(_churn_bootstrap[_CHURN_FEATURES])
        churn_model = DecisionTreeClassifier(random_state=42)
        churn_model.fit(_X_boot, _churn_bootstrap["churned"])
        print("Churn model loaded!")
    return churn_scaler, churn_model

# ==============================================================
# PRICE PREDICTION MODEL — lazy loader
# ==============================================================
_TRAINING_CSV = os.path.join(os.path.dirname(__file__), "synthetic_products_10_categories.csv")

def _generate_training_data(csv_path):
    """Generate a synthetic dataset with positive rating-price correlation."""
    import numpy as np
    np.random.seed(42)
    n_samples = 2000

    categories = ['phone', 'clothing', 'food', 'electronics', 'book',
                  'home', 'beauty', 'sports', 'toy', 'auto']

    data = []
    for _ in range(n_samples):
        cat = np.random.choice(categories)
        rating = np.random.uniform(1, 5)
        num_reviews = np.random.randint(10, 5000)
        brand_tier = np.random.randint(1, 4)   # 1=budget, 2=mid, 3=premium

        # Base price influenced by category
        base_price = {
            'phone': 3000, 'clothing': 200, 'food': 50, 'electronics': 1500,
            'book': 80, 'home': 400, 'beauty': 150, 'sports': 250,
            'toy': 100, 'auto': 20000
        }[cat]

        # POSITIVE correlation: higher rating → higher price
        # Also brand_tier increases price
        price_multiplier = (0.7 + 0.3 * (rating / 5)) * (0.5 + 0.5 * brand_tier)
        price = base_price * price_multiplier * np.random.uniform(0.8, 1.2)
        price = max(price, base_price * 0.3)

        data.append([cat, round(rating, 1), num_reviews, brand_tier, round(price, 2)])

    df = pd.DataFrame(data, columns=['category', 'rating', 'num_reviews', 'brand_tier', 'price'])
    df.to_csv(csv_path, index=False)
    print(f"✅ Generated new training data: {csv_path}")
    return df

def _build_price_model(csv_path):
    """Load or create training data, encode categories, scale rating/num_reviews, fit model."""
    if not os.path.exists(csv_path):
        df = _generate_training_data(csv_path)
    else:
        df = pd.read_csv(csv_path)

    df['category'] = df['category'].astype(str).str.strip().str.lower()

    # Category → integer mapping (sorted for determinism)
    known_cats = sorted(df['category'].unique())
    cat_map = {c: i for i, c in enumerate(known_cats)}
    global_avg = df['price'].mean()

    df['category_encoded'] = df['category'].map(cat_map)

    # Scale only continuous features: rating and num_reviews.
    # brand_tier remains ordinal (1-3) – it is not scaled.
    scaler = StandardScaler()
    scale_cols = ['rating', 'num_reviews']
    df[scale_cols] = scaler.fit_transform(df[scale_cols])

    # Random Forest with fixed seed
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(df[['category_encoded', 'rating', 'num_reviews', 'brand_tier']], df['price'])

    return model, scaler, cat_map, global_avg

def _get_price_model():
    global price_model, price_scaler, _category_map, _global_avg_price
    if price_model is None:
        print("Loading Price Prediction model...")
        price_model, price_scaler, _category_map, _global_avg_price = _build_price_model(_TRAINING_CSV)
        print("Price Prediction model loaded!")
    return price_model, price_scaler, _category_map, _global_avg_price

def _prepare_single_prediction(category, rating, num_reviews, brand_tier):
    """Prepare a single product for prediction (manual form input)."""
    _, _, _category_map, _ = _get_price_model()  # ensure loaded
    cat_lower = category.strip().lower()
    encoded_cat = _category_map.get(cat_lower, -1)
    unknown = (encoded_cat == -1)

    # Scale rating and num_reviews
    scaled = price_scaler.transform([[rating, num_reviews]])[0]

    X = pd.DataFrame([[
        encoded_cat,
        scaled[0],      # rating scaled
        scaled[1],      # num_reviews scaled
        brand_tier      # ordinal, unchanged
    ]], columns=['category_encoded', 'rating', 'num_reviews', 'brand_tier'])

    return X, unknown

def _prepare_batch_prediction(df):
    """Prepare an uploaded DataFrame for batch prediction."""
    _, _, _category_map, _ = _get_price_model()
    df = df.copy()
    df['category'] = df['category'].astype(str).str.strip().str.lower()
    unknown_mask = ~df['category'].isin(_category_map)
    df['category_encoded'] = df['category'].map(_category_map).fillna(-1).astype(int)

    # Scale rating and num_reviews (brand_tier is left as is)
    scale_cols = ['rating', 'num_reviews']
    df[scale_cols] = price_scaler.transform(df[scale_cols])

    X = df[['category_encoded', 'rating', 'num_reviews', 'brand_tier']]
    return X, unknown_mask

# ==============================================================
# FAKE REVIEW DETECTOR — lazy loader
# ==============================================================
_FAKEREVIEW_CSV = os.path.join(os.path.dirname(__file__), "fake_review_training_data.csv")

# 5 hand‑crafted linguistic features
def extract_linguistic_features(text):
    """Extract 5 features that help distinguish water army from genuine reviews."""
    # Clean text: keep only Chinese characters for density
    chinese_chars = re.sub(r'[^\u4e00-\u9fff]', '', text)
    total_chars = len(chinese_chars)
    total_len = len(text)
    
    # Feature 1: Punctuation Saturation (bots write walls of text)
    punct_ratio = total_chars / total_len if total_len > 0 else 0
    
    # Feature 2: Template N-Gram Match Score (common water army phrases)
    template_grams = ["很满意", "质量好", "很喜欢", "物流快", "服务好", 
                      "值得购买", "性价比高", "第二次买", "一如既往"]
    seg_list = list(jieba.cut(text))
    count_tmpl = sum(1 for gram in template_grams if gram in text)
    template_score = count_tmpl / len(seg_list) if seg_list else 0
    
    # Feature 3: Specificity Index (vague vs. specific adjectives)
    vague_words = ["不错", "还行", "可以", "挺好", "一般", "差不多"]
    specific_words = ["细腻", "粗糙", "紧致", "松垮", "刺鼻", "香", "硬", "软", "舒服", "难受"]
    vague_count = sum(1 for w in seg_list if w in vague_words)
    specific_count = sum(1 for w in seg_list if w in specific_words)
    specificity_ratio = (specific_count + 1) / (vague_count + 1)
    
    # Feature 4: First-Person Pronoun Presence (humans say "I")
    has_person = 1 if any(w in text for w in ["我", "俺", "自己"]) else 0
    
    # Feature 5: Character Repetitiveness (max char repetition / total)
    from collections import Counter
    char_counts = Counter(chinese_chars)
    max_freq = max(char_counts.values()) if char_counts else 1
    repetition_ratio = max_freq / total_chars if total_chars > 0 else 0
    
    return [punct_ratio, template_score, specificity_ratio, has_person, repetition_ratio]

# Similarity filter – flags duplicates using Levenshtein ratio
def compute_similarity_flag(reviews, threshold=0.85):
    """Mark reviews that are near‑duplicates of any earlier review."""
    flags = [False] * len(reviews)
    for i in range(len(reviews)):
        for j in range(i):
            if Levenshtein.ratio(reviews[i], reviews[j]) > threshold:
                flags[i] = True
                break
    return flags

def _build_fakereview_model(csv_path):
    """
    Train a RandomForest classifier on combined features:
      - TF‑IDF vector of the review text
      - SnowNLP sentiment score (0–1)
      - 5 linguistic features
    """
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["text", "label"])
    df["text"]  = df["text"].astype(str).str.strip()
    df["label"] = df["label"].astype(int)

    # Compute sentiment for every training sample
    sentiments = []
    ling_feats = []
    for review in df["text"]:
        try:
            s = SnowNLP(review)
            sentiments.append(s.sentiments)
        except:
            sentiments.append(0.5)
        ling_feats.append(extract_linguistic_features(review))
    df["sentiment"] = sentiments
    ling_feats = np.array(ling_feats)

    # TF‑IDF vectorizer (keep 5000 features)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)
    X_tfidf = vectorizer.fit_transform(df["text"])

    # Combine TF‑IDF (sparse) with sentiment + linguistic features
    X_combined = np.hstack([
        X_tfidf.toarray(),
        df["sentiment"].values.reshape(-1, 1),
        ling_feats
    ])

    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_combined, df["label"])

    return vectorizer, clf

def _get_fakereview_model():
    global fakereview_vectorizer, fakereview_model
    if fakereview_model is None:
        print("Loading Fake Review model...")
        fakereview_vectorizer, fakereview_model = _build_fakereview_model(_FAKEREVIEW_CSV)
        print("Fake Review model loaded!")
    return fakereview_vectorizer, fakereview_model

# ==============================================================
# KEYWORD EXTRACTION – Category‑Based with TF‑IDF & Stop Words
# ==============================================================

# Expanded Chinese e‑commerce stop words
ECOMMERCE_STOPWORDS = {
    "效果", "功能", "强大", "不错", "还行", "可以", "挺好的", "非常", "特别",
    "真的", "超级", "东西", "质量", "物流", "服务", "态度", "宝贝", "收到",
    "满意", "喜欢", "值得", "购买", "推荐", "好评", "下次", "还会", "再来",
    "价格", "实惠", "便宜", "贵", "性价比", "发货", "速度", "快", "慢",
    "包装", "完好", "精致", "漂亮", "好看", "大气", "上档次", "正品",
    "放心", "信赖", "老顾客", "第二次", "一如既往", "支持", "卖家"
}

# Simple dictionary-based category detection
CATEGORY_KEYWORDS = {
    "electronics": {"手机", "电脑", "耳机", "充电器", "屏幕", "电池", "内存", "处理器", "相机", "智能"},
    "fashion": {"衣服", "裤子", "裙子", "鞋子", "包包", "时尚", "款式", "面料", "穿着", "搭配", "尺码"},
    "food": {"味道", "口感", "好吃", "新鲜", "甜", "咸", "辣", "香", "零食", "饮料", "水果", "保质期"},
}

def detect_category(text):
    """Return the most likely category based on keyword overlap."""
    words = set(jieba.lcut(text))
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = len(words & keywords)
    if not scores or max(scores.values()) == 0:
        return "general"
    return max(scores, key=scores.get)


TOOL_USAGE_KEYS = ["sentiment","keywords","ocr","churn","forecast","recommend","fakereview","imageclassifier","priceprediction"]
TOOL_META = {
    "sentiment":       {"name": "Sentiment Analyzer",    "icon": "💬", "desc": "Analyze Chinese reviews"},
    "keywords":        {"name": "Keyword Extractor",     "icon": "🔍", "desc": "Extract Chinese keywords"},
    "ocr":             {"name": "OCR Scanner",           "icon": "📄", "desc": "Extract text from images"},
    "churn":           {"name": "Churn Prediction",      "icon": "👥", "desc": "Predict customer churn"},
    "forecast":        {"name": "Sales Forecast",        "icon": "📈", "desc": "Predict future sales"},
    "recommend":       {"name": "Recommendations",       "icon": "🛒", "desc": "Product recommendations"},
    "fakereview":      {"name": "Fake Review Detector",  "icon": "🚨", "desc": "Detect fake reviews"},
    "imageclassifier": {"name": "Image Classifier",      "icon": "🖼️", "desc": "Classify product images"},
    "priceprediction": {"name": "Price Prediction",      "icon": "💰", "desc": "Predict product prices"},
}

# ==================== HELPERS ====================

def allowed_file(filename, allowed=None):
    if allowed is None:
        allowed = ALLOWED_EXTENSIONS
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

def save_upload(file, allowed=None):
    if not file or file.filename == "":
        raise ValueError("No file provided")
    if not allowed_file(file.filename, allowed):
        raise ValueError(f"File type not allowed: {file.filename}")
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return path

def get_user_doc(uid):
    return db.collection("users").document(uid).get()

def log_activity(icon, text, user_email=None):
    db.collection("activity_log").add({
        "icon": icon,
        "text": text,
        "user": user_email or "system",
        "time": firestore.SERVER_TIMESTAMP
    })

def increment_tool_usage(tool_key):
    ref = db.collection("tool_usage").document(tool_key)
    ref.set({"count": firestore.Increment(1)}, merge=True)

def send_notification(uid, title, message, notif_type="info"):
    db.collection("users").document(uid).collection("notifications").add({
        "title": title,
        "message": message,
        "type": notif_type,
        "read": False,
        "time": firestore.SERVER_TIMESTAMP
    })

def send_global_announcement(title, message, sender_email):
    db.collection("announcements").add({
        "title": title,
        "message": message,
        "sender": sender_email,
        "time": firestore.SERVER_TIMESTAMP
    })
    log_activity("📢", f"Global announcement sent by {sender_email}", sender_email)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'uid' not in session:
            return redirect(url_for('index'))
        user_doc = get_user_doc(session['uid'])
        if user_doc.exists and user_doc.to_dict().get('suspended'):
            session.clear()
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

# ==================== MAIN SPA ROUTE ====================

@app.route("/")
def index():
    return render_template("spa.html")

# ==================== AUTH API ====================

@app.route("/api/auth/verify", methods=["POST"])
def api_auth_verify():
    start_time = time.time()
    data = request.get_json()
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "No token provided"}), 400

    # Use cached token verification (saves ~1-3 seconds per login)
    decoded = verify_token_cached(id_token)
    if not decoded:
        return jsonify({"error": "Invalid token"}), 401

    uid = decoded["uid"]
    email = decoded.get("email", "")
    name = decoded.get("name", email.split("@")[0])
    is_admin = (email == ADMIN_EMAIL)

    # Fetch username only if needed (Firestore read – still required)
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    username = ""
    if user_doc.exists:
        username = user_doc.to_dict().get("username", "")

    # Ensure user doc exists with minimal fields (merge=True avoids overwrite)
    user_ref.set({
        "uid": uid,
        "email": email,
        "name": name,
        "is_admin": is_admin,
        "last_active": firestore.SERVER_TIMESTAMP,
    }, merge=True)

    # Set session immediately
    session['uid'] = uid
    session['email'] = email
    session['name'] = name
    session['is_admin'] = is_admin
    if username:
        session['username'] = username

    # Async Firestore writes (log_activity, last_active update already done above)
    # We'll still call log_activity async to not block response
    def _log_async():
        log_activity("🔑", f"User logged in: {email}", email)
    threading.Thread(target=_log_async).start()

    print(f"✅ Login completed in {time.time()-start_time:.2f}s")
    return jsonify({
        "uid": uid,
        "email": email,
        "name": name,
        "is_admin": is_admin,
        "username": username
    })

@app.route("/api/user/username", methods=["POST"])
@login_required
def api_set_username():
    data = request.get_json()
    username = data.get("username", "").strip()
    db.collection("users").document(session["uid"]).update({"username": username})
    session["username"] = username
    return jsonify({"ok": True})

@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    session.clear()
    return jsonify({"ok": True})

@app.route("/api/auth/me")
def api_auth_me():
    if 'uid' not in session:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "uid": session['uid'],
        "email": session['email'],
        "name": session['name'],
        "is_admin": session.get('is_admin', False)
    })

# ==================== NOTIFICATIONS ====================

@app.route("/api/notifications")
@login_required
def api_notifications():
    uid = session['uid']
    notifs_ref = db.collection("users").document(uid).collection("notifications") \
                   .order_by("time", direction=firestore.Query.DESCENDING).limit(20)
    notifs = [{"id": d.id, **d.to_dict()} for d in notifs_ref.stream()]

    ann_ref = db.collection("announcements").order_by("time", direction=firestore.Query.DESCENDING).limit(10)
    announcements = [{"id": d.id, "is_announcement": True, **d.to_dict()} for d in ann_ref.stream()]

    all_notifs = notifs + announcements
    unread_count = sum(1 for n in notifs if not n.get("read"))

    return jsonify({"notifications": all_notifs, "unread": unread_count})

@app.route("/api/notifications/<notif_id>/read", methods=["POST"])
@login_required
def api_mark_read(notif_id):
    uid = session['uid']
    db.collection("users").document(uid).collection("notifications").document(notif_id).update({"read": True})
    return jsonify({"ok": True})

# ==================== FEEDBACK ====================

@app.route("/api/feedback", methods=["POST"])
@login_required
def api_feedback():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty feedback"}), 400

    db.collection("feedback").add({
        "uid": session['uid'],
        "email": session['email'],
        "name": session['name'],
        "message": message,
        "time": firestore.SERVER_TIMESTAMP,
        "read": False
    })
    return jsonify({"ok": True})

# ==================== ADMIN API ====================

@app.route("/api/admin/users")
@login_required
@admin_required
def api_admin_users():
    users_ref = db.collection("users").stream()
    users = []
    for doc in users_ref:
        d = doc.to_dict()
        last_active = d.get("last_active")
        inactive = False
        if last_active:
            try:
                delta = datetime.utcnow() - last_active.replace(tzinfo=None)
                inactive = delta.days > 30
            except Exception:
                pass
        users.append({
            "uid": doc.id,
            "name": d.get("name", "Unknown"),
            "email": d.get("email", ""),
            "is_admin": d.get("is_admin", False),
            "suspended": d.get("suspended", False),
            "inactive": inactive,
            "last_active": last_active.strftime("%Y-%m-%d %H:%M") if last_active else "Never"
        })
    return jsonify({"users": users})

@app.route("/api/admin/users/<uid>/suspend", methods=["POST"])
@login_required
@admin_required
def api_admin_suspend(uid):
    db.collection("users").document(uid).update({"suspended": True})
    user_doc = db.collection("users").document(uid).get().to_dict()
    log_activity("🚫", f"User suspended: {user_doc.get('email', uid)}", session['email'])
    return jsonify({"ok": True, "message": "User suspended."})

@app.route("/api/admin/users/<uid>/unsuspend", methods=["POST"])
@login_required
@admin_required
def api_admin_unsuspend(uid):
    db.collection("users").document(uid).update({"suspended": False})
    user_doc = db.collection("users").document(uid).get().to_dict()
    log_activity("✅", f"User re-enabled: {user_doc.get('email', uid)}", session['email'])
    return jsonify({"ok": True, "message": "User re-enabled."})

@app.route("/api/admin/users/<uid>/remind", methods=["POST"])
@login_required
@admin_required
def api_admin_remind(uid):
    data = request.get_json() or {}
    msg = data.get("message", "The admin has sent you a reminder to check out the AI Dashboard!")
    send_notification(uid, "📬 Admin Reminder", msg, "reminder")
    user_doc = db.collection("users").document(uid).get().to_dict()
    log_activity("📧", f"Reminder sent to: {user_doc.get('email', uid)}", session['email'])
    return jsonify({"ok": True, "message": "Reminder sent."})

@app.route("/api/admin/announce", methods=["POST"])
@login_required
@admin_required
def api_admin_announce():
    data = request.get_json() or {}
    title = data.get("title", "Announcement").strip()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    send_global_announcement(title, message, session['email'])
    return jsonify({"ok": True, "message": "Announcement sent to all users."})

@app.route("/api/admin/activity")
@login_required
@admin_required
def api_admin_activity():
    logs = db.collection("activity_log").order_by("time", direction=firestore.Query.DESCENDING).limit(50).stream()
    result = []
    for doc in logs:
        d = doc.to_dict()
        t = d.get("time")
        result.append({
            "icon": d.get("icon", "📋"),
            "text": d.get("text", ""),
            "user": d.get("user", ""),
            "time": t.strftime("%Y-%m-%d %H:%M:%S") if t else ""
        })
    return jsonify({"activities": result})

@app.route("/api/admin/feedback")
@login_required
@admin_required
def api_admin_feedback():
    feedbacks = db.collection("feedback").order_by("time", direction=firestore.Query.DESCENDING).limit(30).stream()
    result = []
    for doc in feedbacks:
        d = doc.to_dict()
        t = d.get("time")
        result.append({
            "id": doc.id,
            "name": d.get("name", "Unknown"),
            "email": d.get("email", ""),
            "message": d.get("message", ""),
            "read": d.get("read", False),
            "time": t.strftime("%Y-%m-%d %H:%M") if t else ""
        })
    return jsonify({"feedback": result})

@app.route("/api/admin/tool-usage")
@login_required
@admin_required
def api_admin_tool_usage():
    result = []
    for key in TOOL_USAGE_KEYS:
        doc = db.collection("tool_usage").document(key).get()
        count = doc.to_dict().get("count", 0) if doc.exists else 0
        result.append({**TOOL_META[key], "key": key, "count": count})
    total = sum(t["count"] for t in result)
    for t in result:
        t["percentage"] = round((t["count"] / total * 100) if total > 0 else 0)
    return jsonify({"tools": result, "total": total})

@app.route("/api/admin/stats")
@login_required
@admin_required
def api_admin_stats():
    users = list(db.collection("users").stream())
    total = len(users)
    inactive = 0
    for doc in users:
        d = doc.to_dict()
        la = d.get("last_active")
        if la:
            try:
                delta = datetime.utcnow() - la.replace(tzinfo=None)
                if delta.days > 30:
                    inactive += 1
            except Exception:
                pass
    tool_docs = db.collection("tool_usage").stream()
    total_uses = sum(d.to_dict().get("count", 0) for d in tool_docs)
    return jsonify({"total_users": total, "inactive_count": inactive, "total_tool_uses": total_uses})

# ==================== AI TOOL ROUTES ====================

@app.route("/api/sentiment", methods=["POST"])
@login_required
def api_sentiment():
    reviews = []
    if 'file' in request.files and request.files['file'].filename:
        try:
            path = save_upload(request.files['file'], allowed={"csv"})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        df = pd.read_csv(path, header=None)
        reviews = df.iloc[:,0].tolist()
    elif request.form.get("review"):
        reviews = [request.form["review"]]

    results, labels, values = [], [], []
    for review in reviews:
        s = SnowNLP(str(review))
        score = round(s.sentiments * 100, 1)
        label = "😊 Positive" if score > 60 else ("😐 Neutral" if score > 40 else "😞 Negative")
        results.append(f"{label} ({score}%) — {str(review)[:40]}...")
        labels.append(str(review)[:20])
        values.append(score)

    # Convert numpy types to Python floats for JSON serialization
    values = [float(v) for v in values]

    increment_tool_usage("sentiment")
    log_activity("💬", f"Sentiment analysis by {session.get('email','Unknown')}", session.get('email'))
    return jsonify({"result": "\n".join(results), "chart": {"labels": labels, "values": values}})

# ------------------------------------------------------------
# KEYWORD EXTRACTION – Professional TF‑IDF with fallback
# ------------------------------------------------------------
@app.route("/api/keywords", methods=["POST"])
@login_required
def api_keywords():
    n = int(request.form.get("n", 10))
    manual_category = request.form.get("category", "").strip().lower()
    combined_text = ""

    # 1. File upload handling (CSV/Excel only)
    if 'file' in request.files and request.files['file'].filename:
        try:
            file = request.files['file']
            ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
            if ext in ("xlsx", "xls"):
                path = save_upload(file, allowed={"xlsx", "xls"})
                df = pd.read_excel(path)
            elif ext == "csv":
                path = save_upload(file, allowed={"csv"})
                df = pd.read_csv(path)
            else:
                return jsonify({"error": "Unsupported file type. Upload CSV or Excel."}), 400
        except Exception as e:
            return jsonify({"error": f"File processing error: {str(e)}"}), 400

        # Find the text column
        text_col = None
        for col in df.columns:
            if col.strip().lower() == 'text':
                text_col = col
                break
        if text_col is None:
            text_col = df.columns[0]

        texts = df[text_col].dropna().astype(str).tolist()
        texts = [t.strip() for t in texts if t.strip() and t.strip().lower() != "nan"]
        if not texts:
            return jsonify({"error": f"No valid text found in column '{text_col}'"}), 400
        combined_text = " ".join(texts)
    else:
        combined_text = request.form.get("text", "").strip()
        if not combined_text:
            return jsonify({"error": "Please enter text or upload a file."}), 400

    # 2. Category detection (manual override or auto‑detect)
    if manual_category and manual_category in CATEGORY_KEYWORDS:
        category = manual_category
    else:
        category = detect_category(combined_text)

    # 3. TF‑IDF keyword extraction with custom stop words
    original_stop_words = jieba.analyse.default_tfidf.stop_words.copy()
    try:
        # Add our custom stop words to the existing set
        jieba.analyse.default_tfidf.stop_words.update(ECOMMERCE_STOPWORDS)

        keywords = jieba.analyse.extract_tags(
            combined_text,
            topK=n,
            withWeight=True
        )

        # Fallback: if nothing found, try without stop words
        if not keywords:
            jieba.analyse.default_tfidf.stop_words = set()
            keywords = jieba.analyse.extract_tags(
                combined_text,
                topK=n,
                withWeight=True
            )
    finally:
        # Restore original stop words
        jieba.analyse.default_tfidf.stop_words = original_stop_words

    if not keywords:
        return jsonify({"result": "No keywords found.", "chart": None, "category": category}), 200

    lines  = [f"• {w} ({round(s, 3)})" for w, s in keywords]
    labels = [w for w, _ in keywords]
    values = [round(s * 100, 1) for _, s in keywords]

    # Convert numpy types to Python floats for JSON serialization
    values = [float(v) for v in values]

    increment_tool_usage("keywords")
    log_activity("🔍", f"Keywords extracted ({category}) by {session.get('email')}", session.get('email'))

    return jsonify({
        "result": f"📂 Category: {category.title()}\n" + "\n".join(lines),
        "chart":  {"labels": labels, "values": values},
        "stats":  {
            "Keywords Found": len(keywords),
            "Text Length": len(combined_text),
            "Category": category.title()
        },
    })

@app.route("/api/ocr", methods=["POST"])
@login_required
def api_ocr():
    try:
        path = save_upload(request.files["image"], allowed={"png","jpg","jpeg","gif","webp"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    img = Image.open(path)
    text = pytesseract.image_to_string(img, lang="chi_sim+eng")
    increment_tool_usage("ocr")
    log_activity("📄", f"OCR scan by {session.get('email','Unknown')}", session.get('email'))
    return jsonify({"result": text or "No text detected.", "chart": None})

@app.route("/api/churn", methods=["POST"])
@login_required
def api_churn():
    # Lazy load churn model
    churn_scaler, churn_model = _get_churn_model()

    if 'file' in request.files and request.files['file'].filename:
        try:
            path = save_upload(request.files['file'], allowed={"csv", "xlsx", "xls"})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        ext = path.rsplit(".", 1)[1].lower()
        df = pd.read_excel(path) if ext in ("xlsx", "xls") else pd.read_csv(path)

        missing = set(_CHURN_FEATURES) - set(df.columns)
        if missing:
            return jsonify({"error": f"Missing columns: {sorted(missing)}. Required: {_CHURN_FEATURES}"}), 400

        df = df[_CHURN_FEATURES].copy()
        for col in _CHURN_FEATURES:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna()

        if df.empty:
            return jsonify({"error": "No valid rows found after cleaning."}), 400

        churn_scaler = StandardScaler()
        X_scaled = churn_scaler.fit_transform(df)

        probs = churn_model.predict_proba(X_scaled)
        preds = churn_model.predict(X_scaled)

        churn_prob_avg   = round(float(probs[:, 1].mean() * 100), 1)
        retain_prob_avg  = round(100 - churn_prob_avg, 1)
        avg_spend        = round(float(df["total_spent"].mean()), 2)
        high_risk_count  = int((preds == 1).sum())
        low_risk_count   = int((preds == 0).sum())
        total_customers  = len(df)

        result = (
            f"📊 Churn Analysis — {total_customers} customers\n"
            f"{'─'*40}\n"
            f"🚨 High Churn Risk:      {high_risk_count} customers ({round(high_risk_count/total_customers*100)}%)\n"
            f"✅ Low Churn Risk:       {low_risk_count} customers ({round(low_risk_count/total_customers*100)}%)\n\n"
            f"Average Churn Probability:   {churn_prob_avg}%\n"
            f"Average Retention Rate:      {retain_prob_avg}%\n"
            f"Average Spend per Customer:  ¥{avg_spend:,.2f}"
        )
        stats = {
            "Total Customers": total_customers,
            "High Risk":       f"{high_risk_count} ({round(high_risk_count/total_customers*100)}%)",
            "Avg Churn Prob":  f"{churn_prob_avg}%",
            "Avg Spend":       f"¥{avg_spend:,.2f}",
        }
        chart = {
            "labels": ["Churn Risk", "Retention"],
            "values": [churn_prob_avg, retain_prob_avg],
        }
    else:
        months    = float(request.form.get("months",    6))
        purchases = float(request.form.get("purchases", 10))
        spent     = float(request.form.get("spent",     500))
        days      = float(request.form.get("days",      30))

        row = pd.DataFrame([[months, purchases, spent, days]], columns=_CHURN_FEATURES)
        row_scaled = churn_scaler.transform(row)
        pred = churn_model.predict(row_scaled)[0]
        prob = churn_model.predict_proba(row_scaled)[0]

        churn_pct   = round(prob[1] * 100)
        retain_pct  = round(prob[0] * 100)
        result = (
            f"{'🚨 HIGH CHURN RISK' if pred == 1 else '✅ LOW CHURN RISK'}\n\n"
            f"Churn probability:     {churn_pct}%\n"
            f"Retention probability: {retain_pct}%\n"
            f"Avg spend on file:     ¥{spent:,.2f}"
        )
        stats = {
            "Churn Risk":  f"{churn_pct}%",
            "Retention":   f"{retain_pct}%",
            "Months Active": int(months),
            "Days Inactive": int(days),
        }
        chart = {
            "labels": ["Churn Risk", "Retention"],
            "values": [churn_pct, retain_pct],
        }

    increment_tool_usage("churn")
    log_activity("👥", f"Churn prediction by {session.get('email','Unknown')}", session.get('email'))
    return jsonify({"result": result, "chart": chart, "stats": stats})

@app.route("/api/forecast", methods=["POST"])
@login_required
def api_forecast():
    months = int(request.form.get("months", 3))
    if not ('file' in request.files and request.files['file'].filename):
        return jsonify({"error": "Please upload a CSV or Excel file with your sales data. Required columns: date (YYYY-MM-DD), sales_amount"}), 400
    try:
        file = request.files['file']
        ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
        if ext in ("xlsx", "xls"):
            path = save_upload(file, allowed={"xlsx", "xls"})
            sales_df = pd.read_excel(path)
        elif ext == "csv":
            path = save_upload(file, allowed={"csv"})
            sales_df = pd.read_csv(path)
        else:
            return jsonify({"error": "Unsupported file type. Please upload CSV or Excel (.xlsx/.xls)."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if sales_df.shape[1] < 2:
        return jsonify({"error": "File must have at least 2 columns: date and sales_amount"}), 400
    sales_df = sales_df.iloc[:, :2]
    sales_df.columns = ['ds', 'y']
    try:
        sales_df['ds'] = pd.to_datetime(sales_df['ds'])
    except Exception:
        return jsonify({"error": "Could not parse dates. Make sure column 1 is a date in YYYY-MM-DD format."}), 400
    sales_df['y'] = pd.to_numeric(sales_df['y'], errors='coerce')
    sales_df = sales_df.dropna()
    model = Prophet()
    model.fit(sales_df)
    future = model.make_future_dataframe(periods=months, freq="MS")
    fc = model.predict(future)
    predictions = fc[["ds","yhat"]].tail(months)
    lines, labels, values = [], [], []
    for _, row in predictions.iterrows():
        month = row['ds'].strftime('%B %Y')
        val = round(row['yhat'])
        lines.append(f"{month} → {val} units")
        labels.append(month)
        values.append(val)
    increment_tool_usage("forecast")
    log_activity("📈", f"Sales forecast by {session.get('email','Unknown')}", session.get('email'))
    return jsonify({"result": "Sales Forecast:\n" + "\n".join(lines), "chart": {"labels": labels, "values": values}})

@app.route("/api/recommend", methods=["POST"])
@login_required
def api_recommend():
    ratings_df = None

    if 'file' in request.files and request.files['file'].filename:
        try:
            file = request.files['file']
            ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
            if ext in ("xlsx", "xls"):
                path = save_upload(file, allowed={"xlsx", "xls"})
                ratings_df = pd.read_excel(path)
            elif ext == "csv":
                path = save_upload(file, allowed={"csv"})
                ratings_df = pd.read_csv(path)
            else:
                return jsonify({"error": "Unsupported file type. Please upload CSV or Excel."}), 400
            if ratings_df.shape[1] < 3:
                return jsonify({"error": "File must have 3 columns: user, product, rating"}), 400
            ratings_df = ratings_df.iloc[:, :3]
            ratings_df.columns = ['user', 'product', 'rating']
            ratings_df['rating'] = pd.to_numeric(ratings_df['rating'], errors='coerce')
            ratings_df = ratings_df.dropna()
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    else:
        return jsonify({"error": "Please upload a CSV or Excel file. Required columns: user, product, rating (1–5)"}), 400

    all_users = sorted(ratings_df['user'].unique().tolist())
    user = request.form.get("user", "").strip()
    if not user or user not in all_users:
        user = all_users[0] if all_users else None

    if not user:
        return jsonify({"error": "No valid user found in data."}), 400

    ratings_table = ratings_df.pivot_table(index="user", columns="product", values="rating")
    correlation = ratings_table.T.corr()
    try:
        if user not in correlation.columns:
            return jsonify({"error": f"User '{user}' not found in data."}), 400
        similar_users = correlation[user].dropna().sort_values(ascending=False)
        similar_users = similar_users.drop(user) if user in similar_users.index else similar_users
        already_bought = ratings_table.loc[user].dropna().index.tolist()
        recs = []
        for su in similar_users.index:
            for p in ratings_table.loc[su].dropna().index.tolist():
                if p not in already_bought and p not in recs:
                    recs.append(p)
        result = f"✅ Recommendations for {user}:\n" + "\n".join(f"  • {r}" for r in recs) if recs else f"No new recommendations for {user} — they may have already rated all available products."
        increment_tool_usage("recommend")
        log_activity("🛒", f"Recommendations by {session.get('email','Unknown')}", session.get('email'))
        return jsonify({
            "result": result,
            "chart": {"labels": recs, "values": [5]*len(recs)} if recs else None,
            "all_users": all_users
        })
    except Exception as e:
        return jsonify({"result": f"Error: {str(e)}", "chart": None})

# ------------------------------------------------------------
# FAKE REVIEW DETECTOR – ENHANCED: Linguistic Features + Similarity Filter
# ------------------------------------------------------------
@app.route("/api/fakereview", methods=["POST"])
@login_required
def api_fakereview():
    # Lazy load model
    fakereview_vectorizer, fakereview_model = _get_fakereview_model()

    reviews = []
    sources = []

    # 1. File upload handling (CSV/Excel)
    if 'file' in request.files and request.files['file'].filename:
        try:
            file = request.files['file']
            ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
            if ext in ("xlsx", "xls"):
                path = save_upload(file, allowed={"xlsx", "xls"})
                df = pd.read_excel(path)
            elif ext == "csv":
                path = save_upload(file, allowed={"csv"})
                df = pd.read_csv(path)
            else:
                return jsonify({"error": "Unsupported file type. Upload CSV or Excel."}), 400
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Robust column detection
        text_col = None
        candidates = ["text", "review", "content", "comment", "message"]
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(cand in col_lower for cand in candidates):
                text_col = col
                break
        if text_col is None:
            text_col = df.columns[0]

        for idx, row in df.iterrows():
            try:
                val = str(row[text_col]).strip()
                if val and val.lower() not in ["nan", "none", "null", ""] and len(val) > 5:
                    reviews.append(val)
                    sources.append(f"row_{idx}")
            except:
                continue

    # 2. Single review from form
    elif request.form.get("review"):
        review_text = request.form["review"].strip()
        if len(review_text) > 5:
            reviews = [review_text]
            sources = ["manual_input"]
        else:
            return jsonify({"error": "Review too short (minimum 6 characters)."}), 400

    if not reviews:
        return jsonify({"error": "No valid review text provided."}), 400

    # 3. Similarity filter – mark near‑duplicates
    dup_flags = compute_similarity_flag(reviews, threshold=0.85)
    
    # 4. Feature fusion for each review
    results_list = []
    fake_count = 0
    genuine_count = 0
    sentiment_scores = []
    duplicate_count = sum(dup_flags)

    for idx, review in enumerate(reviews):
        # Compute sentiment
        try:
            s = SnowNLP(review)
            sentiment = s.sentiments
        except:
            sentiment = 0.5
        sentiment_scores.append(sentiment)

        # TF‑IDF vector
        tfidf_vec = fakereview_vectorizer.transform([review])
        
        # Linguistic features
        ling_feats = np.array([extract_linguistic_features(review)])

        # Combine into a single feature vector
        combined = np.hstack([
            tfidf_vec.toarray(),
            np.array([[sentiment]]),
            ling_feats
        ])

        # Predict
        pred = fakereview_model.predict(combined)[0]
        prob = fakereview_model.predict_proba(combined)[0]
        confidence = round(max(prob) * 100, 1)

        preview = review[:50] + "..." if len(review) > 50 else review
        dup_note = " ⚠️ DUPLICATE" if dup_flags[idx] else ""
        
        if pred == 1:
            fake_count += 1
            results_list.append(f"🚨 FAKE ({confidence}% confidence){dup_note}\n    → {preview}")
        else:
            genuine_count += 1
            results_list.append(f"✅ GENUINE ({confidence}% confidence){dup_note}\n    → {preview}")

    total = fake_count + genuine_count
    avg_sentiment = round(sum(sentiment_scores)/len(sentiment_scores), 2) if sentiment_scores else 0.5

    summary = (
        f"🔍 Fake Review Detection — {total} reviews analysed\n"
        f"{'─'*50}\n"
        f"🚨 Fake:    {fake_count} ({round(fake_count/total*100)}%)\n"
        f"✅ Genuine: {genuine_count} ({round(genuine_count/total*100)}%)\n"
        f"🔄 Duplicates flagged: {duplicate_count}\n\n"
        f"📊 Average Sentiment: {avg_sentiment} (0=negative, 1=positive)\n\n"
        f"📝 Detailed Results:\n" +
        "\n".join(f"{i+1}. {r}" for i, r in enumerate(results_list))
    )

    increment_tool_usage("fakereview")
    log_activity("🚨", f"Fake review detection ({total} reviews) by {session.get('email','Unknown')}", session.get('email'))

    return jsonify({
        "result": summary,
        "chart": {"fake": fake_count, "genuine": genuine_count},
        "stats": {
            "Total Reviews": total,
            "Fake": f"{fake_count} ({round(fake_count/total*100)}%)",
            "Genuine": f"{genuine_count} ({round(genuine_count/total*100)}%)",
            "Duplicates": duplicate_count,
            "Avg Sentiment": avg_sentiment,
            "Model": "TF‑IDF + SnowNLP + 5 Linguistic Features",
        }
    })

@app.route("/api/imageclassifier", methods=["POST"])
@login_required
def api_imageclassifier():
    global mobilenet_model, preprocess_input_fn, decode_predictions_fn
    # Lazy-load MobileNetV2 only when this tool is first used
    if mobilenet_model is None:
        print("Loading MobileNetV2...")
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
        mobilenet_model = MobileNetV2(weights='imagenet')
        preprocess_input_fn = preprocess_input
        decode_predictions_fn = decode_predictions
        print("MobileNetV2 loaded!")
    else:
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as preprocess_input_fn
        from tensorflow.keras.applications.mobilenet_v2 import decode_predictions as decode_predictions_fn

    try:
        path = save_upload(request.files["image"], allowed={"png","jpg","jpeg","webp"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    img = Image.open(path).convert('RGB').resize((224, 224))
    img_array = preprocess_input_fn(np.expand_dims(np.array(img), axis=0).astype(np.float32))
    predictions = mobilenet_model.predict(img_array)
    results = decode_predictions_fn(predictions, top=5)[0]

    lines, labels, values = [], [], []
    for i, (_, label, score) in enumerate(results):
        lines.append(f"{i+1}. {label} — {round(score*100,1)}%")
        labels.append(label)
        values.append(round(score*100, 1))

    # Convert numpy types to Python floats for JSON serialization
    values = [float(v) for v in values]

    increment_tool_usage("imageclassifier")
    log_activity("🖼️", f"Image classification by {session.get('email','Unknown')}", session.get('email'))
    return jsonify({"result": "Classification Results:\n" + "\n".join(lines), "chart": {"labels": labels, "values": values}})

@app.route("/api/priceprediction", methods=["POST"])
@login_required
def api_priceprediction():
    # Lazy load price model
    price_model, price_scaler, _category_map, _global_avg_price = _get_price_model()

    category = request.form.get("category", "").strip()
    rating_str = request.form.get("rating", "").strip()
    num_reviews_str = request.form.get("num_reviews", "").strip()
    brand_tier_str = request.form.get("brand_tier", "").strip()

    if category and rating_str and num_reviews_str and brand_tier_str:
        # Validate numeric fields
        try:
            rating = float(rating_str)
            num_reviews = float(num_reviews_str)
            brand_tier = int(brand_tier_str)
        except ValueError:
            return jsonify({"error": "Rating, num_reviews, and brand_tier must be numbers."}), 400

        if not (1 <= rating <= 5):
            return jsonify({"error": "Rating must be between 1 and 5."}), 400
        if num_reviews < 0:
            return jsonify({"error": "Number of reviews cannot be negative."}), 400
        if brand_tier not in (1, 2, 3):
            return jsonify({"error": "Brand tier must be 1, 2, or 3."}), 400

        X, unknown = _prepare_single_prediction(category, rating, num_reviews, brand_tier)
        pred = price_model.predict(X)[0]

        # Use global average for unknown categories
        if unknown:
            pred = _global_avg_price
            note = " ⚠️ Unknown category — using global average price."
        else:
            note = ""

        result_text = (
            f"📦 Product: {category.title()}\n"
            f"   Rating: {rating} ★  ·  Reviews: {int(num_reviews):,}  ·  Brand Tier: {brand_tier}\n"
            f"   → Predicted Price: ¥{pred:,.2f}{note}"
        )

        increment_tool_usage("priceprediction")
        log_activity("💰", f"Price prediction (single) by {session.get('email','Unknown')}", session.get('email'))

        return jsonify({
            "result": result_text,
            "chart": None,
            "stats": {
                "Predicted Price": f"¥{pred:,.0f}",
                "Category": category.title(),
                "Brand Tier": f"Tier {brand_tier}",
                "Rating": f"{rating} ★",
                "Reviews": f"{int(num_reviews):,}",
            }
        })

    # ------------------------------------------------------------------
    # MODE 2: Batch file upload
    # ------------------------------------------------------------------
    if 'file' not in request.files or not request.files['file'].filename:
        return jsonify({
            "error": "Please either fill in all manual fields OR upload a CSV/Excel file.\n\n"
                     "Manual fields required: Category, Rating (1-5), Number of Reviews, Brand Tier (1-3).\n"
                     "File must contain columns: category, rating, num_reviews, brand_tier."
        }), 400

    try:
        file = request.files['file']
        ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
        if ext in ("xlsx", "xls"):
            path = save_upload(file, allowed={"xlsx", "xls"})
            df = pd.read_excel(path)
        elif ext == "csv":
            path = save_upload(file, allowed={"csv"})
            df = pd.read_csv(path)
        else:
            return jsonify({"error": "Unsupported file type. Please upload CSV or Excel (.xlsx/.xls)."}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Validate required columns
    required_cols = {'category', 'rating', 'num_reviews', 'brand_tier'}
    missing = required_cols - set(df.columns)
    if missing:
        return jsonify({
            "error": f"File is missing required columns: {sorted(missing)}.\n"
                     f"Found columns: {list(df.columns)}"
        }), 400

    # Clean and prepare data
    df['category'] = df['category'].astype(str).str.strip().str.lower()
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(3.0).clip(1, 5)
    df['num_reviews'] = pd.to_numeric(df['num_reviews'], errors='coerce').fillna(100).clip(0)
    df['brand_tier'] = pd.to_numeric(df['brand_tier'], errors='coerce').fillna(1).clip(1, 3).astype(int)

    X, unknown_mask = _prepare_batch_prediction(df)
    preds = price_model.predict(X)
    preds[unknown_mask] = _global_avg_price

    df['predicted_price'] = preds

    # Build summary by category
    category_stats = {}
    grouped = df.groupby('category', sort=False)
    lines = []
    labels = []
    values = []

    for cat, group in grouped:
        prices = group['predicted_price']
        avg_price = round(float(prices.mean()), 2)
        count = len(group)
        is_unknown = cat not in _category_map
        unknown_note = " ⚠️ (unknown — global avg)" if is_unknown else ""

        lines.append(
            f"📦 {cat.title()}{unknown_note} ({count} item{'s' if count > 1 else ''})\n"
            f"   Avg Price: ¥{avg_price:,.2f}"
        )
        labels.append(cat.title())
        values.append(avg_price)

        category_stats[cat] = {
            "count": count,
            "average_price": avg_price,
            "min_price": round(float(prices.min()), 2),
            "max_price": round(float(prices.max()), 2),
        }

    total_items = len(df)
    categories_found = len(grouped)
    overall_avg = round(df['predicted_price'].mean(), 2)

    summary = (
        f"✅ Price Prediction Results\n"
        f"   {total_items} items · {categories_found} categor{'ies' if categories_found != 1 else 'y'}\n"
        f"   Overall Average: ¥{overall_avg:,.2f}\n"
        f"{'─'*40}\n"
        + "\n".join(lines)
    )

    increment_tool_usage("priceprediction")
    log_activity("💰", f"Price prediction batch ({total_items} items) by {session.get('email','Unknown')}", session.get('email'))

    return jsonify({
        "result": summary,
        "chart": {"labels": labels, "values": values} if labels else None,
        "stats": {
            "Total Items": total_items,
            "Categories": categories_found,
            "Overall Avg": f"¥{overall_avg:,.0f}",
            "Price Range": f"¥{df['predicted_price'].min():,.0f} – ¥{df['predicted_price'].max():,.0f}",
        },
        "category_stats": category_stats
    })

# ==============================================================
# BERT FINE‑TUNING TEMPLATE (commented out – use for production)
# ==============================================================
# """
# from transformers import BertTokenizer, TFBertForSequenceClassification
# import tensorflow as tf
#
# tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
# model = TFBertForSequenceClassification.from_pretrained('bert-base-chinese', num_labels=2)
#
# def bert_predict(reviews):
#     inputs = tokenizer(reviews, padding=True, truncation=True, return_tensors='tf', max_length=128)
#     outputs = model(inputs)
#     probs = tf.nn.softmax(outputs.logits, axis=-1).numpy()
#     preds = np.argmax(probs, axis=1)
#     return preds, probs
# """

if __name__ == "__main__":
    # Use the PORT environment variable provided by Render or Hugging Face Spaces
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)
