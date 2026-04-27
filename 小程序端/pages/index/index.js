const SPORT_FACTORS = {
  '走路': 1.0, '瑜伽': 1.2, '骑行': 1.5, '跑步': 1.8, '游泳': 2.0, '健身': 2.2, '球类': 2.5, '爬山': 2.8
};

Page({
  data: {
    openid: '', // 新增：存储微信身份标识
    hasUserInfo: false,
    temp_gender: 1,
    temp_intention: '维持健康',
    intentions: ['维持健康', '减肥', '增肌'],
    temp_age: '', temp_height: '', temp_weight: '',
    sleep_duration: '', daily_steps: '', // 统一变量名
    sportTypes: ['跑步', '健身', '爬山', '游泳', '球类', '骑行', '瑜伽'],
    sportList: [],
    isProMode: false,
    showResult: false,
    level: '', advice_normal: '', advice_pro: '', stress_score: 0, predicted_activity: ''
  },

  onLoad() {
    this.checkLogin(); // 启动即检查登录
  },

  // --- 新增：对接后端登录接口 ---
  checkLogin() {
    wx.showLoading({ title: '加载中...' });
    wx.login({
      success: (res) => {
        if (res.code) {
          wx.request({
            url: 'http://127.0.0.1:5000/api/login', // 请确保后端已启动
            method: 'POST',
            data: { code: res.code },
            success: (loginRes) => {
              wx.hideLoading();
              const { status, openid, userInfo } = loginRes.data;
              this.setData({ openid });
              if (status === 'registered') {
                const fullProfile = {
                  ...userInfo,
                  openid: openid // 强制把 openid 存进去
                };
                // 已注册用户，直接加载档案
                this.setData({
                  hasUserInfo: true,
                  temp_age: userInfo.age,
                  temp_gender: userInfo.gender,
                  temp_height: userInfo.height,
                  temp_weight: userInfo.weight,
                  temp_intention: userInfo.intention
                });
                wx.setStorageSync('user_profile', fullProfile);
              }
            }
          });
        }
      }
    });
  },

  // --- 重构：档案保存对接后端 ---
  saveProfile() {
    const d = this.data;
    if (!d.temp_age || !d.temp_height || !d.temp_weight) {
      return wx.showToast({ title: '请填写完整', icon: 'none' });
    }

    const profile = {
      openid: d.openid, // 关键：带着身份标识
      nickname: "健康用户",
      avatar_url: "",
      age: parseInt(d.temp_age),
      gender: d.temp_gender,
      height: parseFloat(d.temp_height),
      weight: parseFloat(d.temp_weight),
      intention: d.temp_intention
    };

    wx.showLoading({ title: '档案创建中...' });
    wx.request({
      url: 'http://127.0.0.1:5000/api/register',
      method: 'POST',
      data: profile,
      success: (res) => {
        wx.hideLoading();
        this.setData({ hasUserInfo: true });
        wx.setStorageSync('user_profile', profile);
        wx.showToast({ title: '档案已同步' });
      }
    });
  },

  // --- 核心打卡提交 ---
  onSubmit() {
    const d = this.data;
    if (!d.daily_steps || !d.sleep_duration) return this.showErr('请填写完整打卡信息');

    // --- 修改逻辑：计算总加权运动量 ---
    let total_activity_value = 0;

    // 1. 计算专项运动的加权值 (时长 * 系数)
    d.sportList.forEach(item => {
      if (item.type && item.duration) {
        const factor = SPORT_FACTORS[item.type] || 1.0;
        total_activity_value += parseFloat(item.duration) * factor;
      }
    });

    // 2. 累加步数的基础加权值
    // 逻辑：每 1000 步折算为 10 分钟走路，系数取 SPORT_FACTORS['走路']
    if (d.daily_steps) {
      const step_minutes = (parseFloat(d.daily_steps) / 1000) * 10;
      const walk_factor = SPORT_FACTORS['走路'] || 1.0;
      total_activity_value += step_minutes * walk_factor;
    }

    wx.showLoading({ title: 'AI 专家诊断中' });
    wx.request({
      url: 'http://127.0.0.1:5000/predict',
      method: 'POST',
      data: {
        openid: d.openid,
        age: d.temp_age,
        gender: d.temp_gender,
        height: d.temp_height,
        weight: d.temp_weight,
        intention: d.temp_intention,
        steps: d.daily_steps,
        sleep_duration: d.sleep_duration,
        // 【关键】：发送合并后的加权运动量到后端
        activity_value: total_activity_value 
      },
      success: (res) => {
        wx.hideLoading();
        if (res.data.code === 200) {
          const r = res.data.data;
          this.setData({
            showResult: true,
            stress_score: r.stress_score,
            level: r.level,
            advice_normal: r.advice_normal,
            advice_pro: r.advice_pro,
            predicted_activity: r.predicted_activity
          });
        }
      },
      fail: () => {
        wx.hideLoading();
        this.showErr('后端连接失败');
      }
    });
  },
  addSport() {
    const newList = this.data.sportList;
    newList.push({ type: '', duration: '' }); // 默认类型和时长为空
    this.setData({ sportList: newList });
  },

  // 2. 选择运动类型（对应 Picker）
  typeChange(e) {
    const index = e.currentTarget.dataset.index; // 获取是第几行
    const selectedType = this.data.sportTypes[e.detail.value];
    const newList = this.data.sportList;
    newList[index].type = selectedType;
    this.setData({ sportList: newList });
  },

  // 3. 输入运动时长
  durationChange(e) {
    const index = e.currentTarget.dataset.index;
    const val = e.detail.value;
    const newList = this.data.sportList;
    newList[index].duration = val;
    this.setData({ sportList: newList });
  },

  // 4. 删除指定的运动行
  removeSport(e) {
    const index = e.currentTarget.dataset.index;
    const newList = this.data.sportList;
    newList.splice(index, 1);
    this.setData({ sportList: newList });
  },
  // ... 其余辅助方法（toggleMode, addSport等）保持不变 ...
  inputChange(e) { this.setData({ [e.currentTarget.dataset.key]: e.detail.value }); },
  choseGender(e) { this.setData({ temp_gender: parseInt(e.currentTarget.dataset.val) }); },
  choseIntention(e) { this.setData({ temp_intention: e.currentTarget.dataset.val }); },
  toggleMode(e) { this.setData({ isProMode: e.currentTarget.dataset.mode === 'pro' }); },
  showErr(m) { wx.showToast({ title: m, icon: 'none' }); },
  clearProfile() {
    wx.showModal({
      title: '重置', content: '确定清除数据吗？',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorageSync();
          this.setData({ hasUserInfo: false, showResult: false });
        }
      }
    });
  }
});