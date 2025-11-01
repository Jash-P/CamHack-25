from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

# Set up Chrome options (headless for stealth)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Remove for visible debugging
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Initialize driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Navigate to Uber Eats
    driver.get("https://www.ubereats.com")
    time.sleep(2)

    # Step 2: Log in (replace with your email/password; handle 2FA manually)
    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')]")))
    login_button.click()
    time.sleep(2)

    email_input = wait.until(EC.presence_of_element_located((By.ID, "login-username")))  # Adjust selector if needed
    email_input.send_keys("your_email@example.com")
    
    password_input = driver.find_element(By.ID, "login-password")  # Adjust
    password_input.send_keys("your_password")
    
    submit_login = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit_login.click()
    time.sleep(5)  # Wait for login/2FA

    # Step 3: Search for food (e.g., "pizza near me")
    search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search for restaurants']")))
    search_input.send_keys("pizza")
    search_input.submit()
    time.sleep(3)

    # Step 4: Select first restaurant
    first_restaurant = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'restaurant')]")))  # Adjust for actual class
    first_restaurant.click()
    time.sleep(3)

    # Step 5: Add first menu item to cart
    first_item = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add to cart')]")))
    first_item.click()
    time.sleep(2)

    # Step 6: Proceed to checkout
    checkout_button = driver.find_element(By.XPATH, "//button[contains(text(), 'View cart and checkout')]")
    checkout_button.click()
    time.sleep(3)

    # Enter delivery address (if not saved)
    # address_input = driver.find_element(By.ID, "address-input")
    # address_input.send_keys("123 Main St, City, State 12345")
    # ... continue similarly for payment/confirm

    print("Order process initiated successfully! Review manually before completing.")

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()