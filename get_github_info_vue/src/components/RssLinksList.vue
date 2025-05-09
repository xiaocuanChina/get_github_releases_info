<template>
  <div class="rss-dialog-content" v-loading="loading">
    <div v-if="rssMode === 'single'" class="single-rss-container">
      <p>您可以使用以下链接订阅 {{ repoName }} 的 Releases:</p>
      <div class="rss-link-container">
        <el-input v-model="internalRssLink" readonly></el-input>
        <el-button type="primary" @click="copyToClipboard(internalRssLink)">复制</el-button>
      </div>
    </div>
    <div v-else-if="rssMode === 'batch'" class="batch-rss-container">
      <div class="batch-rss-header">
        <div class="batch-info">
          <p>已为您生成 {{ total }} 个订阅链接：</p>
          <el-tag v-if="fromCache" size="small" type="success">从缓存加载</el-tag>
          <el-tag v-else size="small" type="primary">实时获取</el-tag>
        </div>
        <div class="batch-actions">
          <el-button size="small" type="primary" @click="copyAllRssLinks">一键复制所有链接</el-button>
          <el-button size="small" type="success" @click="downloadOpml">下载 OPML 文件</el-button>
          <el-button size="small" type="warning" @click="refreshRssLinks">刷新链接</el-button>
        </div>
      </div>

      <!-- 添加搜索框 -->
      <div class="rss-search-box">
        <el-input
            v-model="searchQuery"
            placeholder="搜索仓库名称..."
            prefix-icon="el-icon-search"
            clearable
            @input="currentPage = 1"
        ></el-input>
      </div>

      <el-table
          :data="paginatedRssLinks"
          style="width: 100%"
          height="350px"
          border
      >
        <el-table-column prop="repo_name" label="仓库名称" width="180">
          <template slot-scope="scope">
            <a :href="`https://github.com/${scope.row.repo_name}`" target="_blank" class="repo-name-link">
              {{ scope.row.repo_name }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="rss_link" label="RSS 链接" show-overflow-tooltip>
          <template slot-scope="scope">
            <div class="table-rss-link">
              <span>{{ scope.row.rss_link }}</span>
              <el-button
                  size="mini"
                  type="text"
                  @click="copyToClipboard(scope.row.rss_link)"
                  icon="el-icon-document-copy"
              >复制
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 添加分页器 -->
      <div class="rss-pagination">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredRssLinks.length">
        </el-pagination>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_ENDPOINTS } from '@/api/config'

export default {
  name: 'RssLinksList',
  
  props: {
    accessToken: {
      type: String,
      required: true
    },
    rssMode: {
      type: String,
      default: 'batch', // 'single' 或 'batch'
      validator: value => ['single', 'batch'].includes(value)
    },
    repoName: {
      type: String,
      default: ''
    },
    singleRssLink: {
      type: String,
      default: ''
    }
  },
  
  data() {
    return {
      loading: false,
      rssLinks: [],
      searchQuery: '',
      currentPage: 1,
      pageSize: 10,
      total: 0,
      fromCache: false,
      internalRssLink: this.singleRssLink
    }
  },
  
  computed: {
    filteredRssLinks() {
      if (!this.searchQuery) {
        return this.rssLinks;
      }
      
      const query = this.searchQuery.toLowerCase();
      return this.rssLinks.filter(item =>
        item.repo_name.toLowerCase().includes(query)
      );
    },
    
    paginatedRssLinks() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.filteredRssLinks.slice(start, end);
    }
  },
  
  watch: {
    singleRssLink: {
      immediate: true,
      handler(newVal) {
        this.internalRssLink = newVal;
      }
    }
  },
  
  created() {
    if (this.rssMode === 'batch') {
      this.fetchRssLinks();
    }
  },
  
  methods: {
    // 获取RSS链接
    async fetchRssLinks() {
      this.loading = true;
      
      try {
        const response = await axios.get(API_ENDPOINTS.ALL_STARRED_RSS, {
          headers: {
            Authorization: `Bearer ${this.accessToken}`
          }
        });

        if (response.data.status === 'success') {
          this.rssLinks = response.data.data;
          this.total = response.data.total || this.rssLinks.length;
          this.fromCache = response.data.from_cache || false;
        } else {
          this.$message.error('获取RSS链接失败');
        }
      } catch (error) {
        console.error('批量获取RSS链接失败:', error);
        this.$message.error('批量获取RSS链接失败');
      } finally {
        this.loading = false;
      }
    },
    
    // 刷新RSS链接
    async refreshRssLinks() {
      this.loading = true;
      
      try {
        // 调用检查更新接口
        const checkResponse = await axios.get(API_ENDPOINTS.CHECK_RSS_UPDATES, {
          headers: {
            Authorization: `Bearer ${this.accessToken}`
          }
        });
        
        if (checkResponse.data.status === 'success') {
          const updateInfo = checkResponse.data;
          
          // 如果不需要更新，显示提示并直接获取RSS链接
          if (!updateInfo.need_update) {
            this.$message({
              type: 'info',
              message: `RSS链接已是最新，上次更新时间: ${this.formatLastUpdate(updateInfo.last_update)}`
            });
            // 不执行刷新，直接获取链接
            this.fetchRssLinks();
            return;
          } else {
            // 需要更新，显示确认对话框
            const updates = updateInfo.updates;
            const confirmMessage = `
              检测到仓库变动，是否刷新RSS链接？
              • 新增仓库: ${updates.new_repos}个
              • 移除仓库: ${updates.removed_repos}个
              • 保持不变: ${updates.unchanged}个
              • 上次更新: ${this.formatLastUpdate(updateInfo.last_update)}
            `;
            
            try {
              await this.$confirm(confirmMessage, '提示', {
                confirmButtonText: '立即刷新',
                cancelButtonText: '取消',
                type: 'warning'
              });
              
              // 用户确认刷新，调用刷新接口
              await axios.post(API_ENDPOINTS.REFRESH_RSS_LINKS, {}, {
                headers: {
                  Authorization: `Bearer ${this.accessToken}`
                }
              });
              
              // 刷新完成后重新获取RSS链接
              this.fetchRssLinks();
              this.$message.success(`成功刷新 RSS 链接`);
            } catch (e) {
              // 用户取消，不执行刷新
              this.loading = false;
            }
          }
        }
      } catch (error) {
        console.error('刷新RSS链接失败:', error);
        this.$message.error('刷新RSS链接失败');
        this.loading = false;
      }
    },
    
    // 复制文本到剪贴板
    copyToClipboard(text) {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();

      try {
        const successful = document.execCommand('copy');
        if (successful) {
          this.$message.success('已复制到剪贴板');
        } else {
          this.$message.error('复制失败');
        }
      } catch (err) {
        this.$message.error('复制失败');
      }

      document.body.removeChild(textArea);
    },
    
    // 复制所有链接
    copyAllRssLinks() {
      const linkTexts = this.filteredRssLinks.map(item => item.rss_link).join('\n');
      this.copyToClipboard(linkTexts);
    },
    
    // 下载OPML文件
    downloadOpml() {
      // 创建OPML格式文件
      let opmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="1.0">
  <head>
    <title>GitHub Starred 仓库 RSS 订阅</title>
  </head>
  <body>
    <outline text="GitHub Starred Releases" title="GitHub Starred Releases">`;

      this.rssLinks.forEach(item => {
        opmlContent += `
      <outline type="rss" text="${item.repo_name}" title="${item.repo_name}" xmlUrl="${item.rss_link}" htmlUrl="https://github.com/${item.repo_name}/releases"/>`;
      });

      opmlContent += `
    </outline>
  </body>
</opml>`;

      // 创建下载
      const blob = new Blob([opmlContent], {type: 'text/xml'});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'github_starred_releases.opml';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      this.$message.success('OPML文件已下载');
    },
    
    // 处理每页显示数量变化
    handleSizeChange(val) {
      this.pageSize = val;
      this.currentPage = 1;
    },
    
    // 处理页码变化
    handleCurrentChange(val) {
      this.currentPage = val;
    },
    
    // 格式化最后更新时间
    formatLastUpdate(isoTimeStr) {
      if (!isoTimeStr) return '无记录';
      try {
        const date = new Date(isoTimeStr);
        return `${date.getFullYear()}-${(date.getMonth()+1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
      } catch (e) {
        return isoTimeStr || '未知';
      }
    }
  }
}
</script>

<style scoped>
/* RSS 对话框样式 */
.single-rss-container {
  padding: 10px;
}

.rss-link-container {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.batch-rss-container {
  padding: 10px;
}

.batch-rss-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* RSS搜索框样式 */
.rss-search-box {
  margin-bottom: 15px;
}

/* RSS表格中的仓库名链接样式 */
.repo-name-link {
  color: #409EFF;
  text-decoration: none;
  transition: all 0.3s;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.repo-name-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

/* 表格链接样式 */
.table-rss-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-rss-link span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-rss-link .el-button {
  margin-left: 8px;
  white-space: nowrap;
}

/* RSS分页样式 */
.rss-pagination {
  margin-top: 15px;
  text-align: center;
}
</style> 