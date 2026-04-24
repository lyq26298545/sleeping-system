from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import joblib
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

# --- 数据库配置 [cite: 1, 10] ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sleep_admin:admin@localhost:3306/health_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- 数据库模型 [cite: 1, 2] ---
class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True)
    bmi = db.Column(db.Float)
    intention = db.Column(db.String(20))
    stress_score = db.Column(db.Float)
    predicted_activity = db.Column(db.String(50))
    health_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)


# --- 加载模型组件 [cite: 1, 3] ---
MODEL_DIR = "model"
stress_expert = joblib.load(os.path.join(MODEL_DIR, "stress_expert.pkl"))
motion_expert = joblib.load(os.path.join(MODEL_DIR, "motion_expert.pkl"))
activity_le = joblib.load(os.path.join(MODEL_DIR, "activity_label_encoder.pkl"))


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        # 提取参数 [cite: 1, 4]
        age, gender = int(data['age']), int(data['gender'])
        height, weight = float(data['height']), float(data['weight'])
        intention = data.get('intention', '维持健康')
        sleep_hr = float(data['sleep_duration'])
        steps = float(data.get('steps', 0))

        # 计算 BMI [cite: 1, 4]
        bmi = weight / ((height / 100) ** 2)
        bmi_class = 1 if bmi >= 25 else 0

        # 专家模型推理 [cite: 1, 4, 5]
        input_s = pd.DataFrame([[age, gender, sleep_hr, 7.0, bmi_class]],
                               columns=['Age', 'Gender_Encoded', 'Sleep Duration', 'Quality of Sleep', 'BMI_Class'])
        pred_stress = float(stress_expert.predict(input_s)[0])

        input_m = pd.DataFrame([[age, gender, bmi, 75.0, steps, 6.2, 6.1]],
                               columns=['age', 'gender', 'BMI', 'Applewatch.Heart_LE', 'Applewatch.Steps_LE',
                                        'EntropyApplewatchHeartPerDay_LE', 'EntropyApplewatchStepsPerDay_LE'])
        current_activity = activity_le.inverse_transform([motion_expert.predict(input_m)])[0]

        # --- 核心：多意图建议生成逻辑 ---
        is_exhausted = pred_stress > 7.5 or sleep_hr < 6
        res_level = "⚠️ 疲劳警戒" if is_exhausted else "状态优良"

        advice_map = {
            '减肥': {
                'normal': f"燃脂模式开启！再坚持40分钟脂肪就开始撤退啦！🔥",
                'pro': f"BMI {bmi:.1f}。建议维持40分钟中低强度恒定功率有氧（LISS），确保脂质氧化效率最大化。"
            },
            '增肌': {
                'normal': f"现在的状态很适合举铁！去健身房挑战下重量吧！💪",
                'pro': f"生理机能处于高峰。建议进行高负荷抗阻训练，注意离心收缩控制，促进肌纤维肥大。"
            },
            '维持健康': {
                'normal': f"状态很稳！继续保持,每天进步一点点！✨",
                'pro': f"生理指标平稳。建议完成30分钟功能性训练，维持心肺耐力与关节柔韧性。"
            }
        }

        # 获取对应意图的建议（若无匹配则使用维持健康）
        target_advice = advice_map.get(intention, advice_map['维持健康'])

        if is_exhausted:
            adv_n = f"身体电量不足（睡眠{sleep_hr}h），今天咱们先休息，好吗？❤️"
            adv_p = f"【熔断】压力值过高。强行运动将诱发过度训练综合征（OTS），建议强制静养。"
        else:
            adv_n, adv_p = target_advice['normal'], target_advice['pro']

        # 存储并返回 [cite: 1, 7]
        return jsonify({
            "code": 200,
            "data": {
                "stress_score": round(pred_stress, 2),
                "predicted_activity": current_activity,
                "level": res_level,
                "advice_normal": adv_n,
                "advice_pro": adv_p
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)