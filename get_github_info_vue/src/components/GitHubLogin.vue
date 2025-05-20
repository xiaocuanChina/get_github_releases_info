<template>
  <div class="login-container">
    <div class="login-content">
      <h2>GitHub Starred Releases</h2>
      <p class="login-description">跟踪你 Star 的 GitHub 仓库的最新发布</p>

      <div class="features">
        <div class="feature-item">
          <div class="feature-icon">
            <img src="/track.png" alt="追踪" class="feature-img" />
          </div>
          <div class="feature-text">
            <h3>Star 仓库追踪</h3>
            <p>自动获取你 Star 过的所有 GitHub 仓库的最新发布信息</p>
          </div>
        </div>
        
        <div class="feature-item">
          <div class="feature-icon">
            <img src="/real_time.png" alt="实时更新" class="feature-img" />
          </div>
          <div class="feature-text">
            <h3>实时更新</h3>
            <p>及时获取最新版本发布通知，不错过任何重要更新</p>
          </div>
        </div>
        
        <div class="feature-item">
          <div class="feature-icon">
            <img src="/view.png" alt="多种视图" class="feature-img" />
          </div>
          <div class="feature-text">
            <h3>多种视图</h3>
            <p>支持列表视图和日历视图，满足不同的浏览需求</p>
          </div>
        </div>
      </div>

      <el-button type="primary" @click="handleLogin" class="login-button">
        <GitHubLogo :size="20" class="github-logo" :color="'#ffffff'" />
        使用 GitHub 登录
      </el-button>

      <div class="login-footer">
        <p>本应用仅用于展示你 Star 的仓库更新信息，不会修改你的 GitHub 账户</p>
      </div>
    </div>

    <div class="preview-image">
      <div class="preview-cards-container">
        <div class="preview-card calendar-card">
          <div class="preview-img-wrapper">
            <img src="/calendar_view.png" alt="日历视图" class="preview-img" />
          </div>
          <div class="preview-label">
            <h3>日历视图</h3>
            <p>按日期查看更新，一目了然掌握项目动态</p>
          </div>
        </div>
        
        <div class="preview-card list-card">
          <div class="preview-img-wrapper">
            <img src="/list_view.png" alt="列表视图" class="preview-img" />
          </div>
          <div class="preview-label">
            <h3>列表视图</h3>
            <p>详细展示更新内容，方便深入了解</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import GitHubLogo from '@/components/GitHubLogo.vue'
import { API_ENDPOINTS } from '@/api/config'
import axios from 'axios'

export default {
  name: 'GitHubLogin',
  
  components: {
    GitHubLogo
  },
  
  data() {
    return {
      isCheckingToken: false,
      loginFailed: false,
      errorMessage: ''
    }
  },
  
  mounted() {
    // 检查URL参数中是否有code、token或error
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const tokenFromUrl = urlParams.get('token');
    const errorFromUrl = urlParams.get('error');
    const messageFromUrl = urlParams.get('message');
    
    console.log('URL参数检查 - code:', code ? '存在' : '不存在', 'token:', tokenFromUrl ? '存在' : '不存在');
    
    if (code) {
      // 如果URL中有授权码，处理GitHub回调
      this.handleGitHubCallback(code);
      return;
    } else if (tokenFromUrl) {
      console.log('从URL接收到token');
      localStorage.setItem('github_token', tokenFromUrl);
      // 清除URL中的参数
      window.history.replaceState({}, document.title, window.location.pathname);
      // 刷新页面以应用新token
      window.location.reload();
      return;
    } else if (errorFromUrl) {
      this.loginFailed = true;
      this.errorMessage = messageFromUrl || '登录失败，请重试';
      console.error('登录错误:', this.errorMessage);
      this.$message.error(this.errorMessage);
      return;
    }
    
    // 检查是否已有本地存储的token
    this.checkExistingToken();
  },
  
  methods: {
    async checkExistingToken() {
      const storedToken = localStorage.getItem('github_token');
      if (storedToken) {
        this.isCheckingToken = true;
        
        try {
          console.log('检查存储的token...');
          const response = await axios.get(API_ENDPOINTS.AUTH_VERIFY, {
            headers: {
              Authorization: `Bearer ${storedToken}`
            }
          });
          
          if (response.data.status === 'success') {
            console.log('已验证本地存储的token有效');
            this.$emit('auth-success', {
              token: storedToken,
              user: response.data.user
            });
            return;
          }
        } catch (error) {
          console.error('验证已存储token失败:', error);
          // 清除无效token
          localStorage.removeItem('github_token');
        } finally {
          this.isCheckingToken = false;
        }
      }
    },
    
    handleLogin() {
      try {
        // 保存当前的URL，用于登录后重定向回来
        localStorage.setItem('redirect_after_login', window.location.href);
        
        // 显示加载中提示
        this.$message({
          message: '正在跳转到GitHub授权页面...',
          type: 'info',
          duration: 2000
        });
        
        console.log('准备跳转到GitHub授权页面:', API_ENDPOINTS.AUTH_GITHUB);
        
        // 跳转到后端的 GitHub 认证端点
        window.location.href = API_ENDPOINTS.AUTH_GITHUB;
      } catch (error) {
        console.error('跳转到GitHub授权页面失败:', error);
        this.$message.error('无法跳转到GitHub授权页面，请检查网络连接');
      }
    },
    
    // 用于处理GitHub回调的方法
    async handleGitHubCallback(code) {
      console.log('处理GitHub回调，授权码:', code.substring(0, 5) + '...');
      
      try {
        // 先清除URL中的code参数
        console.log('清除URL中的code参数');
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // 显示加载提示
        this.$message({
          message: '正在处理GitHub授权...',
          type: 'info',
          duration: 5000
        });
        
        console.log('向后端发送请求，URL:', `${API_ENDPOINTS.AUTH_CALLBACK}?code=${code}`);
        
        // 向后端发送授权码获取token
        const response = await axios.get(`${API_ENDPOINTS.AUTH_CALLBACK}?code=${code}`, {
          // 添加超时设置
          timeout: 30000,
          // 增加重试配置
          retry: 3,
          retryDelay: 1000,
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });
        
        console.log('认证响应状态:', response.status);
        console.log('认证响应数据:', JSON.stringify(response.data).substring(0, 100) + '...');
        
        if (response.data && response.data.access_token) {
          // 保存token
          const token = response.data.access_token;
          localStorage.setItem('github_token', token);
          console.log('成功获取并保存token');
          
          // 验证token
          try {
            console.log('验证令牌有效性...');
            const verifyResponse = await axios.get(API_ENDPOINTS.AUTH_VERIFY, {
              headers: {
                Authorization: `Bearer ${token}`
              },
              // 添加超时设置
              timeout: 20000
            });
            
            if (verifyResponse.data.status === 'success') {
              console.log('令牌验证成功');
              this.$emit('auth-success', {
                token: token,
                user: verifyResponse.data.user
              });
              
              // 检查是否有需要重定向的URL
              const redirectUrl = localStorage.getItem('redirect_after_login');
              if (redirectUrl) {
                localStorage.removeItem('redirect_after_login');
                if (redirectUrl !== window.location.href) {
                  window.location.href = redirectUrl;
                  return;
                }
              }
              
              // 刷新页面以应用新token
              window.location.reload();
            } else {
              throw new Error('令牌验证响应无效');
            }
          } catch (verifyError) {
            console.error('令牌验证失败:', verifyError);
            this.$message.error('获取令牌成功，但验证失败，请重试');
            localStorage.removeItem('github_token');
          }
        } else if (response.data && response.data.status === 'error') {
          // 处理错误响应
          console.error('GitHub授权返回错误:', response.data.error);
          throw new Error(response.data.error || '授权失败');
        } else {
          console.error('响应中没有访问令牌:', response.data);
          throw new Error(response.data?.detail || '响应中没有访问令牌');
        }
      } catch (error) {
        console.error('处理GitHub回调失败:', error);
        this.loginFailed = true;
        
        let errorMessage = '认证失败，请重试';
        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        this.errorMessage = errorMessage;
        console.error('详细错误信息:', errorMessage);
        
        // 显示友好的错误信息
        if (errorMessage.includes('code') && errorMessage.includes('incorrect or expired')) {
          this.$message.error('授权码已过期或无效，请重新登录');
        } else if (errorMessage.includes('验证码无效或已过期')) {
          this.$message.error('授权码已过期或无效，请重新登录');
        } else if (errorMessage.includes('Failed to get user information')) {
          this.$message.error('无法获取用户信息，请重试');
        } else {
          this.$message.error(`GitHub授权失败: ${errorMessage}`);
        }
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  min-height: 100vh;
  padding: 20px;
  background: #f6f8fa;
  box-sizing: border-box;
}

.login-content {
  flex: 1;
  max-width: 600px;
  padding: 40px;
  background-color: white;
  border-radius: 6px;
  box-shadow: 0 3px 12px rgba(27, 31, 36, 0.1);
  border: 1px solid #d0d7de;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 30px;
}

.login-content h2 {
  font-size: 32px;
  font-weight: 600;
  color: #24292f;
  margin: 0;
}

.login-description {
  font-size: 18px;
  color: #57606a;
  margin: 0;
  max-width: 80%;
  line-height: 1.6;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 15px;
  background-color: #f9f9fb;
  border-radius: 12px;
  transition: all 0.3s;
}

.feature-item:hover {
  background-color: #ecf5ff;
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05);
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: #0969da;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
  overflow: hidden;
  padding: 10px;
}

.feature-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: brightness(0) invert(1);
}

.feature-text {
  flex: 1;
}

.feature-text h3 {
  margin: 0;
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #24292f;
}

.feature-text p {
  margin: 0;
  color: #57606a;
  font-size: 14px;
  line-height: 1.5;
}

.login-button {
  margin-top: 10px;
  height: 48px;
  font-size: 16px;
  min-width: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background-color: #2da44e;
  border-color: #2da44e;
  transition: all 0.3s;
}

.login-button:hover {
  background-color: #2c974b;
  border-color: #2c974b;
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(45, 164, 78, 0.2);
}

.github-logo {
  margin-right: 8px;
}

.login-footer {
  margin-top: 20px;
  color: #57606a;
  font-size: 13px;
  line-height: 1.5;
  padding-top: 16px;
  border-top: 1px solid #eaeef2;
  width: 100%;
}

.preview-image {
  flex: 1;
  max-width: 50%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 30px; /* 减小间距 */
  position: relative;
  padding: 20px;
}

.preview-cards-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  max-width: 400px;
}

.preview-card {
  width: 100%;
  position: relative;
  background: white;
  border-radius: 6px;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s;
  height: 320px; /* 再次增加卡片高度，确保内容能完整显示无需滚动条 */
  border: 1px solid #d0d7de;
  display: flex; /* 添加flex布局 */
  flex-direction: column; /* 垂直排列 */
}

.preview-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.preview-img-wrapper {
  width: 100%;
  height: 180px; /* 保持图片区域高度不变 */
  background: #f6f8fa;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-bottom: 1px solid #d0d7de;
  flex-shrink: 0; /* 防止图片区域被压缩 */
}

.preview-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

.preview-label {
  padding: 16px 20px;
  text-align: center;
  flex: 1; /* 让标签区域自动占据剩余空间 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden; /* 修改为hidden，不显示滚动条 */
}

.preview-label h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #24292f;
  font-weight: 600;
}

.preview-label p {
  margin: 0;
  font-size: 14px;
  color: #57606a;
  line-height: 1.5;
  max-height: none; /* 确保文字不被截断 */
}

.calendar-card {
  transform: none;
  z-index: 1;
}

.list-card {
  transform: none;
  margin-top: 0;
  z-index: 1;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .login-container {
    flex-direction: column;
    gap: 40px;
    padding-top: 40px;
    padding-bottom: 40px;
  }
  
  .login-content,
  .preview-image {
    max-width: 100%;
  }
  
  .preview-cards-container {
    max-width: 100%;
    flex-direction: row;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .preview-card {
    max-width: 350px;
    height: 320px; /* 在响应式布局中保持高度 */
  }
  
  .login-description {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .login-content {
    padding: 30px 20px;
  }
  
  .login-button {
    width: 100%;
  }
  
  .preview-image {
    display: none; /* 在小屏幕上隐藏预览图 */
  }
}
</style> 