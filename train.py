import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1. 读取数据
df = pd.read_csv("datasets/Sleep_health_and_lifestyle_dataset.csv")

# 2. 特征选择
X = df[['Sleep Duration','Physical Activity Level','Stress Level','Heart Rate','Daily Steps']]
y = df['Quality of Sleep']

# 3. 分层抽样
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# 4. 标准化
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

# 5. 模型（适中复杂度，不极端）
model = RandomForestClassifier(
    n_estimators=50,
    max_depth=4,
    random_state=42
)
model.fit(X_train, y_train)

# 6. 预测
y_pred = model.predict(X_test)

# 7. 输出结果（加 zero_division=0 关闭警告）
print("模型准确率：", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, zero_division=0))  # 关键！

# 8. 混淆矩阵
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d')
plt.xlabel("预测")
plt.ylabel("真实")
plt.show()

# 9. 保存模型
joblib.dump(model, "model/sleep_model.pkl")
joblib.dump(sc, "model/scaler.pkl")