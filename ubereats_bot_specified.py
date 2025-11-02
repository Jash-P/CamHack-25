# ubereats_bot_specified.py
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
import warnings

# Suppress urllib3 warning (optional)
warnings.filterwarnings("ignore", category=UserWarning)

# === CONFIG ==============================================================
HEADLESS = False
BOT_PROFILE = "/Users/jash/Documents/CamHack-25/chrome-bot-profile"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "debug_screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# === CUSTOMIZE HERE ======================================================
RESTAURANT_NAME = "Domino's"          # Any name – will fall back if not found
ITEMS_TO_ADD = [
    "Margherita",
    "Pepperoni Passion",
    "Garlic Bread with Cheese"
]
# =========================================================================

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
wait = WebDriverWait(driver, 10)

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
def snap(name: str):
    ts = time.strftime("%Y%m%d-%H%M%S")
    safe_name = "".join(c for c in name if c.isalnum() or c in " _-")
    path = os.path.join(SCREENSHOT_DIR, f"{ts}_{safe_name}.png")
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

# -------------------------------------------------------------------------
# Add specific item by EXACT name (SAFE for quotes, spaces, etc.)
# -------------------------------------------------------------------------
def add_item_by_name(item_name: str):
    print(f"   Adding: '{item_name}'...")

    item_elem = WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("""
            const target = arguments[0].trim().toLowerCase();
            const candidates = Array.from(document.querySelectorAll('a, button, div[role="button"], [data-testid*="item"]'))
                .filter(el => {
                    const title = (el.getAttribute('aria-label') || el.textContent || '').trim();
                    const img = el.querySelector('img');
                    const height = el.offsetHeight;
                    const visible = height > 30 && window.getComputedStyle(el).visibility !== 'hidden';
                    return title.toLowerCase() === target && img && visible;
                });
            return candidates.length > 0 ? candidates[0] : null;
        """, item_name)
    )

    if not item_elem:
        raise RuntimeError(f"Item not found: '{item_name}'")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_elem)
    time.sleep(0.5)
    safe_name = "".join(c for c in item_name if c.isalnum() or c in " _-")
    snap(f"before_add_{safe_name}")
    driver.execute_script("arguments[0].click();", item_elem)
    snap(f"modal_{safe_name}")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@role,'dialog') or contains(@class,'modal')]"))
    )

    add_btn = WebDriverWait(driver, 12).until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add') "
             "and (contains(., 'to order') or contains(., 'to cart'))]")
        )
    )
    ActionChains(driver).move_to_element(add_btn).click().perform()
    print(f"   '{item_name}' added to cart")
    snap(f"added_{safe_name}")
    time.sleep(1.0)

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

    # ---- search for restaurant -----------------------------------------
    print(f"2. Searching for '{RESTAURANT_NAME}'...")
    search = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder,'Search')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", search)
    time.sleep(0.3)
    ActionChains(driver).click(search).send_keys(RESTAURANT_NAME).send_keys(Keys.ENTER).perform()
    wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/store/')]")))
    snap("search_results")

    # ---- select restaurant – prefer match, fall back to first open -----
    print(f"3. Selecting restaurant (prefer '{RESTAURANT_NAME}')...")
    restaurant = WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("""
            const target = arguments[0].toLowerCase();

            // 1. Try to find a store that contains the searched name
            const matches = Array.from(document.querySelectorAll('a[href*="/store/"]'))
                .filter(el => {
                    const txt = (el.textContent || '').toLowerCase();
                    return txt.includes(target) && !txt.includes('closed') && el.offsetHeight > 50;
                });

            if (matches.length > 0) return matches[0];

            // 2. No match → take the very first open store
            const anyOpen = Array.from(document.querySelectorAll('a[href*="/store/"]'))
                .filter(el => {
                    const txt = (el.textContent || '').toLowerCase();
                    return !txt.includes('closed') && el.offsetHeight > 50;
                });

            return anyOpen.length > 0 ? anyOpen[0] : null;
        """, RESTAURANT_NAME)
    )

    if not restaurant:
        raise RuntimeError("No open restaurants found after search")

    # Figure out which case we used
    store_text = driver.execute_script("return arguments[0].textContent;", restaurant)
    if RESTAURANT_NAME.lower() in store_text.lower():
        print(f"   Matched: {store_text.strip()}")
    else:
        print(f"   No match – using first open: {store_text.strip()}")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restaurant)
    time.sleep(0.6)
    driver.execute_script("arguments[0].click();", restaurant)
    wait_page_load()
    snap("restaurant_page")

    # ---- wait for menu -------------------------------------------------
    print("4. Loading menu...")
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2 | //h3 | //div[contains(text(), 'Menu') or contains(text(), 'Featured')]")))
    time.sleep(1.0)

    # ---- scroll to load all items --------------------------------------
    print("   Scrolling to load full menu...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    snap("menu_fully_loaded")

    # ---- add all items from list ---------------------------------------
    print(f"5. Adding {len(ITEMS_TO_ADD)} items...")
    added_count = 0
    for item in ITEMS_TO_ADD:
        try:
            add_item_by_name(item)
            added_count += 1
        except Exception as e:
            print(f"   Could not add '{item}': {e}")
            safe_name = "".join(c for c in item if c.isalnum() or c in " _-")
            snap(f"failed_{safe_name}")
    if added_count == 0:
        raise RuntimeError("No items were added!")

    # ---- checkout ------------------------------------------------------
    print("6. Going to checkout...")
    checkout_elem = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH,
            "//button[contains(., 'Checkout')] | //a[contains(., 'Checkout')] | "
            "//button[contains(., 'View cart')] | //*[contains(@href, '/checkout')]"))
    )
    ActionChains(driver).move_to_element(checkout_elem).click().perform()
    wait_page_load()
    snap("checkout_page_loaded")

    # ---- order and pay (CONFIRMED) -------------------------------------
    print("7. Clicking 'Order and Pay'...")
    pay_button = WebDriverWait(driver, 12).until(
        EC.element_to_be_clickable((By.XPATH,
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'place order') or "
            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order and pay') or "
            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pay')]"))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});"
        "window.scrollBy(0, -120);", pay_button)
    time.sleep(0.6)

    try:
        ActionChains(driver).move_to_element(pay_button).pause(0.4).click().perform()
        print("   Clicked via ActionChains")
    except:
        driver.execute_script("arguments[0].click();", pay_button)
        print("   Clicked via JS")

    # Confirm click worked
    try:
        WebDriverWait(driver, 8).until(EC.staleness_of(pay_button))
        print("   Pay button disappeared")
    except:
        print("   Retrying click...")
        driver.execute_script("arguments[0].click();", pay_button)
        WebDriverWait(driver, 8).until(EC.staleness_of(pay_button))

    # Confirm order placed
    WebDriverWait(driver, 15).until(
        lambda d: (
            d.execute_script("return document.location.pathname.includes('/order/')") or
            len(d.find_elements(By.XPATH,
                "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order received') or "
                "contains(., 'Thank you')]")) > 0
        )
    )
    snap("order_submitted")
    print(f"\nORDER PLACED! {added_count} items from selected restaurant")
    print("   Check order_submitted.png")

except Exception as e:
    print(f"\nERROR: {e}")
    snap("FINAL_ERROR")
finally:
    input("\nPress ENTER to close…")
    driver.quit()