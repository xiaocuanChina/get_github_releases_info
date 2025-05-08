// API 配置文件
export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  STARRED_RELEASES: `${API_BASE_URL}/api/starred-releases`,
  STARRED_RELEASES_PROGRESS: `${API_BASE_URL}/api/starred-releases/progress`,
  AUTH_GITHUB: `${API_BASE_URL}/api/auth/github`,
  AUTH_CALLBACK: `${API_BASE_URL}/api/auth/callback`,
  AUTH_VERIFY: `${API_BASE_URL}/api/auth/verify`,
  RECORD_CLICK: `${API_BASE_URL}/api/record-click`,
  CLICK_LOGS: `${API_BASE_URL}/api/click-logs`,
  // 添加RSS链接相关端点
  REPO_RSS_LINK: `${API_BASE_URL}/api/repo-rss-link`,
  BATCH_RSS_LINKS: `${API_BASE_URL}/api/batch-rss-links`,
  ALL_STARRED_RSS: `${API_BASE_URL}/api/all-starred-rss`
};