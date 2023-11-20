from asyncio.log import logger
from selenium import webdriver
from faker import Faker
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import json
import pandas as pd
import boto3

# FUNCTION TO ALLOW THE DOWNLOAD OF THE FILEs ON HEADLESS CHROME
def enable_download_headless(browser,download_dir):
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)

#   -------------------------------------------------------

prefs = {
    "profile.default_content_settings.popups": 0,
    "download.default_directory": r"/tmp",
    "directory_upgrade": True
    }

def get_driver():
    fake_user_agent = Faker()
    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)
    options.binary_location = '/opt/chrome-linux/chrome'
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--disable-web-security')
    options.add_argument('--user-agent=' + fake_user_agent.user_agent())
    options.add_argument('--headless')
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument("--single-process")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("window-size=1400,1200")
    options.add_argument("--disable-dev-tools")
    options.add_argument(f"--user-data-dir={'/tmp'}")
    options.add_argument(f"--data-path={'/tmp'}")
    options.add_argument(f"--disk-cache-dir={'/tmp'}")
    chrome = webdriver.Chrome("/opt/chromedriver", options=options)

    return chrome

#Our main Lambda function
def lambda_handler(event, context):
    # Open browser
    driver = get_driver()
    
    enable_download_headless(driver,'/tmp')

    username = os.environ.get('focus_username')
    password = os.environ.get('focus_password')
    
    current_direct = os.getcwd()
    print(f'Current Directory: {current_direct}')
    
    attendance = os.environ.get('attendance_url')
    
    enrollment = os.environ.get('enrollment_url')
    time.sleep(10)
    driver.get(enrollment)
    DCPS = WebDriverWait(driver, 70).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class = "idp"]')))
    
    DCPS.click()
    print('starting login')
    time.sleep(10)
    
    user = WebDriverWait(driver,25).until(
        EC.presence_of_element_located((By.ID, 'userNameInput')))
    
    user.send_keys(username)
    print('sent username')
    
    passw = WebDriverWait(driver,30).until(
        EC.presence_of_element_located((By.ID, 'passwordInput')))
    
    passw.send_keys(password)
    print('sent password')
    time.sleep(10)
    submit = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'submitButton')))
    
    submit.click()
    
    time.sleep(15)

    driver.get(enrollment)
    print('Signed in, getting enrollment')
    logger.info(f"URL McDuff: {attendance}")
    
    # Wait for the CSV export button to be clickable
    csv_button = WebDriverWait(driver, 130).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'lo_export_csv')))
    csv_button.click()
    print('Give it time to download')
    
    while not os.path.exists('/tmp/Portal.xls'):
        time.sleep(1)

    if os.path.isfile('/tmp/Portal.xls'):
        enrolled_df = pd.read_table('/tmp/Portal.xls',engine='python')
        print(f'There are {enrolled_df.shape[0]} students. Now moving onto Impact attendance')
    else:
        raise ValueError("%s isn't a file!" % '/tmp/Portal.xls')    
    
    #   Going to Impact Attendance url ------------------------------------------------------------------------------Impact
    
    driver.get(attendance)

    swift_box = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//div[@data-site-session="UserSchool"]/swift-box')))
    
    swift_box.click()
    
    print('school name box opened')
    
    impact_selection = WebDriverWait(driver, 40).until(
       EC.element_to_be_clickable((By.ID, 'swift-box-option-0')))
    
    impact_selection.click()
    
    print('selected Impact')
    
    csv_button = WebDriverWait(driver, 70).until(
    EC.element_to_be_clickable((By.CLASS_NAME, 'dataTable-csvButton')))
    csv_button.click()
    
    while not os.path.exists('/tmp/Report.csv'):
        time.sleep(1)

    if os.path.isfile('/tmp/Report.csv'):
        imp_df = pd.read_csv('/tmp/Report.csv')
        print(f'There are {imp_df.shape[0]} students with attendance at Impact. Now moving onto McDuff attendance')
    else:
        raise ValueError("%s isn't a file!" % '/tmp/Report.csv')
    
    
    #  Going to McDuff Attendance Next ----------------------------------------------------------------------------McDuff
    
    
    
    if os.path.exists("/tmp/Report.csv"):
        os.remove("/tmp/Report.csv")
    else:
        print("The file does not exist")
    
    swift_box = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//div[@data-site-session="UserSchool"]/swift-box')))
    
    swift_box.click()
    
    print('school name box opened')
    
    mcduff_select = WebDriverWait(driver, 40).until(
       EC.element_to_be_clickable((By.ID, 'swift-box-option-1')))
    
    mcduff_select.click() 
    print('Mcduff selected')
    
    driver.get(attendance)
    
    csv_button = WebDriverWait(driver, 70).until(
    EC.element_to_be_clickable((By.CLASS_NAME, 'dataTable-csvButton')))
    csv_button.click()
    
    while not os.path.exists('/tmp/Report.csv'):
        time.sleep(1)

    if os.path.isfile('/tmp/Report.csv'):
        mcd_df = pd.read_csv('/tmp/Report.csv')
        print(f'There are {mcd_df.shape[0]} students at McDuff. Now moving onto Voice attendance')
    else:
        raise ValueError("%s isn't a file!" % '/tmp/Report.csv') 
    
    
    #  Going into Voice attendance -------------------------------------------------------------------------------------VOICE
        
    
    if os.path.exists("/tmp/Report.csv"):
        os.remove("/tmp/Report.csv")
    else:
        print("The file does not exist")
    
    swift_box = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, '//div[@data-site-session="UserSchool"]/swift-box')))
    
    swift_box.click()
    
    print('school name box opened')

    voice_select = WebDriverWait(driver, 40).until(
       EC.element_to_be_clickable((By.ID, 'swift-box-option-2')))
    
    voice_select.click() 
    
    driver.get(attendance)     
    
    csv_button = WebDriverWait(driver, 70).until(
    EC.element_to_be_clickable((By.CLASS_NAME, 'dataTable-csvButton')))
    csv_button.click()
    
    while not os.path.exists('/tmp/Report.csv'):
        time.sleep(1)

    if os.path.isfile('/tmp/Report.csv'):
        voi_df = pd.read_csv('/tmp/Report.csv')
        print(f'There are {voi_df.shape[0]} students at Voice.')
    else:
        raise ValueError("%s isn't a file!" % '/tmp/Report.csv') 
    
    driver.quit()
    
    attendance_bucket = os.environ.get('attendance_bucket')
    enrollment_bucket = os.environ.get('enrollment_bucket')
    

    enrolled_df.to_csv('/tmp/enrollment.csv', index=False)
    
    mcd_df.to_csv('/tmp/Report.csv', index=False)
    imp_df.to_csv('/tmp/Report (1).csv', index=False)
    voi_df.to_csv('/tmp/Report (2).csv', index=False)
    
    s3 = boto3.resource('s3')
    
    enrollment_data = open(r'''/tmp/enrollment.csv''', 'rb')
    
    mcd_data = open(r'''/tmp/Report.csv''', 'rb')
    imp_data = open(r'''/tmp/Report (1).csv''', 'rb')
    voi_data = open(r'''/tmp/Report (2).csv''', 'rb')
    
    s3.Bucket(attendance_bucket).put_object(Key='Report.csv', Body=mcd_data)
    s3.Bucket(attendance_bucket).put_object(Key='Report (1).csv', Body=imp_data)
    s3.Bucket(attendance_bucket).put_object(Key='Report (2).csv', Body=voi_data)
    
    s3.Bucket(enrollment_bucket).put_object(Key='enrollment.csv', Body=enrollment_data)
    
    print(f'Attendance and Enrollment Files have been deposited to their respective buckets. \n Initiate other lambda functions')
    