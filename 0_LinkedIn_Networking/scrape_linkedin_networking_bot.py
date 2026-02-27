# FILE: ./0_LinkedIn_Networking/scrape_linkedin_networking_bot.py

import os
import time
import json
import datetime
import random
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# --- Dynamic Path Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# Switched to JSON format for richer logging
BIRTHDAY_LOG_FILE_JSON = os.path.join(PROJECT_ROOT, 'birthday_log.json')
NEWS_LOG_FILE_JSON = os.path.join(PROJECT_ROOT, 'news_log.json')
LIKED_POSTS_LOG_JSON = os.path.join(PROJECT_ROOT, 'liked_posts_log.json')
CONNECTION_LOG_FILE_JSON = os.path.join(PROJECT_ROOT, 'connection_log.json')
BIRTHDAY_LOG_FILE_OLD = os.path.join(PROJECT_ROOT, 'birthday_log.txt')
BIRTHDAY_URL = "https://www.linkedin.com/mynetwork/catch-up/birthday/"

def load_log():
    """Loads birthday log from JSON file. Returns a list of log entries."""
    if not os.path.exists(BIRTHDAY_LOG_FILE_JSON):
        return []
    try:
        with open(BIRTHDAY_LOG_FILE_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is empty, corrupted, or not found, start with a fresh log
        return []

def save_log(log_data):
    """Saves the entire log data list to the JSON file."""
    with open(BIRTHDAY_LOG_FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)

def load_news_log():
    """Loads news log from JSON file. Returns a list of URLs."""
    if not os.path.exists(NEWS_LOG_FILE_JSON):
        return []
    try:
        with open(NEWS_LOG_FILE_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_news_log(log_data):
    """Saves the entire log data list to the JSON file."""
    with open(NEWS_LOG_FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)

def load_liked_posts_log():
    """Loads liked posts log from JSON file. Returns a list of post URNs."""
    if not os.path.exists(LIKED_POSTS_LOG_JSON):
        return []
    try:
        with open(LIKED_POSTS_LOG_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_liked_posts_log(log_data):
    """Saves the entire log data list to the JSON file."""
    with open(LIKED_POSTS_LOG_JSON, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)

def load_connection_log():
    """Loads connection log from JSON file. Returns a list of log entry dicts."""
    if not os.path.exists(CONNECTION_LOG_FILE_JSON):
        return []
    try:
        with open(CONNECTION_LOG_FILE_JSON, 'r', encoding='utf-8') as f:
            # Handle empty file case
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_connection_log(log_data):
    """Saves the entire log data list (of dicts) to the JSON file."""
    with open(CONNECTION_LOG_FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)

def connect_to_chrome():
    """Establishes a connection to the running Chrome debugger instance with retries."""
    print("Attempting to connect to Chrome...")
    retries = 10
    wait_time = 3 # seconds
    for i in range(retries):
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            driver = webdriver.Chrome(options=chrome_options)
            
            # Verify the connection is stable
            _ = driver.title
            print(f"Successfully connected to browser with title: '{driver.title}'")
            return driver
        except Exception as e:
            print(f"Connection attempt {i+1}/{retries} failed.")
            if i < retries - 1:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"FATAL: Could not connect to Chrome after multiple retries. Error: {e}")
                return None

def wish_birthdays(driver):
    """Navigates to the birthday page and sends wishes."""
    # --- Timezone Check ---
    try:
        est_tz = pytz.timezone('America/New_York')
        now_est = datetime.datetime.now(est_tz)
        
        start_hour = 9
        end_hour = 17

        if not (start_hour <= now_est.hour < end_hour):
            print(f"Current time ({now_est.strftime('%H:%M:%S %Z')}) is outside the operational window ({start_hour}:00 to {end_hour}:00 EST). Skipping birthday wishes.")
            return
    except Exception as e:
        print(f"Could not perform timezone check due to an error: {e}. Proceeding with caution.")
        
    print("--- Phase 0: Wishing Birthdays ---")
    driver.get(BIRTHDAY_URL)
    print("Navigated to birthdays page. Waiting for a random time...")
    time.sleep(random.uniform(3, 7))
    
    log_data = load_log()
    processed_today_set = {(entry['fullName'], entry['date']) for entry in log_data}
    print(f"Loaded {len(log_data)} log entries.")
    
    actions = ActionChains(driver)

    same_day_messages = [
        "Happy Birthday, [Name]! Wishing you a fantastic day and a highly successful year ahead.",
        "Wishing you the happiest of birthdays, [Name]! Hope you get some time to unplug and celebrate today.",
        "Happy Birthday, [Name]! Always great having you in my network. Have a wonderful day!",
        "Have a fantastic birthday, [Name]! Wishing you all the best both personally and professionally this year.",
        "Happy Birthday! Hope you get to enjoy some great food and good company today, [Name].",
        "Wishing you a very happy birthday, [Name]! Hope this next year brings you lots of great opportunities.",
        "Happy Birthday, [Name]! Make sure you take some time to celebrate yourself today.",
        "Have a wonderful birthday, [Name]! Hope this next trip around the sun is your best one yet.",
        "Happy Birthday, [Name]! Wishing you a great day and a year full of big wins.",
        "Wishing you a fantastic birthday today, [Name]! Keep up the great work this year."
    ]

    belated_messages = [
        "Happy belated birthday, [Name]! I hope you had a wonderful time celebrating.",
        "Happy belated, [Name]! Sorry I missed the actual day, but I hope it was a great one.",
        "Wishing you a happy belated birthday, [Name]! I hope the celebrations are still going strong.",
        "Happy belated birthday, [Name]! Hope you got to take some time offline to enjoy it.",
        "Sorry to miss the big day, but happy belated birthday, [Name]! Wishing you a fantastic year ahead.",
        "Happy belated birthday,[Name]! I’m a little late to the party, but wishing you nothing but the best this year.",
        "Wishing you a happy belated birthday, [Name]! Hope this coming year is full of great projects and personal wins.",
        "Happy belated, [Name]! Always great being connected here. Hope you had a fantastic time celebrating.",
        "Happy belated birthday, [Name]! Hope it was a memorable one and that you have a great year ahead.",
        "Wishing you a happy belated birthday, [Name]! Hope you had a great day surrounded by friends and family."
    ]

    wished_count = 0
    daily_limit = random.randint(1, 8)
    print(f"Today's birthday wish limit is set to {daily_limit}.")
    max_tabs_without_finding_new_person = random.randint(50, 150)
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_person:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(random.uniform(0.5, 0.9))

        try:
            active_element = driver.switch_to.active_element
            
            if active_element.tag_name == 'a' and active_element.get_attribute('data-view-name') == 'nurture-card-primary-button':
                
                aria_label = active_element.get_attribute("aria-label")
                if not aria_label or not aria_label.startswith("Message "):
                    continue
                
                name = aria_label.split(':')[0].replace("Message ", "").strip()
                today_str = datetime.date.today().isoformat()

                if (name, today_str) in processed_today_set:
                    print(f"Skipping {name}, already wished today ({today_str}).")
                    continue

                if wished_count >= daily_limit:
                    print(f"Reached the processing limit of {daily_limit} people for this run. Stopping.")
                    break

                print(f"Found unprocessed birthday for: {name}")
                tabs_count = 0 # Reset counter

                first_name = name.split()[0]
                
                if "belated" in aria_label.lower():
                    birthday_type = "belated birthday"
                    message_template = random.choice(belated_messages)
                    new_message = message_template.replace("[Name]", first_name)
                    print("Identified as a belated birthday.")
                else:
                    birthday_type = "birthday"
                    message_template = random.choice(same_day_messages)
                    new_message = message_template.replace("[Name]", first_name)


                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter. Waiting for message dialog to appear...")
                time.sleep(random.uniform(1, 3))

                try:
                    print("Assuming focus is now on the message box.")
                    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
                    print("Cleared default message.")
                    time.sleep(random.uniform(1, 3))
                    
                    actions.send_keys(new_message).perform()
                    print(f"Typed new message: '{new_message}'")
                    time.sleep(random.uniform(1, 3))

                    print("Following hardcoded tabbing strategy...")
                    send_button_found = False
                    
                    for i in range(5):
                        actions.send_keys(Keys.TAB).perform()
                        time.sleep(random.uniform(0.5, 0.9))
                        print(f"Tab {i+1}/5")
                    
                    print("Now focused on the presumed 'Send' button. Waiting 5 seconds...")
                    time.sleep(random.uniform(1, 3))
                    
                    actions.send_keys(Keys.ENTER).perform()
                    print("Sent Enter key.")
                    send_button_found = True 

                    if not send_button_found:
                        raise Exception("Hardcoded tabbing strategy failed.")

                    new_log_entry = {"fullName": name, "date": today_str, "type": birthday_type}
                    log_data.append(new_log_entry)
                    save_log(log_data)
                    processed_today_set.add((name, today_str))
                    print(f"Logged {name} as processed for {today_str}.")
                    wished_count += 1
                    time.sleep(random.randint(480, 1080))

                    print("Message sent. Reloading birthdays page to refresh the list...")
                    driver.get(BIRTHDAY_URL)
                    print("Page reloaded. Waiting 5 seconds to load...")
                    time.sleep(random.uniform(3, 7))

                except Exception as e:
                    print(f"Error: An error occurred while handling the message dialog for {name}: {e}")
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(random.uniform(1, 3))

        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"An unexpected error occurred in the main loop: {e}")
            continue

    if wished_count > 0:
        print(f"Successfully wished {wished_count} people a happy birthday.")
    else:
        print("No new birthdays found to process on the page.")

    print("--- Birthday wishing complete ---")


def like_job_changes(driver):
    """Navigates to the job changes page and likes new job updates."""
    print("--- Phase 1: Liking Job Changes ---")
    job_changes_url = "https://www.linkedin.com/mynetwork/catch-up/job_changes/"
    driver.get(job_changes_url)
    print("Navigated to job changes page. Waiting for a random time...")
    time.sleep(random.uniform(3, 7))

    actions = ActionChains(driver)

    liked_count = 0
    daily_limit = random.randint(1, 3)
    print(f"Today's job change like limit is set to {daily_limit}.")
    max_tabs_without_finding_new_card = random.randint(50, 150)
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_card:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(random.uniform(0.5, 0.9))

        try:
            active_element = driver.switch_to.active_element
            
            # The active element could be the button or a container.
            # We look for the SVG with the right aria-label within the active element.
            try:
                svg_element = active_element.find_element(By.CSS_SELECTOR, "svg[aria-label='Reaction button state: no reaction']")
                
                # If we found it, we are on the right element (or its container)
                print("Found an un-liked job change.")
                tabs_count = 0  # Reset counter

                # SAFETY LIMIT: Stop after processing 20 people in a single run.
                if liked_count >= daily_limit:
                    print(f"Reached the processing limit of {daily_limit} likes for this run. Stopping.")
                    break

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter to like the post.")
                liked_count += 1
                time.sleep(random.uniform(1, 3))  # Wait a bit before continuing

            except NoSuchElementException:
                # This active element doesn't contain the like button we're looking for.
                continue
        
        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"An unexpected error occurred in the job change loop: {e}")
            continue

    if liked_count > 0:
        print(f"Successfully liked {liked_count} job changes.")
    else:
        print("No new job changes found to like on the page.")

    print("--- Job change liking complete ---")


def like_work_anniversaries(driver):
    """Navigates to the work anniversaries page and likes new anniversary updates."""
    print("--- Phase 2: Liking Work Anniversaries ---")
    work_anniversaries_url = "https://www.linkedin.com/mynetwork/catch-up/work_anniversaries/"
    driver.get(work_anniversaries_url)
    print("Navigated to work anniversaries page. Waiting for a random time...")
    time.sleep(random.uniform(3, 7))

    actions = ActionChains(driver)

    liked_count = 0
    daily_limit = random.randint(2, 6)
    print(f"Today's work anniversary like limit is set to {daily_limit}.")
    max_tabs_without_finding_new_card = random.randint(50, 150)
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_card:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(random.uniform(0.5, 0.9))

        try:
            active_element = driver.switch_to.active_element
            
            # The active element could be the button or a container.
            # We look for the SVG with the right aria-label within the active element.
            try:
                svg_element = active_element.find_element(By.CSS_SELECTOR, "svg[aria-label='Reaction button state: no reaction']")
                
                # If we found it, we are on the right element (or its container)
                print("Found an un-liked work anniversary.")
                tabs_count = 0  # Reset counter

                # SAFETY LIMIT: Stop after processing 20 people in a single run.
                if liked_count >= daily_limit:
                    print(f"Reached the processing limit of {daily_limit} likes for this run. Stopping.")
                    break

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter to like the post.")
                liked_count += 1
                time.sleep(random.uniform(1, 3))  # Wait a bit before continuing

            except NoSuchElementException:
                # This active element doesn't contain the like button we're looking for.
                continue
        
        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"An unexpected error occurred in the work anniversary loop: {e}")
            continue

    if liked_count > 0:
        print(f"Successfully liked {liked_count} work anniversaries.")
    else:
        print("No new work anniversaries found to like on the page.")

    print("--- Work anniversary liking complete ---")


def like_education_updates(driver):
    """Navigates to the education updates page and likes new updates."""
    print("--- Phase 3: Liking Education Updates ---")
    education_updates_url = "https://www.linkedin.com/mynetwork/catch-up/education/"
    driver.get(education_updates_url)
    print("Navigated to education updates page. Waiting for a random time...")
    time.sleep(random.uniform(3, 7))

    actions = ActionChains(driver)

    liked_count = 0
    daily_limit = random.randint(1, 3)
    print(f"Today's education update like limit is set to {daily_limit}.")
    max_tabs_without_finding_new_card = random.randint(50, 150)
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_card:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(random.uniform(0.5, 0.9))

        try:
            active_element = driver.switch_to.active_element
            
            try:
                svg_element = active_element.find_element(By.CSS_SELECTOR, "svg[aria-label='Reaction button state: no reaction']")
                
                print("Found an un-liked education update.")
                tabs_count = 0  # Reset counter

                if liked_count >= daily_limit:
                    print(f"Reached the processing limit of {daily_limit} likes for this run. Stopping.")
                    break

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter to like the post.")
                liked_count += 1
                time.sleep(random.uniform(1, 3))  # Wait a bit before continuing

            except NoSuchElementException:
                continue
        
        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"An unexpected error occurred in the education update loop: {e}")
            continue

    if liked_count > 0:
        print(f"Successfully liked {liked_count} education updates.")
    else:
        print("No new education updates found to like on the page.")

    print("--- Education update liking complete ---")


def view_connection_profiles(driver, base_search_url, keyword):
    """
    Navigates through paginated search results for a given keyword to find, and view new profiles.
    """
    print(f"--- Phase 4: Viewing Profiles for keyword '{keyword}' ---")
    
    profile_urls_to_visit = []
    
    # Load the full log data, and create a set of just the URLs for efficient checking
    processed_log_data = load_connection_log()
    processed_urls = {entry['url'] for entry in processed_log_data}
    
    # 1. Iterate through pages to find new people
    print("Scanning search result pages for new profiles...")
    for page_num in range(1, 6): # Pages 1 to 5
        if len(profile_urls_to_visit) >= 15:
            break
        print(f"Scanning page {page_num}...")
        driver.get(base_search_url + str(page_num))
        time.sleep(5)
        profile_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='search-entity-result-universal-template']")

        for card in profile_cards:
            if len(profile_urls_to_visit) >= 15:
                break
            try:
                card.find_element(By.CSS_SELECTOR, "button[aria-label*='Invite']")
                profile_link_element = card.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
                profile_url = profile_link_element.get_attribute('href').split('?')[0]
                if profile_url not in processed_urls and profile_url not in profile_urls_to_visit:
                    profile_urls_to_visit.append(profile_url)
            except NoSuchElementException:
                continue

    print(f"Finished scanning. Found {len(profile_urls_to_visit)} new profiles to visit.")

    # 2. Visit pages, scrape data, and log
    viewed_count = 0
    for url in profile_urls_to_visit:
        print(f"Viewing and scraping profile {viewed_count + 1}/{len(profile_urls_to_visit)}: {url}")
        driver.get(url)
        time.sleep(5) # Wait for page to load

        # --- Scrape data ---
        name, role, about_text, company = None, None, None, None

        # Per user request, we are temporarily disabling the complex scraping logic 
        # to focus on just visiting and logging the URL and timestamp.
        name, role, about_text, company = None, None, None, None

        # Create the new log entry object
        new_log_entry = {
            "url": url,
            "dateTimeVisited": datetime.datetime.now().isoformat(),
            "name": name,
            "role": role,
            "company": company, # Intentionally left null for now
            "about": about_text,
            "connectionSent": False
        }
        
        processed_log_data.append(new_log_entry)
        save_connection_log(processed_log_data)
        viewed_count += 1
        print(f"Logged scraped data for {url}. Now starting wait period.")

        wait_time_seconds = 75
        print(f"Waiting for {wait_time_seconds} seconds...")
        time.sleep(wait_time_seconds)

    if viewed_count > 0:
        print(f"Successfully viewed and scraped {viewed_count} profiles.")
    else:
        print("No new profiles to view/scrape were found within the first 5 pages.")
        
    print("--- Profile viewing and scraping complete ---")


def share_linkedin_news(driver):
    print("--- Phase 5: Sharing LinkedIn News ---")
    driver.get("https://www.linkedin.com/feed/")
    print("Navigated to LinkedIn feed. Waiting for 5 seconds...")
    time.sleep(5)

    actions = ActionChains(driver)

    # 1. Tab until we are inside the LinkedIn News module
    news_module = None
    print("Tabbing to find LinkedIn News module...")
    for i in range(200): # Safety limit
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.randint(1, 9))
        try:
            active_element = driver.switch_to.active_element
            # Check if we've landed inside the news module
            news_module_container = active_element.find_element(By.XPATH, "ancestor-or-self::div[@data-view-name='news-module']")
            if news_module_container:
                print(f"Found LinkedIn News module after {i+1} tabs.")
                news_module = news_module_container
                break
        except NoSuchElementException:
            continue
    
    if not news_module:
        print("Could not tab to the LinkedIn News module. Aborting.")
        return

    # 2. Find the first unread news article
    processed_urls = load_news_log()
    news_links = news_module.find_elements(By.CSS_SELECTOR, "a[data-view-name='news-module-storyline-card-click']")
    
    unread_news_url = None
    for link_element in news_links:
        url = link_element.get_attribute('href')
        if url and url not in processed_urls:
            unread_news_url = url
            break # Found the first unread one
    
    if not unread_news_url:
        print("No unread news articles found in the module.")
        return

    # 3. Navigate to the news page
    print(f"Navigating to unread news article: {unread_news_url}")
    driver.get(unread_news_url)
    print("Waiting for news page to load...")
    time.sleep(5)

    # 4. Tab to find the Share button and click it
    print("Tabbing to find the 'Share' button...")
    share_button_found = False
    for i in range(150): # Safety limit
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.randint(8, 38))
        try:
            active_element = driver.switch_to.active_element
            if active_element.get_attribute("aria-label") == "Open share menu":
                print(f"Found 'Share' button after {i+1} tabs.")
                active_element.send_keys(Keys.ENTER)
                print("Clicked 'Share' button.")
                share_button_found = True
                
                # Log that this URL has been processed
                processed_urls.append(unread_news_url)
                save_news_log(processed_urls)
                print(f"Logged {unread_news_url} as processed.")
                break
        except NoSuchElementException:
            continue
            
    if not share_button_found:
        print("Could not find the 'Share' button on the news page.")

    print("--- LinkedIn News sharing complete ---")

def like_search_results(driver, search_url, keyword):
    print(f"--- Phase 6: Liking from Search Results for '{keyword}' ---")
    
    # 1. Navigate to URL
    driver.get(search_url)
    print(f"Navigated to search results page for '{keyword}'. Waiting for page to load...")
    time.sleep(7) # Give it a bit more time for posts to load

    actions = ActionChains(driver)

    processed_urns = load_liked_posts_log()
    liked_this_session = 0
    
    # Main tabbing loop
    for i in range(500): # Generous tabbing limit
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.randint(8, 38))
        
        try:
            active_element = driver.switch_to.active_element
            
            # 2. Check if the element is a "Like" button that hasn't been pressed
            is_like_button = active_element.get_attribute("aria-label") == "React Like"
            is_unpressed = active_element.get_attribute("aria-pressed") == "false"

            if is_like_button and is_unpressed:
                print(f"Found a potential un-liked post for '{keyword}'.")
                
                # 3. Find the parent post's URN to check if it's already processed
                post_card = active_element.find_element(By.XPATH, "ancestor::div[@data-urn]")
                post_urn = post_card.get_attribute("data-urn")
                
                if not post_urn:
                    print("Could not find post URN. Skipping.")
                    continue
                    
                if post_urn in processed_urns:
                    print(f"Post {post_urn} already processed. Skipping.")
                    continue
                    
                # 4. Like the post and log it
                print(f"Liking new post: {post_urn}")
                time.sleep(5) # Per user request
                active_element.send_keys(Keys.ENTER)
                
                processed_urns.append(post_urn)
                save_liked_posts_log(processed_urns)
                print("Post liked and logged.")
                time.sleep(5) # Per user request
                
                liked_this_session += 1
                if liked_this_session >= 5: # Safety break for the session
                    print(f"Liked 20 posts for '{keyword}' this session. Stopping.")
                    break
                    
        except NoSuchElementException:
            # The active element wasn't a like button or didn't have the post URN ancestor.
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue

    print(f"--- Liking from search results for '{keyword}' complete. ---")


def main():
    """Main function to run the LinkedIn networking bot."""
    print("--- LinkedIn Networking Bot Starting ---")
    
    # --- Cleanup old log file ---
    if os.path.exists(BIRTHDAY_LOG_FILE_OLD):
        print(f"Removing old log file: {BIRTHDAY_LOG_FILE_OLD}")
        os.remove(BIRTHDAY_LOG_FILE_OLD)

    driver = connect_to_chrome()
    if not driver:
        return

    tasks = [
        wish_birthdays,
        like_job_changes,
        like_work_anniversaries,
        like_education_updates
    ]

    random.shuffle(tasks)

    for i, task in enumerate(tasks):
        task(driver)
        if i < len(tasks) - 1:  # Don't sleep after the last task
            sleep_time = random.randint(180, 900)
            print(f"Waiting for {sleep_time // 60} minutes and {sleep_time % 60} seconds before the next task...")
            time.sleep(sleep_time)
    
    search_tasks = {
        "project manager": "https://www.linkedin.com/search/results/people/?keywords=project%20manager&network=%5B%22S%22%5D&origin=FACETED_SEARCH&page=",
        "hiring": "https://www.linkedin.com/search/results/people/?keywords=hiring&network=%5B%22S%22%5D&origin=FACETED_SEARCH&page=",
        "recruiter": "https://www.linkedin.com/search/results/people/?keywords=recruiter&network=%5B%22S%22%5D&origin=GLOBAL_SEARCH_HEADER&page=",
        "scrum": "https://www.linkedin.com/search/results/people/?keywords=scrum&network=%5B%22S%22%5D&origin=GLOBAL_SEARCH_HEADER&page=",
        "safe": "https://www.linkedin.com/search/results/people/?keywords=safe&network=%5B%22S%22%5D&origin=GLOBAL_SEARCH_HEADER&page="
    }
    
    # for keyword, url in search_tasks.items():
    #     view_connection_profiles(driver, url, keyword)
    # # share_linkedin_news(driver)

    like_tasks = {
        "ai": "https://www.linkedin.com/search/results/content/?keywords=AI%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "tech": "https://www.linkedin.com/search/results/content/?keywords=tech%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "pmp": "https://www.linkedin.com/search/results/content/?keywords=pmp%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "project manager": "https://www.linkedin.com/search/results/content/?keywords=project%25manager&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "product management": "https://www.linkedin.com/search/results/content/?keywords=product%25management&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "agile": "https://www.linkedin.com/search/results/content/?keywords=agile%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "safe": "https://www.linkedin.com/search/results/content/?keywords=safe%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "scrum": "https://www.linkedin.com/search/results/content/?keywords=scrum%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "systems": "https://www.linkedin.com/search/results/content/?keywords=systems%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "robot": "https://www.linkedin.com/search/results/content/?keywords=robot%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "future": "https://www.linkedin.com/search/results/content/?keywords=future%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "innovation": "https://www.linkedin.com/search/results/content/?keywords=innovation%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "digital": "https://www.linkedin.com/search/results/content/?keywords=digital%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
        "transformation": "https://www.linkedin.com/search/results/content/?keywords=transformation%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22",
    }

    # for keyword, url in like_tasks.items():
    #     like_search_results(driver, url, keyword)
    
    print("--- LinkedIn Networking Bot Finished ---")


if __name__ == '__main__':
    main()