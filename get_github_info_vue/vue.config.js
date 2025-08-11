const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: config => {
    config
      .plugin('html')
      .tap(args => {
        args[0].title = '获取最新Releases列表'
        return args
      })
  },
  publicPath: '/',
  devServer: {
    // 从环境变量获取前端端口，默认为8080
    port: process.env.FRONTEND_PORT || 8080,
    historyApiFallback: {
      rewrites: [
        { from: /^\/auth\/callback/, to: '/index.html' },
        { from: /^\/api\/auth\/callback/, to: '/api/auth/callback.html' }
      ]
    }
  }
})
