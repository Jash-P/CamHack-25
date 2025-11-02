# save_cookies.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pickle
import os

# Reuse your real Chrome profile (where you're already logged in)
options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/Users/jash/Library/Application Support/Google/Chrome")
options.add_argument("--profile-directory=Default")  # Change if you use "Profile 1", etc.

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

print("Opening Uber Eats in your logged-in Chrome profile...")
driver.get("https://www.ubereats.com")

input("\nPress Enter AFTER you see you're logged in (check your name in top-right)...\n")

# Save cookies
cookies_file = "ubereats_cookies.pkl"
pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
print(f"Cookies saved to {cookies_file}")

driver.quit()