// index.js

// 运动强度系数表（保留原有逻辑）
const SPORT_FACTORS = {
  '走路': 1.0,
  '瑜伽': 1.2,
  '骑行': 1.5,
  '跑步': 1.8,
  '游泳': 2.0,
  '健身': 2.2,
  '球类': 2.5,
  '爬山': 2.8
};

Page({
  data: {
    hasUserInfo: false,
    temp_gender: 1,
    temp_intention: '维持健康',
    // 扩展意图列表，确保前端有对应的选择逻辑
    intentions: ['维持健康', '减肥', '增肌'],
    temp_age: '', temp_height: '', temp_weight: '',
    sleep_duration: '', heart_rate: '',
    sportTypes: ['跑步', '健身', '爬山', '游泳', '球类', '骑行', '瑜伽'],
    sportList: [], 
    isProMode: false, // 切换普通/专家模式的状态
    showResult: false,
    // 结果接收变量
    level: '', 
    advice_normal: '', // 对应后端的普通建议
    advice_pro: '',    // 对应后端的专家建议
    stress_score: 0, 
    predicted_activity: ''
  },

  onLoad() {
    const profile = wx.getStorageSync('user_profile');
    if (profile) this.setData({ hasUserInfo: true });
  },

  // --- 模式切换逻辑 ---
  toggleMode(e) {
    const mode = e.currentTarget.dataset.mode === 'pro';
    this.setData({ isProMode: mode });
  },

  // --- 运动列表管理（保留原有逻辑） ---
  addSport() {
    let list = this.data.sportList;
    list.push({ type: '跑步', duration: '' });
    this.setData({ sportList: list });
  },

  removeSport(e) {
    let index = e.currentTarget.dataset.index;
    let list = this.data.sportList;
    list.splice(index, 1);
    this.setData({ sportList: list });
  },

  typeChange(e) {
    let { index } = e.currentTarget.dataset;
    let val = this.data.sportTypes[e.detail.value];
    let list = this.data.sportList;
    list[index].type = val;
    this.setData({ sportList: list });
  },

  durationChange(e) {
    let { index } = e.currentTarget.dataset;
    let list = this.data.sportList;
    list[index].duration = e.detail.value;
    this.setData({ sportList: list });
  },

  // --- 基础表单处理 ---
  inputChange(e) {
    this.setData({ [e.currentTarget.dataset.key]: e.detail.value });
  },

  choseGender(e) {
    this.setData({ temp_gender: parseInt(e.currentTarget.dataset.val) });
  },

  choseIntention(e) {
    this.setData({ temp_intention: e.currentTarget.dataset.val });
  },

  saveProfile() {
    const d = this.data;
    const age = parseInt(d.temp_age);
    const h = parseFloat(d.temp_height);
    const w = parseFloat(d.temp_weight);

    if (isNaN(age) || age < 0 || age > 100) return this.showErr('年龄要在0-100之间');
    if (isNaN(h) || h <= 0 || h > 240) return this.showErr('身高要在0-240cm之间');
    if (isNaN(w) || w <= 0 || w > 200) return this.showErr('体重要在0-200kg之间');

    const profile = { age, gender: d.temp_gender, height: h, weight: w, intention: d.temp_intention };
    wx.setStorageSync('user_profile', profile);
    this.setData({ hasUserInfo: true });
  },

  // --- 核心提交逻辑 ---
  onSubmit() {
    const profile = wx.getStorageSync('user_profile');
    const { daily_steps, sportList, sleep_duration, heart_rate } = this.data;
  
    if (!daily_steps) return this.showErr('请输入昨日总步数');
    if (!sleep_duration) return this.showErr('请输入昨日睡眠时长');
  
    // 2. 核心加权计算（完全保留你的逻辑）
    let totalActivity = parseFloat(daily_steps) / 1000; 
    sportList.forEach(item => {
      const factor = SPORT_FACTORS[item.type] || 1.0;
      const duration = parseFloat(item.duration) || 0; 
      totalActivity += (duration / 10) * factor;
    });
    totalActivity = parseFloat(totalActivity.toFixed(1));
  
    console.log('汇总后的活动量：', totalActivity);
  
    wx.showLoading({ title: 'AI 专家诊断中' });
    wx.request({
      url: 'http://127.0.0.1:5000/predict',
      method: 'POST',
      data: {
        ...profile,
        user_id: "1", // 后续可改为真实用户ID
        steps: daily_steps,
        physical_activity: totalActivity, 
        sleep_duration: sleep_duration,
        heart_rate: heart_rate || 70,
        sport_count: sportList.length
      },
      success: (res) => {
        wx.hideLoading();
        console.log("后端返回数据对象:", res.data.data);
        if (res.data.code === 200) {
          const r = res.data.data;
          this.setData({ 
            showResult: true, 
            stress_score: r.stress_score, 
            level: r.level, 
            // 接收后端返回的双模建议
            advice_normal: r.advice_normal, 
            advice_pro: r.advice_pro, 
            predicted_activity: r.predicted_activity 
          });
        }
      },
      fail: () => {
        wx.hideLoading();
        this.showErr('服务器连接失败');
      }
    });
  },

  showErr(m) { wx.showToast({ title: m, icon: 'none' }); },
  
  clearProfile() {
    wx.showModal({
      title: '提示',
      content: '确定要重置档案吗？现有的个人信息将被清空。',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('user_profile');
          this.setData({
            hasUserInfo: false,    // 切回登记态
            showResult: false,     // 隐藏结果
            sportList: [],         // 清空运动列表
            temp_age: '', 
            temp_height: '', 
            temp_weight: ''
          });
          wx.showToast({ title: '已重置', icon: 'success' });
        }
      }
    });
  },
  
  // 修改 saveProfile 确保保存后切换状态
  saveProfile() {
    const d = this.data;
    if (!d.temp_age || !d.temp_height || !d.temp_weight) {
      return wx.showToast({ title: '请填写完整', icon: 'none' });
    }
    const profile = {
      age: d.temp_age,
      gender: d.temp_gender,
      height: d.temp_height,
      weight: d.temp_weight,
      intention: d.temp_intention
    };
    wx.setStorageSync('user_profile', profile);
    this.setData({ hasUserInfo: true }); // 关键：切到打卡态
    wx.showToast({ title: '档案已创建', icon: 'success' });
  }
});