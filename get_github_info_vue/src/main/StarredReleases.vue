<template>
  <div class="releases-container">
    <!-- 未登录时显示登录组件 -->
    <github-login v-if="!isAuthenticated" />

    <!-- 登录后显示主内容 -->
    <template v-else>
      <el-card class="header-card">
        <div class="header">
          <!-- 左侧：标题和用户信息 -->
          <div class="header-left">
            <div class="title-section">
              <h2>GitHub Starred Releases</h2>
              <div class="user-info" v-if="userInfo">
                <img :src="userInfo.avatar_url" class="user-avatar" :alt="userInfo.login">
                <a :href="'https://github.com/' + userInfo.login" target="_blank" class="username">{{ userInfo.login }}</a>
                <el-button 
                  type="danger" 
                  size="mini" 
                  @click="handleLogout" 
                  class="logout-btn" 
                  icon="el-icon-switch-button"
                  round
                >
                  退出登录
                </el-button>
              </div>
            </div>
          </div>

          <!-- 右侧：刷新按钮和批量获取RSS链接按钮 -->
          <div class="header-right">
            <div class="action-buttons">
              <el-tooltip content="批量获取RSS链接" placement="top">
                <el-button 
                  size="small"
                  @click="handleBatchRss"
                  :disabled="loading"
                  icon="el-icon-link"
                  circle
                ></el-button>
              </el-tooltip>
              <div class="refresh-section">
                <el-button
                  type="primary"
                  @click="handleManualRefresh"
                  :loading="false"
                  class="refresh-button progress-button"
                  :class="{'custom-loading': loading}"
                  round
                >
                  <div class="button-content">
                    <span v-if="loading" class="loading-spinner"></span>
                    <span class="button-text">{{ loading ? `${loadingProgress}%` : '刷新数据' }}</span>
                  </div>
                  <div v-if="loading" class="button-progress" :style="{ width: `${loadingProgress}%` }"></div>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 搜索区域和控件组，移除scrolled类 -->
      <div class="search-controls-container">
        <!-- 搜索框 -->
        <el-input
            v-model="searchQuery"
            placeholder="搜索仓库..."
            prefix-icon="el-icon-search"
            clearable
            class="search-input"
        />

        <!-- 控件区域 -->
        <div class="view-filter-controls">
          <div class="control-group">
            <div class="control-label">视图：</div>
            <div class="view-controls">
              <el-tooltip content="列表视图" placement="top">
                <div class="icon-button" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">
                  <AppIcon name="tickets" />
                </div>
              </el-tooltip>
              <el-tooltip content="日历视图" placement="top">
                <div class="icon-button" :class="{ active: viewMode === 'calendar' }" @click="viewMode = 'calendar'">
                  <AppIcon name="date" />
                </div>
              </el-tooltip>
            </div>
          </div>

          <div class="control-group">
            <div class="control-label">筛选：</div>
            <div class="filter-controls">
              <el-tooltip content="显示全部" placement="top">
                <div class="icon-button" :class="{ active: filterType === 'all' }" @click="filterType = 'all'">
                  <AppIcon name="document" />
                </div>
              </el-tooltip>
              <el-tooltip content="仅源代码（无下载内容）" placement="top">
                <div class="icon-button" :class="{ active: filterType === 'source' }" @click="filterType = 'source'">
                  <AppIcon name="document-delete" />
                </div>
              </el-tooltip>
              <el-tooltip content="包含二进制" placement="top">
                <div class="icon-button" :class="{ active: filterType === 'binary' }" @click="filterType = 'binary'">
                  <AppIcon name="download" />
                </div>
              </el-tooltip>
            </div>
          </div>
        </div>
      </div>

      <!-- 主内容区域使用左右布局 -->
      <div class="main-content">
        <!-- 左侧足迹区域 -->
        <div class="footprints-section">
          <el-card class="footprints-card">
            <template #header>
              <div class="footprints-header">
                <span>我的足迹</span>
                <el-tooltip content="刷新足迹" placement="top">
                  <div
                    class="icon-button refresh-icon"
                    :class="{ 'is-loading': logsLoading }"
                    @click="fetchClickLogs(1)"
                  >
                    <AppIcon name="refresh" />
                    <span v-if="logsLoading" class="loading-indicator"></span>
                  </div>
                </el-tooltip>
              </div>
            </template>

            <div v-if="logsLoading" class="logs-loading">加载中...</div>
            <el-alert v-else-if="logsError" :title="logsError" type="error" show-icon :closable="false" />
            <div v-else-if="clickLogs.length === 0" class="logs-empty">您还没有留下任何足迹哦！</div>
            <div v-else class="footprints-content">
              <el-timeline>
                <el-timeline-item
                  v-for="log in clickLogs"
                  :key="log.id"
                  :timestamp="formatLogTime(log.click_time)"
                  placement="top"
                  type="primary"
                >
                  <div class="footprint-item">
                    <div class="repo-name">
                      <a :href="`https://github.com/${log.repo_name}`" target="_blank">
                        {{ log.repo_name.split('/')[1] }}
                      </a>
                    </div>
                    <div class="release-info">
                      <el-tag
                        size="small"
                        type="success"
                        class="clickable-tag"
                        @click="goToRelease(log.repo_name, log.release_tag)"
                      >{{ log.release_tag }}</el-tag>
                    </div>
                  </div>
                </el-timeline-item>
              </el-timeline>

              <!-- 足迹分页器 -->
              <div v-if="logsTotal > logsPageSize" class="logs-pagination">
                <el-pagination
                  small
                  background
                  @current-change="handleLogsPageChange"
                  :current-page="logsCurrentPage"
                  :page-size="logsPageSize"
                  layout="prev, pager, next"
                  :total="logsTotal"
                >
                </el-pagination>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 右侧主内容区域 -->
        <div class="main-section">
          <!-- 添加日历视图 -->
          <el-card v-if="viewMode === 'calendar'" class="calendar-card">
            <div class="custom-calendar-header">
              <span class="current-month">{{ formatCalendarHeader(calendarDate) }}</span>
              <div class="calendar-controls">
                <el-button-group>
                  <el-button size="small" @click="handlePrevMonth" class="calendar-control-btn">上个月</el-button>
                  <el-button size="small" @click="handleNextMonth" class="calendar-control-btn">下个月</el-button>
                </el-button-group>
                <el-button size="small" type="primary" @click="handleToday" class="calendar-control-btn">今天</el-button>
              </div>
            </div>
            <el-calendar v-model="calendarDate">
              <!-- 不使用原有的header插槽 -->
              <template #dateCell="{ data }">
                <div class="calendar-cell" :class="{ 
                  'today': isToday(data.day),
                  'highlight-calendar-cell': data.day === highlightCalendarDate 
                }">
                  <p :class="{
                    'calendar-day': true,
                    'weekend': isWeekend(data.day),
                    'other-month': !isCurrentMonth(data.day)
                  }">
                    {{ data.day.split('-').slice(-1)[0] }}
                  </p>
                  <div class="releases-summary">
                    <template v-if="getReleasesForDate(data.day).length > 0">
                      <el-tooltip
                        v-if="getReleasesForDate(data.day).length === 1"
                        :content="getReleasesForDate(data.day)[0].repo_name"
                        placement="top"
                      >
                        <a
                          class="single-release"
                          :href="getReleasesForDate(data.day)[0].latest_release.html_url"
                          target="_blank"
                          @click="recordClick(getReleasesForDate(data.day)[0].repo_name, getReleasesForDate(data.day)[0].latest_release.tag_name, getReleasesForDate(data.day)[0].latest_release.published_at)"
                        >
                          {{ getReleasesForDate(data.day)[0].repo_name.split('/')[1] }}
                          <span class="single-release-version">
                            {{ getReleasesForDate(data.day)[0].latest_release.tag_name }}
                            <span v-if="isPreRelease(getReleasesForDate(data.day)[0].latest_release)"
                                  class="pre-badge">预发布</span>
                          </span>
                        </a>
                      </el-tooltip>
                      <el-popover
                        v-else
                        placement="top"
                        trigger="hover"
                        :width="280"
                        popper-class="releases-popover"
                      >
                        <template #reference>
                          <div class="multiple-releases">
                            {{ getReleasesForDate(data.day).length }} 个更新
                          </div>
                        </template>
                        <div class="releases-list-popup">
                          <a
                            v-for="release in getReleasesForDate(data.day)"
                            :key="release.repo_name"
                            class="release-item"
                            target="_blank"
                            :href="release.latest_release.html_url"
                            @click="recordClick(release.repo_name, release.latest_release.tag_name, release.latest_release.published_at)"
                          >
                            <div class="release-item-content">
                              <div class="release-main-info">
                                <span class="repo-name">{{ release.repo_name.split('/')[1] }}</span>
                                <span class="release-version">
                                  {{ release.latest_release.tag_name }}
                                  <span v-if="isPreRelease(release.latest_release)"
                                        class="pre-badge">预发布</span>
                                </span>
                              </div>
                              <div class="release-time">{{ formatTime(release.latest_release.published_at) }}</div>
                            </div>
                            <a
                              class="release-detail-link"
                              :href="release.latest_release.html_url"
                              target="_blank"
                            >
                              查看详情
                            </a>
                          </a>
                        </div>
                      </el-popover>
                    </template>
                    <!-- 修改：最后活动提示 -->
                    <div v-if="isLastActivityDate(data.day)" class="last-activity-indicator">
                      <el-tooltip content="上次活动" placement="top">
                        <AppIcon name="user" />
                      </el-tooltip>
                    </div>
                  </div>
                </div>
              </template>
            </el-calendar>
          </el-card>

          <el-card v-if="error" class="error-card">
            <el-alert
                :title="error"
                type="error"
                show-icon
            />
          </el-card>

          <!-- 仓库列表 -->
          <div v-else-if="viewMode === 'list'" class="releases-list">
            <el-card
              v-for="repo in paginatedRepos"
              :key="repo.repo_name"
              :data-repo-name="repo.repo_name"
              class="repo-card"
            >
              <div class="repo-header">
                <div class="repo-title">
                  <img
                    v-if="repo.avatar_url"
                    :src="repo.avatar_url"
                    class="repo-avatar"
                    :alt="repo.repo_name"
                  />
                  <div class="repo-info">
                    <h3>
                      <a
                        :href="'https://github.com/' + repo.repo_name"
                        target="_blank"
                        @click="recordClick(repo.repo_name, repo.latest_release.tag_name, repo.latest_release.published_at)"
                      >
                        {{ repo.repo_name }}
                      </a>
                      <el-tooltip content="复制RSS链接" placement="top">
                        <div class="rss-icon-container" @mouseenter="setHoverRepo(repo.repo_name)" @mouseleave="setHoverRepo(null)" @click.stop="copyToClipboard(`https://github.com/${repo.repo_name}/releases.atom`)">
                          <img :src="isHoverRepo(repo.repo_name) ? '/rss_true.png' : '/rss_false.png'" class="rss-icon" alt="RSS" />
                        </div>
                      </el-tooltip>
                    </h3>
                    <p v-if="repo.description" class="repo-description">
                      {{ repo.description }}
                    </p>
                  </div>
                  <!-- 将发布时间移到这里，与标题相对居中 -->
                  <div class="release-date-container">
                    <span class="release-date">{{ formatDate(repo.latest_release.published_at) }}</span>
                  </div>
                </div>
              </div>

              <div class="release-content">
                <h4>
                  <div class="release-info-left">
                    <a
                      :href="repo.latest_release.html_url"
                      target="_blank"
                      @click="recordClick(repo.repo_name, repo.latest_release.tag_name, repo.latest_release.published_at)"
                    >
                      {{ repo.latest_release.name || repo.latest_release.tag_name }}
                    </a>
                    <el-tag
                      v-if="isPreRelease(repo.latest_release)"
                      size="small"
                      type="warning"
                      class="release-type-tag"
                    >
                      预发布
                    </el-tag>
                    <el-tag
                      v-else
                      size="small"
                      type="success"
                      class="release-type-tag"
                    >
                      正式版
                    </el-tag>
                  </div>
                  <!-- 移除这里的发布时间 -->
                </h4>
                <div v-if="isSourceCodeOnly(repo.latest_release)" class="source-code-notice">
                  <el-tag size="small" type="info">仅包含源代码</el-tag>
                </div>
                <div class="markdown-wrapper" v-if="repo.latest_release.body">
                  <div
                    class="markdown-body"
                    :class="{ 'collapsed': needsExpansion(repo.latest_release.body) && !expandedRepos.includes(repo.repo_name) }"
                    v-html="renderMarkdown(repo.latest_release.body)"
                  ></div>
                  <div
                    class="expand-button"
                    v-if="needsExpansion(repo.latest_release.body)"
                    @click="toggleExpand(repo.repo_name)"
                  >
                    {{ expandedRepos.includes(repo.repo_name) ? '收起' : '展开' }}
                  </div>
                </div>
                <div class="release-footer">
                  <el-button
                    type="text"
                    @click="openAllReleases(repo.latest_release.all_releases_url, repo.repo_name, repo.latest_release.tag_name, repo.latest_release.published_at)"
                  >
                    查看所有版本
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 分页器 -->
          <div v-if="viewMode === 'list'" class="pagination-container">
            <el-pagination
              background
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="currentPage"
              :page-sizes="[10, 20, 50, 100]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="filteredRepos.length"
            >
            </el-pagination>
          </div>
        </div>
      </div>
      
      <!-- 添加GitHub项目链接，移到main-content外部 -->
      <div class="github-footer">
        <a href="https://github.com/xiaocuanChina/get_github_releases_info" target="_blank">
          <GitHubLogo :size="24" />
          访问 GitHub 项目仓库
        </a>
      </div>
    </template>

    <!-- 添加 RSS 对话框 -->
    <el-dialog
      title="RSS 订阅链接"
      :visible.sync="rssDialogVisible"
      width="60%"
      :close-on-click-modal="false"
    >
      <div v-loading="rssLoading">
        <div v-if="rssMode === 'single'" class="single-rss-container">
          <p>您可以使用以下链接订阅 {{ currentRepoName }} 的 Releases:</p>
          <div class="rss-link-container">
            <el-input v-model="singleRssLink" readonly></el-input>
            <el-button type="primary" @click="copyToClipboard(singleRssLink)">复制</el-button>
          </div>
        </div>
        <div v-else-if="rssMode === 'batch'" class="batch-rss-container">
          <div class="batch-rss-header">
            <p>已为您生成 {{ batchRssLinks.length }} 个订阅链接：</p>
            <div class="batch-actions">
              <el-button size="small" type="primary" @click="copyAllRssLinks">一键复制所有链接</el-button>
              <el-button size="small" type="success" @click="downloadOpml">下载 OPML 文件</el-button>
            </div>
          </div>
          
          <!-- 添加搜索框 -->
          <div class="rss-search-box">
            <el-input
              v-model="rssSearchQuery"
              placeholder="搜索仓库名称..."
              prefix-icon="el-icon-search"
              clearable
            ></el-input>
          </div>
          
          <el-table 
            :data="filteredRssLinks" 
            style="width: 100%" 
            height="350px" 
            border
          >
            <el-table-column prop="repo_name" label="仓库名称" width="180"></el-table-column>
            <el-table-column prop="rss_link" label="RSS 链接" show-overflow-tooltip>
              <template slot-scope="scope">
                <div class="table-rss-link">
                  <span>{{ scope.row.rss_link }}</span>
                  <el-button 
                    size="mini" 
                    type="text" 
                    @click="copyToClipboard(scope.row.rss_link)"
                    icon="el-icon-document-copy"
                  >复制</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import { format, isToday, isWeekend, isSameMonth, parseISO } from 'date-fns'
import { marked } from 'marked'
import DOMPurify from 'dompurify'  // 用于防止 XSS 攻击
import GitHubLogin from '@/auth/GitHubLogin.vue'  // 修改导入路径
import { zhCN } from 'date-fns/locale'
import { API_ENDPOINTS } from '@/api/config'  // 导入 API 配置
import GitHubLogo from '@/components/GitHubLogo.vue'  // 导入 GitHubLogo 组件

export default {
  name: 'StarredReleases',

  components: {
    'github-login': GitHubLogin,  // 确保组件名称匹配模板中使用的名称
    GitHubLogo  // 确保组件名称匹配模板中使用的名称
  },

  data() {
    return {
      releases: [],
      loading: false,
      error: null,
      searchQuery: '',
      currentPage: 1,
      pageSize: 10,
      filterType: 'all',  // 添加筛选类型
      isAuthenticated: false,
      accessToken: null,
      userInfo: null, // 添加用户信息
      expandedRepos: [], // 用于跟踪展开状态的仓库列表
      maxCollapsedHeight: 300, // 收起状态下的最大高度（像素）
      contentHeights: {}, // 缓存内容高度
      cacheExpireTime: 5 * 60 * 1000, // 缓存有效期，默认5分钟
      lastFetchTime: null,
      minFetchInterval: 5 * 60 * 1000, // 5分钟
      viewMode: 'list',
      calendarDate: new Date(),
      loadingProgress: 0,
      loadingMessage: '正在加载数据...',
      totalRepos: 0,
      processedRepos: 0,
      clickLogs: [],
      logsLoading: false,
      logsError: null,
      logsCurrentPage: 1,
      logsPageSize: 6, // 增加每页数量
      logsTotal: 0,
      lastActivityTime: null, // 修改：存储最后活动时间
      rssDialogVisible: false,
      rssLoading: false,
      rssMode: 'single', // 'single' 或 'batch'
      currentRepoName: '',
      singleRssLink: '',
      batchRssLinks: [],
      rssSearchQuery: '', // 添加RSS搜索查询
      highlightCalendarDate: null, // 需要在日历中高亮显示的日期
      hoverRepoName: null, // 添加鼠标悬浮的仓库名
    }
  },

  computed: {
    filteredRepos() {
      let result = this.releases;

      // 先按筛选类型过滤
      if (this.filterType !== 'all') {
        result = result.filter(repo => {
          const isSourceOnly = this.isSourceCodeOnly(repo.latest_release)
          return this.filterType === 'source' ? isSourceOnly : !isSourceOnly
        })
      }

      // 再按搜索关键词过滤
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase()
        result = result.filter(repo =>
          repo.repo_name.toLowerCase().includes(query)
        )
      }

      return result
    },
    paginatedRepos() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return this.filteredRepos.slice(start, end)
    },
    progressButtonStyle() {
      if (!this.loading) return {}

      return {
        background: `linear-gradient(to right, 
          var(--el-color-primary) 0%, 
          var(--el-color-primary) ${this.loadingProgress}%, 
          rgba(144, 147, 153, 0.3) ${this.loadingProgress}%, 
          rgba(144, 147, 153, 0.3) 100%)`
      }
    },
    filteredRssLinks() {
      if (!this.rssSearchQuery) {
        return this.batchRssLinks;
      }
      
      const query = this.rssSearchQuery.toLowerCase();
      return this.batchRssLinks.filter(item => 
        item.repo_name.toLowerCase().includes(query)
      );
    }
  },

  methods: {
    async fetchUserInfo() {
      try {
        const response = await axios.get(API_ENDPOINTS.AUTH_VERIFY.replace('/verify', '/user'), {
          headers: {
            Authorization: `Bearer ${this.accessToken}`
          }
        })
        this.userInfo = response.data
        // 注意：此处的 /user 端点通常不直接返回聚合的活动时间，
        // verify 端点是获取这个信息的地方。checkAuthStatus 已处理。
        // 如果确实需要在这里也获取，需要确认 /user 端点是否也返回了。
        // 暂时注释掉，依赖 checkAuthStatus 的设置
        // this.lastActivityTime = response.data.last_activity_time
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    },

    handleLogout() {
      this.$confirm('确定要退出登录吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        localStorage.removeItem('github_token')
        this.clearCache() // 清除缓存
        this.isAuthenticated = false
        this.userInfo = null
        this.accessToken = null
        this.releases = []
        this.$message({
          type: 'success',
          message: '已退出登录'
        })
      }).catch(() => {
        // 取消退出
      })
    },

    async checkAuthStatus() {
      const storedToken = localStorage.getItem('github_token')
      if (storedToken) {
        try {
          const response = await axios.get(API_ENDPOINTS.AUTH_VERIFY, {
            headers: {
              Authorization: `Bearer ${storedToken}`
            }
          })

          if (response.data.status === 'success') {
            this.accessToken = storedToken
            this.isAuthenticated = true
            this.userInfo = response.data.user
            this.lastActivityTime = response.data.user.last_activity_time // 修改：存储最后活动时间

            // 检查是否需要重新获取数据
            const now = new Date().getTime()
            const lastFetch = localStorage.getItem('last_fetch_time')

            if (!lastFetch || (now - parseInt(lastFetch)) > this.minFetchInterval) {
              await this.fetchReleases()
            } else {
              // 使用缓存的数据
              const cachedData = localStorage.getItem('releases_cache')
              if (cachedData) {
                this.releases = JSON.parse(cachedData)
                console.log('使用本地缓存数据')
              }
            }
            return true
          }
        } catch (error) {
          console.error('Token 验证失败:', error)
          this.clearCache()
          // ... 其他错误处理 ...
        }
      }
      return false
    },

    async handleCallback(code) {
      try {
        const response = await axios.get(`${API_ENDPOINTS.AUTH_CALLBACK}?code=${code}`)
        this.accessToken = response.data.access_token
        this.isAuthenticated = true
        localStorage.setItem('github_token', this.accessToken)

        // 获取用户信息
        await this.fetchUserInfo()
        await this.fetchReleases()

        // 清除 URL 中的 code 参数
        window.history.replaceState({}, document.title, window.location.pathname)

        // 如果有保存的重定向地址，则跳转回去
        const redirectUrl = localStorage.getItem('redirect_after_login')
        if (redirectUrl) {
          localStorage.removeItem('redirect_after_login')
          window.location.href = redirectUrl
        }
      } catch (error) {
        console.error('认证失败:', error)
        this.error = 'GitHub 认证失败'
        this.isAuthenticated = false
        localStorage.removeItem('github_token')
      }
    },

    async fetchReleases(forceRefresh = false) {
      try {
        this.loading = true
        this.error = null
        this.loadingProgress = 0
        this.loadingMessage = '正在获取仓库列表...'
        this.processedRepos = 0

        // 创建 EventSource 连接
        const eventSource = new EventSource(`${API_ENDPOINTS.STARRED_RELEASES_PROGRESS}?token=${this.accessToken}&force_refresh=${forceRefresh}`)

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data)
          // 确保进度值为整数，避免小数点导致的渲染问题
          this.loadingProgress = Math.round(data.progress)
          this.loadingMessage = data.message
          this.processedRepos = data.processed_repos || 0
          this.totalRepos = data.total_repos || 0

          if (data.status === 'complete') {
            this.releases = data.releases
            localStorage.setItem('releases_cache', JSON.stringify(this.releases))
            localStorage.setItem('last_fetch_time', new Date().getTime().toString())

            // 完成后关闭连接
            eventSource.close()
            setTimeout(() => {
              this.loading = false
            }, 500)
          }
        }

        eventSource.onerror = (error) => {
          console.error('EventSource failed:', error)
          eventSource.close()
          this.loading = false
          this.error = '获取数据失败'
        }

      } catch (error) {
        this.loading = false
        this.loadingProgress = 0
        this.loadingMessage = '加载失败'

        if (error.response?.status === 429) {
          this.$message({
            type: 'warning',
            message: '请求过于频繁，请稍后再试',
            duration: 5000
          })
        } else {
          this.error = error.response?.data?.detail || '获取数据失败'
        }
      }
    },

    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1  // 重置到第一页
    },

    handleCurrentChange(val) {
      this.currentPage = val
    },

    formatDate(dateString) {
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm')
    },

    formatTime(dateString) {
      const date = new Date(dateString);
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      return `${hours}:${minutes}`;
    },

    renderMarkdown(text) {
      const html = DOMPurify.sanitize(marked(text))
      // 在下一个 tick 中处理图片加载
      this.$nextTick(() => {
        this.handleImages()
      })
      return html
    },

    handleImages() {
      // 获取所有 markdown 内容中的图片
      const images = document.querySelectorAll('.markdown-body img')
      images.forEach(img => {
        // 添加加载事件监听器
        img.onload = () => {
          img.classList.add('loaded')
        }
        // 添加错误处理
        img.onerror = () => {
          img.style.display = 'none'
        }
        // 如果图片已经加载完成
        if (img.complete) {
          img.classList.add('loaded')
        }
      })
    },

    truncateText(text, maxLength) {
      if (text.length <= maxLength) return text
      return text.substr(0, maxLength) + '...'
    },

    openAllReleases(url, repoName, releaseTag, releasePublishedAt) {
      if (url) {
        this.recordClick(repoName, releaseTag, releasePublishedAt);
        window.open(url, '_blank');
      }
    },

    isSourceCodeOnly(release) {
      if (!release.assets || release.assets.length === 0) {
        // 如果没有自定义资源，只有自动生成的源代码
        return true
      }
      // 检查是否所有资源都是源代码文件
      return release.assets.every(asset =>
        asset.name.endsWith('.zip') ||
        asset.name.endsWith('.tar.gz') ||
        asset.name.endsWith('.tar.xz')
      )
    },

    toggleExpand(repoName) {
      const index = this.expandedRepos.indexOf(repoName)
      if (index === -1) {
        this.expandedRepos.push(repoName)
      } else {
        this.expandedRepos.splice(index, 1)
      }
    },

    needsExpansion(content) {
      if (!content) return false

      const cacheKey = content.substring(0, 100)
      if (this.contentHeights[cacheKey] !== undefined) {
        return this.contentHeights[cacheKey] > this.maxCollapsedHeight
      }

      const temp = document.createElement('div')
      temp.className = 'markdown-body'
      temp.style.position = 'absolute'
      temp.style.visibility = 'hidden'
      temp.style.width = this.$el.querySelector('.markdown-wrapper')?.offsetWidth + 'px'
      temp.innerHTML = this.renderMarkdown(content)
      document.body.appendChild(temp)

      // 等待图片加载完成后再计算高度
      const images = temp.getElementsByTagName('img')
      if (images.length > 0) {
        Array.from(images).forEach(img => {
          img.style.maxWidth = '100%'
          img.style.height = 'auto'
        })
      }

      const height = temp.offsetHeight
      document.body.removeChild(temp)

      this.contentHeights[cacheKey] = height
      return height > this.maxCollapsedHeight
    },

    shouldShowExpandButton(content) {
      return this.needsExpansion(content)
    },

    // 新增：从缓存加载数据
    async loadFromCache() {
      const cachedData = localStorage.getItem('releases_cache')
      const cacheTime = localStorage.getItem('releases_cache_time')

      if (cachedData && cacheTime) {
        const now = new Date().getTime()
        const cacheAge = now - parseInt(cacheTime)

        if (cacheAge < this.cacheExpireTime) {
          // 缓存未过期，使用缓存数据
          this.releases = JSON.parse(cachedData)
          console.log('从缓存加载数据')
          return
        }
      }
      // 缓存不存在或已过期，重新获取数据
      await this.fetchReleases()
    },

    // 新增：清除缓存
    clearCache() {
      localStorage.removeItem('releases_cache')
      localStorage.removeItem('last_fetch_time')
    },

    // 手动刷新数据的方法
    async handleManualRefresh() {
      await this.fetchReleases(true)  // 传入 true 表示强制刷新
    },

    getReleasesForDate(dateString) {
      return this.releases.filter(release => {
        const releaseDate = format(new Date(release.latest_release.published_at), 'yyyy-MM-dd')
        return releaseDate === dateString
      })
    },

    scrollToRelease(repoName) {
      if (this.viewMode === 'calendar') {
        this.viewMode = 'list'
        this.$nextTick(() => {
          const element = document.querySelector(`[data-repo-name="${repoName}"]`)
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' })
            // 添加高亮效果
            element.classList.add('highlight')
            setTimeout(() => {
              element.classList.remove('highlight')
            }, 2000)
          }
        })
      }
    },

    isNewRelease(publishedAt) {
      const now = new Date();
      const publishDate = new Date(publishedAt);
      const timeDiff = now - publishDate;
      const hoursDiff = timeDiff / (1000 * 60 * 60);

      // 如果发布时间在24小时内，则认为是最新版本
      return hoursDiff <= 24;
    },

    isPreRelease(release) {
      return release.prerelease;
    },

    formatCalendarHeader(date) {
      // 确保参数是Date对象
      const dateObj = date instanceof Date ? date : new Date(date);
      return format(dateObj, 'yyyy年 MM月', { locale: zhCN });
    },

    isToday(dateString) {
      return isToday(new Date(dateString))
    },

    isWeekend(dateString) {
      return isWeekend(new Date(dateString))
    },

    isCurrentMonth(dateString) {
      return isSameMonth(new Date(dateString), this.calendarDate)
    },

    handlePrevMonth() {
      const newDate = new Date(this.calendarDate)
      newDate.setMonth(newDate.getMonth() - 1)
      this.calendarDate = newDate
    },

    handleNextMonth() {
      const newDate = new Date(this.calendarDate)
      newDate.setMonth(newDate.getMonth() + 1)
      this.calendarDate = newDate
    },

    handleToday() {
      this.calendarDate = new Date()
    },

    // 添加进度格式化方法
    progressFormat(percentage) {
      return percentage === 100 ? '完成' : `${percentage}%`
    },

    handleLogin() {
      // 直接跳转到后端的 GitHub 认证端点
      window.location.href = API_ENDPOINTS.AUTH_GITHUB;
    },

    async recordClick(repoName, releaseTag, releasePublishedAt) {
      if (!this.accessToken) return;
      try {
        await axios.post(API_ENDPOINTS.RECORD_CLICK,
          {
            repo_name: repoName,
            release_tag: releaseTag,
            release_published_at: releasePublishedAt
          },
          {
            headers: { Authorization: `Bearer ${this.accessToken}` }
          }
        );
      } catch (error) {
        console.error('Failed to record click:', error);
      }
    },

    // 获取点击日志
    async fetchClickLogs(page = 1) {
      if (!this.accessToken) return;
      console.log(`[fetchClickLogs] Attempting to fetch logs for page: ${page}`);
      this.logsLoading = true;
      this.logsError = null;
      this.logsCurrentPage = page;
      try {
        const response = await axios.get(API_ENDPOINTS.CLICK_LOGS, {
          headers: { Authorization: `Bearer ${this.accessToken}` },
          params: { page: this.logsCurrentPage, limit: this.logsPageSize }
        });
        console.log('[fetchClickLogs] Raw API Response:', response);
        if (response.data.status === 'success') {
          this.clickLogs = response.data.logs;
          this.logsTotal = response.data.total;
          console.log('[fetchClickLogs] Processed clickLogs:', JSON.parse(JSON.stringify(this.clickLogs)), 'Total logs:', this.logsTotal);
        } else {
          throw new Error(response.data.message || '获取日志失败');
        }
      } catch (error) {
        console.error('Failed to fetch click logs:', error);
        this.logsError = `获取点击记录失败: ${error.message || '请稍后再试'}`;
        this.clickLogs = [];
        this.logsTotal = 0;
      } finally {
        this.logsLoading = false;
        console.log('[fetchClickLogs] Finished fetching logs. Loading state:', this.logsLoading);
      }
    },

    // 处理日志分页改变
    handleLogsPageChange(newPage) {
      this.fetchClickLogs(newPage);
    },

    // 添加：跳转到发布页面
    goToRelease(repoName, releaseTag) {
      const releaseUrl = `https://github.com/${repoName}/releases/tag/${releaseTag}`;
      window.open(releaseUrl, '_blank');
    },

    // 修改：格式化日志中的点击时间
    formatLogTime(isoString) {
      if (!isoString) return '-';
      try {
        const date = parseISO(isoString);
        return format(date, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
      } catch (e) {
        return isoString;
      }
    },

    // 跳转到列表中最接近指定时间的项目
    jumpToNearestTimeInList(targetTimeStr) {
      if (!targetTimeStr || this.viewMode !== 'list') {
        return;
      }

      try {
        const targetTime = new Date(targetTimeStr).getTime();

        // 计算每个项目与目标时间的时间差
        const timeDistances = this.releases.map((repo, index) => {
          const repoTime = new Date(repo.latest_release.published_at).getTime();
          return {
            index,
            repoName: repo.repo_name,
            distance: Math.abs(repoTime - targetTime)
          };
        });

        // 按时间差排序，找出最接近的项目
        const nearestRepo = timeDistances.sort((a, b) => a.distance - b.distance)[0];

        if (nearestRepo) {
          // 计算该项目在哪一页
          const repoIndex = this.releases.findIndex(r => r.repo_name === nearestRepo.repoName);
          if (repoIndex === -1) return;

          // 计算目标页码
          const targetPage = Math.floor(repoIndex / this.pageSize) + 1;

          // 先设置当前页
          this.currentPage = targetPage;

          // 等待DOM更新后滚动到对应元素
          this.$nextTick(() => {
            const element = document.querySelector(`[data-repo-name="${nearestRepo.repoName}"]`);
            if (element) {
              // 先清除可能存在的其他高亮元素
              document.querySelectorAll('.highlight').forEach(el => {
                if (el !== element) {
                  el.classList.remove('highlight');
                }
              });

              // 平滑滚动到目标元素
              element.scrollIntoView({ behavior: 'smooth', block: 'center' });

              // 添加高亮效果
              element.classList.add('highlight');

              // 延长高亮显示时间
              setTimeout(() => {
                // 使用渐变过渡移除高亮
                element.style.transition = 'all 1s ease-out';
                element.style.boxShadow = '0 0 0 rgba(64, 158, 255, 0)';
                element.style.border = '1px solid transparent';

                // 完全移除高亮类
                setTimeout(() => {
                  element.classList.remove('highlight');
                  element.style.transition = '';
                  element.style.boxShadow = '';
                  element.style.border = '';
                }, 1000);
              }, 2000);

              //// 显示提示消息
              //this.$message({
              //  message: `已跳转到最接近该时间的项目: ${nearestRepo.repoName.split('/')[1]}`,
              //  type: 'success',
              //  duration: 3000
              //});
            }
          });
        }
      } catch (error) {
        console.error('跳转到最近时间项目失败:', error);
        this.$message.error('跳转失败，请重试');
      }
    },

    // 为时间轴时间戳添加点击事件处理器
    addTimelineClickHandlers() {
      // 获取所有时间轴时间戳元素
      const timestamps = document.querySelectorAll('.footprints-section .el-timeline-item__timestamp')

      timestamps.forEach(el => {
        // 移除旧的事件监听器（避免重复添加）
        el.removeEventListener('click', this.handleTimeStampClick)

        // 添加新的点击样式和事件监听器
        el.classList.add('timeline-timestamp-clickable')
        el.setAttribute('title', '点击跳转到列表中最接近该时间的项目')

        // 为每个时间戳绑定点击事件
        el.addEventListener('click', this.handleTimeStampClick)
      })
    },

    // 处理时间戳点击事件
    handleTimeStampClick(event) {
      // 获取对应的日志项（通过DOM关系查找）
      const timelineItem = event.target.closest('.el-timeline-item')
      if (!timelineItem) return

      // 获取日志项索引
      const index = Array.from(timelineItem.parentNode.children).indexOf(timelineItem)
      if (index === -1 || index >= this.clickLogs.length) return

      // 获取对应的日志数据
      const log = this.clickLogs[index]
      
      // 如果当前是列表视图，跳转到列表中最接近的项目
      if (this.viewMode === 'list') {
        this.jumpToNearestTimeInList(log.click_time)
      } else if (this.viewMode === 'calendar') {
        // 如果当前是日历视图，跳转到对应的日期
        this.jumpToDateInCalendar(log.click_time)
      }
    },

    // 新增：格式化日志中的发布时间
    formatReleaseTime(isoString) {
      if (!isoString) return '-';
      try {
        const date = parseISO(isoString);
        return format(date, 'yyyy-MM-dd HH:mm', { locale: zhCN }); // 省略秒
      } catch (e) {
        return isoString;
      }
    },

    // 修改：检查是否为最后活动日期
    isLastActivityDate(dateString) {
      if (!this.lastActivityTime) return false;
      try {
        // click_time 存储的是带时区的 ISO 格式，直接转 Date 对象比较日期部分
        const activityDate = format(new Date(this.lastActivityTime), 'yyyy-MM-dd');
        return activityDate === dateString;
      } catch (e) {
        console.error("解析最后活动时间失败:", e);
        return false;
      }
    },

    // 复制单个仓库的RSS链接
    async copyRssLink(repoName) {
      this.rssMode = 'single';
      this.currentRepoName = repoName;
      this.rssLoading = true;
      this.rssDialogVisible = true;
      
      try {
        const response = await axios.get(`${API_ENDPOINTS.REPO_RSS_LINK}/${repoName}`);
        if (response.data.status === 'success') {
          this.singleRssLink = response.data.rss_link;
        } else {
          this.$message.error('获取RSS链接失败');
        }
      } catch (error) {
        console.error('获取RSS链接失败:', error);
        this.$message.error('获取RSS链接失败');
      } finally {
        this.rssLoading = false;
      }
    },
    
    // 批量获取RSS链接
    async handleBatchRss() {
      this.rssMode = 'batch';
      this.rssLoading = true;
      this.rssDialogVisible = true;
      this.batchRssLinks = [];
      
      try {
        const response = await axios.get(API_ENDPOINTS.ALL_STARRED_RSS, {
          headers: {
            Authorization: `Bearer ${this.accessToken}`
          }
        });
        
        if (response.data.status === 'success') {
          this.batchRssLinks = response.data.data;
        } else {
          this.$message.error('获取RSS链接失败');
        }
      } catch (error) {
        console.error('批量获取RSS链接失败:', error);
        this.$message.error('批量获取RSS链接失败');
      } finally {
        this.rssLoading = false;
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
    
    // 复制所有RSS链接
    copyAllRssLinks() {
      const linkTexts = this.batchRssLinks.map(item => item.rss_link).join('\n');
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
      
      this.batchRssLinks.forEach(item => {
        opmlContent += `
      <outline type="rss" text="${item.repo_name}" title="${item.repo_name}" xmlUrl="${item.rss_link}" htmlUrl="https://github.com/${item.repo_name}/releases"/>`;
      });
      
      opmlContent += `
    </outline>
  </body>
</opml>`;
      
      // 创建下载
      const blob = new Blob([opmlContent], { type: 'text/xml' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'github_starred_releases.opml';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      this.$message.success('OPML文件已下载');
    },

    // 添加跳转到日历特定日期的方法
    jumpToDateInCalendar(timeStr) {
      if (!timeStr) return;
      
      try {
        // 解析时间
        const targetDate = new Date(timeStr);
        
        // 设置日历显示的月份
        this.calendarDate = new Date(
          targetDate.getFullYear(),
          targetDate.getMonth(),
          1
        );
        
        // 标记需要高亮的日期
        this.highlightCalendarDate = format(targetDate, 'yyyy-MM-dd');
        
        // 显示提示消息
        this.$message({
          message: `已跳转到日历中的 ${format(targetDate, 'yyyy-MM-dd')} 日期`,
          type: 'success',
          duration: 3000
        });
        
        // 3秒后取消高亮
        setTimeout(() => {
          this.highlightCalendarDate = null;
        }, 3000);
        
      } catch (error) {
        console.error('跳转到日历日期失败:', error);
        this.$message.error('日期跳转失败，请重试');
      }
    },

    // 设置当前悬浮的仓库名
    setHoverRepo(repoName) {
      this.hoverRepoName = repoName;
    },
    
    // 判断是否是当前悬浮的仓库
    isHoverRepo(repoName) {
      return this.hoverRepoName === repoName;
    },
  },

  async mounted() {
    // 检查 URL 中是否有认证码
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')

    if (code) {
      await this.handleCallback(code)
    } else {
      // 检查存储的 token 是否有效
      const isAuthenticated = await this.checkAuthStatus()
      if (isAuthenticated) {
        await this.fetchReleases()
        // 添加：自动加载足迹数据
        this.fetchClickLogs(1)

        // 为时间轴时间戳添加点击事件
        this.$nextTick(() => {
          this.addTimelineClickHandlers()
        })
      }
    }
  },

  beforeUnmount() {
    // 移除滚动事件监听器
    // window.removeEventListener('scroll', this.handleScroll);
  },

  updated() {
    // 在组件更新后重新添加事件监听器
    this.$nextTick(() => {
      this.addTimelineClickHandlers()
    })
  },

  watch: {
    searchQuery() {
      this.currentPage = 1
    },
    filterType() {  // 添加对筛选类型的监听
      this.currentPage = 1
    }
  }
}
</script>

<style scoped>
.releases-container {
  max-width: 1600px; /* 保持页面宽度 */
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box; /* 确保padding不会增加宽度 */
}

.header-card {
  margin-bottom: 20px;
  min-height: 120px;
  border-radius: 12px;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  max-width: 300px;
}

.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

/* 卡片圆角样式 */
:deep(.el-card) {
  border-radius: 12px;
  overflow: hidden;
  transition: box-shadow 0.3s;
  width: 100%; /* 所有卡片统一宽度 */
  box-sizing: border-box;
}

:deep(.el-card:hover) {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.05);
}

:deep(.el-card__body) {
  border-radius: 12px;
}

/* 按钮圆角样式 */
:deep(.el-button) {
  border-radius: 20px;
}

:deep(.el-tag) {
  border-radius: 10px;
}

/* 输入框圆角 */
:deep(.el-input__inner) {
  border-radius: 20px;
}

/* 搜索区域和控件样式 */
.search-controls-container {
  position: sticky;
  top: 0;
  background-color: #fff;
  z-index: 100;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 15px;
  width: 100%;
  box-sizing: border-box;
}

.search-input {
  flex: 1;
  min-width: 300px;
  margin: 0;
}

.view-filter-controls {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
}

/* 控件组样式 */
.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
}

.control-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

/* 视图和筛选控件样式 */
.view-controls, .filter-controls {
  display: flex;
  gap: 6px;
  background-color: #f5f7fa;
  border-radius: 20px;
  padding: 4px;
}

/* 图标按钮样式 */
.icon-button {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: transparent;
  color: #606266;
}

.icon-button:hover {
  background-color: #e6e9ed;
  transform: translateY(-2px);
}

.icon-button.active {
  background-color: #409EFF;
  color: white;
}

.icon-button .el-icon {
  font-size: 16px;
}

/* 主内容区域左右布局 */
.main-content {
  display: flex;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
}

/* 左侧足迹区域 */
.footprints-section {
  width: 300px;
  flex-shrink: 0;
}

/* 右侧主内容区域 */
.main-section {
  flex: 1; /* 占据剩余空间 */
  min-width: 0; /* 避免flex项目溢出 */
}

.footprints-card {
  position: sticky;
  top: 90px; /* 增加顶部距离，与搜索栏保持更远的距离 */
  height: calc(100vh - 260px); /* 调整高度 */
  display: flex;
  flex-direction: column;
}

:deep(.footprints-card .el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.footprints-content {
  max-height: none;
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  position: relative;
}

/* 用户信息样式 */
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid #eaeaea;
  transition: all 0.3s;
}

.user-avatar:hover {
  transform: scale(1.1);
  border-color: #409eff;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  text-decoration: none;
  transition: all 0.3s;
}

.username:hover {
  color: #409eff;
  text-decoration: underline;
}

.logout-btn {
  margin-left: auto;
  opacity: 1 !important;
  transition: all 0.3s;
}

.logout-btn:hover {
  transform: translateY(-2px);
  opacity: 0.9 !important;
}

/* 左侧足迹区域 */
.footprints-card {
  position: sticky;
  top: 90px; /* 增加顶部距离，与搜索栏保持更远的距离 */
}

.footprints-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footprints-content {
  max-height: none;
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  position: relative;
}

/* GitHub项目链接样式 */
.github-footer {
  margin-top: 20px;
  text-align: center;
  padding: 15px 0;
  border-top: 1px solid #eee;
  border-radius: 0 0 12px 12px;
  background-color: #f8f9fa;
  width: 100%; /* 设置宽度为100% */
  box-sizing: border-box;
}

.github-footer a {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  text-decoration: none;
  transition: color 0.3s, transform 0.3s, box-shadow 0.3s;
  font-size: 14px;
  padding: 10px 20px;
  border-radius: 20px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-width: 200px; /* 设置最小宽度 */
}

.github-footer a:hover {
  color: #409EFF;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 刷新相关样式 */
.refresh-section {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  width: 120px;
}

.refresh-button {
  width: 100%;
}

/* 注释掉原有进度条样式
.refresh-progress {
  margin-top: 4px;
  width: 100%;
}
*/

/* 新增进度按钮样式 */
.progress-button {
  position: relative;
  overflow: hidden;
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 2;
}

.button-text {
  position: relative;
  z-index: 2;
  color: white !important; /* 强制文字始终为白色 */
}

/* 自定义加载状态 */
.custom-loading {
  pointer-events: none; /* 防止重复点击 */
  background-color: rgba(64, 144, 255, 0.3) !important; /* 保持淡蓝色背景 */
  border-color: transparent !important; /* 移除边框 */
}

/* 自定义加载动画 */
.loading-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid white;
  border-radius: 50%;
  border-top-color: transparent;
  margin-right: 8px; /* 调整为右边距，使其位于文字左侧 */
  animation: spin 1s linear infinite;
  position: relative;
  z-index: 2;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.button-progress {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background-color:#409eff; /* 主色调进度条 */
  transition: width 0.3s ease;
  z-index: 1;
  border-radius: 20px 0 0 20px; /* 保持左侧圆角 */
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.5); /* 添加蓝色阴影 */
}

/* 当宽度达到100%时，右侧也需要圆角 */
.button-progress[style*="width: 100%"] {
  border-radius: 20px;
}

.refresh-button.is-loading {
  background-color: rgba(64, 144, 255, 0.3) !important; /* 保持淡蓝色背景 */
  border-color: transparent !important; /* 移除边框 */
}

/* 添加额外的视觉效果增强对比度 */
.button-progress::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to right, rgba(255,255,255,0.1), rgba(255,255,255,0.2));
  border-radius: inherit;
}

/* 确保没有其他加载动画干扰 */
:deep(.el-button .el-icon) {
  display: none !important; /* 隐藏所有的 Element 图标 */
}

:deep(.el-button.is-loading .el-icon),
:deep(.el-button.is-loading .el-icon.is-loading) {
  display: none !important; /* 强制隐藏加载图标 */
}

:deep(.el-button.is-loading)::before {
  display: none !important; /* 移除原生加载状态的背景遮罩 */
}

.header-right {
  position: relative;
}

/* 确保任何状态下按钮文字都是白色 */
:deep(.el-button) {
  color: white;
}

/* 确保加载状态下图标也是白色 */
:deep(.el-button.is-loading .el-icon) {
  color: white !important;
}

/* Markdown 内容样式 */
.markdown-body {
  transition: max-height 0.3s ease-out;
  width: 100%;
  overflow-x: hidden;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
  border-radius: 8px;
}

/* Markdown 中的图片样式 */
.markdown-body img {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  background-color: #fff;
  border-style: none;
  box-sizing: border-box;
  margin: 16px 0; /* 调整上下间距 */
  border: 1px solid #d0d7de; /* GitHub 风格的边框 */
  border-radius: 8px;
  box-shadow: none;
  opacity: 0;
  transition: opacity 0.2s ease-in;
}

.markdown-body img.loaded {
  opacity: 1;
}

/* 确保图片容器样式 */
.markdown-wrapper {
  width: 100%;
  overflow-x: hidden;
  padding: 16px;
  background-color: #fff;
  border-radius: 8px;
}

/* 优化收起状态的样式 */
.markdown-body.collapsed {
  max-height: 300px;
  overflow: hidden;
  position: relative;
}

/* 渐变遮罩效果 */
.markdown-body.collapsed::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 60px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 1) 100%);
  pointer-events: none;
  border-radius: 0 0 8px 8px;
}

/* 展开按钮样式 */
.expand-button {
  text-align: center;
  padding: 8px;
  color: #0969da; /* GitHub 的链接蓝色 */
  cursor: pointer;
  position: relative;
  margin-top: -20px;
  z-index: 1;
  background: none;
  border: none;
  font-size: 14px;
  border-radius: 20px;
}

.expand-button:hover {
  color: #1a7f37; /* GitHub 的悬停颜色 */
  text-decoration: underline;
}

/* 分页样式 */
.pagination-container {
  margin-top: 20px;
  text-align: center;
}

/* 标题样式 */
h2 {
  margin: 0;
  margin-bottom: 4px;
}

/* 日历卡片样式 */
.calendar-card {
  margin-top: 0px; /* 移除顶部边距 */
  margin-bottom: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 260px); /* 改为与足迹区域高度一致 */
  overflow: hidden; /* 添加溢出隐藏 */
}

:deep(.calendar-card .el-card__body) {
  padding: 8px;
  height: 100%; /* 修改为100%高度 */
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 添加溢出隐藏 */
}

:deep(.calendar-card .el-calendar) {
  height: 100%; /* 改为100%高度 */
  display: flex;
  flex-direction: column;
  padding: 0;
  margin: 0;
  overflow: hidden; /* 改为隐藏溢出 */
}

:deep(.calendar-card .el-calendar__body) {
  flex: 1; /* 改为弹性布局，占据剩余空间 */
  overflow: auto; /* 改为可滚动 */
}

:deep(.el-calendar__header) {
  padding: 6px 10px;
  display: flex;
  justify-content: space-between;
  margin-bottom: 0;
}

/* 确保按钮文字可见 */
:deep(.el-button) {
  min-width: auto;
  padding: 8px 15px;
}

:deep(.el-button.is-text) {
  min-width: auto;
}

/* 确保日历表头按钮内容可见 */
:deep(.el-calendar__button-group .el-button-group) {
  display: flex;
  align-items: center;
}

:deep(.el-calendar__button-group .el-button) {
  min-width: 70px;
  white-space: nowrap;
  overflow: visible;
  padding: 8px 12px;
}

/* 保持原有的隐藏样式，但移除position:absolute以避免影响布局 */
:deep(.el-calendar__title) {
  visibility: hidden;
  height: 0;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

:deep(.el-button-group .el-button) {
  margin: 0;
}

:deep(.el-calendar-table th) {
  padding: 8px;
  text-align: center;
  border-bottom: 1px solid #EBEEF5;
}

:deep(.el-calendar-table td) {
  height: auto;
  border-bottom: 1px solid #EBEEF5;
  border-right: 1px solid #EBEEF5;
}

:deep(.el-calendar-table td:last-child) {
  border-right: none;
}

:deep(.el-calendar-table .el-calendar-day) {
  height: 100%;
  padding: 0;
  display: flex;
}

/* 错误卡片样式 */
.error-card {
  margin-bottom: 20px;
}

/* 仓库卡片圆角 */
.repo-card {
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
  margin-bottom: 20px;
}

.repo-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.repo-title {
  display: flex;
  align-items: center; /* 保持垂直居中对齐 */
  gap: 12px; /* 调整头像与文字的间距 */
  position: relative; /* 为绝对定位提供参考 */
}

.repo-avatar {
  width: 32px; /* 保持项目头像尺寸 */
  height: 32px;
  border-radius: 4px;
  flex-shrink: 0;
  align-self: center; /* 确保头像始终垂直居中 */
}

.repo-info {
  flex: 1;
  display: flex; /* 保持flex布局 */
  flex-direction: column; /* 修改为垂直方向排列 */
  justify-content: center; /* 垂直居中 */
}

.repo-info h3 {
  margin: 0; /* 移除标题的外边距 */
  margin-bottom: 4px; /* 标题与描述之间的间距 */
  line-height: 1.4; /* 调整行高 */
}

.repo-description {
  margin: 0; /* 移除描述的外边距 */
  color: #606266;
  font-size: 14px;
  overflow: hidden; /* 隐藏溢出部分 */
  text-overflow: ellipsis; /* 显示省略号 */
  white-space: nowrap; /* 防止文本换行 */
  line-height: 1.4; /* 与标题保持一致的行高 */
}

/* 发布日期容器样式 */
.release-date-container {
  margin-left: auto; /* 推到最右侧 */
  display: flex;
  align-items: center;
  height: 100%;
}

.release-date {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}

/* 版本信息和状态标签的间距 */
.release-info-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px; /* 增加标签之间的间距 */
}

.release-type-tag {
  margin-left: 10px; /* 增加版本和标签之间的间距 */
}

/* 添加可点击标签的样式 */
.clickable-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.clickable-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 为时间轴时间戳添加可点击样式 */
:deep(.timeline-timestamp-clickable) {
  cursor: pointer !important;
  transition: all 0.3s;
  position: relative;
  display: inline-block !important;
}

:deep(.timeline-timestamp-clickable:hover) {
  color: #409EFF !important;
  text-decoration: underline;
}

:deep(.timeline-timestamp-clickable::after) {
  content: none; /* 移除箭头图标 */
}

:deep(.timeline-timestamp-clickable:hover::after) {
  opacity: 1;
  color: #409EFF;
}

/* 修改时间轴样式，让内容更紧凑 */
:deep(.el-timeline-item__wrapper) {
  padding-left: 24px;
}

:deep(.el-timeline-item__timestamp) {
  margin-bottom: 6px;
  line-height: 1.2;
}

:deep(.el-timeline-item__tail) {
  left: 6px;
}

:deep(.el-timeline-item__node) {
  left: 6px;
}

/* 分页器圆角 */
:deep(.el-pagination .el-pager li) {
  border-radius: 4px;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  border-radius: 4px;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .main-content {
    flex-direction: column;
  }

  .footprints-section {
    width: 100%;
    margin-bottom: 20px;
  }

  .main-section {
    width: 100%; /* 在小屏幕上占据全宽 */
  }

  .search-controls-container {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    width: 100%;
    margin-bottom: 10px;
  }

  .view-filter-controls {
    width: 100%;
    justify-content: center;
  }

  .footprints-content {
    max-height: 400px;
  }
}

/* 更小的屏幕 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }

  .header-left, .header-right {
    width: 100%;
  }

  .refresh-section {
    width: 100%;
  }

  .control-group {
    margin-bottom: 8px;
  }

  .repo-info {
    /* 已经是垂直布局，不需要改变 */
  }

  .repo-description {
    white-space: normal; /* 小屏幕上允许文本换行 */
    -webkit-line-clamp: 2; /* 最多显示两行 */
    display: -webkit-box;
    -webkit-box-orient: vertical;
    white-space: normal;
  }
}

/* 添加高亮效果样式 */
.highlight {
  animation: highlight-pulse 2s ease-in-out;
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.8);
  border: 1px solid #409EFF;
}

@keyframes highlight-pulse {
  0% {
    background-color: rgba(64, 158, 255, 0.1);
    transform: scale(1);
  }
  50% {
    background-color: rgba(64, 158, 255, 0.2);
    transform: scale(1.01);
  }
  100% {
    background-color: transparent;
    transform: scale(1);
  }
}

/* 调整足迹项目布局 */
.footprint-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.footprint-item .repo-name {
  margin-right: 12px; /* 增加项目名称和标签之间的间距 */
  flex: 1;
}

.footprint-item .release-info {
  flex-shrink: 0;
  margin-left: 8px; /* 增加左边距 */
}

/* 日历相关样式 */
.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  width: 100%;
  padding: 0 10px;
}

.current-month {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.calendar-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  opacity: 1; /* 确保始终可见 */
  transition: none; /* 移除过渡效果 */
}

/* 覆盖Element UI可能的隐藏逻辑 */
:deep(.el-calendar__header) {
  display: none !important; /* 隐藏原始头部 */
}

:deep(.el-calendar__body) {
  padding-top: 12px; /* 弥补头部隐藏后的间距 */
}

/* 确保自定义头部显示 */
:deep(.el-calendar > .el-calendar__header + .calendar-header) {
  display: flex !important;
}

/* 调整按钮大小和可见性 */
.calendar-control-btn {
  min-width: 60px;
  opacity: 1 !important;
  visibility: visible !important;
}

.calendar-control-btn[type="primary"] {
  color: #fff !important;
}

/* 确保日历体正常显示 */
:deep(.el-calendar) {
  display: flex;
  flex-direction: column;
}

:deep(.el-calendar-table td) {
  height: auto;
}

:deep(.el-calendar-table .el-calendar-day) {
  height: 100%;
  padding: 0;
  display: flex;
}

.calendar-cell.today {
  background-color: rgba(64, 158, 255, 0.1);
}

.calendar-day {
  margin: 0;
  padding: 0 3px;
  text-align: right;
  font-size: 13px;
  color: #606266;
  border-radius: 4px;
}

.calendar-day.weekend {
  color: #f56c6c;
}

.calendar-day.other-month {
  opacity: 0.5;
}

/* 发布项目样式 */
.releases-summary {
  margin-top: 3px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow: auto; /* 改为可滚动 */
  max-height: none; /* 移除高度限制 */
}

.single-release {
  display: block;
  background-color: #f0f9eb;
  color: #67c23a;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.3s;
}

.single-release:hover {
  background-color: #e1f3d8;
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.single-release-version {
  margin-left: 4px;
  font-size: 11px;
  opacity: 0.8;
  white-space: nowrap;
}

.pre-badge {
  font-size: 10px;
  background-color: #fdf6ec;
  color: #e6a23c;
  padding: 1px 3px;
  border-radius: 3px;
  margin-left: 3px;
}

.multiple-releases {
  background-color: #ecf5ff;
  color: #409eff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.multiple-releases:hover {
  background-color: #d9ecff;
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 弹出层样式 */
:deep(.releases-popover) {
  padding: 0;
  max-height: 300px;
  overflow-y: auto;
}

.releases-list-popup {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.release-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #ebeef5;
  text-decoration: none;
  color: #606266;
}

.release-item:last-child {
  border-bottom: none;
}

.release-item-content {
  flex: 1;
  overflow: hidden;
}

.release-main-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.release-main-info .repo-name {
  font-weight: bold;
  color: #303133;
}

.release-version {
  font-size: 12px;
  color: #67c23a;
}

.release-time {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.release-detail-link {
  font-size: 12px;
  color: #409eff;
  margin-left: 8px;
  flex-shrink: 0;
}

/* 最后活动指示器 */
.last-activity-indicator {
  position: absolute;
  top: 5px;
  right: 5px;
  color: #409eff;
  font-size: 14px;
  z-index: 2;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 加载状态 */
.logs-loading {
  text-align: center;
  color: #909399;
  padding: 20px;
}

/* 空状态 */
.logs-empty {
  text-align: center;
  color: #909399;
  padding: 20px;
}

/* 分页器 */
.logs-pagination {
  margin-top: 15px;
  text-align: center;
}

/* 确保日历控制按钮的文字可见 */
.calendar-control-btn {
  color: #606266 !important;
}

.calendar-control-btn[type="primary"] {
  color: #fff !important;
}

:deep(.el-button--default) {
  color: #606266 !important;
}

:deep(.el-button--primary) {
  color: #fff !important;
}

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
  align-items: center;
  margin-bottom: 15px;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.table-rss-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 添加头部新样式 */
.action-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 调整头部样式 */
.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

/* RSS图标样式 */
.rss-icon-container {
  display: inline-flex;
  margin-left: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.rss-icon-container:hover {
  transform: scale(1.2);
}

.rss-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

/* RSS搜索框样式 */
.rss-search-box {
  margin-bottom: 15px;
}

/* 调整repo-info样式 */
.repo-info h3 {
  display: flex;
  align-items: center;
}

/* 表格样式调整 */
:deep(.el-table) {
  margin-top: 15px;
}

/* 日历单元格高亮样式 */
.highlight-calendar-cell {
  animation: calendar-highlight-pulse 3s ease-in-out;
  box-shadow: inset 0 0 0 2px #409eff;
  background-color: rgba(64, 158, 255, 0.1);
}

@keyframes calendar-highlight-pulse {
  0% {
    box-shadow: inset 0 0 0 2px #409eff;
    background-color: rgba(64, 158, 255, 0.3);
  }
  50% {
    box-shadow: inset 0 0 0 3px #409eff;
    background-color: rgba(64, 158, 255, 0.2);
  }
  100% {
    box-shadow: inset 0 0 0 2px #409eff;
    background-color: rgba(64, 158, 255, 0.1);
  }
}

/* 恢复日历单元格样式 */
.calendar-cell {
  height: 100%;
  min-height: 60px;
  max-height: none; /* 移除最大高度限制 */
  padding: 5px;
  border-radius: 6px;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden; /* 防止内容溢出 */
}

/* 添加自定义日历头部样式 */
.custom-calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 8px 10px;
  border-bottom: 1px solid #ebeef5;
}

.custom-calendar-header .current-month {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.custom-calendar-header .calendar-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 隐藏Element UI原生日历头部 */
:deep(.el-calendar__header) {
  display: none !important;
}

/* 覆盖按钮文本颜色 */
.calendar-control-btn {
  min-width: 60px;
}

.calendar-control-btn[type="primary"] {
  color: #fff !important;
}

/* 确保任何状态下按钮文字都是白色 */
:deep(.el-button) {
  color: white;
}

/* 确保加载状态下图标也是白色 */
:deep(.el-button.is-loading .el-icon) {
  color: white !important;
}

/* 添加对文本按钮的特殊处理，让它们在页面上可见 */
:deep(.el-button--text) {
  color: #409EFF !important; /* 使用主题蓝色 */
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 4px;
  opacity: 1 !important;
  visibility: visible !important;
}

:deep(.el-button--text:hover) {
  color: #66b1ff !important; /* 悬停时颜色稍浅 */
  background-color: rgba(64, 158, 255, 0.1);
}

/* 特别处理release-footer中的按钮 */
.release-footer {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #eee;
}

.release-footer .el-button {
  margin-left: 0;
}

/* 表格中的文本按钮样式 */
:deep(.el-table .el-button--text) {
  color: #409EFF !important;
  padding: 3px 8px;
  font-size: 12px;
  opacity: 1 !important;
  visibility: visible !important;
}

/* 调整表格链接样式 */
.table-rss-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-rss-link .el-button {
  margin-left: 8px;
  white-space: nowrap;
}

/* 确保有背景色的按钮文字为白色 */
:deep(.el-button--primary),
:deep(.el-button--success),
:deep(.el-button--warning),
:deep(.el-button--danger),
:deep(.el-button--info) {
  color: white !important;
}

/* 原始样式设置 */
:deep(.el-button) {
  color: inherit; /* 使用默认颜色 */
}

/* 确保加载状态下图标也是白色 */
:deep(.el-button.is-loading .el-icon) {
  color: white !important;
}

/* 添加对文本按钮的特殊处理，让它们在页面上可见 */
:deep(.el-button--text) {
  color: #409EFF !important; /* 使用主题蓝色 */
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 4px;
  opacity: 1 !important;
  visibility: visible !important;
}

:deep(.el-button--text:hover) {
  color: #66b1ff !important; /* 悬停时颜色稍浅 */
  background-color: rgba(64, 158, 255, 0.1);
}

/* 特别处理release-footer中的按钮 */
.release-footer {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #eee;
}

.release-footer .el-button {
  margin-left: 0;
}

/* 表格中的文本按钮样式 */
:deep(.el-table .el-button--text) {
  color: #409EFF !important;
  padding: 3px 8px;
  font-size: 12px;
  opacity: 1 !important;
  visibility: visible !important;
}

/* 清除之前错误的全局设置 */
:deep(.el-button--default) {
  color: #606266 !important; /* 默认按钮文字颜色 */
}
</style>

<!-- 添加全局样式，使日历控制按钮始终可见 -->
<style>
/* 覆盖Element UI日历控件的默认行为 */
.el-calendar-table .el-calendar-day .el-calendar-day__layer {
  opacity: 1 !important;
  visibility: visible !important;
}

.el-calendar__header .el-calendar__button-group {
  opacity: 1 !important;
  visibility: visible !important;
  transition: none !important;
  display: flex !important;
}

.el-calendar__header:hover .el-calendar__button-group {
  opacity: 1 !important;
}
</style>
