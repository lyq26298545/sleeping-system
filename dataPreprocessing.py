import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

# --- 1. 加载数据 ---
df_aw = pd.read_csv('datasets/data_for_weka_aw.csv', index_col=0)
df_sleep = pd.read_csv('datasets/Sleep_health_and_lifestyle_dataset.csv')

# --- 2. 运动数据集 (df_aw) 预处理 ---
# 计算 BMI (体重kg / 身高m^2)
# 1. 强制转换为浮点数，防止整数除法溢出或归零
df_aw = df_aw[(df_aw['height'] > 0) & (df_aw['weight'] > 0)]

# 3. 确保类型为浮点数并计算 BMI
df_aw['BMI'] = df_aw['weight'].astype(float) / ((df_aw['height'].astype(float) / 100.0) ** 2)

# 统一性别编码 (假设 0: Female, 1: Male)
# 原数据中 gender 已经是 0 和 1

# 处理运动标签
le_activity = LabelEncoder()
df_aw['activity_encoded'] = le_activity.fit_transform(df_aw['activity_trimmed'])

# --- 3. 睡眠数据集 (df_sleep) 预处理 ---
# 统一 BMI 类别，使其与运动数据集可比
# 映射：Normal -> 0, Normal Weight -> 0, Overweight -> 1, Obese -> 2
bmi_map = {'Normal': 0, 'Normal Weight': 0, 'Overweight': 1, 'Obese': 2}
df_sleep['BMI_Class'] = df_sleep['BMI Category'].map(bmi_map)

# 统一性别编码
df_sleep['Gender_Encoded'] = df_sleep['Gender'].map({'Male': 1, 'Female': 0})

# 分割血压 (120/80 -> 120, 80)
df_sleep[['Systolic_BP', 'Diastolic_BP']] = df_sleep['Blood Pressure'].str.split('/', expand=True).astype(int)

# --- 4. 特征对齐与归一化 ---
scaler = MinMaxScaler()

# 对步数进行归一化，使不同数据集的“运动量”具有可比性
df_aw['Steps_Scaled'] = scaler.fit_transform(df_aw[['Applewatch.Steps_LE']])
df_sleep['Steps_Scaled'] = scaler.fit_transform(df_sleep[['Daily Steps']])

print("预处理完成：")
print(f"运动数据集特征: {df_aw.columns.tolist()[:5]} ...")
print(f"睡眠数据集特征: {df_sleep.columns.tolist()[:5]} ...")
# 查看最后新增的几个字段
print(f"运动数据集新增字段: {df_aw[['BMI', 'activity_encoded', 'Steps_Scaled']].head()}")
print(f"睡眠数据集新增字段: {df_sleep[['BMI_Class', 'Gender_Encoded', 'Systolic_BP', 'Diastolic_BP', 'Steps_Scaled']].head()}")

# 保存运动数据集
df_aw.to_csv('datasets/data_for_weka_aw_processed.csv', index=True)

# 保存睡眠数据集
df_sleep.to_csv('datasets/Sleep_health_and_lifestyle_processed.csv', index=False)

print("文件已成功保存到磁盘！")
