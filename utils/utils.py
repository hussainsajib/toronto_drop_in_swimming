"""
Script to scrape Toronto.ca website to find leisure swimming schedules
"""
import os
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime


BASE_URL = "https://www.toronto.ca/data/parks/prd/swimming/dropin/leisure/index.html"
mongodb_hostname = os.getenv('MONGODB_HOSTNAME', 'mongodb')
DB_URL = f"mongodb://{mongodb_hostname}:27017/"

def get_collection():
    client = MongoClient(DB_URL)
    db = client['community_centers']
    return db["leisure_swimming"]


def generate_data():
    collection = get_collection()
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, "html.parser")
    programs = soup.find_all('div', class_='pfrListing')
    current_year = datetime.now().year
    counter = 0
    for p in programs:
        center_name = p.find('h2').text.strip()
        is_exists = collection.find_one({"center": center_name})
        if not is_exists:
            output = {
                "center": center_name,
                "last_updated": datetime.today(),
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
            
            collection.insert_one(output)
        else:
            print(f"{center_name} already exists in the database")
        