from motor.motor_asyncio import AsyncIOMotorClient
import os
import certifi

mongo_url = os.environ['MONGO_URL']

# Use certifi CA bundle for Atlas SSL connections
if 'mongodb+srv' in mongo_url or 'mongodb.net' in mongo_url:
    client = AsyncIOMotorClient(mongo_url, tlsCAFile=certifi.where())
else:
    client = AsyncIOMotorClient(mongo_url)

db = client[os.environ['DB_NAME']]
