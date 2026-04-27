// mine.js 修改后
Page({
  data: {
    bgImgUrl: '', 
    avatarUrl: '/images/avatar.png', // 1. 明确默认头像路径
    userName: '未登录',
    userDesc: '点击完善个人信息',
    openid: '' 
  },

  onShow() {
    // 2. 页面显示时，尝试同步本地缓存的资料
    const profile = wx.getStorageSync('user_profile');
    if (profile) {
      this.setData({
        openid: profile.openid,
        userName: profile.nickname || '健康用户',
        // 如果缓存里有头像就用缓存的，没有就保持默认的 /images/avatar.png
        avatarUrl: profile.avatar_url || '/images/avatar.png',
        userDesc: `${profile.age}岁 | ${profile.height}cm | ${profile.weight}kg`
      });
    }
  },

  // 3. 修改头像并同步数据库
  chooseAvatar() {
    const that = this;
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath;
        
        // 发送请求到后端更新数据库
        wx.request({
          url: 'http://127.0.0.1:5000/api/update_user',
          method: 'POST',
          data: {
            openid: this.data.openid,
            avatar_url: path
          },
          success: (resp) => {
            if (resp.data.status === 'success') {
              // 更新成功后，同时修改内存和缓存
              that.setData({ avatarUrl: path });
              const profile = wx.getStorageSync('user_profile');
              profile.avatar_url = path;
              wx.setStorageSync('user_profile', profile);
              wx.showToast({ title: '头像更新成功' });
            }
          }
        });
      }
    });
  },

  // 4. 修改昵称弹窗
  editUserInfo() {
    wx.showModal({
      title: '修改昵称',
      editable: true,
      content: this.data.userName,
      success: (res) => {
        if (res.confirm && res.content) {
          wx.request({
            url: 'http://127.0.0.1:5000/api/update_user',
            method: 'POST',
            data: {
              openid: this.data.openid,
              nickname: res.content
            },
            success: (resp) => {
              if (resp.data.status === 'success') {
                this.setData({ userName: res.content });
                const profile = wx.getStorageSync('user_profile');
                profile.nickname = res.content;
                wx.setStorageSync('user_profile', profile);
              }
            }
          });
        }
      }
    });
  }
});