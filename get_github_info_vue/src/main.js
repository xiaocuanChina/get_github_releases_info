import Vue from 'vue'
import App from './App.vue'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'

// 全局引入Element UI图标
import 'element-ui/lib/theme-chalk/icon.css'

Vue.use(ElementUI)
Vue.config.productionTip = false

// 设置网页标题
document.title = '获取最新Releases列表'

// 添加GitHub回调处理逻辑
const handleGitHubCallback = () => {
  // 检查当前路径是否是GitHub回调路径
  if (window.location.pathname.startsWith('/auth/callback') || window.location.pathname.startsWith('/api/auth/callback')) {
    console.log('检测到GitHub回调路径，保留查询参数');
    
    // 获取当前URL的查询参数
    const queryParams = window.location.search;
    const urlParams = new URLSearchParams(queryParams);
    const code = urlParams.get('code');
    
    if (code) {
      console.log('检测到授权码，重定向到首页并保留code参数');
      // 重定向到首页，但保留查询参数
      window.history.replaceState({}, document.title, '/' + queryParams);
    } else {
      console.log('未检测到有效的授权码，直接返回首页');
      window.history.replaceState({}, document.title, '/');
    }
  }
};

// 在页面加载时处理可能的GitHub回调
handleGitHubCallback();

// 添加图标尺寸样式到document
const style = document.createElement('style')
style.textContent = `
  .icon-size-small { font-size: 12px; }
  .icon-size-normal { font-size: 16px; }
  .icon-size-medium { font-size: 20px; }
  .icon-size-large { font-size: 24px; }
`
document.head.appendChild(style)

// 创建图标组件，直接使用class名自动匹配图标
Vue.component('AppIcon', {
  props: {
    name: {
      type: String,
      required: true
    },
    size: {
      type: String,
      default: 'normal'
    }
  },
  render(h) {
    return h('i', {
      class: [
        `el-icon-${this.name}`,
        `icon-size-${this.size}`
      ]
    })
  }
})

new Vue({
  render: h => h(App),
}).$mount('#app')
