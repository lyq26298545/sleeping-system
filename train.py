import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os

from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import LabelEncoder

# --- 1. 环境准备 ---
model_path='model'
# 加载预处理后的数据
df_aw = pd.read_csv('datasets/data_for_weka_aw_processed.csv')
df_sleep = pd.read_csv('datasets/Sleep_health_and_lifestyle_processed.csv')

# --- 2. 训练：生理压力专家 (基于睡眠数据集) ---
X_s = df_sleep[['Age', 'Gender_Encoded', 'Sleep Duration', 'Quality of Sleep', 'BMI_Class']]
y_s = df_sleep['Stress Level']

stress_model = xgb.XGBRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    objective='reg:squarederror'
)
stress_model.fit(X_s, y_s)

# --- 3. 训练：运动机能专家 (基于运动数据集) ---
# 注意：我们要保存 LabelEncoder，以便以后解码运动类型
features_m = [
    'age', 'gender', 'BMI',
    'Applewatch.Heart_LE',
    'Applewatch.Steps_LE',
    'EntropyApplewatchHeartPerDay_LE',
    'EntropyApplewatchStepsPerDay_LE'
]

X_m = df_aw[features_m]

# 处理目标标签
le = joblib.load(os.path.join(model_path, 'activity_label_encoder.pkl')) # 复用之前的编码器
y_m = le.transform(df_aw['activity_trimmed'])

# --- 3. 重新训练运动专家 ---
# 稍微增加一点深度，让它能消化更多特征
motion_model = xgb.XGBClassifier(
    n_estimators=200,      # 增加树的数量
    learning_rate=0.05,    # 学习率调小，学得更细
    max_depth=6,           # 允许更深的逻辑分支
    objective='multi:softmax'
)
motion_model.fit(X_m, y_m)

# 4
# 检查压力预测模型的误差（数值越小越好）
y_s_pred = stress_model.predict(X_s)
print(f"压力模型平均误差: {np.sqrt(mean_squared_error(y_s, y_s_pred)):.4f}")

# 检查运动模型准确率（1.0 说明完全拟合，0.8 以上算优秀）
y_m_pred = motion_model.predict(X_m)
print(f"运动模型准确率: {accuracy_score(y_m, y_m_pred):.4f}")

# --- 4. 保存模型文件 ---
# 使用 joblib 保存，它对包含大量 numpy 数组的模型（如 XGBoost）效率更高
joblib.dump(stress_model, os.path.join(model_path, 'stress_expert.pkl'))
joblib.dump(motion_model, os.path.join(model_path, 'motion_expert.pkl'))
joblib.dump(le, os.path.join(model_path, 'activity_label_encoder.pkl'))

print(f"✅ 模型训练完成并已保存至 {model_path} 目录下。")
print("文件列表: stress_expert.pkl, motion_expert.pkl, activity_label_encoder.pkl")


# --- 4. 核心逻辑：意向驱动与安全熔断评价系统 ---

def health_advice_system(user_data):
    """
    user_data = {
        'age': 25, 'gender': 1, 'height': 175, 'weight': 70,
        'sleep_hr': 5.5, 'sleep_quality': 4, 'intention': '减肥'
    }
    """
    # 计算实时 BMI
    bmi = user_data['weight'] / ((user_data['height'] / 100) ** 2)
    bmi_class = 1 if bmi >= 25 else 0

    # A. 压力预测
    input_s = pd.DataFrame([[
        user_data['age'], user_data['gender'],
        user_data['sleep_hr'], user_data['sleep_quality'], bmi_class
    ]], columns=['Age', 'Gender_Encoded', 'Sleep Duration', 'Quality of Sleep', 'BMI_Class'])

    pred_stress = stress_model.predict(input_s)[0]

    # B. 安全熔断逻辑 (针对中青年的纠正标准)
    is_exhausted = pred_stress > 7.5 or user_data['sleep_hr'] < 6

    # C. 生成差异化建议
    goal = user_data['intention']
    result = f"--- 智能健康报告 (目标: {goal}) ---\n"
    result += f"预测生理压力指数: {pred_stress:.1f} / 10\n"

    if is_exhausted:
        result += "【🚨 安全熔断触发】评价：身体处于高压状态，睡眠严重不足。\n"
        result += "建议：今日禁止高强度训练。强行运动会抑制脂肪代谢并损伤心脏，请优先补觉。"
    else:
        if goal == '减肥':
            result += f"【🟢 状态优良】评价：你的 BMI 为 {bmi:.1f}，代谢窗口开启。\n"
            result += "建议：维持 40 分钟稳态有氧（快走或慢跑），保持心率平稳。"
        elif goal == '锻炼':
            result += "【🔵 恢复充分】评价：肌肉募集能力处于高峰。\n"
            result += "建议：今日适合进行抗阻力训练或高强度间歇（HIIT）。"
        else:  # 维持健康
            result += "【🟡 状态平稳】评价：生理基准线稳定。\n"
            result += "建议：完成 30 分钟适度活动，保持身体柔韧性与心肺活力。"

    return result


# --- 5. 模拟测试 ---
test_user = {
    'age': 28,
    'gender': 1,
    'height': 180,
    'weight': 85,
    'sleep_hr': 5.5,  # 睡眠不足 6 小时
    'sleep_quality': 4,
    'intention': '减肥'
}

print(health_advice_system(test_user))