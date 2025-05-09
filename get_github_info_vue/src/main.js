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
