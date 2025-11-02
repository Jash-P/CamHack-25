# ubereats_bot_no_login.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
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
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label,'Account')]")))
        return True
    except:
        return True

try:
    print(f"Using profile: {BOT_PROFILE}\n")
    print("1. Opening Uber Eats...")
    driver.get("https://www.ubereats.com")
    wait_page_load()
    snap("home")

    if not is_logged_in():
        print("NOT LOGGED IN – log in manually.")
        input("   Press ENTER when done…")
    print("Login confirmed!\n")

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'delivery address')]")))
        print("Address missing – set it.")
        input("   Press ENTER after…")
    except:
        print("Address set.\n")

    print("2. Searching for pizza...")
    search = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder,'Search')]")))
    search.clear()
    search.send_keys("pizza")
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

    # ---- 6. Add first menu item (USING href="/store/…") ----
    print("4. Adding first item to cart...")

    print("   Waiting for menu section...")
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2 | //h3 | //div[contains(text(), 'Menu') or contains(text(), 'Featured')]")))

    print("   Scrolling to load items...")
    for i in range(6):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1.5)
        snap(f"scroll_{i+1}")

    print("   Finding first visible menu item by href...")
    item_link = None
    for attempt in range(15):
        candidates = driver.find_elements(
            By.XPATH,
            "//a[contains(@href, '/store/') and not(contains(.,'Closed')) and .//img]"
        )
        for cand in candidates:
            if cand.is_displayed() and cand.size['height'] > 30:   # not a hidden stub
                item_link = cand
                break
        if item_link:
            break
        time.sleep(1)

    if not item_link:
        raise RuntimeError("No visible store-item found – see last scroll_*.png")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item_link)
    time.sleep(0.8)
    snap("before_click_store_item")

    # Click via JS – bypasses any overlay that Selenium sometimes misses
    driver.execute_script("arguments[0].click();", item_link)
    snap("after_click_store_item")
    time.sleep(3)          # give the modal animation a moment

    # ---- Modal verification (unchanged) ----
    print("   Waiting for modal...")
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@role,'dialog') or contains(@class,'modal') or contains(@class,'sheet')]"))
    )
    snap("modal_opened")

    print("   Clicking 'Add'...")
    add_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add') and not(contains(., 'all'))]"))
    )
    driver.execute_script("arguments[0].click();", add_btn)
    snap("add_clicked")
    time.sleep(2)

    try:
        bag = WebDriverWait(driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add to bag')]"))
        )
        driver.execute_script("arguments[0].click();", bag)
        print("   Added to bag")
    except:
        pass

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//span[text()='1' and (ancestor::button | ancestor::a)]"))
    )
    snap("item_added")
    print("   Item added! Cart = 1")

    print("5. Going to checkout...")
    checkout = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Checkout')]")))
    driver.execute_script("arguments[0].click();", checkout)
    wait_page_load()
    snap("checkout_ready")
    print("\nSUCCESS! At checkout – open checkout_ready.png")

except Exception as e:
    print(f"\nERROR: {e}")
    snap("FINAL_ERROR")
finally:
    input("\nPress ENTER to close…")
    driver.quit()