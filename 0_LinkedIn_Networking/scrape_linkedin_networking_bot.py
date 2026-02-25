# FILE: ./0_LinkedIn_Networking/scrape_linkedin_networking_bot.py

import os
import time
import json
import datetime
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

def connect_to_chrome():
    """Establishes a connection to the running Chrome debugger instance."""
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        print("Successfully connected to the browser.")
        return driver
    except Exception as e:
        print(f"FATAL: Could not connect to Chrome. Error: {e}")
        return None

def wish_birthdays(driver):
    """Navigates to the birthday page and sends wishes."""
    print("--- Phase 0: Wishing Birthdays ---")
    driver.get(BIRTHDAY_URL)
    print("Navigated to birthdays page. Waiting for 5 seconds...")
    time.sleep(5)
    
    log_data = load_log()
    processed_today_set = {(entry['fullName'], entry['date']) for entry in log_data}
    print(f"Loaded {len(log_data)} log entries.")
    
    actions = ActionChains(driver)
    # driver.find_element(By.TAG_NAME, 'body').click()
    time.sleep(1)

    wished_count = 0
    max_tabs_without_finding_new_person = 150 
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_person:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(0.2)

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

                if wished_count >= 20:
                    print("Reached the processing limit of 20 people for this run. Stopping.")
                    break

                print(f"Found unprocessed birthday for: {name}")
                tabs_count = 0 # Reset counter

                birthday_type = "birthday"
                first_name = name.split()[0]
                new_message = f"Wishing you a very Happy Birthday, {first_name}! I hope you’re taking some well-deserved time to celebrate. Here’s to a year of great projects and continued success!"
                
                if "belated" in aria_label.lower():
                    birthday_type = "belated birthday"
                    new_message = f"Happy belated birthday, {first_name}! Hope you had a fantastic day. I’m looking forward to seeing all the great things you and your team accomplish this year!"
                    print("Identified as a belated birthday.")

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter. Waiting for message dialog to appear...")
                time.sleep(5)

                try:
                    print("Assuming focus is now on the message box.")
                    actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).send_keys(Keys.DELETE).perform()
                    print("Cleared default message.")
                    time.sleep(1)
                    
                    actions.send_keys(new_message).perform()
                    print(f"Typed new message: '{new_message}'")
                    time.sleep(5)

                    print("Following hardcoded tabbing strategy...")
                    send_button_found = False
                    
                    for i in range(5):
                        actions.send_keys(Keys.TAB).perform()
                        time.sleep(0.2)
                        print(f"Tab {i+1}/5")
                    
                    print("Now focused on the presumed 'Send' button. Waiting 5 seconds...")
                    time.sleep(5)
                    
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
                    time.sleep(10)

                    print("Message sent. Reloading birthdays page to refresh the list...")
                    driver.get(BIRTHDAY_URL)
                    print("Page reloaded. Waiting 5 seconds to load...")
                    time.sleep(5)

                except Exception as e:
                    print(f"Error: An error occurred while handling the message dialog for {name}: {e}")
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(2)

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
    print("Navigated to job changes page. Waiting for 5 seconds...")
    time.sleep(5)

    actions = ActionChains(driver)
    # driver.find_element(By.TAG_NAME, 'body').click()
    time.sleep(1)

    liked_count = 0
    max_tabs_without_finding_new_card = 150
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_card:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(0.2)

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
                if liked_count >= 20:
                    print("Reached the processing limit of 20 likes for this run. Stopping.")
                    break

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter to like the post.")
                liked_count += 1
                time.sleep(2)  # Wait a bit before continuing

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
    print("Navigated to work anniversaries page. Waiting for 5 seconds...")
    time.sleep(5)

    actions = ActionChains(driver)
    # driver.find_element(By.TAG_NAME, 'body').click()
    # time.sleep(1)

    liked_count = 0
    max_tabs_without_finding_new_card = 150
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_card:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(0.2)

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
                if liked_count >= 20:
                    print("Reached the processing limit of 20 likes for this run. Stopping.")
                    break

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter to like the post.")
                liked_count += 1
                time.sleep(2)  # Wait a bit before continuing

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
    print("Navigated to education updates page. Waiting for 5 seconds...")
    time.sleep(5)

    actions = ActionChains(driver)
    # driver.find_element(By.TAG_NAME, 'body').click() # Assuming similar behavior to anniversaries page
    # time.sleep(1)

    liked_count = 0
    max_tabs_without_finding_new_card = 150
    tabs_count = 0

    while tabs_count < max_tabs_without_finding_new_card:
        actions.send_keys(Keys.TAB).perform()
        tabs_count += 1
        time.sleep(0.2)

        try:
            active_element = driver.switch_to.active_element
            
            try:
                svg_element = active_element.find_element(By.CSS_SELECTOR, "svg[aria-label='Reaction button state: no reaction']")
                
                print("Found an un-liked education update.")
                tabs_count = 0  # Reset counter

                if liked_count >= 20:
                    print("Reached the processing limit of 20 likes for this run. Stopping.")
                    break

                active_element.send_keys(Keys.ENTER)
                print("Pressed Enter to like the post.")
                liked_count += 1
                time.sleep(2)  # Wait a bit before continuing

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

def share_linkedin_news(driver):
    print("--- Phase 4: Sharing LinkedIn News ---")
    driver.get("https://www.linkedin.com/feed/")
    print("Navigated to LinkedIn feed. Waiting for 5 seconds...")
    time.sleep(5)

    actions = ActionChains(driver)

    # 1. Tab until we are inside the LinkedIn News module
    news_module = None
    print("Tabbing to find LinkedIn News module...")
    for i in range(200): # Safety limit
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.2)
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
        time.sleep(0.2)
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
    print(f"--- Phase 5: Liking from Search Results for '{keyword}' ---")
    
    # 1. Navigate to URL
    driver.get(search_url)
    print(f"Navigated to search results page for '{keyword}'. Waiting for page to load...")
    time.sleep(7) # Give it a bit more time for posts to load

    actions = ActionChains(driver)
    driver.find_element(By.TAG_NAME, 'body').click()
    time.sleep(1)
    processed_urns = load_liked_posts_log()
    liked_this_session = 0
    
    # Main tabbing loop
    for i in range(500): # Generous tabbing limit
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.2)
        
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
                if liked_this_session >= 20: # Safety break for the session
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

    wish_birthdays(driver)
    like_job_changes(driver)
    like_work_anniversaries(driver)
    like_education_updates(driver)
    # share_linkedin_news(driver)

    search_url_ai = "https://www.linkedin.com/search/results/content/?keywords=AI%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"
    search_url_tech = "https://www.linkedin.com/search/results/content/?keywords=tech%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"
    search_url_pmp = "https://www.linkedin.com/search/results/content/?keywords=pmp%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"
    search_url_project_manager = "https://www.linkedin.com/search/results/content/?keywords=project%25Bmanager&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"
    search_url_product_management = "https://www.linkedin.com/search/results/content/?keywords=product%25Bmanagement&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"
    search_url_agile = "https://www.linkedin.com/search/results/content/?keywords=agile%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"
    search_url_safe = "https://www.linkedin.com/search/results/content/?keywords=safe%25&origin=FACETED_SEARCH&sid=0Q4&sortBy=%22date_posted%22"

    # For debugging, let's just run the new one.
    like_search_results(driver, search_url_ai, "ai")
    like_search_results(driver, search_url_tech, "tech")
    like_search_results(driver, search_url_pmp, "pmp")
    like_search_results(driver, search_url_project_manager, "pm")
    like_search_results(driver, search_url_product_management, "pmm")
    like_search_results(driver, search_url_agile, "agile")
    like_search_results(driver, search_url_safe, "safe")
    
    print("--- LinkedIn Networking Bot Finished ---")


if __name__ == '__main__':
    main()
