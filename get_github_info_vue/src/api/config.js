// API 配置文件
// 从环境变量获取后端端口，默认为8000
const BACKEND_PORT = process.env.VUE_APP_BACKEND_PORT || '8000';
export const API_BASE_URL = `http://localhost:${BACKEND_PORT}`;

export const API_ENDPOINTS = {
  STARRED_RELEASES: `${API_BASE_URL}/api/starred-releases`,
  STARRED_RELEASES_PROGRESS: `${API_BASE_URL}/api/starred-releases/progress`,
  AUTH_GITHUB: `${API_BASE_URL}/api/auth/github`,
  AUTH_CALLBACK: `${API_BASE_URL}/api/auth/callback`,
  AUTH_VERIFY: `${API_BASE_URL}/api/auth/verify`,
  RECORD_CLICK: `${API_BASE_URL}/api/record-click`,
  CLICK_LOGS: `${API_BASE_URL}/api/click-logs`,
  REPO_RSS_LINK: `${API_BASE_URL}/api/repo-rss-link`,
  BATCH_RSS_LINKS: `${API_BASE_URL}/api/batch-rss-links`,
  ALL_STARRED_RSS: `${API_BASE_URL}/api/all-starred-rss`,
  REFRESH_RSS_LINKS: `${API_BASE_URL}/api/refresh-rss-links`,
  CHECK_RSS_UPDATES: `${API_BASE_URL}/api/check-rss-updates`,
  REPO_STARS: `${API_BASE_URL}/api/repo-stars`
};
