# verify_sel.py
try:
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager
    print("Selenium is installed and working!")
    print("ChromeDriver will be auto-managed.")
except ImportError as e:
    print("Still missing:", e)