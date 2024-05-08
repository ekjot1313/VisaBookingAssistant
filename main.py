import configparser
import os
import subprocess
import time
import traceback
from datetime import datetime

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Create a configparser object
config = configparser.ConfigParser()

# Read the properties file
config.read('project.properties')

sign_in_url = config.get('URL', 'sign_in_url')
url = config.get('URL', 'booking_url')

username = config.get('Login', 'username')
password = config.get('Login', 'password')
already_booked_date_str = config.get('Booking', 'already_booked_date')
you_want_to_confirm_booking = config.get('Booking', 'book_automatically') == 'True'
fav_consulate = config.get('Booking', 'consulate')

schedule_start_time = datetime.strptime('00:00:00', '%H:%M:%S').time()
schedule_end_time = datetime.strptime('23:59:59', '%H:%M:%S').time()
golden_period_start_time = datetime.strptime('04:18:00', '%H:%M:%S').time()
golden_period_end_time = datetime.strptime('14:39:00', '%H:%M:%S').time()
# golden_period_start_time = datetime.strptime('00:00:00', '%H:%M:%S').time()
# golden_period_end_time = datetime.strptime('23:59:59', '%H:%M:%S').time()


golden_period_refresh_secs_upper_limit = 10
maximum_refresh_secs_upper_limit = 600
refresh_secs_upper_limit = golden_period_refresh_secs_upper_limit

inc_by = 1
sec_to_wait = 1
specific_date = datetime.strptime(already_booked_date_str, '%d-%m-%Y').date()
early_date_found = False
calendar_month_is_before_last_booking = True
date_field_was_not_found_times = 0


def capture_screenshot(filename):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshot_dir = "media/screenshots"
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)
    filepath = os.path.join(screenshot_dir, f"{filename}_{timestamp}.png")
    driver.save_screenshot(filepath)
    print(f"Screenshot saved: {filepath}")


def click_ok_button():
    try:
        ok_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='OK']"))
        )
        ok_button.click()
    except Exception as e:
        print("OK button not found or clickable:", e)


def click_continue():
    try:
        # Find the Continue button by its attributes
        continue_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Continue']"))
        )

        # Click on the Continue button
        continue_button.click()
    except Exception as e:
        print("An error occurred while clicking the Continue button:", e)


def sign_in(email, pwd):
    try:
        email_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "user_email"))
        )
        email_input.send_keys(email)

        password_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "user_password"))
        )
        password_input.send_keys(pwd)
    except Exception as e:
        print("Sign-in fields not found or clickable:", e)


def get_date_picker():
    return WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'ui-datepicker-div')))


def get_available_dates(datepicker):
    first_group = datepicker.find_element(By.CLASS_NAME, "ui-datepicker-group-first")
    last_group = datepicker.find_element(By.CLASS_NAME, "ui-datepicker-group-last")

    return get_available_dates_from_group(first_group) + get_available_dates_from_group(last_group)


def is_appointment_time_field_available():
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_time")))
        return True
    except Exception:
        return False


def click_on_appointment_time_field():
    time_select = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_time")))
    time_select.click()


def click_reschedule_button():
    reschedule_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "appointments_submit")))
    reschedule_button.click()


def click_confirm_reschedule_button():
    confirm_modal = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "reveal")))
    confirm_button = confirm_modal.find_element(By.XPATH, "//a[@class='button alert']")
    if you_want_to_confirm_booking:
        confirm_button.click()
    else:
        cancel_button = confirm_modal.find_element(By.XPATH, "//a[@data-confirm-cancel]")
        cancel_button.click()


def try_to_book_first_selectable_date(date_elements, month, year):
    global specific_date, already_booked_date_str

    if len(date_elements) > 0:

        first_date_element = date_elements[0]
        date_text = first_date_element.text.strip()
        if date_text:
            date_obj = datetime.strptime(date_text, '%d').date()
            date_obj = date_obj.replace(year=year, month=month)
            if date_obj < specific_date:
                print('Found a date ', date_obj, 'Trying to book it automatically.')
                first_date_element.click()
                if is_appointment_time_field_available():
                    print('Found a time slot.')
                    click_on_appointment_time_field()
                    select_first_time_slot()
                    click_reschedule_button()
                    click_confirm_reschedule_button()
                    print('Completed booking try.')
                    notify_if_early_date_found(date_obj)
                    input('Press Enter to exit.')
                else:
                    print("Did not find a time slot.")


def select_first_time_slot():
    first_time_slot = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, "//select[@id='appointments_consulate_appointment_time']/option[2]")))
    first_time_slot.click()


def get_available_dates_from_group(group):
    group_month, group_year = extract_group_month_year(group)
    group_month_number = datetime.strptime(group_month, '%B').month
    group_year_number = int(group_year)

    print(f"Checking dates for {group_month} {group_year}")
    date_elements = group.find_elements(By.XPATH, ".//td[not(contains(@class, 'ui-datepicker-unselectable'))]/a")
    dates = []
    for element in date_elements:
        date_text = element.text.strip()
        if date_text:
            date_obj = datetime.strptime(date_text, '%d').date()
            date_obj = date_obj.replace(year=group_year_number, month=group_month_number)
            dates.append(date_obj)
            print(f"Date found: {date_obj} at ", now())
    print(dates)
    if len(dates) > 0:
        try_to_book_first_selectable_date(date_elements, group_month_number, group_year_number)
    inform_loop_to_stop_search_if_no_date_found_till_last_appointment(group_month_number, group_year_number)
    return dates


def now():
    return datetime.now().time()


def inform_loop_to_stop_search_if_no_date_found_till_last_appointment(group_month_number, group_year_number):
    compare_date = datetime(group_year_number, group_month_number, 1).date()
    global calendar_month_is_before_last_booking
    if specific_date < compare_date:
        print('Stopping current search because no date found before ', already_booked_date_str)
        calendar_month_is_before_last_booking = False


def extract_group_month_year(group):
    try:
        header_elements = group.find_elements(By.CLASS_NAME, "ui-datepicker-title")
        group_year = None
        group_month = None
        if header_elements is not None:
            # Iterate through the header elements to extract the year and month information
            for header_element in header_elements:
                if header_element is not None:
                    month_element = header_element.find_element(By.CLASS_NAME, "ui-datepicker-month")
                    year_element = header_element.find_element(By.CLASS_NAME, "ui-datepicker-year")
                    group_month = month_element.text.strip()
                    group_year_text = year_element.text.strip()
                    # print('Group month=', group_month)
                    group_year = int(group_year_text)
                    # print('Group month=', group_year)
                else:
                    capture_screenshot('specific_header_element_not_found')
                    print('extract_group_month_year(): The specific header_element is null.')
                    return None, None
            return group_month, group_year
        else:
            capture_screenshot('header_elements_not_found')
            print('extract_group_month_year(): The header_elements is null.')
            return None, None
    except Exception as e:
        capture_screenshot('Error_in_extract_group_month_year')
        print('Error in extract_group_month_year():', e)
        return None, None


def notify_if_early_date_found(date):
    global early_date_found
    if date < specific_date:
        print("Found an early date than the ", already_booked_date_str, ' >>>>>> ', date, 'at time: ', now())
        early_date_found = True

        subprocess.run(["python", "alertNotification.py", date.strftime('%d-%m-%Y')])


def click_on_date_field():
    try:
        # Wait for the Date of Appointment input field to be clickable
        date_of_appointment_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_date_input"))
        )

        # Click on the Date of Appointment field to trigger the date picker
        date_of_appointment_field.click()
    except Exception as ex:
        print("Error in click_on_date_field(): Cannot click on Date field. ", ex)


def change_to_next_month():
    next_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ui-datepicker-next"))
    )
    # Once the button is clickable, click on it
    next_button.click()


def check_checkbox():
    try:
        # Wait for the parent label element to be clickable
        checkbox_label = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//label[@for='policy_confirmed']"))
        )

        # Click on the label element
        checkbox_label.click()
    except Exception as e:
        print("An error occurred while checking the checkbox:", e)


def click_sign_in_button():
    try:
        # Find the Sign In button by its attributes
        sign_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @name='commit' and @value='Sign In']"))
        )

        # Click on the Sign In button
        sign_in_button.click()
    except Exception as e:
        print("An error occurred while clicking the Sign In button:", e)


def is_golden_period():
    current_time = now()
    return golden_period_start_time <= current_time < golden_period_end_time


def refresh_page_after_fibonnaci_seconds():
    global sec_to_wait, inc_by, refresh_secs_upper_limit

    if sec_to_wait >= refresh_secs_upper_limit:
        reset_wait_timer()
    if is_golden_period():
        refresh_secs_upper_limit = golden_period_refresh_secs_upper_limit
    else:
        refresh_secs_upper_limit = maximum_refresh_secs_upper_limit

    sec_to_wait += inc_by
    inc_by = sec_to_wait - inc_by

    print(f'Waiting for {sec_to_wait} seconds before refreshing.')
    countdown_timer(sec_to_wait)
    print('\nRefreshing at ', now())
    driver.refresh()

    if driver.current_url == sign_in_url:
        print('Signed out while refreshing. Trying to restart the session.')
        quit_and_restart_session()
        handle_sign_in()


def quit_and_restart_session():
    global driver
    print('Account signed out. Restarting the session.')
    driver.quit()
    driver = webdriver.Chrome()
    driver.get(url)


def countdown_timer(secs):
    for i in range(secs, 0, -1):
        print(f"\r{i} seconds left before refreshing...", end='', flush=True)  # \r clears the current line
        time.sleep(1)
    print()


def iterate_through_months_indefinitely():
    while not early_date_found:
        if not is_time_in_scheduled_range():
            print('Stopping search because time is out of scheduled range. Now is ', now())
            break
        refresh_page_after_fibonnaci_seconds()
        select_consulate(fav_consulate)
        iterate_through_months_once()


def iterate_through_months_once():
    if is_date_field_available():
        click_on_date_field()
        check_all_months_for_early_date_and_notify()


def is_date_field_available():
    global date_field_was_not_found_times
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_date_input"))
        )
        if date_field_was_not_found_times > 0:
            print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<New dates available at ', now(),
                  '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            reset_wait_timer()
        return True
    except Exception:
        print('Date field not available.')
        if date_field_was_not_found_times > 100:
            date_field_was_not_found_times = 0
        date_field_was_not_found_times += 1
        return False


def reset_wait_timer():
    global inc_by, sec_to_wait, date_field_was_not_found_times
    inc_by = 1
    sec_to_wait = 1
    date_field_was_not_found_times = 0


def is_ok_button_available():
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='OK']"))
        )
        return True
    except Exception:
        print("OK button not found or clickable")
        return False


def is_multiple_applicants_button_available():
    try:
        WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Continue']"))
        )
        return True
    except Exception:
        print("Continue button not found or clickable")
        return False


def is_date_picker_available():
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'ui-datepicker-div')))
        return True
    except Exception:
        print('Error in is_date_picker_available(): Date picker not available.')
        return False


def check_all_months_for_early_date_and_notify():
    global calendar_month_is_before_last_booking
    calendar_month_is_before_last_booking = True

    while calendar_month_is_before_last_booking:
        try:
            if is_date_picker_available():
                available_datepicker = get_date_picker()
                available_dates = get_available_dates(available_datepicker)
                if available_dates:
                    notify_if_early_date_found(min(available_dates))
                    if early_date_found:
                        break

                # time.sleep(1)
                change_to_next_month()
        except TimeoutException:
            print("Timeout occurred while waiting for the next month button to be clickable.")
            break

        except Exception as e:
            print("Error:", e)
            break


def is_sign_in_possible():
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "user_email"))
        )
        return True
    except Exception:
        print("Sign in is not possible.")
        return False


def handle_sign_in():
    print('Handling sign-in')
    if is_ok_button_available():
        click_ok_button()
    if is_sign_in_possible():
        sign_in(username, password)
        check_checkbox()
        click_sign_in_button()
    if is_multiple_applicants_button_available():
        click_continue()


def select_consulate(cons):
    try:
        consulate_select = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "appointments_consulate_appointment_facility_id"))
        )
        consulate_select.click()
        consulate_option = consulate_select.find_element(By.XPATH, f"//option[text()='{cons}']")
        time.sleep(1)
        print("Selecting consulate: ", cons)
        consulate_option.click()
        consulate_select.click()
    except Exception as e:
        print("Error in selecting favourite consulate:", e)


def start_booking():
    try:
        handle_sign_in()
        iterate_through_months_indefinitely()

        # input('Checking finished. Press Enter to exit.')
    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()


# Set up the Selenium WebDriver
driver = webdriver.Chrome()


def is_time_in_scheduled_range():
    current_time = now()
    return schedule_start_time <= current_time < schedule_end_time


while True:
    time.sleep(1)
    print(f"\rBooking will start in scheduled range ", schedule_start_time, '-', schedule_end_time, ' now is: ', now(),
          end='', flush=True)
    if is_time_in_scheduled_range():
        print('\nTime is in scheduled range.\nStarting the process.')
        driver.get(url)
        start_booking()
driver.quit()
