Page({
  data: {
    list: [],
    selectedDate: '',
    showModal: false,
    activeItem: null, // 当前选中的记录详情
    openid: ''
  },

  onLoad() {
    const profile = wx.getStorageSync('user_profile');
    
    // 调试用：看一眼缓存里到底有没有 openid
    console.log('当前缓存的资料：', profile);
  
    if (profile && profile.openid) {
      this.setData({ openid: profile.openid });
      this.fetchHistory();
    } else {
      // 如果没有 openid，引导用户回到首页
      wx.showModal({
        title: '提示',
        content: '未找到用户信息，请先前往首页完成档案登记',
        showCancel: false,
        success: () => {
          wx.switchTab({ url: '/pages/index/index' });
        }
      });
    }
  },

  // 获取历史数据
  fetchHistory(date = '') {
    wx.showLoading({ title: '加载中' });
    wx.request({
      url: 'http://127.0.0.1:5000/api/get_history',
      data: {
        openid: this.data.openid,
        date: date
      },
      success: (res) => {
        this.setData({ list: res.data });
      },
      complete: () => {
        wx.hideLoading();
      }
    });
  },

  // 日期筛选
  onDateChange(e) {
    const date = e.detail.value;
    this.setData({ selectedDate: date });
    this.fetchHistory(date);
  },

  // 重置搜索
  resetSearch() {
    this.setData({ selectedDate: '' });
    this.fetchHistory();
  },

  // 显示详情弹窗
  showDetail(e) {
    const item = e.currentTarget.dataset.item;
    this.setData({
      activeItem: item,
      showModal: true
    });
  },

  closeModal() {
    this.setData({ showModal: false });
  }
})