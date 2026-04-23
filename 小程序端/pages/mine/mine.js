Page({
  data: {
    // 预留自定义路径 - 背景图（你替换成自己的图片路径即可）
    bgImgUrl: '/images/avatar.png', 
    // 预留自定义路径 - 头像（默认占位，你替换成自己的默认头像路径）
    avatarUrl: '/images/avatar.png', 
    // 预留用户信息
    userName: '',
    userDesc: ''
  },

  // 预留：选择/更换头像方法（你后续对接微信头像选择API即可）
  chooseAvatar() {
    wx.showToast({title: '暂未开放头像编辑', icon: 'none'});
    // 后续可对接 wx.chooseAvatar 微信API
  },

  // 预留：编辑个人信息方法（你后续做表单编辑即可）
  editUserInfo() {
    wx.showToast({title: '暂未开放信息编辑', icon: 'none'});
  },
 })