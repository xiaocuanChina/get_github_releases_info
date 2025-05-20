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
    historyApiFallback: {
      rewrites: [
        { from: /^\/auth\/callback/, to: '/index.html' }
      ]
    }
  }
})
