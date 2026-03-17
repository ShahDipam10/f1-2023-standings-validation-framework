"""
test_login_flow.py

THE EXACT FLOW:
  1. Go to www.formula1.com
  2. Click "Sign In"
  3. Enter email + password
  4. Click "Sign In" button
  5. Assert "Sign In" link is GONE (logged in)
  6. Click profile icon
  7. Click "Sign Out"
  8. Assert "Sign In" link is BACK (logged out)

Run:  python -m pytest tests/test_login_flow.py -v -s
"""

import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, expect

load_dotenv()

EMAIL    = os.getenv("F1_EMAIL")
PASSWORD = os.getenv("F1_PASSWORD")

# XPaths provided directly — no guessing
XPATH_SIGN_IN_NAV    = "//a[@class='Button-module_button__j6Qut Button-module_black__TI5dn Button-module_small__3QaV7 typography-module_body-xs-bold__TovJz Button-module_showSpacers__iMklt']"
XPATH_EMAIL          = "//input[@placeholder='Enter your username']"
XPATH_PASSWORD       = "//input[@name='Password']"
XPATH_SIGN_IN_BTN    = "//button[normalize-space()='Sign In']"
XPATH_PROFILE_ICON   = "//a[contains(@href,'account.formula1.com') and contains(@class,'IconButton')]"
XPATH_SIGN_OUT       = "//a[normalize-space()='Sign Out'] | //button[normalize-space()='Sign Out']"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=False, slow_mo=300)
        yield b
        b.close()


@pytest.fixture(scope="module")
def page(browser):
    ctx = browser.new_context()
    p = ctx.new_page()
    yield p
    ctx.close()


def dismiss_cookie_popup(page):
    """Dismiss the SP consent iframe popup if present."""
    try:
        frame = page.frame_locator('iframe[id^="sp_message_iframe"]')
        btn = frame.get_by_role("button", name="Accept all")
        if btn.is_visible(timeout=3000):
            btn.click()
            page.wait_for_timeout(800)
    except Exception:
        pass


def test_full_login_logout_flow(page):
    """
    Complete flow:
    homepage -> sign in -> enter creds -> logged in check -> profile -> sign out
    """
    assert EMAIL, "F1_EMAIL not set in .env"
    assert PASSWORD, "F1_PASSWORD not set in .env"

    # ── STEP 1: Go to F1 homepage ─────────────────────────────────────────────
    print("\n→ Opening F1 homepage...")
    page.goto("https://www.formula1.com")
    page.wait_for_load_state("domcontentloaded")
    dismiss_cookie_popup(page)

    # ── STEP 2: Assert "Sign In" is visible, then click it ────────────────────
    print("→ Clicking Sign In...")
    sign_in_link = page.locator("a:has-text('Sign In')").first
    expect(sign_in_link).to_be_visible(timeout=8000)
    sign_in_link.click()

    # ── STEP 3: Fill in credentials ───────────────────────────────────────────
    print("→ Filling credentials...")
    page.wait_for_selector(XPATH_EMAIL, timeout=15000)
    dismiss_cookie_popup(page)

    page.locator(XPATH_EMAIL).fill(EMAIL)
    page.locator(XPATH_PASSWORD).fill(PASSWORD)

    # ── STEP 4: Click Sign In ─────────────────────────────────────────────────
    print("→ Submitting login...")
    page.locator(XPATH_SIGN_IN_BTN).click()

    # ── STEP 5: Wait for redirect back to formula1.com ────────────────────────
    print("→ Waiting for redirect to formula1.com...")
    page.wait_for_url("**/formula1.com/**", timeout=25000)
    page.wait_for_load_state("domcontentloaded")
    dismiss_cookie_popup(page)
    print(f"→ Redirected to: {page.url}")

    # ── ASSERT: Sign In link is gone ──────────────────────────────────────────
    print("→ Asserting Sign In is gone...")
    sign_in_links = page.locator("a:has-text('Sign In')")
    assert sign_in_links.count() == 0 or not sign_in_links.first.is_visible(timeout=3000), (
        "FAIL: Sign In link still visible after login!"
    )
    print("✓ Sign In link is gone — user is logged in")

    # ── STEP 6: Click profile icon ────────────────────────────────────────────
    print("→ Looking for profile/account icon...")
    # Try the profile icon by common patterns
    profile = (
        page.locator("a[href*='account.formula1.com']").first
        .or_(page.locator("[aria-label*='account' i]").first)
        .or_(page.locator("[aria-label*='profile' i]").first)
        .or_(page.locator("[data-testid*='account' i]").first)
    )
    if profile.is_visible(timeout=4000):
        profile.click()
        page.wait_for_timeout(1500)
        print("→ Profile menu opened")
    else:
        print("→ Profile icon not found via standard selectors — trying XPath...")
        page.locator(XPATH_PROFILE_ICON).first.click()
        page.wait_for_timeout(1500)

    # ── STEP 7: Click Sign Out ────────────────────────────────────────────────
    print("→ Clicking Sign Out...")
    sign_out = page.locator(XPATH_SIGN_OUT).first
    sign_out.wait_for(timeout=6000)
    sign_out.click()
    page.wait_for_timeout(3000)
    print("→ Clicked Sign Out")

    # ── ASSERT: Sign In link is back ──────────────────────────────────────────
    print("→ Asserting Sign In is back...")
    expect(page.locator("a:has-text('Sign In')").first).to_be_visible(timeout=10000)
    print("✓ Sign In link is back — user is logged out")
