Page({
  data: {
    list: []
  },
  onLoad() {
    let history = wx.getStorageSync('history') || []
    this.setData({ list: history })
  }
})