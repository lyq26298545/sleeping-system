Page({
  data: {
    hasUserInfo: false,
    temp_gender: 1,
    temp_intention: '维持健康',
    temp_age: '', temp_height: '', temp_weight: '',
    sleep_duration: '', heart_rate: '',
    showResult: false,
    level: '', advice: '', stress_score: 0, predicted_activity: ''
  },

  onLoad() {
    const profile = wx.getStorageSync('user_profile');
    if (profile) this.setData({ hasUserInfo: true });
  },

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

    // 数值范围严格校验
    if (isNaN(age) || age < 0 || age > 100) return this.showErr('年龄要在0-100之间');
    if (isNaN(h) || h <= 0 || h > 240) return this.showErr('身高要在0-240cm之间');
    if (isNaN(w) || w <= 0 || w > 200) return this.showErr('体重要在0-200kg之间');

    const profile = { age, gender: d.temp_gender, height: h, weight: w, intention: d.temp_intention };
    wx.setStorageSync('user_profile', profile);
    this.setData({ hasUserInfo: true });
  },

  onSubmit() {
    const profile = wx.getStorageSync('user_profile');
    if (!this.data.sleep_duration || !this.data.heart_rate) return this.showErr('请填全今日数据');

    wx.showLoading({ title: 'AI 专家诊断中' });
    wx.request({
      url: 'http://127.0.0.1:5000/predict',
      method: 'POST',
      data: {
        ...profile,
        user_id: "1",//后面要改成真实的id
        sleep_duration: this.data.sleep_duration,
        sleep_quality: 7,
        heart_rate: this.data.heart_rate,
        steps: 5000, hr_entropy: 6.2, steps_entropy: 6.1
      },
      success: (res) => {
        wx.hideLoading();
        if (res.data.code === 200) {
          const r = res.data.data;
          this.setData({ showResult: true, stress_score: r.stress_score, level: r.level, advice: r.advice, predicted_activity: r.predicted_activity });
        }
      }
    });
  },

  showErr(m) { wx.showToast({ title: m, icon: 'none' }); },
  clearProfile() { 
    wx.removeStorageSync('user_profile'); 
    this.setData({ hasUserInfo: false, showResult: false }); 
  }
});