from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from datetime import datetime, timedelta, timezone
from calendly_fetcher.calendly_fetcher import get_calendly_availability, availability_to_list_of_strings, convert_basic_date_to_datetime
import time
import os
import sys
import pytz

# For future debugging/reference, see https://chatgpt.com/c/6735efaf-4d14-8012-a7d7-f05c9912e5fc for conversation that helped me write this code.

USER_NAME = 'Malek Ibrahim'
CALENDLY_API_KEY = os.getenv('CALENDLY_API_KEY')
MY_TIMEZONE = 'America/New_York'

# get the when2meet url from the sys arg position after the script name (i.e., python controller.py <when2meet_url>)
if len(sys.argv) < 2:
    raise Exception("Please provide the When2Meet URL as a command-line argument.")

WHEN2MEET_URL = sys.argv[1]

# function for getting the date range of the When2Meet grid
def get_when2meet_date_range(driver):
    # Wait for the grid to load
    time.sleep(5)
    
    # Find date headers
    date_elements = driver.find_elements(By.XPATH, '//div[@id="GroupGrid"]/div[3]/div')
    
    dates = []
    for date_element in date_elements:
        date_text = date_element.text.strip()
        if date_text:
            # Extract date, e.g., "Nov 17\nSun"
            date_lines = date_text.split('\n')
            date_str = date_lines[0]
            try:
                # convert time into proper timezone
                date_obj = datetime.strptime(date_str + ' ' + str(datetime.now().year), '%b %d %Y')
                date_obj = pytz.timezone('America/New_York').localize(date_obj)
                dates.append(date_obj)
            except ValueError:
                continue
    
    if dates:
        start_date = min(dates)
        end_date = max(dates) + timedelta(days=1)  # Assuming end_date is inclusive
    else:
        raise Exception("Could not extract dates from When2Meet")
    
    return start_date, end_date

def parse_availability_data(availability_text):
    availability_list = []
    lines = availability_text.strip().split('\n')
    for line in lines:
        parts = line.replace('Available: ', '').split(' - ')
        start_time = datetime.fromisoformat(parts[0])
        end_time = datetime.fromisoformat(parts[1])
        availability_list.append((start_time, end_time))
    return availability_list

def open_when2meet(url, user_name):
    driver = webdriver.Firefox()

    driver.get(url)

    # Wait for the name input to be present
    time.sleep(5)

    # Enter the user name
    name_input = driver.find_element(By.ID, 'name')
    name_input.send_keys(user_name)

    # Click the Sign In button
    sign_in_button = driver.find_element(By.XPATH, '//*[@id="SignIn"]/div/div/input')
    sign_in_button.click()

    # Wait for the availability grid to load
    time.sleep(5)

    return driver

def map_availability_to_slots(availability_list):
    slot_ids = []

    for start_time, end_time in availability_list:
        current_time = start_time
        while current_time < end_time:
            # Ensure current_time is timezone-aware
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            else:
                current_time = current_time.astimezone(timezone.utc)

            # Convert current_time to Unix timestamp in seconds
            timestamp = int(current_time.timestamp())

            slot_id = f'YouTime{timestamp}'
            slot_ids.append(slot_id)

            current_time += timedelta(minutes=15)  # Move to the next 15-minute slot

    return slot_ids

def mark_availability(driver, slot_ids):
    for slot_id in slot_ids:
        try:
            slot_element = driver.find_element(By.ID, slot_id)
            slot_element.click()
            time.sleep(0.01)  # Small delay to ensure the click registers
        except Exception as e:
            print(f"Could not click slot {slot_id}: {e}")

def parse_availability_data(availability_text_list):
    availability_list = []
    for line in availability_text_list:
        parts = line.replace('Available: ', '').split(' - ')
        start_time = datetime.fromisoformat(parts[0])
        end_time = datetime.fromisoformat(parts[1])
        availability_list.append((start_time, end_time))
    return availability_list

def main():
    # Open When2Meet and sign in
    driver = open_when2meet(WHEN2MEET_URL, USER_NAME)

    # get the start and end date of the When2Meet grid
    start_date, end_date = get_when2meet_date_range(driver)

    # Adjust start date to be at least current time + 1 hour
    current_time_plus_one_hour = datetime.now().replace(tzinfo=pytz.timezone(MY_TIMEZONE)) + timedelta(hours=1)
    adjusted_start_date = max(start_date, current_time_plus_one_hour).replace(tzinfo=pytz.timezone(MY_TIMEZONE))

    if end_date <= adjusted_start_date:
        driver.quit()
        raise Exception("End date is not ahead of start date")
    
    # if the end date is more than 7 days from the start date, we will need to do n availabilities and concatenate them, where n is the number of weeks between the start and end date
    starts = []
    ends = []
    if end_date > adjusted_start_date + timedelta(days=7):
        # calculate the number of weeks between the start and end date
        weeks_between_dates = (end_date - adjusted_start_date).days // 7
        # create a list of availabilities
        availabilities = []
        for i in range(weeks_between_dates):
            # get the start and end date for the current week
            current_start_date = adjusted_start_date + timedelta(weeks=i)
            current_end_date = current_start_date + timedelta(weeks=1)
            starts.append(current_start_date)
            ends.append(current_end_date)
    else: # if the end date is less than 7 days from the start date, we only need to do one availability
        starts.append(adjusted_start_date)
        ends.append(end_date)
    
    # Fetch availability from Calendly for all the start and end dates
    availability_text_list = []
    for start, end in zip(starts, ends):
        availability = get_calendly_availability(CALENDLY_API_KEY, start, end)
        availability_text_list.extend(availability_to_list_of_strings(availability, MY_TIMEZONE))

    # Parse availability data
    availability_list = parse_availability_data(availability_text_list)

    # Map your availability to When2Meet slot IDs
    slot_ids = map_availability_to_slots(availability_list)

    # Mark your availability on When2Meet
    mark_availability(driver, slot_ids)

    print("Availability has been marked on When2Meet.")

    driver.quit()

if __name__ == "__main__":
    main()
