<template>
  <div class="github-login">
    <h2>请登录 GitHub 账号</h2>
    <el-button type="primary" @click="handleLogin" class="login-button">
      使用 GitHub 登录
    </el-button>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '@/api/config'

export default {
  name: 'GitHubLogin',
  methods: {
    handleLogin() {
      // 直接跳转到后端的 GitHub 认证端点
      window.location.href = API_ENDPOINTS.AUTH_GITHUB;
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