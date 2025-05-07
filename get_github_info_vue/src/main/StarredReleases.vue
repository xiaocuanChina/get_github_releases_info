<template>
  <div class="releases-container">
    <!-- 未登录时显示登录组件 -->
    <github-login v-if="!isAuthenticated" />

    <!-- 登录后显示主内容 -->
    <template v-else>
      <el-card class="header-card">
        <div class="header">
          <div class="header-left">
            <div class="title-section">
              <h2>GitHub Starred Releases</h2>
              <div class="user-info" v-if="userInfo">
                <img :src="userInfo.avatar_url" class="user-avatar" :alt="userInfo.login">
                <span class="username">{{ userInfo.login }}</span>
                <!-- <el-button type="text" @click="showLogsDialog" class="logs-button">查看日志</el-button> -->
                <el-button type="text" @click="handleLogout" class="logout-btn">退出登录</el-button>
              </div>
            </div>
          </div>
          <div class="header-right">
            <el-radio-group v-model="viewMode" size="small" class="view-mode-group">
              <el-radio-button label="list">列表视图</el-radio-button>
              <el-radio-button label="calendar">日历视图</el-radio-button>
            </el-radio-group>
            <el-radio-group v-model="filterType" size="small" class="filter-group">
              <el-radio-button label="all">全部</el-radio-button>
              <el-radio-button label="source">仅源代码</el-radio-button>
              <el-radio-button label="binary">包含二进制</el-radio-button>
            </el-radio-group>
            <div class="refresh-section">
              <el-button
                type="primary"
                @click="handleManualRefresh"
                :loading="loading"
                class="refresh-button"
              >
                刷新数据
              </el-button>
              <!-- 进度条 -->
              <div v-if="loading" class="refresh-progress">
                <el-progress
                  :percentage="loadingProgress"
                  :stroke-width="2"
                  :show-text="false"
                  status="success"
                />
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 添加日历视图 -->
      <el-card v-if="viewMode === 'calendar'" class="calendar-card">
        <el-calendar v-model="calendarDate">
          <template #header="{ date }">
            <div class="calendar-header">
              <span class="current-month">{{ formatCalendarHeader(date) }}</span>
              <div class="calendar-controls">
                <el-button-group>
                  <el-button size="small" @click="handlePrevMonth">上个月</el-button>
                  <el-button size="small" @click="handleNextMonth">下个月</el-button>
                </el-button-group>
                <el-button size="small" type="primary" @click="handleToday">今天</el-button>
              </div>
            </div>
          </template>
          <template #dateCell="{ data }">
            <div class="calendar-cell" :class="{ 'today': isToday(data.day) }">
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
                    <el-icon><UserFilled /></el-icon>
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

      <!-- 搜索框 -->
      <el-input
          v-model="searchQuery"
          placeholder="搜索仓库..."
          prefix-icon="el-icon-search"
          clearable
          class="search-input"
      />

      <!-- 仓库列表 -->
      <div class="releases-list">
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
                </h3>
                <p v-if="repo.description" class="repo-description">
                  {{ repo.description }}
                </p>
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
              <span class="release-date">{{ formatDate(repo.latest_release.published_at) }}</span>
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
      <div class="pagination-container">
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

      <!-- 新增：日志弹窗 -->
      <el-dialog
        title="最近点击记录"
        v-model="logsDialogVisible"
        width="70%"
        top="5vh"
      >
        <div v-if="logsLoading" class="logs-loading">加载中...</div>
        <el-alert v-else-if="logsError" :title="logsError" type="error" show-icon :closable="false" />
        <div v-else-if="clickLogs.length === 0" class="logs-empty">暂无记录</div>
        <div v-else>
          <el-table :data="clickLogs" stripe style="width: 100%" size="small" height="calc(80vh - 150px)">
            <el-table-column prop="repo_name" label="仓库" min-width="200" show-overflow-tooltip></el-table-column>
            <el-table-column prop="release_tag" label="版本标签" min-width="150" show-overflow-tooltip></el-table-column>
            <el-table-column label="版本发布时间" min-width="170">
              <template #default="scope">
                <span>{{ formatReleaseTime(scope.row.release_published_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="最近点击时间" min-width="170">
              <template #default="scope">
                <span>{{ formatLogTime(scope.row.click_time) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="logs-pagination-container" v-if="logsTotal > logsPageSize">
            <el-pagination
              background
              small
              @current-change="handleLogsPageChange"
              :current-page="logsCurrentPage"
              :page-size="logsPageSize"
              layout="total, prev, pager, next"
              :total="logsTotal"
            >
            </el-pagination>
          </div>
        </div>
        <template #footer>
          <el-button @click="logsDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="fetchClickLogs(1)" :loading="logsLoading">刷新</el-button>
        </template>
      </el-dialog>
    </template>
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

export default {
  name: 'StarredReleases',

  components: {
    'github-login': GitHubLogin  // 确保组件名称匹配模板中使用的名称
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
      logsPageSize: 15, // 增加每页数量
      logsTotal: 0,
      logsDialogVisible: false, // 控制日志弹窗
      lastActivityTime: null, // 修改：存储最后活动时间
    }
  },

  computed: {
    filteredRepos() {
      let result = this.releases

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
          var(--el-color-primary) ${this.loadingProgress}%,
          var(--el-color-primary-light-3) ${this.loadingProgress}%)`
      }
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
          this.loadingProgress = data.progress
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
      return format(date, 'yyyy年 MM月', { locale: zhCN })
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

    // 新增：显示日志弹窗的方法
    async showLogsDialog() {
      console.log('showLogsDialog method called');
      this.logsDialogVisible = true;
      await this.$nextTick(); // 等待 DOM 更新
      console.log('logsDialogVisible 状态:', this.logsDialogVisible); // 确认状态
      // 首次打开、日志为空且不在加载中时加载
      if (this.clickLogs.length === 0 && !this.logsLoading) {
          this.fetchClickLogs(1);
      }
    },

    // 获取点击日志 (参数和错误处理不变，只是调用的地方变了)
    async fetchClickLogs(page = 1) {
      if (!this.accessToken) return;
      this.logsLoading = true;
      this.logsError = null;
      this.logsCurrentPage = page;
      try {
        const response = await axios.get(API_ENDPOINTS.CLICK_LOGS, {
          headers: { Authorization: `Bearer ${this.accessToken}` },
          params: { page: this.logsCurrentPage, limit: this.logsPageSize }
        });
        if (response.data.status === 'success') {
          this.clickLogs = response.data.logs;
          this.logsTotal = response.data.total;
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
      }
    },

    // 格式化日志中的点击时间
    formatLogTime(isoString) {
      if (!isoString) return '-';
      try {
        const date = parseISO(isoString);
        return format(date, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
      } catch (e) {
        return isoString;
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

    // 处理日志分页改变
    handleLogsPageChange(newPage) {
      this.fetchClickLogs(newPage);
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
      }
    }
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  min-height: 120px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-input {
  margin: 20px 0;
}

.repo-card {
  margin-bottom: 20px;
}

.repo-header {
  margin-bottom: 15px;
}

.repo-header a {
  color: #409EFF;
  text-decoration: none;
}

.release-content {
  padding: 15px;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.release-date {
  font-size: 0.9em;
  color: #666;
  margin-left: 10px;
}

.release-footer {
  margin-top: 15px;
  text-align: right;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

h4 {
  margin: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.release-body {
  margin-top: 10px;
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
}

.error-card {
  margin-bottom: 20px;
}

/* Markdown 内容样式 */
.markdown-body {
  transition: max-height 0.3s ease-out;
  width: 100%;
  overflow-x: hidden;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
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
  border-radius: 6px;
}

/* 移除不必要的阴影效果 */
.markdown-body img {
  box-shadow: none;
}

/* 确保图片容器样式 */
.markdown-wrapper {
  width: 100%;
  overflow-x: hidden;
  padding: 16px;
  background-color: #fff;
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
}

.expand-button:hover {
  color: #1a7f37; /* GitHub 的悬停颜色 */
  text-decoration: underline;
}

/* 图片加载动画 */
.markdown-body img {
  opacity: 0;
  transition: opacity 0.2s ease-in;
}

.markdown-body img.loaded {
  opacity: 1;
}

/* 链接中的图片特殊处理 */
.markdown-body a img {
  border: 1px solid rgba(31, 35, 40, 0.15);
}

/* 表格中的图片处理 */
.markdown-body table img {
  margin: 0;
  border: none;
}

/* 添加分页样式 */
.pagination-container {
  margin-top: 20px;
  text-align: center;
}

.source-code-notice {
  margin: 8px 0;
  color: #909399;
}

.source-code-notice .el-tag {
  margin-right: 8px;
}

.filter-group {
  margin-right: 10px;
}

/* 调整标题样式 */
h2 {
  margin: 0;
  margin-bottom: 4px;
}

/* 确保头部布局正确 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.repo-title {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.repo-avatar {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  flex-shrink: 0;
}

.repo-info {
  flex: 1;
}

.repo-info h3 {
  margin: 0;
  line-height: 1.4;
}

.repo-description {
  margin: 4px 0 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 0;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
}

.user-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.username {
  font-size: 14px;
  color: #606266;
}

.logout-btn {
  color: #F56C6C;
  padding: 0;
}

.logout-btn:hover {
  color: #f78989;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 添加日历视图相关样式 */
.calendar-card {
  margin-top: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
}

.current-month {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.calendar-controls {
  display: flex;
  gap: 8px;
}

.calendar-cell {
  height: 100%;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.calendar-cell.today {
  background-color: rgba(64, 158, 255, 0.1);
}

.calendar-day {
  margin: 0;
  padding: 4px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}

.calendar-day.weekend {
  color: #F56C6C;
}

.calendar-day.other-month {
  color: #C0C4CC;
}

.releases-summary {
  margin-top: 4px;
  min-height: 40px;
}

.single-release {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 8px;
  background-color: #F2F6FC;
  border-radius: 4px;
  transition: all 0.3s;
  text-decoration: none;
  color: #409EFF;
}

.single-release:hover {
  background-color: #ECF5FF;
  transform: translateY(-1px);
}

.single-release-version {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #67C23A;
}

.multiple-releases {
  display: inline-block;
  padding: 4px 8px;
  background-color: #F0F9EB;
  color: #67C23A;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.multiple-releases:hover {
  background-color: #E1F3D8;
  transform: translateY(-1px);
}

.releases-list-popup {
  max-height: 300px;
  overflow-y: auto;
}

.release-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #EBEEF5;
  text-decoration: none;
  color: inherit;
  transition: background-color 0.3s;
}

.release-item:last-child {
  border-bottom: none;
}

.release-item:hover {
  background-color: #F5F7FA;
}

.release-item-content {
  flex: 1;
  min-width: 0;
  margin-right: 12px;
}

.release-main-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.repo-name {
  font-weight: 500;
  color: #303133;
}

.release-version {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #67C23A;
  font-size: 12px;
}

.release-time {
  font-size: 12px;
  color: #909399;
}

.pre-badge {
  background-color: #E6A23C;
  color: white;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 2px;
  font-weight: normal;
}

:deep(.el-calendar-table) {
  border-collapse: separate;
  border-spacing: 4px;
}

:deep(.el-calendar-table td) {
  border: none;
  padding: 0;
}

:deep(.el-calendar-table .el-calendar-day) {
  height: 110px;
  padding: 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  transition: all 0.3s;
}

:deep(.el-calendar-table .el-calendar-day:hover) {
  box-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 自定义滚动条样式 */
.releases-list-popup::-webkit-scrollbar {
  width: 6px;
}

.releases-list-popup::-webkit-scrollbar-thumb {
  background-color: #E4E7ED;
  border-radius: 3px;
}

.releases-list-popup::-webkit-scrollbar-track {
  background-color: #F5F7FA;
}

/* 弹出框样式 */
:deep(.releases-popover) {
  padding: 0;
  border-radius: 8px;
}

/* 添加高亮动画效果 */
@keyframes highlight-pulse {
  0% { background-color: transparent; }
  50% { background-color: rgba(64, 158, 255, 0.1); }
  100% { background-color: transparent; }
}

.highlight {
  animation: highlight-pulse 2s ease-in-out;
}

.refresh-section {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  width: 120px; /* 固定宽度 */
}

.refresh-button {
  width: 100%;
}

.refresh-progress {
  margin-top: 4px;
  width: 100%;
}

/* 添加 release 类型标签样式 */
.release-type-tag {
  margin-left: 8px;
  vertical-align: middle;
}

/* 新增样式，用于左侧内容对齐 */
.release-info-left {
  display: flex;
  align-items: center;
  gap: 8px; /* 在链接和标签之间添加一些间距 */
}

/* 新增日志按钮样式 */
.logs-button {
  margin-left: 10px; /* 调整与其他按钮的间距 */
  padding: 0 5px; /* 微调内边距 */
  color: #409EFF; /* 保持链接颜色 */
}
.logs-button:hover {
  color: #66b1ff;
}

/* 弹窗内分页器样式 */
.logs-pagination-container {
  margin-top: 15px;
  text-align: right; /* 改为右对齐 */
}

/* 弹窗内加载/空状态 */
.logs-loading,
.logs-empty {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

/* 修改：最后活动日期指示器样式 */
.last-activity-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  color: #E6A23C; /* 使用一个醒目的颜色 */
  font-size: 14px;
  cursor: help;
}

/* 可以给弹窗的表格设置一个最大高度，使其可滚动 */
:deep(.el-dialog__body) {
  padding-top: 10px;
  padding-bottom: 10px;
}
</style>
