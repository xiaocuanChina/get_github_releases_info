<template>
  <div class="debug-helper">
    <h3>认证调试助手</h3>
    
    <el-card class="debug-card">
      <div class="debug-section">
        <h4>当前状态</h4>
        <div class="debug-info">
          <p><b>认证状态:</b> {{ isAuthenticated ? '已登录' : '未登录' }}</p>
          <p><b>本地存储Token:</b> {{ hasToken ? '存在' : '不存在' }}</p>
          <p v-if="hasToken"><b>Token前缀:</b> {{ tokenPrefix }}</p>
          <p><b>当前URL:</b> {{ currentUrl }}</p>
          <p v-if="code"><b>授权码:</b> {{ code.substring(0, 5) + '...' }}</p>
        </div>
      </div>
      
      <div class="debug-section">
        <h4>操作</h4>
        <div class="actions">
          <el-button @click="clearToken" type="danger" size="small">
            清除令牌
          </el-button>
          <el-button @click="checkToken" :loading="checking" type="primary" size="small">
            检查令牌有效性
          </el-button>
          <el-button @click="refreshPage" type="success" size="small">
            刷新页面
          </el-button>
        </div>
      </div>
      
      <div class="debug-section" v-if="verifyResult">
        <h4>验证结果</h4>
        <pre class="result-json">{{ JSON.stringify(verifyResult, null, 2) }}</pre>
      </div>
      
      <div class="debug-section" v-if="error">
        <h4>错误信息</h4>
        <pre class="error-json">{{ error }}</pre>
      </div>
    </el-card>
  </div>
</template>

<script>
import { API_ENDPOINTS } from '@/api/config';
import axios from 'axios';

export default {
  name: 'DebugHelper',
  
  data() {
    return {
      isAuthenticated: false,
      hasToken: false,
      tokenPrefix: '',
      currentUrl: '',
      code: '',
      checking: false,
      verifyResult: null,
      error: null
    };
  },
  
  mounted() {
    this.updateState();
  },
  
  methods: {
    updateState() {
      // 获取当前URL和参数
      this.currentUrl = window.location.href;
      const urlParams = new URLSearchParams(window.location.search);
      this.code = urlParams.get('code');
      
      // 检查令牌
      const token = localStorage.getItem('github_token');
      this.hasToken = !!token;
      
      if (token) {
        this.tokenPrefix = token.substring(0, 5) + '...';
      }
    },
    
    clearToken() {
      localStorage.removeItem('github_token');
      this.updateState();
      this.$message.success('已清除令牌');
    },
    
    async checkToken() {
      this.checking = true;
      this.verifyResult = null;
      this.error = null;
      
      const token = localStorage.getItem('github_token');
      
      if (!token) {
        this.error = '本地存储中不存在令牌';
        this.checking = false;
        return;
      }
      
      try {
        const response = await axios.get(API_ENDPOINTS.AUTH_VERIFY, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        
        this.verifyResult = response.data;
        this.isAuthenticated = response.data.status === 'success';
      } catch (error) {
        this.error = error.response?.data?.detail || error.message || '验证令牌失败';
        console.error('验证令牌失败:', error);
      } finally {
        this.checking = false;
      }
    },
    
    refreshPage() {
      window.location.reload();
    }
  }
};
</script>

<style scoped>
.debug-helper {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.debug-card {
  margin-top: 20px;
}

.debug-section {
  margin-bottom: 20px;
}

h3 {
  color: #409EFF;
  margin-bottom: 20px;
}

h4 {
  color: #606266;
  border-bottom: 1px solid #EBEEF5;
  padding-bottom: 10px;
  margin-bottom: 15px;
}

.debug-info p {
  margin: 5px 0;
  line-height: 1.5;
}

.actions {
  display: flex;
  gap: 10px;
}

.result-json, .error-json {
  background-color: #f6f8fa;
  padding: 15px;
  border-radius: 4px;
  overflow: auto;
  max-height: 300px;
}

.error-json {
  background-color: #fff5f5;
  color: #f56c6c;
}
</style> 