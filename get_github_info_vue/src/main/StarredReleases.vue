<template>
  <div class="releases-container">
    <!-- 未登录时显示登录组件 -->
    <GitHubLogin v-if="!isAuthenticated" @auth-success="handleAuthSuccess" />

    <!-- 调试帮助组件，仅在未登录状态下显示 -->
    <div v-if="!isAuthenticated" class="debug-helper-container">
      <el-button type="text" @click="showDebugHelper = !showDebugHelper">
        {{ showDebugHelper ? '关闭' : '显示' }}认证调试助手
      </el-button>
      <DebugHelper v-if="showDebugHelper" />
    </div>

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
                <a :href="'https://github.com/' + userInfo.login" target="_blank" class="username">{{
                    userInfo.login
                  }}</a>
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
                    @click="handleBatchRss(false)"
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
        <!-- 这个区域已移到搜索工具栏中，这里不再需要 -->

        <!-- 搜索控制工具栏 -->
        <div class="search-toolbar">
          <!-- 左侧：搜索范围选择 -->
          <div class="search-scope-selector">
            <div class="control-label">搜索范围：</div>
            <div class="view-controls">
              <el-tooltip content="在已收藏的仓库中搜索" placement="top">
                <div class="icon-button" :class="{ active: searchScope === 'starred' }" @click="searchScope = 'starred'">
                  <i class="el-icon-star-off"></i>
                </div>
              </el-tooltip>
              <el-tooltip content="在全局GitHub中搜索" placement="top">
                <div class="icon-button" :class="{ active: searchScope === 'global' }" @click="searchScope = 'global'">
                  <i class="el-icon-place"></i>
                </div>
              </el-tooltip>
            </div>
          </div>
          
          <!-- 中间：搜索框 -->
          <div class="search-input-wrapper">
            <el-input
                v-model="searchQuery"
                :placeholder="searchScope === 'starred' ? '搜索仓库...' : '在GitHub中搜索...'"
                prefix-icon="el-icon-search"
                clearable
                class="search-input"
                @keyup="handleSearchKeyPress"
            >
              <!-- 全局搜索按钮 -->
              <template v-if="searchScope === 'global'" #append>
                <el-button @click="handleGlobalSearch" icon="el-icon-search" class="global-search-btn">搜索</el-button>
              </template>
            </el-input>
          </div>
          
          <!-- 右侧：控制栏和提示 -->
          <div class="controls-and-tips">
            <!-- 控件区域 -->
            <div v-if="searchScope === 'starred'" class="controls-container">
              <div class="view-filter-controls">
                <div class="control-group">
                  <div class="control-label">视图：</div>
                  <div class="view-controls">
                    <el-tooltip content="列表视图" placement="top">
                      <div class="icon-button" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">
                        <i class="el-icon-tickets"></i>
                      </div>
                    </el-tooltip>
                    <el-tooltip content="日历视图" placement="top">
                      <div class="icon-button" :class="{ active: viewMode === 'calendar' }" @click="viewMode = 'calendar'">
                        <i class="el-icon-date"></i>
                      </div>
                    </el-tooltip>
                  </div>
                </div>

                <div class="control-group">
                  <div class="control-label">内容：</div>
                  <div class="filter-controls">
                    <el-tooltip content="显示全部" placement="top">
                      <div class="icon-button" :class="{ active: contentFilter === 'all' }" @click="contentFilter = 'all'">
                        <i class="el-icon-view"></i>
                      </div>
                    </el-tooltip>
                    <el-tooltip content="仅源代码" placement="top">
                      <div class="icon-button" :class="{ active: contentFilter === 'source' }" @click="contentFilter = 'source'">
                        <i class="el-icon-document"></i>
                      </div>
                    </el-tooltip>
                    <el-tooltip content="包含二进制" placement="top">
                      <div class="icon-button" :class="{ active: contentFilter === 'binary' }" @click="contentFilter = 'binary'">
                        <i class="el-icon-coin"></i>
                      </div>
                    </el-tooltip>
                  </div>
                </div>

                <div class="control-group">
                  <div class="control-label">版本：</div>
                  <div class="filter-controls">
                    <el-tooltip content="显示全部" placement="top">
                      <div class="icon-button" :class="{ active: releaseTypeFilter === 'all' }" @click="releaseTypeFilter = 'all'">
                        <i class="el-icon-view"></i>
                      </div>
                    </el-tooltip>
                    <el-tooltip content="仅正式版" placement="top">
                      <div class="icon-button" :class="{ active: releaseTypeFilter === 'release' }" @click="releaseTypeFilter = 'release'">
                        <i class="el-icon-check"></i>
                      </div>
                    </el-tooltip>
                    <el-tooltip content="仅预发布" placement="top">
                      <div class="icon-button" :class="{ active: releaseTypeFilter === 'prerelease' }" @click="releaseTypeFilter = 'prerelease'">
                        <i class="el-icon-bell"></i>
                      </div>
                    </el-tooltip>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 全局搜索模式提示 -->
            <div v-if="searchScope === 'global'" class="global-search-tip">
              <img src="/global_search.png" class="tip-icon" alt="全局搜索" />
              <span>在GitHub上搜索</span>
            </div>
          </div>
        </div>

      </div>

      <!-- 主内容区域使用左右布局 -->
      <div class="main-content">
        <!-- 左侧足迹区域，使用新组件 -->
        <div class="footprints-section">
          <footprints-panel
            :access-token="accessToken"
            :last-activity-time="lastActivityTime"
            @jump-to-time="handleJumpToTime"
            @record-click="recordClick"
          />
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
                <el-button size="small" type="primary" @click="handleToday" class="calendar-control-btn">今天
                </el-button>
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
                          width="180"
                          popper-class="stars-popover"
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
                        <img src="/track.png" class="user-activity-icon" alt="上次活动" />
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
                        <div class="rss-icon-container" @mouseenter="setHoverRepo(repo.repo_name)"
                             @mouseleave="setHoverRepo(null)"
                             @click.stop="copyToClipboard(`https://github.com/${repo.repo_name}/releases.atom`)">
                          <img :src="isHoverRepo(repo.repo_name) ? '/rss_true.png' : '/rss_false.png'" class="rss-icon"
                               alt="RSS"/>
                        </div>
                      </el-tooltip>
                    </h3>
                    <div class="repo-meta">
                      <p v-if="repo.description" class="repo-description">
                        {{ repo.description }}
                      </p>
                      <div class="release-time">
                        <i class="el-icon-time"></i>
                        <span class="release-date">{{ formatDate(repo.latest_release.published_at) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 添加收藏数和趋势图 -->
                <div class="repo-stats">

                  <!-- 趋势图 -->
                  <el-popover
                      placement="bottom"
                      trigger="hover"
                      width="330"
                      popper-class="trends-popover"
                  >
                    <template #reference>
                      <div class="trends-icon">
                        <img src="/trend.png" class="trend-icon" alt="趋势"/>
                      </div>
                    </template>
                    <div class="trend-container">
                      <div class="trend-header">
                        <a :href="`https://github.com/${repo.repo_name}`" target="_blank" class="repo-title-link">
                          {{ repo.repo_name }} Star历史
                        </a>
                      </div>
                      <div class="trend-content">
                        <!-- 使用star-history的SVG趋势图，点击查看大图 -->
                        <div class="trend-history-container"
                             @click="showLargeImageDialog(repo.repo_name, `https://api.star-history.com/svg?repos=${repo.repo_name}&type=Date`)">
                          <img
                              :src="`https://api.star-history.com/svg?repos=${repo.repo_name}&type=Date`"
                              class="trend-history"
                              :alt="`${repo.repo_name} Star历史`"
                          />
                          <div class="view-large-overlay">
                            <span>点击查看大图</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </el-popover>
                  <!-- 收藏数 -->
                  <el-popover
                      placement="top"
                      trigger="hover"
                      width="150"
                      popper-class="stars-popover"
                  >
                    <template #reference>
                      <div class="stars-count">
                        <img src="/collect.png" class="star-icon" alt="收藏"/>
                        <span class="star-count-value">{{ formatStarCount(repo.stargazers_count) }}</span>
                      </div>
                    </template>
                    <div class="stars-detail">
                      <div class="stars-number">有 {{ Number(repo.stargazers_count).toLocaleString() }} 位眼光一致的朋友</div>
                      <div class="stars-link">
                        <a :href="`https://github.com/${repo.repo_name}/stargazers`" target="_blank">
                          点我查看
                        </a>
                      </div>
                    </div>
                  </el-popover>


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
                    <el-tag
                        v-if="isSourceCodeOnly(repo.latest_release)"
                        size="small"
                        type="info"
                        class="release-type-tag"
                    >
                      仅包含源代码
                    </el-tag>
                  </div>
                  <!-- 移除这里的发布时间 -->
                </h4>
                <!-- 添加回markdown-wrapper容器 -->
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
          <GitHubLogo :size="24"/>
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
      <rss-links-list
        :access-token="accessToken"
        :rss-mode="rssMode"
        :repo-name="currentRepoName"
        :single-rss-link="singleRssLink"
      />
    </el-dialog>

    <!-- 添加大图预览模态框 -->
    <el-dialog
        :visible.sync="showLargeImage"
        :title="currentRepoName + ' Star历史'"
        width="80%"
        class="trend-dialog"
        @closed="currentLargeImage = ''"
    >
      <div class="large-image-container">
        <img v-if="currentLargeImage" :src="currentLargeImage" class="large-trend-image"
             :alt="currentRepoName + ' Star历史'">
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import {format, isToday, isWeekend, isSameMonth, parseISO} from 'date-fns'
import {marked} from 'marked'
import DOMPurify from 'dompurify'  // 用于防止 XSS 攻击
import {zhCN} from 'date-fns/locale'
import {API_ENDPOINTS} from '@/api/config'  // 导入 API 配置
import GitHubLogo from '@/components/GitHubLogo.vue'  // 导入 GitHubLogo 组件
import FootprintsPanel from '@/components/FootprintsPanel.vue'  // 导入关注轨迹组件
import RssLinksList from '@/components/RssLinksList.vue'  // 导入RSS链接列表组件
import GitHubLogin from '@/components/GitHubLogin.vue'  // 导入GitHubLogin组件
import DebugHelper from '@/components/DebugHelper.vue'  // 导入DebugHelper组件

// 添加响应拦截器，但不自动重载页面
// 让组件自己处理授权错误
axios.interceptors.response.use(
  response => response,
  error => {
    // 记录但不自动处理，由组件处理
    if (error.response && error.response.status === 401) {
      console.log('检测到401错误，组件将处理授权');
    }
    return Promise.reject(error);
  }
)

export default {
  name: 'StarredReleases',

  components: {
    GitHubLogo,  // 确保组件名称匹配模板中使用的名称
    FootprintsPanel,  // 添加关注轨迹组件
    RssLinksList,  // 添加RSS链接列表组件
    GitHubLogin,  // 添加GitHubLogin组件
    DebugHelper,  // 添加DebugHelper组件
  },

  data() {
    return {
      releases: [],
      loading: false,
      error: null,
      searchQuery: '',
      currentPage: 1,
      pageSize: 10,
      contentFilter: 'all',  // 内容筛选类型
      releaseTypeFilter: 'all', // 版本类型筛选
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
      showLargeImage: false,
      currentLargeImage: '',
      rssFromCache: false, // 添加一个标记表示RSS数据是否来自缓存
      rssCurrentPage: 1, // 当前RSS分页
      rssPageSize: 10,   // RSS每页显示数量
      rssTotal: 0,       // RSS总数量,
      searchScope: 'starred', // 添加搜索范围选择
      showDebugHelper: false, // 添加调试助手显示状态
    }
  },

  computed: {
    filteredRepos() {
      let result = this.releases;

      // 如果是全局搜索模式，不过滤本地列表
      if (this.searchScope === 'global') {
        return result;
      }

      // 按内容类型筛选
      if (this.contentFilter !== 'all') {
        result = result.filter(repo => {
          const isSourceOnly = this.isSourceCodeOnly(repo.latest_release);
          return this.contentFilter === 'source' ? isSourceOnly : !isSourceOnly;
        });
      }

      // 按版本类型筛选
      if (this.releaseTypeFilter !== 'all') {
        result = result.filter(repo => {
          const isPreRelease = this.isPreRelease(repo.latest_release);
          return this.releaseTypeFilter === 'prerelease' ? isPreRelease : !isPreRelease;
        });
      }

      // 再按搜索关键词筛选
      if (this.searchQuery) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(repo =>
            repo.repo_name.toLowerCase().includes(query)
        );
      }

      return result;
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
    },
    paginatedRssLinks() {
      const start = (this.rssCurrentPage - 1) * this.rssPageSize;
      const end = start + this.rssPageSize;
      return this.filteredRssLinks.slice(start, end);
    }
  },

  methods: {
    // 处理来自GitHubLogin组件的认证成功事件
    handleAuthSuccess(authData) {
      console.log('收到认证成功事件:', authData);
      this.accessToken = authData.token;
      this.isAuthenticated = true;
      this.userInfo = authData.user;
      this.lastActivityTime = authData.user.last_activity_time;
      
      // 获取数据
      this.fetchReleases();
    },
    
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
      console.log('正在检查认证状态...');
      const storedToken = localStorage.getItem('github_token');
      if (!storedToken) {
        console.log('未找到存储的token');
        this.isAuthenticated = false;
        return false;
      }
      
      try {
        console.log('开始验证token有效性...');
        const response = await axios.get(API_ENDPOINTS.AUTH_VERIFY, {
          headers: {
            Authorization: `Bearer ${storedToken}`
          }
        });

        if (response.data.status === 'success') {
          console.log('Token验证成功');
          this.accessToken = storedToken;
          this.isAuthenticated = true;
          this.userInfo = response.data.user;
          this.lastActivityTime = response.data.user.last_activity_time; // 修改：存储最后活动时间

          // 检查是否需要重新获取数据
          const now = new Date().getTime();
          const lastFetch = localStorage.getItem('last_fetch_time');

          if (!lastFetch || (now - parseInt(lastFetch)) > this.minFetchInterval) {
            console.log('需要获取最新数据');
            await this.fetchReleases();
          } else {
            // 使用缓存的数据
            const cachedData = localStorage.getItem('releases_cache');
            if (cachedData) {
              try {
                this.releases = JSON.parse(cachedData);
                console.log('使用本地缓存数据');
              } catch (e) {
                console.error('解析缓存数据失败:', e);
                await this.fetchReleases(); // 如果解析失败，重新获取数据
              }
            } else {
              await this.fetchReleases(); // 没有缓存数据，获取新数据
            }
          }
          return true;
        } else {
          console.warn('Token验证不成功:', response.data);
          this.handleInvalidToken();
          return false;
        }
      } catch (error) {
        console.error('Token验证失败:', error);
        
        // 判断是否为401错误
        if (error.response && error.response.status === 401) {
          this.handleInvalidToken();
        } else {
          // 其他错误，尝试继续使用缓存
          const cachedData = localStorage.getItem('releases_cache');
          if (cachedData) {
            try {
              this.releases = JSON.parse(cachedData);
              console.log('由于验证错误，使用本地缓存数据');
              this.$message.warning('验证服务暂时不可用，使用缓存数据');
              return true;
            } catch (e) {
              console.error('解析缓存数据失败:', e);
            }
          }
        }
      }
      return false;
    },
    
    // 处理无效token的情况
    handleInvalidToken() {
      console.log('token无效，清除登录状态');
      localStorage.removeItem('github_token');
      // 不要立即删除缓存，可能还需要显示
      this.isAuthenticated = false;
      this.accessToken = null;
      this.userInfo = null;
      
      this.$message({
        type: 'warning',
        message: 'GitHub授权已失效，请重新登录',
        duration: 5000
      });
    },

    async handleCallback(code) {
      try {
        console.log('向后端发送授权码，获取访问令牌...');
        const response = await axios.get(`${API_ENDPOINTS.AUTH_CALLBACK}?code=${code}`);
        
        console.log('接收到后端响应:', response.data);
        
        // 检查新的响应格式
        if (response.data.status === 'success' && response.data.access_token) {
          // 成功获取token
          const accessToken = response.data.access_token;
          
          // 保存token
          this.accessToken = accessToken;
          this.isAuthenticated = true;
          localStorage.setItem('github_token', this.accessToken);
          console.log('成功获取访问令牌并保存');
          
          // 如果响应中包含用户信息，直接使用
          if (response.data.user) {
            this.userInfo = response.data.user;
            console.log('从响应中获取到用户信息');
          } else {
            // 否则获取用户信息
            await this.fetchUserInfo();
          }
          
          // 如果有保存的重定向地址，则跳转回去
          const redirectUrl = localStorage.getItem('redirect_after_login');
          if (redirectUrl) {
            localStorage.removeItem('redirect_after_login');
            console.log('检测到重定向URL，跳转到:', redirectUrl);
            window.location.href = redirectUrl;
            return; // 中断后续操作，因为页面将重定向
          }
          
          return true; // 回调处理成功
        } else if (response.data.status === 'error') {
          // 处理错误响应
          const errorMsg = response.data.error || '授权失败';
          console.error('GitHub授权失败:', errorMsg);
          
          // 显示错误信息
          this.$message.error(`GitHub授权失败: ${errorMsg}`);
          
          // 清除token
          this.error = 'GitHub 认证失败';
          this.isAuthenticated = false;
          localStorage.removeItem('github_token');
          
          throw new Error(errorMsg);
        } else {
          // 旧格式或意外响应格式
          if (!response.data.access_token) {
            throw new Error('后端未返回访问令牌');
          }
          
          // 保存token (旧格式)
          this.accessToken = response.data.access_token;
          this.isAuthenticated = true;
          localStorage.setItem('github_token', this.accessToken);
          console.log('成功获取访问令牌并保存 (旧格式)');

          // 获取用户信息
          await this.fetchUserInfo();
          
          // 如果有保存的重定向地址，则跳转回去
          const redirectUrl = localStorage.getItem('redirect_after_login');
          if (redirectUrl) {
            localStorage.removeItem('redirect_after_login');
            console.log('检测到重定向URL，跳转到:', redirectUrl);
            window.location.href = redirectUrl;
            return; // 中断后续操作，因为页面将重定向
          }
          
          return true; // 回调处理成功
        }
      } catch (error) {
        console.error('GitHub授权回调处理失败:', error);
        
        // 显示错误信息
        this.$message.error(error.response?.data?.detail || error.message || 'GitHub 授权失败，请重试');
        
        // 清除任何可能保存的token
        this.error = 'GitHub 认证失败';
        this.isAuthenticated = false;
        localStorage.removeItem('github_token');
        
        throw error; // 抛出异常以便调用者知道处理失败
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
              // 修复1：在获取数据完成后立即获取收藏数
              this.fetchRepoStars()
              // 修复2：每次刷新数据后，获取最新的点击记录
              this.fetchClickLogs(1)
              // 获取最新的用户活动时间
              this.checkUserActivityTime()
            }, 500)
          }

          // 处理401错误（token过期或无效）
          if (data.status === 'error' && data.message && data.message.includes('401')) {
            eventSource.close()
            this.loading = false
            // 拦截器会自动处理401错误，这里只需关闭连接和更新状态
          }
        }

        eventSource.onerror = (error) => {
          console.error('EventSource failed:', error)
          eventSource.close()
          this.loading = false
          this.error = '获取数据失败'

          // 尝试检查是否是认证问题
          this.checkAuthStatus().catch(err => {
            console.error('检查认证状态失败:', err)
          })
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
        } else if (error.response?.status === 401) {
          // 401错误由全局拦截器统一处理
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
            element.scrollIntoView({behavior: 'smooth', block: 'center'})
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
      return format(dateObj, 'yyyy年 MM月', {locale: zhCN});
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
              headers: {Authorization: `Bearer ${this.accessToken}`}
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
          headers: {Authorization: `Bearer ${this.accessToken}`},
          params: {page: this.logsCurrentPage, limit: this.logsPageSize}
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
        return format(date, 'yyyy-MM-dd HH:mm:ss', {locale: zhCN});
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
              element.scrollIntoView({behavior: 'smooth', block: 'center'});

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
        return format(date, 'yyyy-MM-dd HH:mm', {locale: zhCN}); // 省略秒
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
      this.singleRssLink = ''; // 清空之前的链接
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
      }
    },

    // 显示批量RSS链接对话框
    handleBatchRss() {
      this.rssMode = 'batch';
      this.rssDialogVisible = true;
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

    // 复制所有链接 - 修改为只复制当前筛选的链接
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

      this.batchRssLinks.forEach(item => {
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

    // 添加跳转到最后活动时间的方法
    jumpToLastActivity() {
      if (!this.lastActivityTime) {
        this.$message.warning('没有找到最后浏览记录');
        return;
      }

      if (this.viewMode === 'list') {
        this.jumpToNearestTimeInList(this.lastActivityTime);
      } else if (this.viewMode === 'calendar') {
        this.jumpToDateInCalendar(this.lastActivityTime);
      }

      this.$message.success('已跳转到最后浏览时间');
    },

    // 在 methods 中添加获取收藏数的方法
    async fetchRepoStars() {
      if (!this.accessToken || !this.releases.length) return;

      try {
        // 获取一批仓库的stars信息
        const batchSize = 10; // 每次处理10个仓库

        // 先找出所有没有收藏数的仓库或显示"加载中"的仓库
        const reposToFetch = this.releases.filter(repo =>
          !repo.stargazers_count || repo.stargazers_count === '加载中'
        );

        for (let i = 0; i < reposToFetch.length; i += batchSize) {
          const batch = reposToFetch.slice(i, i + batchSize);
          const repoNames = batch.map(repo => repo.repo_name).join(',');

          const response = await axios.get(`${API_ENDPOINTS.REPO_STARS}?repos=${repoNames}`, {
            headers: {
              Authorization: `Bearer ${this.accessToken}`
            }
          });

          if (response.data.status === 'success') {
            // 更新仓库star数
            response.data.data.forEach(repoData => {
              const repoIndex = this.releases.findIndex(repo => repo.repo_name === repoData.repo_name);
              if (repoIndex !== -1) {
                this.$set(this.releases[repoIndex], 'stargazers_count', repoData.stars);
              }
            });
          }
        }
      } catch (error) {
        console.error('获取仓库收藏数失败:', error);
      }
    },

    // 在methods中添加查看大图的方法
    showLargeImageDialog(repoName, imageUrl) {
      this.currentRepoName = repoName;
      this.currentLargeImage = imageUrl;
      this.showLargeImage = true;
    },

    // 添加收藏数格式化方法
    formatStarCount(count) {
      if (!count && count !== 0) return '加载中';

      // 处理大数字的显示
      if (count >= 1000000) {
        return (count / 1000000).toFixed(1) + 'M';
      } else if (count >= 1000) {
        return (count / 1000).toFixed(1) + 'K';
      }

      return count.toString();
    },

    // 显示RSS对话框
    showRssDialog() {
      this.handleBatchRss(false);
    },

    // 处理RSS页码变化
    handleRssCurrentChange(val) {
      this.rssCurrentPage = val;
    },

    // 处理RSS每页显示数量变化
    handleRssSizeChange(val) {
      this.rssPageSize = val;
      this.rssCurrentPage = 1;
    },

    // 处理从FootprintsPanel组件传递过来的跳转事件
    handleJumpToTime(timeStr) {
      if (this.viewMode === 'list') {
        this.jumpToNearestTimeInList(timeStr);
      } else if (this.viewMode === 'calendar') {
        this.jumpToDateInCalendar(timeStr);
      }
    },

    // 修复2：添加检查最新用户活动时间的方法
    async checkUserActivityTime() {
      try {
        const response = await axios.get(API_ENDPOINTS.AUTH_VERIFY, {
          headers: {
            Authorization: `Bearer ${this.accessToken}`
          }
        })

        if (response.data.status === 'success' && response.data.user.last_activity_time) {
          this.lastActivityTime = response.data.user.last_activity_time
        }
      } catch (error) {
        console.error('获取最新用户活动时间失败:', error)
        // 401错误由全局拦截器统一处理
      }
    },

    handleGlobalSearch() {
      // 在这里添加全局搜索的逻辑
      if (!this.searchQuery.trim()) {
        this.$message.warning('请输入搜索关键词');
        return;
      }

      // 构建GitHub搜索URL
      const searchUrl = `https://github.com/search?q=${encodeURIComponent(this.searchQuery)}`;

      // 打开新窗口进行搜索
      window.open(searchUrl, '_blank');

      // 记录搜索行为
      if (this.accessToken) {
        try {
          axios.post(API_ENDPOINTS.RECORD_SEARCH, {
            search_query: this.searchQuery,
            search_scope: 'global'
          }, {
            headers: { Authorization: `Bearer ${this.accessToken}` }
          }).catch(error => {
            console.error('记录搜索行为失败:', error);
          });
        } catch (error) {
          console.error('记录搜索行为失败:', error);
        }
      }
    },

    // 监听回车键进行搜索
    handleSearchKeyPress(e) {
      if (e.key === 'Enter') {
        if (this.searchScope === 'global') {
          this.handleGlobalSearch();
        } else {
          // 本地过滤已经在computed属性中完成
          // 当本地搜索时，按回车不做额外操作
          e.preventDefault(); // 防止表单提交
        }
      }
    },
  },

  async mounted() {
    console.log('组件挂载，开始初始化...');
    
    // 检查当前路径是否是auth/callback
    const isCallback = window.location.pathname.includes('/auth/callback');
    
    // 检查 URL 中是否有认证码
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const token = urlParams.get('token'); // 检查URL中是否直接包含token
    const error = urlParams.get('error'); // 检查URL是否包含错误信息
    
    // 在控制台输出当前URL
    console.log('当前URL:', window.location.href, '是否是回调路径:', isCallback);
    
    // 清除URL中的参数，避免刷新页面时重复处理
    const shouldClearUrl = code || error || token;
    
    // 处理错误信息
    if (error) {
      console.error('检测到URL中包含错误信息:', error);
      const message = urlParams.get('message') || '授权失败';
      this.$message.error(`GitHub授权失败: ${message}`);
      
      // 清除URL中的参数
      if (shouldClearUrl) {
        console.log('清除URL中的参数');
        window.history.replaceState({}, document.title, window.location.pathname);
      }
      return;
    }
    
    // 处理直接token的情况
    if (token) {
      console.log('从URL中获取到token，保存并清除URL参数');
      localStorage.setItem('github_token', token);
      
      // 清除URL中的参数
      if (shouldClearUrl) {
        console.log('清除URL中的参数');
        window.history.replaceState({}, document.title, window.location.pathname);
      }
      
      this.accessToken = token;
      
      // 验证token并加载数据
      try {
        const isAuthenticated = await this.checkAuthStatus();
        if (isAuthenticated) {
          this.initializeAfterAuth();
        }
      } catch (error) {
        console.error('验证token失败:', error);
        this.$message.error('登录验证失败，请重试');
      }
      return;
    }
    
    // 特别注意: 回调处理由 GitHubLogin 组件处理，这里不再重复处理
    // 处理GitHub授权回调应该只在一个地方进行，避免多次使用同一个code
    if (code) {
      console.log('检测到授权码，将由 GitHubLogin 组件处理，此处不重复处理');
      return;
    }
    
    // 常规检查存储的token
    console.log('检查本地存储的token...');
    try {
      const isAuthenticated = await this.checkAuthStatus();
      if (isAuthenticated) {
        this.initializeAfterAuth();
      } else {
        console.log('未登录状态，显示登录页面');
      }
    } catch (error) {
      console.error('检查认证状态时发生错误:', error);
    }
  },
  
  // 登录成功后的初始化
  async initializeAfterAuth() {
    console.log('初始化已登录用户的数据...');
    
    // 如果有必要，获取最新数据
    if (this.releases.length === 0) {
      await this.fetchReleases();
    }
    
    // 确保获取仓库收藏数
    if (this.releases.length > 0) {
      this.fetchRepoStars();
    }
    
    // 加载足迹数据
    this.fetchClickLogs(1);
    
    // 添加时间轴点击事件处理
    this.$nextTick(() => {
      this.addTimelineClickHandlers();
    });
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
    contentFilter() {  // 添加对筛选类型的监听
      this.currentPage = 1
    },
    releaseTypeFilter() {  // 添加对筛选类型的监听
      this.currentPage = 1
    },
    // 添加对releases的监听，当数据加载完成后获取收藏数
    releases: {
      handler(newReleases) {
        if (newReleases && newReleases.length > 0) {
          this.fetchRepoStars();
        }
      },
      immediate: false
    },
    // 添加对搜索范围的监听
    searchScope(newScope) {
      // 当搜索范围变化时，清空搜索框
      this.searchQuery = '';

      // 如果切换到全局搜索，将视图模式设置为列表
      if (newScope === 'global') {
        this.viewMode = 'list';
      }
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
  flex-direction: column;  /* 修改为纵向排列 */
  align-items: flex-start;  /* 左对齐 */
  gap: 15px;
  width: 100%;
  box-sizing: border-box;
}

.search-input-container {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  width: 100%;  /* 使搜索框占满宽度 */
}

.search-scope-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  min-width: 150px;  /* 调整最小宽度 */
  padding: 5px 10px;
  background-color: #f5f7fa;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  flex-shrink: 0; /* 防止被压缩 */
}

.search-input {
  flex: 1;
}

/* 搜索按钮样式 */
:deep(.el-input-group__append) {
  padding: 0;
  background-color: #2c3e50;
  border-color: #2c3e50;
  border-top-right-radius: 20px;
  border-bottom-right-radius: 20px;
  overflow: hidden;
}

:deep(.el-input-group__append .el-button) {
  border: none;
  background: transparent;
  color: #ffffff;
  padding: 0 20px;
  height: 100%;
  min-width: 100px; /* 确保搜索按钮有足够宽度 */
  font-weight: 600; /* 加粗文字 */
  transition: all 0.3s;
  letter-spacing: 1px; /* 增加字间距 */
}

:deep(.el-input-group__append .el-button:hover) {
  background-color: #34495e;
  color: #ffffff;
  box-shadow: 0 0 10px rgba(52, 73, 94, 0.5);
}

/* 全局搜索按钮特殊样式 */
:deep(.global-search-btn) {
  background: linear-gradient(to right, #2c3e50, #4b6cb7);
  border: none;
  position: relative;
  overflow: hidden;
}

:deep(.global-search-btn:hover) {
  background: linear-gradient(to right, #34495e, #6384cf);
  box-shadow: 0 0 15px rgba(75, 108, 183, 0.7);
  transform: translateY(-1px);
}

:deep(.global-search-btn:hover::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: shine 1.5s infinite;
}

@keyframes shine {
  100% {
    left: 100%;
  }
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
  width: 100%;
  box-sizing: border-box;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
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
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.button-progress {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background-color: #409eff; /* 主色调进度条 */
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
  background: linear-gradient(to right, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.2));
  border-radius: inherit;
}

/* 确保没有其他加载动画干扰，但保留搜索按钮的图标 */
:deep(.el-button .el-icon) {
  display: inline-flex !important; /* 显示图标 */
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
  line-height: 1.5; /* 调整行高 */
  display: -webkit-box;
  -webkit-line-clamp: 2; /* 显示2行 */
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-height: 42px; /* 大约两行的高度 */
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
    -webkit-line-clamp: 3; /* 在小屏幕上允许显示更多行 */
    max-height: 63px; /* 约3行的高度 */
  }

  .search-input-container {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .search-scope-selector {
    justify-content: center;
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
  bottom: 5px;
  left: 5px;
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
  align-items: flex-start;
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

/* 足迹头部样式 */
.footprints-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 添加足迹操作按钮组样式 */
.footprints-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 最后活动按钮样式 */
.last-activity-btn {
  color: #409EFF;
  position: relative;
}

.last-activity-btn:hover {
  color: #66b1ff;
  background-color: rgba(64, 158, 255, 0.1);
}

/* 为刷新图标添加加载效果 */
.refresh-icon {
  position: relative;
}

.refresh-icon.is-loading {
  pointer-events: none;
  opacity: 0.8;
}

.loading-indicator {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  top: 0;
  left: 0;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 修改repo-header样式，使其支持收藏数和趋势图显示 */
.repo-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.repo-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 10px;
}

.stars-count {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 8px;
  background-color: rgba(230, 162, 60, 0.1);
  border-radius: 15px;
  color: #e6a23c;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.3s;
  cursor: default;
  border: 1px solid rgba(230, 162, 60, 0.2);
}

.stars-count:hover {
  background-color: rgba(230, 162, 60, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(230, 162, 60, 0.2);
}

.star-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.star-count-value {
  font-weight: 600;
}

.trends-icon {
  color: #409eff;
  cursor: pointer;
  transition: all 0.3s;
}

.trend-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

.trends-icon:hover {
  transform: scale(1.2);
}

/* 趋势图弹出层样式 */
:deep(.trends-popover) {
  padding: 0;
}

.trend-container {
  width: 100%;
}

.trend-header {
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
  font-weight: bold;
  color: #303133;
  text-align: center;
}

.trend-content {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.trend-history {
  width: 100%;
  max-width: 300px;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.trend-history:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.view-on-github {
  padding: 8px 16px;
  background-color: #24292e;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 14px;
  margin-top: 10px;
  transition: all 0.3s;
  text-align: center;
}

.view-on-github:hover {
  background-color: #1a1e22;
  transform: translateY(-2px);
}

.repo-meta {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.release-time {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
  font-size: 13px;
}

.release-date {
  margin: 0;
}

/* 修改趋势图样式，支持查看大图 */
.trend-history-container {
  position: relative;
  width: 100%;
  max-width: 300px;
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
}

.trend-history {
  width: 100%;
  height: auto;
  border-radius: 4px;
  transition: all 0.3s;
  display: block;
}

.view-large-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.3s;
  color: white;
  font-size: 14px;
}

.trend-history-container:hover .view-large-overlay {
  opacity: 1;
}

.trend-history-container:hover .trend-history {
  transform: scale(1.05);
}

/* 仓库标题链接样式 */
.repo-title-link {
  color: #303133;
  text-decoration: none;
  transition: all 0.3s;
}

.repo-title-link:hover {
  color: #409EFF;
}

/* 删除不再使用的样式 */
.view-on-github {
  display: none;
}

/* 大图预览相关样式 */
.large-image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  overflow: auto;
}

.large-trend-image {
  max-width: 100%;
  height: auto;
  object-fit: contain;
}

:deep(.trend-dialog .el-dialog__body) {
  padding: 10px;
  text-align: center;
}

:deep(.trend-dialog .el-dialog__header) {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
}

/* 添加RSS操作样式 */
.rss-actions {
  display: flex;
  gap: 8px;
}

.batch-rss-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 添加RSS表格中的仓库名链接样式 */
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

/* 添加RSS分页样式 */
.rss-pagination {
  margin-top: 15px;
  text-align: center;
}

.rss-dialog-button {
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 星标Popover样式 */
:deep(.stars-popover) {
  padding: 0;
}

.stars-detail {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
}

.stars-number {
  font-size: 13px;
  color: #606266;
}

.stars-link {
  align-self: flex-end;
}


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


/* 添加登录页面样式 */
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

.preview-fallback {
  display: none;
}

.card-preview.fallback .preview-fallback {
  display: block;
}

.preview-placeholder {
  width: 80%;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
  transition: all 0.5s;
  position: relative;
  background-color: white;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  margin: 0 auto;
}

.preview-placeholder h3 {
  margin: 0;
  color: #303133;
  font-size: 20px;
}

.preview-placeholder p {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
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
    height: 320px; /* 在响应式布局中稍微增加高度 */
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

.search-input-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-scope-selector {
  display: flex;
  align-items: center;
  gap: 5px;
}

/* 搜索工具栏容器 */
.search-toolbar {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 8px 5px;
  flex-wrap: nowrap;
}

.search-input-wrapper {
  flex: 1;
  min-width: 0; /* 允许flex子项收缩 */
}

.controls-and-tips {
  display: flex;
  align-items: center;
  white-space: nowrap;
  min-width: 300px;
}

/* 全局搜索提示样式 */
.global-search-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #f2f6fc;
  color: #606266;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 13px;
  border-left: 3px solid #b3d8ff;
  white-space: nowrap;
  margin-left: 10px;
}

.global-search-tip i {
  font-size: 16px;
}

/* 响应式样式调整 */
@media (max-width: 1200px) {
  .search-toolbar {
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .search-input-wrapper {
    order: 1;
    width: 100%;
    flex: none;
  }
  
  .search-scope-selector {
    order: 0;
    flex: 0 0 auto;
  }
  
  .controls-and-tips {
    order: 2;
    width: 100%;
    justify-content: flex-end;
    min-width: auto;
  }
  
  .view-filter-controls {
    justify-content: flex-end;
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .controls-and-tips {
    justify-content: center;
  }
  
  .search-scope-selector {
    margin: 0 auto;
  }
}

/* 在手机端调整提示框样式 */
@media (max-width: 768px) {
  .global-search-tip {
    padding: 4px 8px;
    font-size: 12px;
    margin-left: 5px;
  }
  
  .global-search-tip .tip-icon {
    width: 16px;
    height: 16px;
  }
  
  .global-search-tip span {
    display: none;
  }
  
  .global-search-tip:after {
    content: "全局";
    font-size: 12px;
  }
}

/* CSS样式添加 */
.scope-icon {
  width: 20px;
  height: 20px;
  object-fit: contain;
}

.tip-icon {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.icon-button.active img.scope-icon {
  filter: brightness(0) invert(1); /* 使图标在选中状态下变为白色 */
}

/* 防止图标在点击状态下模糊 */
.icon-button img.scope-icon {
  transition: all 0.3s;
  transform: scale(1);
}

/* 添加最后活动图标样式 */
.user-activity-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

/* 调试助手样式 */
.debug-helper-container {
  margin-top: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.debug-helper-container .el-button {
  margin-bottom: 10px;
}
</style>
