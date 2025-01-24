<template>
  <el-card class="login-card">
    <div class="login-content">
      <h2>GitHub Starred Releases</h2>
      <p>请使用 GitHub 账号登录以查看您的 Starred 仓库的发布信息</p>
      <el-button type="primary" @click="handleLogin">
        GitHub 登录
      </el-button>
    </div>
  </el-card>
</template>

<script>
export default {
  name: 'GitHubLogin',

  methods: {
    handleLogin() {
      // 保存当前页面 URL 作为回调后的重定向地址
      localStorage.setItem('redirect_after_login', window.location.href)
      window.location.href = 'http://localhost:8000/api/auth/github'
    }
  }
}
</script>

<style scoped>
.login-card {
  max-width: 500px;
  margin: 100px auto;
}

.login-content {
  text-align: center;
  padding: 20px;
}
</style> 