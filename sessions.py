# Selenium stuff.
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC

# System, time and regex stuff.
import sys
import time
import re
#import getopt
#import json

# User credentials
import config

# Get the json export. Stubbing in a static list for now.
sessions = ["http://velocityconf.com/devops-web-performance-eu-2015/public/schedule/detail/43661", "http://velocityconf.com/devops-web-performance-eu-2015/public/schedule/detail/43716", "http://velocityconf.com/devops-web-performance-eu-2015/public/schedule/detail/43757", "http://velocityconf.com/devops-web-performance-eu-2015/public/schedule/detail/43768", "http://velocityconf.com/devops-web-performance-eu-2015/public/schedule/detail/43888", "http://velocityconf.com/devops-web-performance-eu-2015/public/schedule/detail/43962"]

shortURLs = []


# Create a new instance of the Firefox driver.
driver = webdriver.Firefox()

# Get the ORM Sitecatalyst code page.
driver.get("http://www.oreilly.com/campaign/")

# Login
try:
    driver.find_element_by_link_text("login").click()
    # Login form often loads after page, so wait for the form.
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "capture_signIn_traditionalSignIn_emailAddress")))
    driver.find_element_by_name("traditionalSignIn_emailAddress").send_keys(userEmail)
    driver.find_element_by_name("traditionalSignIn_password").send_keys(userPassword)
    driver.find_element_by_name("traditionalSignIn_signInButton").click()
except:
    e = sys.exc_info()[0]
    print e


for session in sessions:
    try:
        WebDriverWait(driver, 10).until(EC.title_is("SiteCatalyst Campaign Code Generator"))
        # Fill in the form and submit.
        Select(driver.find_element_by_name("type")).select_by_visible_text("Twitter")
        Select(driver.find_element_by_name("practicearea")).select_by_visible_text("Web Operations / Performance")
        Select(driver.find_element_by_name("division")).select_by_visible_text("Conference")
        Select(driver.find_element_by_name("product")).select_by_visible_text("Conference Registration")
        Select(driver.find_element_by_name("entry_content")).select_by_visible_text("Article")
        Select(driver.find_element_by_name("camp")).select_by_visible_text(camp)
        driver.find_element_by_name("element").clear()
        driver.find_element_by_name("element").send_keys("session promo")
        driver.find_element_by_name("url").clear()
        driver.find_element_by_name("url").send_keys(session)
        driver.find_element_by_name("x-a").click()
        # Generate the short URL - Note It might be better to save the full URLs and run seperate bitly bulk generation.
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Generate Shortened URL")))
        driver.find_element_by_link_text("Generate Shortened URL").click()
        # Couldn't get a web driver wait to work because the ajax return has no identifiers... this could be improved.
        time.sleep(5)
        # Get the Short URL
        shortURL = driver.find_elements_by_xpath("//p[contains(text(), 'http://oreil.ly/')]")
        shortURLs.append(str(re.search("http://oreil.ly/\S+", shortURL[0].text).group()))
        # Generate new code/Reset form
        driver.find_element_by_link_text("Create New Code").click()
    except:
        e = sys.exc_info()[0]
        print e

#Stop the Selenium driver.
driver.quit()

# Do stuff with the short urls.
print shortURLs
