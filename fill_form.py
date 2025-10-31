from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pickle
import os

COOKIE_FILE = "google_cookies.pkl"
form_url = "https://docs.google.com/forms/d/e/1FAIpQLSdWKAlQPqcteypacqRFwS0DZEx-247xNVUYnIoigx7bjOHvLg/viewform"

driver = webdriver.Chrome()

# 1. Try to visit form directly with existing cookies
if os.path.exists(COOKIE_FILE):
    driver.get("https://accounts.google.com/")
    with open(COOKIE_FILE, "rb") as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            try:
                # Only add cookies that match the current domain
                if 'domain' in cookie and 'google.com' in cookie['domain']:
                    driver.add_cookie(cookie)
            except Exception:
                # Skip cookies that can't be added
                continue

    # Try accessing the form
    driver.get(form_url)
    time.sleep(2)

    # Check if we're on the form page (not redirected to login)
    if "forms" not in driver.current_url or "ServiceLogin" in driver.current_url:
        print("Cookies expired, need to log in again")
        driver.get("https://accounts.google.com/")
        input("Log in to Google, then press Enter here...")

        # Save new cookies
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(cookies, f)

        driver.get(form_url)
    else:
        print("Successfully accessed form with saved cookies")
else:
    # First time: manual login and save cookies
    print("No saved cookies found, logging in...")
    driver.get("https://accounts.google.com/")
    input("Log in to Google, then press Enter here...")

    # Save cookies
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, "wb") as f:
        pickle.dump(cookies, f)
    print("Cookies saved!")

    driver.get(form_url)
    
    
# form fields
# checkbox: records as <email>@nyu.edu
# text: name
# text netid
# text: Attack case you’d like to flag (please mention the attack case filename along with their NetID)
# text: Please describe the reason for flagging this attack case

checkbox_xpath = '//*[@id="i5"]'
name_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/input'
netid_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[3]/div/div/div[2]/div/div[1]/div/div[1]/input'
attack_case_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[4]/div/div/div[2]/div/div[1]/div/div[1]/input'
reason_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[2]/div[5]/div/div/div[2]/div/div[1]/div[2]/textarea'
submit_xpath = '//*[@id="mG61Hd"]/div[2]/div/div[3]/div[2]/div[1]/div/span/span'

# 2. Fill out fields
checkbox = driver.find_element(By.XPATH, checkbox_xpath)
checkbox.click()
name_input = driver.find_element(By.XPATH, name_xpath)
name_input.send_keys("Steven Li")
netid_input = driver.find_element(By.XPATH, netid_xpath)
netid_input.send_keys("sl36325")
attack_case_input = driver.find_element(By.XPATH, attack_case_xpath)
attack_case_input.send_keys("test1.r2py")
reason_input = driver.find_element(By.XPATH, reason_xpath)
reason_input.send_keys("Test reason")
# submit_button = driver.find_element(By.XPATH, submit_xpath)
# submit_button.click()
time.sleep(3000)
driver.quit()
