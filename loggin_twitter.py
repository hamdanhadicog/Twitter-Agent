from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import csv
from Twitter_Agent import *  # Ensure Twitter_Agent.py is in the same directory


def login_and_extract_tokens(driver, username, password):
    """Logs into Twitter using Selenium and extracts auth_token and ct0 cookies."""
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

        # Extract cookies
        cookies = driver.get_cookies()
        ct0 = next((c['value'] for c in cookies if c['name'] == 'ct0'), '')
        auth_token = next((c['value'] for c in cookies if c['name'] == 'auth_token'), '')
        print(f"✅ Successfully logged in and updated tokens for {username}")
        return {'auth_token': auth_token, 'ct0': ct0}

    except Exception as e:
        print(f"❌ Failed to login for {username}: {str(e)}")
        return None

def main():
    # Read characters.csv
    with open('characters.csv', 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        fieldnames = reader.fieldnames  # Includes all original headers

    agent = TwitterAgent()

    for row in rows:
        username = row['username']
        password = row['password']
        current_auth = row['auth_token']
        current_ct0 = row['ct0']

        # Skip if both tokens exist and are valid
        if current_auth and current_ct0:
            try:
                sess = agent.create_twitter_session(current_ct0, current_auth)
                if agent.is_logged_in(sess):
                    print(f"✅ {username} is already logged in. Skipping.")
                    continue
            except Exception as e:
                print(f"⚠️ Token validation failed for {username}. Attempting re-login: {e}")

        # Attempt to login and update tokens
        driver = webdriver.Chrome()
        try:
            result = login_and_extract_tokens(driver, username, password)
            if result:
                row['auth_token'] = result['auth_token']
                row['ct0'] = result['ct0']
        finally:
            driver.quit()

    # Write updated data back to CSV
    with open('characters.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("📄 characters.csv has been updated with new tokens.")

if __name__ == "__main__":
    main()