from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy  # 新增
import joblib
import pandas as pd
import numpy as np
import os
from datetime import datetime  # 新增

app = Flask(__name__)

# --- 数据库配置 (新增) ---
# 格式: mysql+pymysql://用户名:密码@IP地址:端口/数据库名
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Hg123456@localhost:3306/health_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 定义数据库模型 (新增) ---
class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    id = db.Column(db.Integer, primary_key=True)
    # 档案数据
    user_id = db.Column(db.String(64), index=True)
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    bmi = db.Column(db.Float)
    intention = db.Column(db.String(20))
    # 输入指标
    sleep_duration = db.Column(db.Float)
    heart_rate = db.Column(db.Integer)
    # AI 诊断结果
    stress_score = db.Column(db.Float)
    predicted_activity = db.Column(db.String(50))
    health_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

# 自动创建数据库表
with app.app_context():
    db.create_all()

# --- 1. 加载所有“专家”组件 ---
MODEL_DIR = "model"
stress_expert = joblib.load(os.path.join(MODEL_DIR, "stress_expert.pkl"))
motion_expert = joblib.load(os.path.join(MODEL_DIR, "motion_expert.pkl"))
activity_le = joblib.load(os.path.join(MODEL_DIR, "activity_label_encoder.pkl"))


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # 获取小程序传来的 JSON 数据
        data = request.get_json()
        user_id = data.get('user_id', 'unknown_user')
        # 解析基础数据
        age = int(data['age'])
        gender = int(data['gender'])
        height = float(data['height'])
        weight = float(data['weight'])
        intention = data.get('intention', '维持健康')

        # 解析睡眠与运动数据
        sleep_hr = float(data['sleep_duration'])
        sleep_quality = float(data.get('sleep_quality', 7)) # 默认值防止缺失
        heart_rate = float(data['heart_rate'])
        steps = float(data.get('steps', 5000))
        hr_entropy = float(data.get('hr_entropy', 6.2))
        steps_entropy = float(data.get('steps_entropy', 6.1))

        # --- 2. 预处理 ---
        bmi = weight / ((height / 100) ** 2)
        bmi_class = 1 if bmi >= 25 else 0

        # --- 3. 专家一：生理压力评估 ---
        input_s = pd.DataFrame([[
            age, gender, sleep_hr, sleep_quality, bmi_class
        ]], columns=['Age', 'Gender_Encoded', 'Sleep Duration', 'Quality of Sleep', 'BMI_Class'])
        pred_stress = float(stress_expert.predict(input_s)[0])

        # --- 4. 专家二：运动表现识别 ---
        input_m = pd.DataFrame([[
            age, gender, bmi, heart_rate, steps, hr_entropy, steps_entropy
        ]], columns=[
            'age', 'gender', 'BMI', 'Applewatch.Heart_LE',
            'Applewatch.Steps_LE', 'EntropyApplewatchHeartPerDay_LE',
            'EntropyApplewatchStepsPerDay_LE'
        ])
        activity_idx = motion_expert.predict(input_m)[0]
        current_activity = activity_le.inverse_transform([activity_idx])[0]

        # --- 5. 核心逻辑引擎 ---
        is_exhausted = pred_stress > 7.5 or sleep_hr < 6
        res_level = "正常"
        res_advice = ""

        if is_exhausted:
            res_level = "⚠️ 疲劳警戒"
            res_advice = f"检测到你正处于高应激态（压力:{pred_stress:.1f}）。虽目标是{intention}，但强行运动会损伤身体，建议今日休息补觉。"
        else:
            if intention == "减肥":
                res_advice = f"当前判定为{current_activity}。BMI:{bmi:.1f}，处于高效燃脂区，建议保持心率稳定，坚持40分钟。"
            elif intention == "锻炼":
                res_advice = f"状态良好。当前判定为{current_activity}，适合增加阻力或速度，挑战肌肉耐力。"
            else:
                res_advice = f"状态平稳。今日建议完成基础步数目标，保持身体柔韧性。"

        # --- 数据库存储逻辑 (新增) ---
        new_record = HealthRecord(
            user_id=user_id,age=age, gender=gender, height=height, weight=weight,
            bmi=round(bmi, 2), intention=intention,
            sleep_duration=sleep_hr, heart_rate=int(heart_rate),
            stress_score=round(pred_stress, 2),
            predicted_activity=current_activity,
            health_level=res_level
        )
        db.session.add(new_record)
        db.session.commit()

        # --- 6. 返回结果 ---
        return jsonify({
            "code": 200,
            "data": {
                "stress_score": round(pred_stress, 2),
                "predicted_activity": current_activity,
                "bmi": round(bmi, 2),
                "level": res_level,
                "advice": res_advice
            }
        })

    except Exception as e:
        db.session.rollback() # 发生错误时回滚，保证数据库安全
        return jsonify({"code": 500, "msg": f"系统分析失败: {str(e)}"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)