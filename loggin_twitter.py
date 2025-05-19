from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import csv
import json

# List of usernames and passwords
usernames = [
    "lara_hamda76036",
    "ElissaWehb76215",
    "AhamadHach67888",
    "IsSerha21953",
    "AliAlManso3195",
    "DulaimiNoo42353"
]

passwords = [
    "Barca_Real_4_3",
    "Real_Is_The_Worst",
    "Real_Is_The_Worst_1",
    "Real_Is_The_Worst_2",
    "Real_Is_The_Worst_3",
    "Real_Is_The_Worst_4"
]

output_rows = []


def login_and_extract_tokens(driver, username, password, profile_name):
    """
    Performs login on Twitter and extracts cookies (ct0 and auth_token)
    Returns a dictionary with tokens or None if failed
    """
    try:
        driver.get("https://twitter.com/login ")
        time.sleep(3)

        # Enter username
        username_field = driver.find_element(By.NAME, "text")
        username_field.send_keys(username)
        username_field.send_keys(Keys.RETURN)
        time.sleep(2)

        # Enter password
        password_field = driver.find_element(By.NAME, "password")
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        # Get cookies
        cookies = driver.get_cookies()

        # Extract required cookies
        ct0 = next((c['value'] for c in cookies if c['name'] == 'ct0'), '')
        auth_token = next((c['value'] for c in cookies if c['name'] == 'auth_token'), '')

        print(f"✅ Saved cookies and tokens for {username}")
        return {
            "username": username,
            "auth_token": auth_token,
            "ct0": ct0
        }

    except Exception as e:
        print(f"❌ Error processing {username}: {str(e)}")
        return None


# Main loop
for i in range(len(usernames)):
    username = usernames[i]
    password = passwords[i]
    profile_name = f"account{i + 1}"

    driver = webdriver.Chrome()

    try:
        result = login_and_extract_tokens(driver, username, password, profile_name)
        if result:
            output_rows.append(result)
    finally:
        driver.quit()


# Write results to CSV
with open("twitter_tokens.csv", "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["username", "auth_token", "ct0"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in output_rows:
        writer.writerow(row)

print("📄 twitter_tokens.csv has been created.")