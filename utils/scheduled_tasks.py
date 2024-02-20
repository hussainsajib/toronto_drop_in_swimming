import requests
import json

from bs4 import BeautifulSoup
from datetime import datetime
from selenium.webdriver.common.by import By

from .utils import get_collection
from .selenium_utils import get_headless_chrome



BASE_URL = "https://www.toronto.ca/data/parks/prd/swimming/dropin/leisure/index.html"
COMMUNITY_CENTER_URL = "https://www.toronto.ca/data/parks/prd/facilities/recreationcentres/index.html"


def fetch_dropin_swimming_data() -> None:
    collection = get_collection()
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    programs = soup.find_all('div', class_='pfrListing')
    current_year = datetime.now().year

    for p in programs:
        center_name = p.find('h2').text.strip()
        existing_center = collection.find_one({"center": center_name})
        if not existing_center or existing_center["next_update_due"].date() <= datetime.today().date():
            output = {
                "center": center_name,
                "last_updated": datetime.today().date(),
                "next_update_due": datetime.today().date(),
                "schedule": []
            }
            
            # get table heads
            table_head_rows = p.find('thead').find_all('th', scope="col")
            days_of_week = [i.get_text().strip() for i in table_head_rows][1:]
            
            # get table body
            schedule_rows = p.select('tbody > tr')
            for row in schedule_rows:
                course_type = row.th.div.text if row.th.div else None
                date_range_text = row.th.get_text()[len(course_type):].strip() if course_type else None
                start_date_text, end_date_text = date_range_text.split(' to ')
                start_date = datetime.strptime(f"{start_date_text} {current_year}", '%b %d %Y')
                end_date = datetime.strptime(f"{end_date_text} {current_year}", '%b %d %Y')
                for i, td in enumerate(row.find_all('td', {'data-info': True})):
                    timeslot_text = td.get_text(separator=' ').strip()
                    if timeslot_text and timeslot_text != '&nbsp;':
                        schedule_item = {
                            "type": course_type,
                            "start_date": start_date.strftime('%d %B %Y'),
                            "end_date": end_date.strftime('%d %B %Y'),
                            "day": days_of_week[i],
                            "timeslot": timeslot_text
                        }
                        output["schedule"].append(schedule_item)
                    output['next_update_due'] = max(output['next_update_due'], end_date)
                        
            
            collection.insert_one(output)
        else:
            print(f"{center_name} already exists in the database")


def fetch_community_center_data() -> None:
    collection = get_collection("centers")
    driver = get_headless_chrome()
    driver.get(COMMUNITY_CENTER_URL)
    rows = driver.find_elements(By.XPATH, "//tbody/tr")
    all_centers = []
    for row in rows:
        center_name = row.find_element(By.XPATH, f".//th/a").text
        does_exists = collection.find_one({"center_name": center_name})
        if not does_exists:
            center_info = {
                "center_name": center_name,
                "address": row.find_element(By.XPATH, ".//td[@data-info='Address']").text,
                "district": row.find_element(By.XPATH, ".//td[@data-info='District']").text,
                "phone": row.find_element(By.XPATH, ".//td[@data-info='Phone']").text,
                "url": row.find_element(By.XPATH, ".//th[@data-info='Name']/a").get_attribute('href')
            }
            all_centers.append(center_info)
        else:
            print(f"{center_name} already exists in the database")
    if all_centers:
        collection.insert_many(all_centers)
        
    