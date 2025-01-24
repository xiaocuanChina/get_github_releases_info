from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from github import Github
from datetime import datetime
import asyncio
import aiohttp
import os
from typing import List, Dict
from dotenv import load_dotenv
from pathlib import Path
from starlette.responses import RedirectResponse, StreamingResponse
import ssl
import certifi
from cachetools import TTLCache
import json

# 加载 .env 文件
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vue 开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitHub OAuth 配置
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    raise ValueError("GitHub OAuth credentials not found in environment variables")

GITHUB_REDIRECT_URI = "http://localhost:8080/auth/callback"

# 在全局添加缓存
releases_cache = TTLCache(maxsize=100, ttl=300)  # 5分钟缓存


async def fetch_repo_info(session: aiohttp.ClientSession, repo_name: str, access_token: str) -> Dict:
    """获取仓库基本信息"""
    url = f"https://api.github.com/repos/{repo_name}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            repo_data = await response.json()
            return {
                "avatar_url": repo_data.get("owner", {}).get("avatar_url"),
                "description": repo_data.get("description")
            }
    return {}


async def fetch_releases(session: aiohttp.ClientSession, repo_name: str, access_token: str) -> Dict:
    """异步获取单个仓库的最新 release 信息"""
    try:
        # 获取仓库基本信息
        repo_info = await fetch_repo_info(session, repo_name, access_token)

        # 获取 release 信息，增加详细的日志和错误处理
        url = f"https://api.github.com/repos/{repo_name}/releases?per_page=1"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "If-None-Match": ""  # 禁用 GitHub 的 ETag 缓存
        }

        print(f"正在获取 {repo_name} 的最新 release...")
        async with session.get(url, headers=headers) as response:
            print(f"{repo_name} 响应状态码: {response.status}")
            
            if response.status == 200:
                releases = await response.json()
                if releases:
                    latest_release = releases[0]
                    result = {
                        "repo_name": repo_name,
                        "avatar_url": repo_info.get("avatar_url"),
                        "description": repo_info.get("description"),
                        "latest_release": {
                            "tag_name": latest_release["tag_name"],
                            "name": latest_release["name"],
                            "published_at": latest_release["published_at"],
                            "html_url": latest_release["html_url"],
                            "body": latest_release["body"],
                            "all_releases_url": f"https://github.com/{repo_name}/releases",
                            "assets": latest_release.get("assets", [])
                        }
                    }
                    print(f"成功获取 {repo_name} 的 release: {latest_release['tag_name']}, 发布时间: {latest_release['published_at']}")
                    return result
                else:
                    print(f"{repo_name} 没有 releases")
            elif response.status == 403:
                response_json = await response.json()
                print(f"{repo_name} 请求被拒绝: {response_json}")
                if "rate limit exceeded" in response_json.get("message", "").lower():
                    reset_time = response.headers.get('X-RateLimit-Reset')
                    if reset_time:
                        reset_time = datetime.fromtimestamp(int(reset_time))
                        wait_time = (reset_time - datetime.now()).total_seconds()
                        print(f"速率限制将在 {reset_time} 重置（还需等待 {wait_time} 秒）")
                    raise Exception("GitHub API 速率限制已达到，请稍后重试")
            else:
                print(f"{repo_name} 请求失败: {response.status}")
                response_text = await response.text()
                print(f"错误响应: {response_text}")
    except Exception as e:
        print(f"获取 {repo_name} 的 release 时发生错误: {str(e)}")
        raise
    return None


async def fetch_releases_with_limit(session: aiohttp.ClientSession, repo_names: List[str], access_token: str):
    """并发获取 releases"""
    print(f"开始并发获取 {len(repo_names)} 个仓库的 releases...")

    tasks = [fetch_releases(session, repo_name, access_token) for repo_name in repo_names]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"处理时发生错误: {str(result)}")
            if "rate limit exceeded" in str(result).lower():
                raise
        elif result is not None:
            valid_results.append(result)

    return valid_results


async def create_aiohttp_session():
    """创建带有 SSL 上下文的 aiohttp 会话"""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context, force_close=True)
    return aiohttp.ClientSession(connector=connector)


@app.get("/api/auth/github")
async def github_auth():
    """GitHub OAuth 认证入口"""
    auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"redirect_uri={GITHUB_REDIRECT_URI}&"
        f"scope=repo read:user user:email"
    )
    # 使用 status_code=302 确保正确的重定向
    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/api/auth/callback")
async def github_callback(code: str):
    """GitHub OAuth 回调处理"""
    try:
        async with aiohttp.ClientSession() as session:
            print(f"收到授权码: {code[:5]}...")
            print(f"使用的回调 URL: {GITHUB_REDIRECT_URI}")
            
            token_url = "https://github.com/login/oauth/access_token"
            headers = {
                "Accept": "application/json",
                "User-Agent": "GitHub-Starred-Releases-App"
            }
            data = {
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI
            }

            async with session.post(token_url, data=data, headers=headers) as response:
                response_text = await response.text()
                print(f"GitHub OAuth 响应状态码: {response.status}")
                print(f"GitHub OAuth 响应内容: {response_text}")
                
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"GitHub OAuth 错误: {response_text}"
                    )

                try:
                    token_data = json.loads(response_text)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=500,
                        detail="无法解析 GitHub 响应"
                    )

                if "error" in token_data:
                    raise HTTPException(
                        status_code=400,
                        detail=f"GitHub OAuth 错误: {token_data.get('error_description', token_data['error'])}"
                    )

                access_token = token_data.get("access_token")
                if not access_token:
                    raise HTTPException(
                        status_code=400,
                        detail="未能获取访问令牌"
                    )

                return {"access_token": access_token}

    except aiohttp.ClientError as e:
        print(f"网络请求错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        print(f"GitHub 认证回调失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/starred-releases")
async def get_starred_releases(request: Request, force_refresh: bool = False):
    """获取用户 starred 仓库的 releases"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    access_token = auth_header.split(" ")[1]

    # 检查是否有缓存，且不是强制刷新
    cache_key = f"releases_{access_token}"
    if not force_refresh and cache_key in releases_cache:
        print("从缓存返回数据")
        return releases_cache[cache_key]

    try:
        print("开始获取starred仓库列表...")

        async with aiohttp.ClientSession() as session:
            # 首先检查 API 速率限制状态
            rate_limit_url = "https://api.github.com/rate_limit"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHub-Starred-Releases-App"
            }

            async with session.get(rate_limit_url, headers=headers) as response:
                if response.status == 200:
                    rate_data = await response.json()
                    core_rate = rate_data.get("resources", {}).get("core", {})
                    remaining = core_rate.get("remaining", 0)
                    reset_time = datetime.fromtimestamp(core_rate.get("reset", 0))

                    if remaining < 100:  # 如果剩余请求数太少
                        wait_time = (reset_time - datetime.now()).total_seconds()
                        raise HTTPException(
                            status_code=429,
                            detail=f"API rate limit low. Resets in {int(wait_time)} seconds. Please try again later."
                        )

            # 获取starred仓库列表（添加分页处理）
            starred_repos = []
            page = 1
            while True:
                starred_url = f"https://api.github.com/user/starred?per_page=100&page={page}"
                async with session.get(starred_url, headers=headers) as response:
                    print(f"Starred API 第 {page} 页响应状态码: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        print(f"GitHub API 错误响应: {error_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"GitHub API error: {error_text}"
                        )

                    page_data = await response.json()
                    if not page_data:  # 如果没有更多数据，退出循环
                        break

                    starred_repos.extend([repo["full_name"] for repo in page_data])
                    page += 1

            print(f"总共获取到 {len(starred_repos)} 个starred仓库")

            # 获取releases信息
            releases_data = await fetch_releases_with_limit(session, starred_repos, access_token)

            sorted_releases = sorted(
                [r for r in releases_data if r is not None],
                key=lambda x: x["latest_release"]["published_at"],
                reverse=True
            )

            print(f"成功获取到 {len(sorted_releases)} 个仓库的 release 信息")

            result = {
                "status": "success",
                "total_repos": len(sorted_releases),
                "data": sorted_releases,
                "cached": True,
                "cache_time": datetime.now().isoformat()
            }

            # 存入缓存
            releases_cache[cache_key] = result
            return result

    except aiohttp.ClientError as e:
        print(f"网络请求错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        if "rate limit exceeded" in str(e).lower():
            raise HTTPException(status_code=429, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/verify")
async def verify_token(request: Request):
    """验证 token 是否有效并返回用户信息"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    access_token = auth_header.split(" ")[1]
    try:
        async with aiohttp.ClientSession() as session:
            # 获取用户信息
            async with session.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    return {
                        "status": "success",
                        "user": {
                            "login": user_data["login"],
                            "avatar_url": user_data["avatar_url"],
                            "name": user_data.get("name"),
                            "email": user_data.get("email")
                        }
                    }
                else:
                    raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/starred-releases/progress")
async def get_starred_releases_progress(request: Request, token: str, force_refresh: bool = False):
    """使用 SSE 获取带进度的 starred 仓库 releases"""
    
    async def event_generator():
        try:
            # 检查缓存
            cache_key = f"releases_{token}"
            if not force_refresh and cache_key in releases_cache:
                yield "data: " + json.dumps({
                    "status": "complete",
                    "progress": 100,
                    "message": "从缓存加载完成",
                    "releases": releases_cache[cache_key]["data"]
                }) + "\n\n"
                return

            async with aiohttp.ClientSession() as session:
                # 获取 starred 仓库列表
                yield "data: " + json.dumps({
                    "progress": 0,
                    "message": "正在获取仓库列表..."
                }) + "\n\n"
                
                # 获取所有starred仓库
                starred_repos = []
                page = 1
                while True:
                    starred_url = f"https://api.github.com/user/starred?per_page=100&page={page}"
                    async with session.get(
                        starred_url,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Accept": "application/vnd.github.v3+json"
                        }
                    ) as response:
                        if response.status != 200:
                            break
                        page_data = await response.json()
                        if not page_data:
                            break
                        starred_repos.extend([repo["full_name"] for repo in page_data])
                        page += 1

                total_repos = len(starred_repos)
                yield "data: " + json.dumps({
                    "progress": 10,
                    "message": f"找到 {total_repos} 个仓库，正在获取发布信息...",
                    "total_repos": total_repos
                }) + "\n\n"

                # 使用分批并发处理
                batch_size = 10  # 每批处理10个仓库
                processed = 0
                releases_data = []
                
                for i in range(0, len(starred_repos), batch_size):
                    batch = starred_repos[i:i + batch_size]
                    # 并发处理一批仓库
                    tasks = [fetch_releases(session, repo_name, token) for repo_name in batch]
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # 处理批次结果
                    for result in batch_results:
                        if isinstance(result, Exception):
                            print(f"Error in batch: {str(result)}")
                            if "rate limit exceeded" in str(result).lower():
                                raise
                        elif result is not None:
                            releases_data.append(result)
                    
                    processed += len(batch)
                    progress = 10 + int(85 * processed / total_repos)
                    
                    # 每批次后发送一次进度更新
                    yield "data: " + json.dumps({
                        "progress": progress,
                        "message": f"正在处理: {processed}/{total_repos}",
                        "processed_repos": processed,
                        "total_repos": total_repos
                    }) + "\n\n"
                    
                    # 短暂延迟，避免触发 GitHub API 限制
                    await asyncio.sleep(0.05)

                # 排序并返回结果
                sorted_releases = sorted(
                    releases_data,
                    key=lambda x: x["latest_release"]["published_at"],
                    reverse=True
                )

                result = {
                    "status": "complete",
                    "progress": 100,
                    "message": "加载完成",
                    "releases": sorted_releases
                }

                # 更新缓存
                releases_cache[cache_key] = {
                    "status": "success",
                    "total_repos": len(sorted_releases),
                    "data": sorted_releases,
                    "cached": True,
                    "cache_time": datetime.now().isoformat()
                }

                yield "data: " + json.dumps(result) + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({
                "status": "error",
                "message": str(e)
            }) + "\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
