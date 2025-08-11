#!/usr/bin/env python3
"""
配置检查脚本
用于验证环境变量配置是否正确
"""

import os
from dotenv import load_dotenv

def check_config():
    print("=" * 50)
    print("GitHub Releases 项目配置检查")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查必需的配置
    required_configs = [
        'GITHUB_CLIENT_ID',
        'GITHUB_CLIENT_SECRET',
        'FRONTEND_BASE_URL',
        'GITHUB_REDIRECT_URI'
    ]
    
    optional_configs = [
        'BACKEND_PORT',
        'FRONTEND_PORT',
        'PROXY_URL',
        'GITHUB_PERSONAL_TOKEN'
    ]
    
    print("\n📋 必需配置检查:")
    all_required_present = True
    for config in required_configs:
        value = os.getenv(config)
        if value:
            # 隐藏敏感信息
            if 'SECRET' in config or 'TOKEN' in config:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {config}: {display_value}")
        else:
            print(f"  ❌ {config}: 未设置")
            all_required_present = False
    
    print("\n📋 可选配置检查:")
    for config in optional_configs:
        value = os.getenv(config)
        if value:
            if 'SECRET' in config or 'TOKEN' in config:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {config}: {display_value}")
        else:
            print(f"  ⚪ {config}: 未设置 (使用默认值)")
    
    # 端口配置检查
    print("\n🔌 端口配置:")
    backend_port = os.getenv('BACKEND_PORT', '8000')
    frontend_port = os.getenv('FRONTEND_PORT', '8080')
    
    print(f"  后端端口: {backend_port}")
    print(f"  前端端口: {frontend_port}")
    
    # URL一致性检查
    print("\n🔗 URL一致性检查:")
    frontend_url = os.getenv('FRONTEND_BASE_URL', '')
    redirect_uri = os.getenv('GITHUB_REDIRECT_URI', '')
    
    if frontend_url and frontend_port in frontend_url:
        print(f"  ✅ 前端URL端口匹配: {frontend_url}")
    else:
        print(f"  ⚠️  前端URL可能需要更新: {frontend_url}")
    
    if redirect_uri and backend_port in redirect_uri:
        print(f"  ✅ OAuth回调URL端口匹配: {redirect_uri}")
    else:
        print(f"  ⚠️  OAuth回调URL可能需要更新: {redirect_uri}")
    
    # 代理配置检查
    proxy_url = os.getenv('PROXY_URL')
    if proxy_url:
        print(f"\n🌐 代理配置: {proxy_url}")
        print("  注意: 如果不需要代理，可以在.env文件中注释掉此行")
    
    print("\n" + "=" * 50)
    if all_required_present:
        print("✅ 配置检查完成！所有必需配置都已设置。")
    else:
        print("❌ 配置检查失败！请检查缺失的必需配置。")
    print("=" * 50)

if __name__ == "__main__":
    check_config()