from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import csv
import json

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

for i in range(len(usernames)):
    username = usernames[i]
    password = passwords[i]
    profile_name = f"account{i+1}"
    
    driver = webdriver.Chrome()
    
    try:
        driver.get("https://twitter.com/login")
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

        # Save cookies to JSON file
        with open(f"{profile_name}_cookies.json", "w") as f:
            json.dump(cookies, f)

        # Extract required cookies
        ct0 = next((c['value'] for c in cookies if c['name'] == 'ct0'), '')
        auth_token = next((c['value'] for c in cookies if c['name'] == 'auth_token'), '')

        output_rows.append({
            "username": username,
            "auth_token": auth_token,
            "ct0": ct0
        })

        print(f"✅ Saved cookies and tokens for {username}")
    
    except Exception as e:
        print(f"❌ Error processing {username}: {str(e)}")
        
    
    finally:
        driver.quit()
        continue

# Write results to CSV
with open("twitter_tokens.csv", "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["username", "auth_token", "ct0"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in output_rows:
        writer.writerow(row)

print("📄 twitter_tokens.csv has been created.")