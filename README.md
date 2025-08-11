# 需要的环境

## [Node.js](https://nodejs.org/zh-cn/download)

- 需要管理不同版本的nodejs：[nodejs版本管理器](https://github.com/coreybutler/nvm-windows)

## [Python](https://www.python.org/downloads/)

## OAuth Apps

1. [Developer applications](https://github.com/settings/developers)

2. New OAuth App

   1. Application name：随便取个名字
   2. Homepage URL: http://localhost:8080
      - 这里的localhost如果部署到服务器上后可以根据自己的ip来配置
   3. Authorization callback URL: http://localhost:8080/api/auth/callback
      - localhost同理
   4. Register application

3. 创建成功之后点击自己刚才创建的OAuth App

4. Generate a new client secret

   - 复制这里的id

   - 再复制Client ID

5. 将 .env.example 改名为 .env 

6. 将复制的长id粘贴到GITHUB_CLIENT_SECRET后

7. 将复制的Client ID粘贴到GITHUB_CLIENT_ID后



# 安装所需依赖

~~~sh
pip install -r requirements.txt
~~~

# 端口配置

项目现在支持通过配置文件自定义端口：

## 配置文件说明

### 根目录 `.env` 文件（后端配置）
```env
# GitHub OAuth配置
GITHUB_CLIENT_ID=你的客户端ID
GITHUB_CLIENT_SECRET=你的客户端密钥

# 端口配置
BACKEND_PORT=8000   # 后端API服务端口
FRONTEND_PORT=8080  # 前端开发服务器端口

# URL配置（如果修改端口需要相应调整）
FRONTEND_BASE_URL=http://localhost:8080
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/callback

# 可选：代理配置
# PROXY_URL=http://127.0.0.1:10808
```

### 前端目录 `get_github_info_vue/.env` 文件
```env
# 前端连接后端的端口（需要与后端端口一致）
VUE_APP_BACKEND_PORT=8000

# 前端开发服务器端口
FRONTEND_PORT=8080
```

## 配置检查

运行配置检查脚本来验证你的配置：
```sh
python check_config.py
```

**重要提醒**: 
- 如果修改了端口，请确保GitHub OAuth应用中的回调URL也相应更新
- `GITHUB_REDIRECT_URI` 应该指向后端端口（默认8000）
- `FRONTEND_BASE_URL` 应该指向前端端口（默认8080）

# 运行

## 本地运行

1. 切换到get_github_info_vue目录下，执行命令：

~~~sh
npm install
~~~

2. 安装完成依赖之后执行同目录下的 start.bat 文件

3. 访问前端页面（默认端口）：http://localhost:8080/

如果修改了端口配置，请访问对应的端口地址。

## 服务器

~~囊中羞涩，没钱买服务器，还请各位大佬自建吧~~

# 运行效果

<img width="1834" height="922" alt="PixPin_2025-08-11_16-00-46" src="https://github.com/user-attachments/assets/5cbef7ab-ccc0-4a6d-8a93-4495a4d160fe" />





