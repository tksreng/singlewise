import datetime
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import shutil

logging.basicConfig(filename='download_logs.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_user_date(prompt):
    while True:
        user_date_str = input(prompt)
        try:
            user_date = datetime.datetime.strptime(user_date_str, "%d-%m-%Y")
            return user_date
        except ValueError:
            print("Invalid date format. Please enter date in the format dd-mm-yyyy.")

start_date = get_user_date("Enter start date (dd-mm-yyyy): ")
end_date = get_user_date("Enter end date (dd-mm-yyyy): ")

chrome_options = Options()
download_directory = r"h:\cdata\downloads"  
prefs = {"download.default_directory": download_directory}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--headless")  # Run Chrome in headless mode

chrome_driver_path = ChromeDriverManager().install()

service = Service(chrome_driver_path)

driver = webdriver.Chrome(service=service, options=chrome_options)

driver.get("http://tnstckum.in/tnstckum/CFILE.aspx")
driver.maximize_window()

prefixes = ["SRFT",  "SDCN",  "STVK", "SLAL", "SMCR", 
            "STMF",  "SCNT",  "SMNP",  "STKI", 
            "SPBR",  "SALR",  "SJKM",  "SUPM",  "STRR"]

base_url = "http://tnstckum.in/tnstckum/CFILE_Download.aspx"

def download_file(url, filename, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(save_path, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Failed to download {filename}")
            return False
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

def check_files_downloaded(directory):
    downloaded_files = os.listdir(directory)
    if downloaded_files:
        print("Downloaded files:")
        for file in downloaded_files:
            print(file)
    else:
        print("No files downloaded.")

current_date = start_date
while current_date <= end_date:
    current_month_str = current_date.strftime("%m")
    current_day_str = current_date.strftime("%d")
    
    for prefix in prefixes:
        filename = f"{prefix}{current_day_str}{current_month_str}.dbf"
        url = f"{base_url}?filename={filename}"
        
        input_element = driver.find_element(By.ID, "TextBox1")
        input_element.clear()
        input_element.send_keys(filename)

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "ImageButton1"))
        )
        search_button.click()

        try:
            download_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[id^='GridView2_lnkDownload']"))
            )

            if not download_links:
                error_message = f"No download link found for prefix: {prefix}"
                print(error_message)
                logging.error(error_message)
                continue

            for download_link in download_links:
                download_link.click()
                time.sleep(10)

                # Handle insecure download warning dialog
                try:
                    alert = driver.switch_to.alert
                    alert.accept()  # Click the 'Keep' button
                except:
                    pass  # No alert found, or unable to handle it

            source_file_path = os.path.join(download_directory, filename)
            if os.path.exists(source_file_path):
                if prefix.startswith("S"):
                    target_directory = "h:/sdata"                
                else:
                    error_message = f"Unknown prefix: {prefix}"
                    print(error_message)
                    logging.error(error_message)
                    continue

                target_file_path = os.path.join(target_directory, filename)
                shutil.move(source_file_path, target_file_path)
                print(f"{filename} downloaded successfully.")

        except Exception as e:
            error_message = f"Error processing prefix {prefix}: {e}"
            print(error_message)
            logging.error(error_message)
            if "file not in server" in str(e).lower():
                logging.error(f"The file for prefix {prefix} was not found on the server.")
   
    current_date += datetime.timedelta(days=1)

driver.quit()

check_files_downloaded("h:/sdata")
