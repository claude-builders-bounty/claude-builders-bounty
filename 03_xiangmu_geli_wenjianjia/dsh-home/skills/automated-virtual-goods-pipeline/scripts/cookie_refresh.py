#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Cookie Refresh via Playwright
Refreshes XIANYU_COOKIE by logging into goofish.com headlessly and extracting cookies.
Run weekly via systemd timer or cron.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import get_config
from playwright.async_api import async_playwright
from loguru import logger


async def refresh_cookie() -> str:
    """Refresh cookie via headless browser login"""
    logger.info("🔄 Starting cookie refresh via Playwright...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        try:
            # Create context with realistic viewport
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            page = await context.new_page()
            
            # Navigate to闲鱼
            logger.info("  Navigating to https://www.goofish.com...")
            await page.goto('https://www.goofish.com/', wait_until='networkidle', timeout=30000)
            
            # Check if already logged in (look for user avatar or profile link)
            await page.wait_for_timeout(2000)
            
            # Try to find login button or user avatar
            login_indicators = [
                'text=登录',
                'text=注册',
                '[data-spm="login"]',
                '.login-btn',
                '#J_LoginBtn'
            ]
            
            logged_in = False
            for selector in login_indicators:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        logger.info(f"  Found login indicator: {selector}")
                        break
                except:
                    continue
            else:
                # No login button found, might already be logged in
                logged_in = True
            
            if not logged_in:
                logger.warning("  ⚠️ Not logged in. Manual login required.")
                logger.info("  Please log in manually in the browser window...")
                logger.info("  (This automated script cannot handle SMS/QR login)")
                
                # Wait for manual login (max 5 minutes)
                try:
                    await page.wait_for_selector('[data-spm="user"], .user-avatar, .profile-link', timeout=300000)
                    logger.success("  ✅ Manual login detected!")
                except:
                    logger.error("  ❌ Login timeout (5 min)")
                    return ""
            
            # Extract cookies
            logger.info("  Extracting cookies...")
            cookies = await context.cookies()
            
            # Filter for goofish.com cookies
            goofish_cookies = [c for c in cookies if 'goofish.com' in c.get('domain', '') or 'taobao.com' in c.get('domain', '')]
            
            if not goofish_cookies:
                logger.error("  ❌ No goofish/taobao cookies found")
                return ""
            
            # Build cookie string
            cookie_parts = []
            required_keys = ['_m_h5_tk', '_m_h5_tk_enc', 'cookie2', 't', 'cna', 'xlly_s', '_tb_token_']
            found_keys = set()
            
            for cookie in goofish_cookies:
                name = cookie['name']
                value = cookie['value']
                cookie_parts.append(f"{name}={value}")
                if name in required_keys:
                    found_keys.add(name)
            
            cookie_string = "; ".join(cookie_parts)
            
            # Verify critical cookies
            missing = set(required_keys) - found_keys
            if missing:
                logger.warning(f"  ⚠️ Missing critical cookies: {missing}")
            else:
                logger.success(f"  ✅ All critical cookies present")
            
            logger.info(f"  Total cookies: {len(goofish_cookies)}")
            logger.info(f"  Cookie string length: {len(cookie_string)}")
            
            return cookie_string
            
        finally:
            await browser.close()


async def update_env_file(cookie_string: str) -> bool:
    """Update XIANYU_COOKIE in config/.env"""
    try:
        config = get_config()
        env_path = Path(config.config_dir) / ".env"
        
        if not env_path.exists():
            logger.error(f"  ❌ .env file not found at {env_path}")
            return False
        
        # Read current content
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update XIANYU_COOKIE line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('XIANYU_COOKIE='):
                lines[i] = f'XIANYU_COOKIE="{cookie_string}"\n'
                updated = True
                break
        
        if not updated:
            # Add at the end
            lines.append(f'\nXIANYU_COOKIE="{cookie_string}"\n')
        
        # Write back
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.success(f"  ✅ Updated {env_path}")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Failed to update .env: {e}")
        return False


async def main():
    """Main entry point"""
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    logger.info("=" * 50)
    logger.info("🔄 Xianyu Cookie Refresh")
    logger.info("=" * 50)
    
    try:
        # Refresh cookie
        cookie_string = await refresh_cookie()
        
        if not cookie_string:
            logger.error("❌ Cookie refresh failed")
            return 1
        
        # Update .env file
        if not await update_env_file(cookie_string):
            logger.error("❌ Failed to update config/.env")
            return 1
        
        logger.success("🎉 Cookie refresh completed successfully!")
        logger.info("   Restart pipeline services to use new cookie:")
        logger.info("   systemctl --user restart xianyu-pipeline")
        logger.info("   docker compose restart xianyu-delivery")
        
        return 0
        
    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))