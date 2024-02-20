"""
Script to scrape Toronto.ca website to find leisure swimming schedules
"""
import os

from pymongo import MongoClient



mongodb_hostname = os.getenv('MONGODB_HOSTNAME', 'mongodb')
DB_URL = f"mongodb://{mongodb_hostname}:27017/"

def get_collection(collection_name:str="leisure_swimming"):
    client = MongoClient(DB_URL)
    db = client['community_centers']
    return db[collection_name]
