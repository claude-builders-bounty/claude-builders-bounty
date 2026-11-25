#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pyxianyu Connectivity Smoke Test
Verifies: cookie validity, search works, publish dry-run, WebSocket connectivity
Run before deploying pipeline to catch auth/connectivity issues early.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config_loader import get_config
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi, ItemApi
from pyxianyu.xianyu_live import XianyuLive
from pyxianyu.core.exceptions import XianyuApiError
from loguru import logger


async def test_cookie_validity(client: XianyuClient) -> bool:
    """Test 1: Cookie validity via token refresh"""
    logger.info("Test 1: Cookie validity...")
    try:
        token = await client.get_token()
        if token and len(token) > 10:
            logger.success(f"  ✅ Token acquired: {token[:20]}...")
            return True
        else:
            logger.error("  ❌ Token empty or invalid")
            return False
    except XianyuApiError as e:
        if "401" in str(e) or "登录态" in str(e):
            logger.error("  ❌ Cookie expired (401)")
        else:
            logger.error(f"  ❌ API error: {e}")
        return False
    except Exception as e:
        logger.error(f"  ❌ Unexpected error: {e}")
        return False


async def test_search_api(client: XianyuClient) -> bool:
    """Test 2: Search API functionality"""
    logger.info("Test 2: Search API...")
    try:
        search_api = SearchApi(client)
        result = await search_api.search_items(
            keyword="PPT模板",
            page_number=1,
            rows_per_page=5,
            sort_type="want_count"
        )
        
        items = result.get("data", {}).get("items", [])
        if items:
            logger.success(f"  ✅ Search returned {len(items)} items")
            # Log first item for verification
            first = items[0]
            logger.info(f"  Sample: {first.get('title', '')[:30]}... | ¥{first.get('price', 0)} | 想要: {first.get('wantCount', 0)}")
            return True
        else:
            logger.warning("  ⚠️ Search returned empty results")
            return False
    except XianyuApiError as e:
        logger.error(f"  ❌ Search API error: {e}")
        return False
    except Exception as e:
        logger.error(f"  ❌ Search unexpected error: {e}")
        return False


async def test_publish_dry_run(client: XianyuClient) -> bool:
    """Test 3: Publish dry-run (prepublish_check + preget)"""
    logger.info("Test 3: Publish dry-run...")
    try:
        item_api = ItemApi(client)
        
        # Test prepublish_check
        check_result = await item_api.prepublish_check()
        if check_result.get("success"):
            logger.success("  ✅ prepublish_check passed")
        else:
            logger.warning(f"  ⚠️ prepublish_check: {check_result.get('msg', 'unknown')}")
        
        # Test preget
        preget_result = await item_api.preget()
        if preget_result.get("success"):
            logger.success("  ✅ preget passed (got publish params)")
            # Log available categories
            categories = preget_result.get("data", {}).get("categoryList", [])
            if categories:
                logger.info(f"  Available categories: {len(categories)}")
            return True
        else:
            logger.error(f"  ❌ preget failed: {preget_result.get('msg', 'unknown')}")
            return False
    except XianyuApiError as e:
        logger.error(f"  ❌ Publish dry-run error: {e}")
        return False
    except Exception as e:
        logger.error(f"  ❌ Publish dry-run unexpected: {e}")
        return False


async def test_websocket_connectivity(client: XianyuClient) -> bool:
    """Test 4: WebSocket connectivity (quick connect/disconnect)"""
    logger.info("Test 4: WebSocket connectivity...")
    try:
        live = XianyuLive(client)
        # Try to connect with short timeout
        await asyncio.wait_for(live.connect(), timeout=10.0)
        logger.success("  ✅ WebSocket connected")
        
        # Quick disconnect
        await live.disconnect()
        logger.success("  ✅ WebSocket disconnected cleanly")
        return True
    except asyncio.TimeoutError:
        logger.error("  ❌ WebSocket connection timeout (10s)")
        return False
    except Exception as e:
        logger.error(f"  ❌ WebSocket error: {e}")
        return False


async def test_card_inventory() -> bool:
    """Test 5: Card inventory file structure"""
    logger.info("Test 5: Card inventory structure...")
    from pathlib import Path
    
    cards_dir = Path("resources/cards")
    if not cards_dir.exists():
        logger.warning("  ⚠️ resources/cards/ directory not found")
        return True  # Not critical for initial test
    
    card_files = list(cards_dir.glob("*.txt"))
    if not card_files:
        logger.info("  ℹ️ No card inventory files found (OK for new setup)")
        return True
    
    total_codes = 0
    for cf in card_files:
        with open(cf, "r", encoding="utf-8") as f:
            codes = [line.strip() for line in f if line.strip()]
        total_codes += len(codes)
        logger.info(f"  {cf.stem}: {len(codes)} codes")
    
    logger.success(f"  ✅ Card inventory: {len(card_files)} packages, {total_codes} total codes")
    return True


async def main():
    """Run all smoke tests"""
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    
    logger.info("=" * 50)
    logger.info("🧪 Pyxianyu Smoke Test Suite")
    logger.info("=" * 50)
    
    # Load config
    try:
        config = get_config()
        if not config.account.cookie:
            logger.error("❌ XIANYU_COOKIE not set in config/.env")
            logger.info("   Run: python main.py menu -> option 7 to configure")
            return 1
    except Exception as e:
        logger.error(f"❌ Config load failed: {e}")
        return 1
    
    # Initialize client
    client = XianyuClient(cookie=config.account.cookie)
    await client.__aenter__()
    
    try:
        results = []
        
        # Run tests in order
        results.append(("Cookie Validity", await test_cookie_validity(client)))
        results.append(("Search API", await test_search_api(client)))
        results.append(("Publish Dry-run", await test_publish_dry_run(client)))
        results.append(("WebSocket", await test_websocket_connectivity(client)))
        results.append(("Card Inventory", await test_card_inventory()))
        
        # Summary
        logger.info("=" * 50)
        logger.info("📊 Test Summary")
        logger.info("=" * 50)
        
        passed = 0
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status} | {name}")
            if result:
                passed += 1
        
        logger.info(f"\nTotal: {passed}/{len(results)} passed")
        
        if passed == len(results):
            logger.success("🎉 All tests passed! Pipeline ready for deployment.")
            return 0
        else:
            logger.error(f"⚠️  {len(results) - passed} test(s) failed. Fix before deploying.")
            return 1
            
    finally:
        await client.__aexit__(None, None, None)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))