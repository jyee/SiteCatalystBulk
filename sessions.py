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
import json
import csv

# User credentials
import config

# Get the json export. Stubbing in a static list for now.
with open(sys.argv[1]) as dataFile:
    data = json.load(dataFile)

# Create a dictionary of speakers
speakers = {}
for speaker in data["Schedule"]["speakers"]:
    if not speaker["twitter"]:
        speakers[speaker["serial"]] = speaker["name"]
    else:
        speakers[speaker["serial"]] = "@" + speaker["twitter"]

#Create a dictionary of sessions
sessions = {}
for session in data["Schedule"]["events"]:
    if "website_url" in session:
        sessions[session["serial"]] = {"title":session["name"], "type":session["event_type"], "time":session["time_start"], "url":session["website_url"], "speaker":"", "shortURL":""}

        for speakerID in session["speakers"]:
            if speakerID in speakers:
                if not sessions[session["serial"]]["speaker"]:
                    sessions[session["serial"]]["speaker"] = speakers[speakerID]
                else:
                    sessions[session["serial"]]["speaker"] = sessions[session["serial"]]["speaker"] + " & " + speakers[speakerID]

# Create a new instance of the Firefox driver.
driver = webdriver.Firefox()

# Get the ORM Sitecatalyst code page.
driver.get("http://www.oreilly.com/campaign/")

# Login
try:
    driver.find_element_by_link_text("login").click()
    # Login form often loads after page, so wait for the form.
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "capture_signIn_traditionalSignIn_emailAddress")))
    driver.find_element_by_name("traditionalSignIn_emailAddress").send_keys(config.userEmail)
    driver.find_element_by_name("traditionalSignIn_password").send_keys(config.userPassword)
    driver.find_element_by_name("traditionalSignIn_signInButton").click()
except:
    print sys.exc_info()

for session in sessions:
    try:
        WebDriverWait(driver, 10).until(EC.title_is("SiteCatalyst Campaign Code Generator"))
        # Fill in the form and submit.
        Select(driver.find_element_by_name("type")).select_by_visible_text("Twitter")
        Select(driver.find_element_by_name("practicearea")).select_by_visible_text("Web Operations / Performance")
        Select(driver.find_element_by_name("division")).select_by_visible_text("Conference")
        Select(driver.find_element_by_name("product")).select_by_visible_text("Conference Registration")
        Select(driver.find_element_by_name("entry_content")).select_by_visible_text("Article")
        Select(driver.find_element_by_name("camp")).select_by_visible_text(config.camp)
        driver.find_element_by_name("element").clear()
        driver.find_element_by_name("element").send_keys("session promo")
        driver.find_element_by_name("url").clear()
        driver.find_element_by_name("url").send_keys(sessions[session]["url"])
        driver.find_element_by_name("x-a").click()
        # Generate the short URL - Note It might be better to save the full URLs and run seperate bitly bulk generation.
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Generate Shortened URL")))
        driver.find_element_by_link_text("Generate Shortened URL").click()
        # Couldn't get a web driver wait to work because the ajax return has no identifiers... this could be improved.
        time.sleep(5)
        # Get the Short URL
        short = driver.find_elements_by_xpath("//p[contains(text(), 'http://oreil.ly/')]")
        shortURL = re.search("http://oreil.ly/\S+", short[0].text).group()
        if shortURL:
            sessions[session]["shortURL"] = shortURL
        # Generate new code/Reset form
        driver.find_element_by_link_text("Create New Code").click()
    except:
        print sys.exc_info()

#Stop the Selenium driver.
driver.quit()

# Write out to CSV
csvFile = csv.writer(open(sys.argv[1] + ".csv", "wb+"))
for sessionID in sessions:
    session = sessions[sessionID]
    csvFile.writerow([session["title"].encode("ascii", "xmlcharrefreplace"), session["type"], session["time"], session["speaker"].encode("ascii", "xmlcharrefreplace"), session["url"], session["shortURL"]])
