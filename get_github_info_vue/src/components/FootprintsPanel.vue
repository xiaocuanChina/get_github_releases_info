<template>
  <el-card class="footprints-card">
    <template #header>
      <div class="footprints-header">
        <span>关注轨迹</span>
        <div class="footprints-actions">
          <!-- 添加跳转到最后浏览时间的按钮 -->
          <el-tooltip content="跳转到最后浏览" placement="top">
            <div
                class="icon-button last-activity-btn"
                @click="jumpToLastActivity"
            >
              <AppIcon name="position"/>
            </div>
          </el-tooltip>
          <el-tooltip content="刷新记录" placement="top">
            <div
                class="icon-button refresh-icon"
                :class="{ 'is-loading': logsLoading }"
                @click="fetchClickLogs(1)"
            >
              <AppIcon name="refresh"/>
              <span v-if="logsLoading" class="loading-indicator"></span>
            </div>
          </el-tooltip>
        </div>
      </div>
    </template>

    <div v-if="logsLoading" class="logs-loading">加载中...</div>
    <el-alert v-else-if="logsError" :title="logsError" type="error" show-icon :closable="false"/>
    <div v-else-if="clickLogs.length === 0" class="logs-empty">您还没有关注轨迹哦！</div>
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
              >{{ log.release_tag }}
              </el-tag>
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
</template>

<script>
import axios from 'axios'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { API_ENDPOINTS } from '@/api/config'

export default {
  name: 'FootprintsPanel',
  
  props: {
    accessToken: {
      type: String,
      required: true
    },
    lastActivityTime: {
      type: String,
      default: null
    }
  },
  
  data() {
    return {
      clickLogs: [],
      logsLoading: false,
      logsError: null,
      logsCurrentPage: 1,
      logsPageSize: 6,
      logsTotal: 0
    }
  },

  mounted() {
    this.fetchClickLogs(1)
    
    // 为时间轴时间戳添加点击事件
    this.$nextTick(() => {
      this.addTimelineClickHandlers()
    })
  },
  
  updated() {
    // 在组件更新后重新添加事件监听器
    this.$nextTick(() => {
      this.addTimelineClickHandlers()
    })
  },

  methods: {
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
      this.$emit('record-click', repoName, releaseTag, null); // 发送记录点击事件
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

      // 触发外部跳转事件
      this.$emit('jump-to-time', log.click_time);
    },
    
    // 跳转到最后活动记录
    jumpToLastActivity() {
      if (!this.lastActivityTime) {
        this.$message.warning('没有找到最后浏览记录');
        return;
      }
      
      this.$emit('jump-to-time', this.lastActivityTime);
      this.$message.success('已跳转到最后浏览时间');
    }
  }
}
</script>

<style scoped>
/* 左侧足迹区域样式 */
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

/* 添加可点击标签的样式 */
.clickable-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.clickable-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 足迹项目布局 */
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
</style> 