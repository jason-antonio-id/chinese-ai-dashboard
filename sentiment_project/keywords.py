import jieba
from sklearn.feature_extraction.text import TfidfVectorizer

texts = [
    "这款手机性能强大，电池续航时间长，拍照效果非常好",
    "手机屏幕很大，运行速度快，价格实惠",
    "电池容量大，充电速度快，手机很轻薄"
]


def tokenize (text):
    return ' '.join(jieba.cut(text))

tokenized = [tokenize(t) for t in texts]

vectorizer = TfidfVectorizer()
vectorizer.fit_transform(tokenized)

scores = zip (vectorizer.get_feature_names_out(), vectorizer.idf_)
sorted_scores = sorted(scores, key=lambda x : x[1])

print ("Top keywords:")
for word, score in sorted_scores [:5]:
    print(f"{word} → score: {round(score, 2)}")