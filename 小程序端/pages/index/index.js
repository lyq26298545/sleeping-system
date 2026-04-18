// index.js
Page({
  data: {
    sleep_duration: '',
    physical_activity: '',
    stress_level: '',
    heart_rate: '',
    daily_steps: '',
    showResult: false,
    sleep_score: 0,
    sleep_level: '',
    advice: ''
  },

  // 监听输入
  sleep_duration(e){ this.setData({sleep_duration:e.detail.value}) },
  physical_activity(e){ this.setData({physical_activity:e.detail.value}) },
  stress_level(e){ this.setData({stress_level:e.detail.value}) },
  heart_rate(e){ this.setData({heart_rate:e.detail.value}) },
  daily_steps(e){ this.setData({daily_steps:e.detail.value}) },

  // 调用后端模型预测
  async getPredict(){
    wx.showLoading({title:'正在分析中...'})
    const that = this

    // 替换成你电脑局域网IP！！！PyCharm运行后本机IP
    wx.request({
      url: 'http://127.0.0.1:5000/predict',
      method: 'POST',
      header: {'content-type':'application/json'},
      data: {
        sleep_duration: that.data.sleep_duration,
        physical_activity: that.data.physical_activity,
        stress_level: that.data.stress_level,
        heart_rate: that.data.heart_rate,
        daily_steps: that.data.daily_steps
      },
      success(res){
        wx.hideLoading()
        if(res.data.code == 200){
          that.setData({
            showResult: true,
            sleep_score: res.data.sleep_score,
            sleep_level: res.data.sleep_level,
            advice: res.data.advice
          })
          // 存入本地历史记录
          wx.setStorageSync('history', [...wx.getStorageSync('history')||[], res.data])
        }else{
          wx.showToast({title:'预测失败', icon:'none'})
        }
      },
      fail(){
        wx.hideLoading()
        wx.showToast({title:'连接服务器失败', icon:'none'})
      }
    })
  }
})