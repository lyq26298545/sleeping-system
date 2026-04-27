from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import joblib
import pandas as pd
import os
import requests
from datetime import datetime

app = Flask(__name__)

# --- 1. 数据库配置 ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://sleep_admin:admin@localhost:3306/health_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- 2. 数据库模型 ---

class User(db.Model):
    """用户信息表：存储微信基本信息与身体档案"""
    __tablename__ = 'users'
    openid = db.Column(db.String(128), primary_key=True)
    nickname = db.Column(db.String(64))
    avatar_url = db.Column(db.String(512))
    age = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    intention = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.now)


class HealthRecord(db.Model):
    """健康打卡记录表：存储每日打卡数据与 AI 分析结果"""
    __tablename__ = 'health_records'
    id = db.Column(db.Integer, primary_key=True)
    # 统一长度为 128，与 User 表 openid 保持一致
    user_id = db.Column(db.String(128), index=True)
    bmi = db.Column(db.Float)
    intention = db.Column(db.String(20))
    # 新增：原始打卡数据
    sleep_duration = db.Column(db.Float)
    steps = db.Column(db.Float)
    # AI 分析结果
    stress_score = db.Column(db.Float)
    predicted_activity = db.Column(db.String(50))
    health_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    activity_value = db.Column(db.Float)


# --- 3. 加载机器学习模型 ---
MODEL_DIR = "model"
try:
    stress_expert = joblib.load(os.path.join(MODEL_DIR, "stress_expert.pkl"))
    motion_expert = joblib.load(os.path.join(MODEL_DIR, "motion_expert.pkl"))
    activity_le = joblib.load(os.path.join(MODEL_DIR, "activity_label_encoder.pkl"))
except Exception as e:
    print(f"模型加载失败，请检查 model 文件夹: {e}")

# --- 4. 微信身份验证工具 ---
WX_APPID = 'wx349d6136dd3e124b'
WX_SECRET = '7197e9724f64e467da6818a4daceb051'


def get_openid_from_weixin(code):
    """通过 code 向微信服务器换取 openid"""
    url = f"https://api.weixin.qq.com/sns/jscode2session?appid={WX_APPID}&secret={WX_SECRET}&js_code={code}&grant_type=authorization_code"
    try:
        res = requests.get(url).json()
        return res.get('openid')
    except Exception as e:
        print(f"微信登录请求失败: {e}")
        return None


# --- 5. 接口路由 ---

@app.route('/api/login', methods=['POST'])
def login():
    """登录/检查注册状态"""
    data = request.json
    code = data.get('code')
    if not code:
        return jsonify({'error': '缺少 code'}), 400

    openid = get_openid_from_weixin(code)
    if not openid:
        return jsonify({'error': '无法获取 openid'}), 500

    user = User.query.filter_by(openid=openid).first()
    if user:
        return jsonify({
            'status': 'registered',
            'openid': openid,
            'userInfo': {
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'age': user.age,
                'gender': user.gender,
                'height': user.height,
                'weight': user.weight,
                'intention': user.intention
            }
        })
    else:
        return jsonify({
            'status': 'new_user',
            'openid': openid
        })


@app.route('/api/register', methods=['POST'])
def register():
    """新用户注册（保存档案）"""
    data = request.json
    new_user = User(
        openid=data.get('openid'),
        nickname=data.get('nickname'),
        avatar_url=data.get('avatar_url'),
        age=data.get('age'),
        gender=data.get('gender'),
        height=data.get('height'),
        weight=data.get('weight'),
        intention=data.get('intention')
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': '注册成功', 'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/predict', methods=['POST'])
def predict():
    """核心：AI 健康诊断并自动存入数据库"""
    try:
        data = request.get_json()
        # 1. 提取参数
        age, gender = int(data['age']), int(data['gender'])
        height, weight = float(data['height']), float(data['weight'])
        intention = data.get('intention', '维持健康')
        sleep_hr = float(data['sleep_duration'])
        steps = float(data.get('steps', 0))
        openid = data.get('openid', 'unknown')
        activity_val = float(data.get('activity_value', 0))

        # 2. 计算 BMI
        bmi = weight / ((height / 100) ** 2)
        bmi_class = 1 if bmi >= 25 else 0

        # 3. 专家模型推理
        input_s = pd.DataFrame([[age, gender, sleep_hr, 7.0, bmi_class]],
                               columns=['Age', 'Gender_Encoded', 'Sleep Duration', 'Quality of Sleep', 'BMI_Class'])
        pred_stress = float(stress_expert.predict(input_s)[0])

        input_m = pd.DataFrame([[age, gender, bmi, 75.0, steps, 6.2, 6.1]],
                               columns=['age', 'gender', 'BMI', 'Applewatch.Heart_LE', 'Applewatch.Steps_LE',
                                        'EntropyApplewatchHeartPerDay_LE', 'EntropyApplewatchStepsPerDay_LE'])
        current_activity = activity_le.inverse_transform([motion_expert.predict(input_m)])[0]

        # 4. 生成建议
        is_exhausted = pred_stress > 7.5 or sleep_hr < 6
        is_highly_active = activity_val >= 100
        is_active_enough = activity_val >= 60

        # 初始化建议映射
        advice_map = {
            '减肥': {
                'normal': f"加权得分 {activity_val:.0f}。燃脂模式开启！",
                'pro': f"BMI {bmi:.1f}。当前能耗比理想，建议维持 LISS 训练。"
            },
            '增肌': {
                'normal': f"动力充足！今天的运动强度（{activity_val:.0f}）非常适合增肌。",
                'pro': f"生理机能处于高峰。建议摄入 20g 蛋白质进行窗口补给。"
            },
            '维持健康': {
                'normal': f"状态很稳！今日综合运动量达标，继续保持。",
                'pro': f"加权负荷适中。建议进行 10 分钟静态拉伸以缓解代谢压力。"
            }
        }

        # 动态逻辑判断
        if is_exhausted:
            res_level = "⚠️ 疲劳警戒"
            adv_n = f"身体电量不足（睡眠{sleep_hr}h），今天咱们先休息，好吗？❤️"
            adv_p = f"【熔断】压力分 {pred_stress:.1f}。即使已完成 {activity_val:.0f} 分运动，也建议立即停止。"
        elif is_highly_active:
            res_level = "🔥 运动达人"
            adv_n = "你今天的表现太棒了！运动量已经非常充分，注意休息。"
            adv_p = f"加权负荷 {activity_val:.1f} 已触发超量补偿机制，建议增加深睡时间。"
        elif is_active_enough:
            res_level = "✅ 状态优良"
            target_advice = advice_map.get(intention, advice_map['维持健康'])
            adv_n, adv_p = target_advice['normal'], target_advice['pro']
        else:
            res_level = "💤 动力稍欠"
            adv_n = f"今天加权运动量仅 {activity_val:.0f} 分，再动一动，哪怕散散步也好。"
            adv_p = "建议利用碎片化时间完成 2000 步走动，以激活基础代谢。"

        # 5. 持久化数据：存入 HealthRecord 表（包含新字段）
        record = HealthRecord(
            user_id=openid,
            bmi=round(bmi, 2),
            intention=intention,
            sleep_duration=sleep_hr,
            steps=steps,
            activity_value=round(activity_val, 2),  # 存入新字段
            stress_score=round(pred_stress, 2),
            predicted_activity=current_activity,
            health_level=res_level
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            "code": 200,
            "data": {
                "stress_score": round(pred_stress, 2),
                "predicted_activity": current_activity,
                "level": res_level,
                "advice_normal": adv_n,
                "advice_pro": adv_p,
                "activity_value": activity_val  # 回传给前端展示
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/api/update_user', methods=['POST'])
def update_user():
    data = request.json
    openid = data.get('openid')
    if not openid:
        return jsonify({'error': '缺少 openid'}), 400

    user = User.query.filter_by(openid=openid).first()
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    # 动态更新字段
    if 'nickname' in data:
        user.nickname = data['nickname']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

    try:
        db.session.commit()
        return jsonify({'status': 'success', 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_history', methods=['GET'])
def get_history():
    openid = request.args.get('openid')
    search_date = request.args.get('date')  # 格式: YYYY-MM-DD

    if not openid:
        return jsonify({'error': '缺少 openid'}), 400

    # 查询该用户的所有记录
    query = HealthRecord.query.filter_by(user_id=openid)

    # 日期搜索逻辑
    if search_date:
        query = query.filter(db.func.date(HealthRecord.created_at) == search_date)

    # 按时间倒序，最新的打卡排在最上面
    records = query.order_by(HealthRecord.created_at.desc()).all()

    history_list = []
    for r in records:
        history_list.append({
            'id': r.id,
            'time': r.created_at.strftime('%H:%M'),  # 仅展示时分
            'date': r.created_at.strftime('%Y-%m-%d'),  # 用于分组或展示日期
            'display_date': r.created_at.strftime('%m月%d日'),
            'sleep_duration': r.sleep_duration,
            'steps': r.steps,
            'stress_score': r.stress_score,
            'activity_value': r.activity_value,
            'bmi': r.bmi,
            'health_level': r.health_level,
            'predicted_activity': r.predicted_activity
        })

    return jsonify(history_list)


# --- 6. 启动程序 ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("数据库表检查/创建完成。")
    app.run(host="0.0.0.0", port=5000, debug=True)