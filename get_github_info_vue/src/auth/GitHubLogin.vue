<template>
  <div class="github-login">
    <h2>请登录 GitHub 账号</h2>
    <el-button type="primary" @click="handleLogin" class="login-button" :loading="isLoading">
      使用 GitHub 登录
    </el-button>
    
    <!-- 增强错误信息显示 -->
    <div v-if="errorMessage" class="error-message">
      <el-alert
        :title="errorMessage"
        type="error"
        show-icon
        :closable="true"
        @close="errorMessage = ''"
      >
        <template #default>
          <div class="error-details">
            <p>可能原因：</p>
            <ul>
              <li>GitHub服务器暂时不可用</li>
              <li>网络连接问题</li>
              <li>授权码已过期</li>
            </ul>
            <p>请稍后重试或<a href="#" @click.prevent="handleLogin">点击此处</a>重新登录</p>
          </div>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '@/api/config'
import axios from 'axios' // 引入axios用于处理API请求

export default {
  name: 'GitHubLogin',
  data() {
    return {
      isLoading: false,
      errorMessage: ''
    }
  },
  mounted() {
    // 在组件挂载时检查URL中是否包含access_token或error参数
    this.checkUrlParams();
  },
  methods: {
    handleLogin() {
      this.isLoading = true;
      this.errorMessage = '';
      
      try {
        console.log('准备跳转到GitHub授权页面');
        // 直接跳转到后端的 GitHub 认证端点
        window.location.href = API_ENDPOINTS.AUTH_GITHUB;
      } catch (error) {
        console.error('跳转到GitHub授权页面失败:', error);
        this.isLoading = false;
        this.errorMessage = '无法跳转到GitHub授权页面，请检查网络连接';
      }
    },
    
    // 检查URL中是否包含OAuth回调的参数
    async checkUrlParams() {
      const urlParams = new URLSearchParams(window.location.search);
      const accessToken = urlParams.get('access_token');
      const error = urlParams.get('error');
      const code = urlParams.get('code');
      
      console.log('检查URL参数:', { accessToken: !!accessToken, error: !!error, code: !!code });
      
      if (accessToken) {
        console.log('从URL获取到访问令牌');
        // 保存令牌到localStorage
        localStorage.setItem('github_token', accessToken);
        // 清除URL参数
        this.clearUrlParams();
        // 触发授权成功事件
        this.$emit('auth-success', accessToken);
      } else if (error) {
        console.error('GitHub授权错误:', error);
        this.isLoading = false;
        this.errorMessage = `GitHub授权失败: ${decodeURIComponent(error)}`;
        this.clearUrlParams();
      } else if (code) {
        console.log('检测到GitHub授权码，开始处理');
        this.isLoading = true;
        
        try {
          // 直接调用后端API获取token，而不依赖重定向
          const response = await axios.get(`${API_ENDPOINTS.AUTH_CALLBACK}?code=${code}`);
          console.log('获取到API响应:', response.data);
          
          // 根据新的返回格式处理响应
          if (response.data.status === 'success' && response.data.access_token) {
            // 成功获取token
            const token = response.data.access_token;
            console.log('成功获取token:', token.substring(0, 5) + '...');
            
            // 保存令牌到localStorage
            localStorage.setItem('github_token', token);
            
            // 清除URL参数
            this.clearUrlParams();
            
            // 触发授权成功事件
            this.$emit('auth-success', token);
          } else if (response.data.status === 'error') {
            // 处理错误 - 显示服务器返回的错误信息
            console.error('获取token失败:', response.data.error);
            this.errorMessage = `GitHub授权失败: ${response.data.error}`;
            
            // 如果是授权码过期错误，提供重新登录的建议
            if (response.data.error && response.data.error.includes('incorrect or expired')) {
              this.errorMessage = '授权码已过期，请重新登录';
            }
            
            this.isLoading = false;
            this.clearUrlParams();
          } else {
            // 意外的响应格式
            throw new Error('响应格式不符合预期');
          }
        } catch (error) {
          console.error('调用API获取token失败:', error);
          
          // 提供更友好的错误信息
          if (error.response) {
            // 请求已发出，但服务器响应状态码不在 2xx 范围内
            console.error('服务器响应:', error.response.data);
            this.errorMessage = `服务器返回错误 (${error.response.status}): ${error.response.data.detail || '未知错误'}`;
          } else if (error.request) {
            // 请求已发出，但没有收到响应
            console.error('没有收到响应');
            this.errorMessage = '服务器没有响应，请检查网络连接或稍后重试';
          } else {
            // 设置请求时发生错误
            this.errorMessage = `请求处理失败: ${error.message || '未知错误'}`;
          }
          
          this.isLoading = false;
          this.clearUrlParams();
        }
      }
    },
    
    // 清除URL参数
    clearUrlParams() {
      const url = new URL(window.location.href);
      // 保留路径和域名，删除所有查询参数
      window.history.replaceState({}, document.title, url.pathname);
    }
  }
}
</script>

<style scoped>
.github-login {
  max-width: 500px;
  margin: 100px auto;
  text-align: center;
  padding: 20px;
}

.login-button {
  margin: 20px 0;
}

.error-message {
  margin-top: 20px;
}

.error-details {
  text-align: left;
  margin-top: 10px;
}

.error-details ul {
  padding-left: 20px;
  margin: 5px 0;
}

.error-details a {
  color: #409EFF;
  text-decoration: none;
}

.error-details a:hover {
  text-decoration: underline;
}
</style> 