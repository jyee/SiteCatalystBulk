import sys
# User input cache
import os.path
# Get user info
import getpass
# Get session data
import urllib2
import json
# fix session URLs
import re
# Selenium stuff.
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
# Output final data
import csv

def main():
  # Read previous values
  previous = get_inputs()

  # User credentials
  email = user_input("ORM email", "email", previous)
  password = getpass.getpass("ORM password: ")
  
  # Conference info.
  conference_url = clean_url(user_input("Conference URL", "conference_url", previous))
  json_url = conference_url + "public/content/report/schedule"

  # Site Catalyst info.
  pa = user_input("ORM pa", "pa", previous)
  campaign = user_input("ORM campaign", "campaign", previous)
  cm = user_input("ORM cm", "cm", previous)

  # Save values
  set_inputs(email, conference_url, pa, campaign, cm)
  
  # Get the json
  try:
    print "Downloading session data ..."
    http_response = urllib2.urlopen(json_url)
    print "Parsing session data ..."
    event_data = json.load(http_response)
  except:
    sys.exit("Could not retreive session data!")

  # Setup speaker dictionary
  try:
    print "Parsing speaker data ..."
    speakers = speaker_dict(event_data["Schedule"]["speakers"])
  except:
    sys.exit("Could not load speakers")

  # Setup session list
  try:
    print "Compiling session data ..."
    sessions = sessions_addinfo(event_data["Schedule"]["events"], speakers, conference_url)
  except:
    sys.exit("Could not add data to sessions")

  # Generate session short tracked URLS
  try:
    print "Generating tracked session URLs. Do NOT close Firefox! ..."
    sessions = sessions_shorturls(sessions, email, password, pa, campaign, cm)
  except:
    sys.exit("Could not get short URLS")

  #Output to CSV
  try:
    print "Writing data to CSV ..."
    output_sessions(sessions)
  except:
    sys.exit("Could not write data to file")


# Get saved user input values
def get_inputs():
  if os.path.isfile('.orm_sessions'):
    with open('.orm_sessions', 'rb') as datafile:
      return json.load(datafile)
  else:
    return {}

# Save user input values
def set_inputs(email, conference_url, pa, campaign, cm):
  data = {}
  if email:
    data["email"] = email
  if conference_url:
    data["conference_url"] = conference_url
  if pa:
    data["pa"] = pa
  if campaign:
    data["campaign"] = campaign
  if cm:
    data["cm"] = cm

  with open('.orm_sessions', 'wb') as datafile:
    json.dump(data, datafile)

# User input with default value options
def user_input(question, key, previous):
  if previous.has_key(key) and previous[key]:
    return raw_input(question + " [" + previous[key] +"]: ") or previous[key]
  else:
    return raw_input(question + ": ")

# Ensure urls have protocol and trailing slash
def clean_url(url):
  if not url.startswith("http"):
    url = "http://" + url
  if not url.endswith("/"):
    url = url + "/"
  return url

# Format twitter handle or use name if no handle
def speaker_twitter(speaker):
  if type(speaker) is dict:
    if speaker.has_key("twitter") and speaker["twitter"]:
      return "@" + speaker["twitter"]
    elif speaker.has_key("name") and speaker["name"]:
      return speaker["name"].encode("ascii", "xmlcharrefreplace")
    else:
      return ""
  return ""

# Setup a dictionary for speakers
def speaker_dict(speakers):
  speaker_dict = {}
  for speaker in speakers:
    if speaker.has_key("serial"):
      speaker_dict[speaker["serial"]] = speaker_twitter(speaker)
  return speaker_dict

# Properly format the session URL
def session_url(session, conference_url):
  if "website_url" in session:
    return re.sub("http://conferences.oreilly.com/event/\d+", conference_url, session["website_url"])

# Get the twitter speaker list for a session.
def session_speakers(session, speakers):
  session_names = []
  if session.has_key("speakers"):
    for speaker_id in session["speakers"]:
      if speakers.has_key(speaker_id):
        session_names.append(speakers[speaker_id])
  return " & ".join(session_names)

# Add correct url and speaker twitter to sessions
def sessions_addinfo(sessions, speakers, conference_url):
  for i in xrange(len(sessions)):
    # Correct any special chars in the title
    sessions[i]["name"] = sessions[i]["name"].encode("ascii", "xmlcharrefreplace")
    # Add missing info.
    sessions[i]["url"] = session_url(sessions[i], conference_url)
    sessions[i]["twitter"] = session_speakers(sessions[i], speakers)
  return sessions

# Get short urls
def sessions_shorturls(sessions, email, password, pa, campaign, cm):
  site_catalyst = "http://www.oreilly.com/campaign/"

  # Create a new instance of the Firefox driver.
  driver = webdriver.Firefox()
  # Get the ORM Sitecatalyst code page.
  driver.get(site_catalyst)

  # Login
  try:
    driver.find_element_by_link_text("login").click()
    # Login form often loads after page, so wait for the form.
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "capture_signIn_traditionalSignIn_signInButton")))
    driver.find_element_by_name("traditionalSignIn_emailAddress").send_keys(email)
    driver.find_element_by_name("traditionalSignIn_password").send_keys(password)
    driver.find_element_by_name("traditionalSignIn_signInButton").click()
  except:
    sys.exit("Could not log in to code generator")

  session_count = len(sessions)
  for i in xrange(session_count):
    if sessions[i].has_key("url") and sessions[i]["url"]:
      #Report progress
      if not i % 10:
        print str(i) + " of " + str(session_count) + " sessions generated ..."

      try:
        # Wait for the page to load.
        WebDriverWait(driver, 10).until(EC.title_is("SiteCatalyst Campaign Code Generator"))
  
        # Fill in the form and submit.
        Select(driver.find_element_by_name("type")).select_by_visible_text("Twitter")
        Select(driver.find_element_by_name("practicearea")).select_by_visible_text(pa)
        Select(driver.find_element_by_name("division")).select_by_visible_text("Conference")
        Select(driver.find_element_by_name("product")).select_by_visible_text("Conference Registration")
        Select(driver.find_element_by_name("entry_content")).select_by_visible_text("Article")
        Select(driver.find_element_by_name("camp")).select_by_visible_text(campaign)
        driver.find_element_by_name("element").clear()
        driver.find_element_by_name("element").send_keys(cm + " sessions")
        driver.find_element_by_name("url").clear()
        driver.find_element_by_name("url").send_keys(sessions[i]["url"])
        driver.find_element_by_name("x-a").click()
  
        # Wait for the tracking URL result page to load.
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Generate Shortened URL')]")))
        driver.find_element_by_xpath("//a[contains(text(), 'Generate Shortened URL')]").click()
  
        # Get the Short URL
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'http://oreil.ly/')]")))
        short = driver.find_element_by_xpath("//a[contains(text(), 'http://oreil.ly/')]")
        shorturl = re.search("http://oreil.ly/\S+", short.text).group()
        if shorturl:
          sessions[i]["shorturl"] = shorturl
  
        # Generate new code/Reset form
        driver.find_element_by_link_text("Create New Code").click()
  
      except:
        print "An error occured while getting the short url for '" + sessions[i]["name"] + "'"
 
  #Stop the Selenium driver.
  driver.quit()

  return sessions

# Write session info to CSV
def output_sessions(sessions):
  with open("sessions.csv", "wb") as csvfile:
    fieldnames = ["name", "event_type", "time_start", "twitter", "url", "shorturl"]
    writer = csv.DictWriter(csvfile, fieldnames, "", "ignore")
    writer.writeheader()
    for session in sessions:
      writer.writerow(session)


if __name__ == '__main__':
  main()

