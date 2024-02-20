import re
import atexit
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from utils.utils import get_collection
from bson.json_util import dumps

from utils.scheduled_tasks import (
    fetch_dropin_swimming_data, 
    fetch_community_center_data
)

app = FastAPI()
scheduler = BackgroundScheduler()
scheduler.start()

scheduler.add_job(
    fetch_dropin_swimming_data,
    trigger=IntervalTrigger(seconds=60),
    id="scrape_swimming_toronto",
    replace_existing=True
)

scheduler.add_job(
    fetch_community_center_data,
    trigger=IntervalTrigger(seconds=10),
    id="scrape_community_centers",
    replace_existing=True
)


atexit.register(lambda: scheduler.shutdown())

@app.get("/")
def home():
    return "this is home"


@app.get("/clean-db/")
async def clean_database():
    collection = get_collection()
    deleted = collection.delete_many({})
    return {"details": f"Total records deleted: {deleted.deleted_count}"}


@app.get("/generate-data/")
async def populate_database():
    collection = get_collection()
    results = collection.find()
    return {"centers": dumps(list(results))}


@app.get("/swimming")
async def get_swimming_info():
    collection = get_collection()
    results = collection.find()
    return {"centers": dumps(list(results))}    

    
@app.get("/search/")
async def search_swimming_info(
    center: str = "",
    visit_date: str = None,
    day: str = "",
    type: str = ""
):
    collection = get_collection()
    center_pattern = re.compile(center, re.IGNORECASE)
    day_pattern = re.compile(day, re.IGNORECASE)
    type_pattern = re.compile(type, re.IGNORECASE)
    
    match_stage = {}
    if center_pattern:
        match_stage['center'] = {'$regex': center_pattern}  # case-insensitive match
    
    pipeline = []
    if match_stage:
        pipeline.append({'$match': match_stage})
    
    schedule_filter_conditions = []
    if day_pattern:
        schedule_filter_conditions.append({'$regexMatch': {'input': '$$scheduleItem.day', 'regex': day_pattern}})
        
    if visit_date:
        visit_date = {'$dateFromString': {'dateString': visit_date}}
        schedule_filter_conditions.append({'$lte': [{"$dateFromString": {"dateString": "$$scheduleItem.start_date"}}, visit_date]})
        schedule_filter_conditions.append({'$gte': [{"$dateFromString": {"dateString": "$$scheduleItem.end_date"}}, visit_date]})
    
    if type:
        schedule_filter_conditions.append({"$regexMatch": {"input": "$$scheduleItem.type", 'regex': type_pattern}})
    
    if schedule_filter_conditions:
        pipeline.append({
            '$project': {
                'center': 1,
                'schedule': {
                    '$filter': {
                        'input': '$schedule',
                        'as': 'scheduleItem',
                        'cond': {'$and': schedule_filter_conditions}
                    }
                }
            }
        })
    else:
        # If there are no conditions, include the entire schedule without filtering
        pipeline.append({
            '$project': {
                'center': 1,
                'schedule': 1
            }
        })
    results = collection.aggregate(pipeline)
    return {"centers": dumps(list(results))}