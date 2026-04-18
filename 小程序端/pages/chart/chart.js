// 静态引入ec-canvas的init方法，避免动态加载超时
import * as echarts from '../../ec-canvas/echarts';

// 初始化图表的方法（封装成函数，避免重复代码）
function initChart(canvas, width, height, dpr) {
  const chart = echarts.init(canvas, null, {
    width: width,
    height: height,
    devicePixelRatio: dpr // 适配高清屏
  });
  canvas.setChart(chart);
  return chart;
}

Page({
  data: {
    hasData: false,
    ec: {
      onInit: null // 延迟初始化图表
    }
  },

  onLoad() {
    // 1. 先获取历史数据
    const history = wx.getStorageSync('history') || [];
    if (history.length === 0) {
      this.setData({ hasData: false });
      wx.showToast({ title: '暂无睡眠数据', icon: 'none' });
      return;
    }

    // 2. 提取最近7条数据
    let scores = history.map(item => item.sleep_score).slice(-7);
    let days = [];
    for (let i = 0; i < scores.length; i++) {
      days.push(`第${i+1}次`);
    }

    // 3. 初始化图表配置
    this.setData({
      hasData: true,
      ec: {
        onInit: (canvas, width, height, dpr) => {
          const chart = initChart(canvas, width, height, dpr);
          // 设置图表参数
          chart.setOption({
            xAxis: {
              type: 'category',
              data: days,
              axisLabel: { fontSize: 12 }
            },
            yAxis: {
              type: 'value',
              min: 4,
              max: 10,
              name: '睡眠分数'
            },
            series: [{
              data: scores,
              type: 'line',
              smooth: true,
              color: '#409eff'
            }]
          });
          return chart;
        }
      }
    });
  }
});