from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from .config import settings

client = MongoClient(str(settings.MONGO_DSN), server_api=ServerApi('1'))


try:
    db = client["image_processing"]
    users_collection = db["users"]  
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)