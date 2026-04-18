from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd

# 初始化 Flask
app = Flask(__name__)

# 加载你训练好的模型和标准化工具
model = joblib.load("model/sleep_model.pkl")
sc = joblib.load("model/scaler.pkl")

# 预测接口（小程序访问这个地址）
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # 1. 获取小程序传过来的数据
        data = request.get_json()

        sleep_duration = float(data['sleep_duration'])        # 睡眠时长
        physical_activity = float(data['physical_activity'])  # 身体活动量
        stress_level = float(data['stress_level'])            # 压力等级
        heart_rate = float(data['heart_rate'])                # 心率
        daily_steps = float(data['daily_steps'])              # 每日步数

        # 2. 组装成模型需要的格式
        input_features = [
            sleep_duration,
            physical_activity,
            stress_level,
            heart_rate,
            daily_steps
        ]

        # 3. 标准化 + 预测
        arr = np.array([input_features])
        arr_scaled = sc.transform(arr)
        predict_score = model.predict(arr_scaled)[0]  # 输出睡眠质量分数 4~9

        # 4. 根据分数判定等级 + 建议
        if predict_score >= 9:
            level = "优质睡眠"
            advice = "睡眠质量极佳，继续保持规律作息！"
        elif predict_score >= 7:
            level = "良好睡眠"
            advice = "睡眠质量不错，可适当减少熬夜，保持运动。"
        elif predict_score >= 5:
            level = "一般睡眠"
            advice = "睡眠质量一般，建议减少压力，固定入睡时间。"
        else:
            level = "较差睡眠"
            advice = "睡眠质量较差，请注意作息调整，避免熬夜。"

        # 5. 返回给小程序
        return jsonify({
            "code": 200,
            "sleep_score": int(predict_score),
            "sleep_level": level,
            "advice": advice
        })

    except Exception as e:
        return jsonify({"code": 500, "msg": "预测失败：" + str(e)})

# 健康检查
@app.route('/')
def index():
    return "睡眠质量预测服务已启动！"

# 启动服务
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)