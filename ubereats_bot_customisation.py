# ubereats_bot_no_login.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import os

# === CONFIG ==============================================================
HEADLESS = False
BOT_PROFILE = "/Users/jash/Documents/CamHack-25/chrome-bot-profile"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "debug_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

options = Options()
if HEADLESS:
    options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
options.add_argument(f"--user-data-dir={BOT_PROFILE}")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)  # Reduced from 30s

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
def snap(name: str):
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{ts}_{name}.png")
    driver.save_screenshot(path)
    print(f"   Screenshot: {path}")

def wait_page_load():
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def is_logged_in():
    print("   Checking login status...")
    try:
        account_indicators = [
            "//button[contains(@aria-label, 'Account') or contains(@aria-label, 'Profile')]",
            "//button[.//img[contains(@alt, 'profile') or contains(@alt, 'account')]]",
            "//a[contains(@href, '/profile') or contains(@href, '/account')]",
            "//button[.//svg or .//img]"
        ]
        for xpath in account_indicators:
            if driver.find_elements(By.XPATH, xpath):
                print("   Logged in: Account/profile button found")
                return True

        if driver.find_elements(By.XPATH, "//button[contains(., 'Sign in') or contains(., 'Log in')]"):
            print("   Not logged in: Sign-in button visible")
            return False

        url = driver.current_url
        if '/feed' in url or '/city/' in url:
            print(f"   Logged in: URL indicates session ({url})")
            return True

        print("   Login status unclear")
        return False
    except Exception as e:
        print(f"   Login check failed: {e}")
        return False

def wait_for_post_order():
    """Return True when we are definitely on the order-confirmation page."""
    return WebDriverWait(driver, 15).until(
        lambda d: (
            d.execute_script("return document.location.pathname.includes('/order/')") or
            len(d.find_elements(By.XPATH,
                "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), 'order received') or "
                "contains(., 'Thank you') or contains(., 'Estimated')]")) > 0
        )
    )

# -------------------------------------------------------------------------
# Re-usable: add the *n*-th visible menu item (0-based)
# Uses JS to avoid polling loop
# -------------------------------------------------------------------------
def add_item(index: int):
    print(f"   Adding item #{index + 1}...")

    # ---- locate the n-th visible item via JS (fast) --------------------
    item_link = WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("""
            const items = Array.from(document.querySelectorAll('a[href*="/store/"]'))
                .filter(el => {
                    const text = el.textContent || '';
                    const img = el.querySelector('img');
                    const height = el.offsetHeight;
                    return !text.includes('Closed') && img && height > 30;
                });
            return items.length > arguments[0] ? items[arguments[0]] : null;
        """, index)
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_link)
    time.sleep(0.5)
    snap(f"before_click_item_{index+1}")
    driver.execute_script("arguments[0].click();", item_link)
    snap(f"after_click_item_{index+1}")
    time.sleep(1.5)  # modal load

    # ---- modal appears ------------------------------------------------
    modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@role,'dialog') or contains(@class,'modal') or contains(@class,'sheet')]"))
    )
    snap(f"modal_item_{index+1}")

    # ---- Check if "Most popular" section exists -----------------------
    print("      Checking for 'Most popular' section...")
    most_popular_span = None
    try:
        most_popular_span = WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.XPATH, ".//span[normalize-space()='Most popular']"))
        )
        print("      'Most popular' section found → selecting #1")
    except:
        print("      No 'Most popular' section → using default selection")

    # ---- If "Most popular" exists → click #1 -------------------------
    if most_popular_span:
        try:
            option_span = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, ".//span[normalize-space()='Most popular']/../..//span[contains(text(),'#1')]")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option_span)
            time.sleep(0.4)
            ActionChains(driver).move_to_element(option_span).pause(0.3).click().perform()
            print("      #1 option selected")
            snap(f"prebuilt_selected_item_{index+1}")
            time.sleep(1.2)
        except Exception as e:
            print(f"      Failed to click #1 (fallback to default): {e}")

    # ---- Click "Add to order" -----------------------------------------
    print("      Clicking 'Add to order'...")
    add_btn = WebDriverWait(driver, 12).until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add') "
             "and (contains(., 'to order') or contains(., 'to cart'))]")
        )
    )
    ActionChains(driver).move_to_element(add_btn).click().perform()
    print("      Add button clicked")
    snap(f"add_clicked_item_{index+1}")
    time.sleep(1.0)

    # ---- Verify cart badge --------------------------------------------
    expected_qty = index + 1
    try:
        badge = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//*[self::span or self::button or self::a or self::div]"
                 f"[contains(text(), '{expected_qty}') and "
                 f"(contains(@aria-label, 'cart') or contains(@href, '/cart'))]")
            )
        )
        print(f"   Cart now shows: '{badge.text}'")
        snap(f"cart_{expected_qty}_items")
    except:
        print("   Cart badge not updated yet – continuing")
        snap(f"cart_{expected_qty}_fallback")

# -------------------------------------------------------------------------
try:
    print(f"Using profile: {BOT_PROFILE}\n")
    print("1. Opening Uber Eats...")
    driver.get("https://www.ubereats.com")
    wait_page_load()
    snap("home")

    # ---- login handling ------------------------------------------------
    if not is_logged_in():
        print("NOT LOGGED IN – log in manually.")
        input("   Press ENTER when done…")
        if not is_logged_in():
            raise RuntimeError("Still not logged in after manual login")
    print("Login confirmed!\n")

    # ---- address -------------------------------------------------------
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'delivery address')]")))
        print("Address missing – set it.")
        input("   Press ENTER after…")
    except:
        print("Address set.\n")

    # ---- search (FAST) -------------------------------------------------
    print("2. Searching for 'pizza'...")
    search = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder,'Search') or contains(@placeholder,'delivery')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search)
    time.sleep(0.3)
    ActionChains(driver).click(search).send_keys("pizza").send_keys(Keys.ENTER).perform()
    wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/store/')]")))
    snap("search_results")

    # ---- pick first open restaurant ------------------------------------
    print("3. Selecting first open restaurant...")
    restaurant = WebDriverWait(driver, 12).until(
        lambda d: d.execute_script("""
            const stores = Array.from(document.querySelectorAll('a[href*="/store/"]'))
                .filter(el => !el.textContent.includes('Closed') && el.offsetHeight > 50);
            return stores.length > 0 ? stores[0] : null;
        """)
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restaurant)
    time.sleep(0.6)
    driver.execute_script("arguments[0].click();", restaurant)
    wait_page_load()
    snap("restaurant_page")

    # ---- wait for menu -------------------------------------------------
    print("4. Loading menu...")
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2 | //h3 | //div[contains(text(), 'Menu') or contains(text(), 'Featured')]")))
    time.sleep(1.0)  # minimal load

    # ---- add 1st and 3rd items -----------------------------------------
    add_item(0)   # 1st item
    add_item(2)   # 3rd item

    # ---- checkout (INSTANT) --------------------------------------------
    print("5. Going to checkout...")
    checkout_elem = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, 
            "//button[contains(., 'Checkout')] | "
            "//a[contains(., 'Checkout')] | "
            "//button[contains(., 'View cart')] | "
            "//*[contains(@href, '/checkout') or contains(@href, '/cart')]"
        ))
    )
    ActionChains(driver).move_to_element(checkout_elem).click().perform()
    wait_page_load()
    snap("checkout_page_loaded")
    print("   At checkout page")

    # ---- order and pay (SMART SCROLL + CONFIRMATION) --------------------
    print("6. Clicking 'Order and Pay'...")

    # Find the button (tight selector, case-insensitive)
    pay_button = WebDriverWait(driver, 12).until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
             "'place order') or "
             "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
             "'order and pay') or "
             "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
             "'pay')]")
        )
    )

    # Scroll into view (center + small header offset)
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});"
        "window.scrollBy(0, -120);",
        pay_button
    )
    time.sleep(0.5)                     # tiny stabilisation

    # ---- CLICK -------------------------------------------------------
    try:
        ActionChains(driver).move_to_element(pay_button).pause(0.4).click().perform()
        print("   'Order and Pay' clicked (ActionChains)")
    except Exception as e1:
        print(f"   ActionChains failed ({e1}), trying JS click...")
        driver.execute_script("arguments[0].click();", pay_button)
        print("   'Order and Pay' clicked (JS)")

    # ---- CONFIRM THE CLICK TOOK EFFECT -------------------------------
    # 1. Button disappears / becomes stale
    try:
        WebDriverWait(driver, 8).until(EC.staleness_of(pay_button))
        print("   Pay button disappeared – click registered")
    except:
        print("   Pay button still present – possible overlay, retrying once...")
        # retry once with JS
        driver.execute_script("arguments[0].click();", pay_button)
        WebDriverWait(driver, 8).until(EC.staleness_of(pay_button))

    # 2. Wait for a post-order indicator (any of these is enough)
    post_order_indicator = WebDriverWait(driver, 15).until(
        lambda d: (
            d.execute_script("return document.location.pathname.includes('/order/')") or
            len(d.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                                          "'abcdefghijklmnopqrstuvwxyz'), 'order received') or "
                                          "contains(., 'Thank you') or contains(., 'Estimated')]")) > 0
        )
    )
    snap("order_submitted")
    print("\nORDER PLACED! Check order_submitted.png")

except Exception as e:
    print(f"\nERROR: {e}")
    snap("FINAL_ERROR")
finally:
    input("\nPress ENTER to close…")
    driver.quit()