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
wait = WebDriverWait(driver, 30)

def snap(name: str):
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(SCREENSHOT_DIR, f"{ts}_{name}.png")
    driver.save_screenshot(path)
    print(f"   Screenshot: {path}")

def wait_page_load():
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(1)

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
            print("   Not logged in: Sign in button visible")
            return False

        current_url = driver.current_url
        if '/feed' in current_url or '/city/' in current_url:
            print(f"   Logged in: URL indicates session ({current_url})")
            return True

        print("   Login status unclear")
        return False
    except Exception as e:
        print(f"   Login check failed: {e}")
        return False

# -------------------------------------------------------------------------
# Helper: add the *n*-th visible menu item (0-based index)
# -------------------------------------------------------------------------
def add_item(index: int):
    print(f"   Adding item #{index + 1}...")

    # 1. Find all visible items
    print("      Locating visible menu items...")
    item_link = None
    for attempt in range(15):
        candidates = driver.find_elements(
            By.XPATH,
            "//a[contains(@href, '/store/') and not(contains(.,'Closed')) and .//img]"
        )
        visible = [c for c in candidates if c.is_displayed() and c.size['height'] > 30]
        if len(visible) > index:
            item_link = visible[index]
            break
        time.sleep(1)

    if not item_link:
        raise RuntimeError(f"Could not find visible item #{index + 1}")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_link)
    time.sleep(0.8)
    snap(f"before_click_item_{index+1}")
    driver.execute_script("arguments[0].click();", item_link)
    snap(f"after_click_item_{index+1}")
    time.sleep(3)

    # 2. Wait for modal
    modal = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@role,'dialog') or contains(@class,'modal') or contains(@class,'sheet')]"))
    )
    snap(f"modal_item_{index+1}")

    # 3. For Taco Bell the modal already has the default selection → just add
    print("      Waiting for 'Add to order' button...")
    add_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.XPATH,
             "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add') "
             "and (contains(., 'to order') or contains(., 'to cart'))]")
        )
    )
    ActionChains(driver).move_to_element(add_btn).click().perform()
    print("      Add button clicked!")
    snap(f"add_clicked_item_{index+1}")
    time.sleep(2.0)

    # 4. Verify cart badge increased
    expected_qty = index + 1
    try:
        badge = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//*[self::span or self::button or self::a or self::div][contains(text(), '{expected_qty}') "
                 "and (contains(@aria-label, 'cart') or contains(@href, '/cart'))]")
            )
        )
        print(f"   Cart now shows: '{badge.text}'")
        snap(f"cart_{expected_qty}_items")
    except:
        print("   Cart badge not updated yet – continuing anyway")
        snap(f"cart_{expected_qty}_fallback")

# -------------------------------------------------------------------------
try:
    print(f"Using profile: {BOT_PROFILE}\n")
    print("1. Opening Uber Eats...")
    driver.get("https://www.ubereats.com")
    wait_page_load()
    snap("home")

    if not is_logged_in():
        print("NOT LOGGED IN – log in manually.")
        input("   Press ENTER when done…")
        if not is_logged_in():
            raise RuntimeError("Still not logged in after manual login")
    print("Login confirmed!\n")

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'delivery address')]")))
        print("Address missing – set it.")
        input("   Press ENTER after…")
    except:
        print("Address set.\n")

    print("2. Searching for Taco Bell...")
    search = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder,'Search')]")))
    search.clear()
    search.send_keys("Taco Bell")
    search.send_keys(Keys.ENTER)
    wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/store/')]")))
    snap("search_results")

    print("3. Selecting first open restaurant...")
    wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'/store/')]")))
    time.sleep(3)
    stores = driver.find_elements(By.XPATH, "//a[contains(@href,'/store/') and not(contains(.,'Closed'))]")
    if not stores:
        raise RuntimeError("No open restaurants")
    restaurant = stores[0]
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", restaurant)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", restaurant)
    wait_page_load()
    snap("restaurant_page")

    # ---- 4. Load the menu ------------------------------------------------
    print("4. Loading menu...")
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2 | //h3 | //div[contains(text(), 'Menu') or contains(text(), 'Featured')]")))
    for i in range(6):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1.5)
        snap(f"scroll_{i+1}")

    # ---- 5. Add item 1 and item 3 ----------------------------------------
    add_item(0)   # 1st item
    add_item(2)   # 3rd item

    # ---- 6. Checkout -----------------------------------------------------
    print("5. Going to checkout...")
    checkout_selectors = [
        "//button[contains(., 'Checkout')]",
        "//a[contains(., 'Checkout')]",
        "//button[contains(., 'View cart')]",
        "//a[contains(., 'View cart')]",
        "//*[contains(@href, '/checkout') or contains(@href, '/cart')]"
    ]
    checkout_elem = None
    for xpath in checkout_selectors:
        try:
            checkout_elem = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            print(f"   Found checkout button: {xpath}")
            break
        except:
            continue
    if not checkout_elem:
        raise RuntimeError("Could not find checkout button")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkout_elem)
    time.sleep(0.8)
    try:
        checkout_elem.click()
    except:
        ActionChains(driver).move_to_element(checkout_elem).click().perform()

    wait_page_load()
    snap("checkout_page_loaded")
    print("   At checkout page")

    # ---- 7. Order and Pay ------------------------------------------------
    print("6. Clicking 'Order and Pay'...")
    pay_selectors = [
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order and pay')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'place order')]",
        "//button[contains(., 'Pay') and contains(., '£')]",
        "//button[contains(@data-testid, 'place-order')]",
        "//button[.//span[contains(text(), 'Pay')]]",
        "//button[contains(@class, 'place-order') or contains(@class, 'submit')]"
    ]
    pay_button = None
    for xpath in pay_selectors:
        try:
            pay_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            print(f"   Found pay button: {xpath}")
            break
        except:
            continue
    if not pay_button:
        raise RuntimeError("Could not find 'Order and Pay' button")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", pay_button)
    time.sleep(1.0)
    try:
        pay_button.click()
        print("   'Order and Pay' clicked (normal)")
    except:
        ActionChains(driver).move_to_element(pay_button).click().perform()
        print("   'Order and Pay' clicked (ActionChains)")

    snap("order_submitted")
    print("\nORDER PLACED! Check order_submitted.png")

except Exception as e:
    print(f"\nERROR: {e}")
    snap("FINAL_ERROR")
finally:
    input("\nPress ENTER to close…")
    driver.quit()