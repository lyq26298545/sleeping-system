import * as echarts from '../../ec-canvas/echarts';

Page({
  data: {
    hasData: false,
    ec: { lazyLoad: true }, // 改为懒加载，由逻辑手动控制初始化
    historyRaw: []
  },

  onShow() {
    this.fetchData(); // 每次进入页面刷新数据
  },

  fetchData() {
    const profile = wx.getStorageSync('user_profile');
    if (!profile || !profile.openid) {
      this.setData({ hasData: false });
      return;
    }

    wx.showLoading({ title: '趋势分析中...' });
    wx.request({
      url: 'http://127.0.0.1:5000/api/get_history',
      data: { openid: profile.openid }, // 不传日期，获取全部用于分页滚动
      success: (res) => {
        if (res.data && res.data.length > 0) {
          this.setData({ hasData: true, historyRaw: res.data.reverse() }); // 时间正序排列
          this.initChart();
        } else {
          this.setData({ hasData: false });
        }
      },
      complete: () => wx.hideLoading()
    });
  },

  initChart() {
    // 关键修正：确保组件已经挂载，建议加一个小延迟
    setTimeout(() => {
      const chartComponent = this.selectComponent('#mychart-dom-line');
      if (!chartComponent) return;

      chartComponent.init((canvas, width, height, dpr) => {
        const chart = echarts.init(canvas, null, {
          width: width,
          height: height,
          devicePixelRatio: dpr
        });

        const data = this.data.historyRaw;
        const dates = data.map(item => item.display_date || item.date);
        const bmiData = data.map(item => item.bmi);
        const sleepData = data.map(item => item.sleep_duration);
        const stressData = data.map(item => item.stress_score);
        const activityData = data.map(item => item.activity_value || 0);
        const stepsData = data.map(item => item.steps || 0); 

        // 关键修正：安全计算 dataZoom 的起点，防止数据不足 7 条时报错
        const startIdx = Math.max(0, dates.length - 7);

        const option = {
          tooltip: { 
            trigger: 'axis', 
            axisPointer: { type: 'line' },
            confine: true // 限制在图表区域内，防止在小程序边缘被遮挡
          },
          legend: { data: ['BMI', '睡眠', '压力', '步数'], top: 10 },
          grid: { left: '3%', right: '8%', bottom: '15%', containLabel: true },
          dataZoom: [{
            type: 'inside',
            startValue: startIdx, 
            endValue: dates.length - 1,
            zoomLock: true 
          }],
          xAxis: {
            type: 'category',
            boundaryGap: true, 
            data: dates,
            axisLabel: {
              // 【修改1】：文字旋转 30 度，看起来更专业
              rotate: 30, 
              // 【修改2】：自动隐藏重叠标签。如果设为 0 则强制显示所有
              interval: 'auto', 
              // 【修改3】：离坐标轴稍微远一点，避免挨得太近
              margin: 12,
              textStyle: {
                fontSize: 10,
                color: '#999'
              }
            },
            axisTick: {
              show: false // 隐藏刻度线，视觉更简洁
            },
            axisLine: {
              lineStyle: {
                color: '#eee' // 轴线颜色减淡
              }
            }
          },
          yAxis: [
            {
              type: 'value',
              name: '指标',
              position: 'left',
              // 【核心修改】：动态计算 Y 轴最大值，预留 5% 的空间
              max: function (value) {
                // value.max 是当前数据中的最大值，乘以 1.05 即预留 5%
                // 使用 Math.ceil 向上取整，让刻度线更整齐
                return Math.ceil(value.max * 1.05); 
              },
              min: 0,
              splitLine: { lineStyle: { type: 'dashed' } }
            },
            {
              type: 'value',
              name: '步数',
              position: 'right',
              max: function (value) {
                return Math.ceil(value.max * 1.05);
              },
              splitLine: { show: false }
            }
          ],
          series: [
            { name: 'BMI', type: 'line', smooth: true, data: bmiData, color: '#67E0E3' },
            { name: '睡眠', type: 'line', smooth: true, data: sleepData, color: '#FFA502' },
            { name: '压力', type: 'line', smooth: true, data: stressData, color: '#FF4757' },
            {
              name: '运动强度',
              type: 'line',
              smooth: true,
              data: activityData,
              color: '#20bf6b' 
            },
            { 
              name: '步数', type: 'bar', yAxisIndex: 1, 
              data: stepsData, color: 'rgba(157, 150, 245, 0.4)',
              barWidth: '40%' 
            }
          ]
        };

        chart.setOption(option);
        return chart;
      });
    }, 100); // 延时 100ms 确保组件 ID 已生效
  },

  navToIndex() {
    wx.switchTab({ url: '/pages/index/index' });
  }
});