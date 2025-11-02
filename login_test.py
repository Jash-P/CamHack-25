# save_cookies.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pickle
import os

options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/Users/jash/Documents/CamHack-25/chrome-profile")  # Reuse profile
# OR use default: options.add_argument("--user-data-dir=~/Library/Application Support/Google/Chrome")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.ubereats.com")
input("After logging in manually, press Enter to save cookies...")

# Save cookies
pickle.dump(driver.get_cookies(), open("ubereats_cookies.pkl", "wb"))
print("Cookies saved to ubereats_cookies.pkl")

driver.quit()