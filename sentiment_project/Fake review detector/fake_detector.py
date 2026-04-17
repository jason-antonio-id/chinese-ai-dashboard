import pandas as pd
import jieba
from snownlp import SnowNLP

df = pd.read_csv("reviews_fake.csv")

df['word_count'] = df['review'].apply(lambda x: len(jieba.lcut(x)))
df['sentiment'] = df['review'].apply(lambda x: SnowNLP(x).sentiments)

product_words = ['手机', '屏幕', '电池', '拍照', '充电', '续航', '运行', '速度', '外壳', '内存']

def count_product_words(text):
    words = jieba.lcut(text)
    count = 0
    for word in words:
        if word in product_words:
            count += 1
    return count

df['product_word_count'] = df['review'].apply(count_product_words)  # ← only once!

# NEW RULES with 3 parameters
def detect_fake(word_count, sentiment, product_word_count):
    if word_count <= 2: 
        return 1
    elif word_count <= 4 and sentiment >0.9:
        return 1
    elif word_count <= 6 and sentiment >0.95 and product_word_count == 0:
        return 1
    elif sentiment < 0.3:
        return 0        
    else:
        return 0


# Pass all 3 features!
df['predicted'] = df.apply(lambda row: detect_fake(row['word_count'], row['sentiment'], row['product_word_count']), axis=1)

print("===== FAKE REVIEW DETECTOR RESULTS =====\n")

for i, row in df.iterrows():
    status = "✅ CORRECT" if row['is_fake'] == row['predicted'] else "❌ WRONG"
    fake_label = "FAKE" if row['predicted'] == 1 else "GENUINE"
    print(f"{i+1}. {row['review'][:20]}... → {fake_label} ({status})")

print(f"\nAccuracy: {(df['is_fake'] == df['predicted']).sum()}/{len(df)} = {(df['is_fake'] == df['predicted']).mean():.0%}")