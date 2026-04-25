import asyncio

from pymongo import AsyncMongoClient
from beanie import init_beanie

from application_model import Application
from user_model import User

# I use AsyncMongoClient instead of AsyncIOMotorClient, since I was originally using AsynCMongoClient when I shared a project with several group members earlier. 
# i could have also used AsyncIOMOtorClient; I believe the only part that would change are the versions for some of the packages (ex. bcrypt, beanie). Based off the versions my 
# group members used, I had to use AsyncMongoClient to avoid version conflicts with their chosen models. I also had to use an older version of beanie (1.19.1) since the newer versions don't support AsyncMongoClient.
# However, AsyncMongoClient seems to work fine.
async def init_mongo():
    client = AsyncMongoClient(
        "mongodb+srv://chriss:VRf4H6BafmZbe8C@cluster0.acnynb2.mongodb.net/?appName=Cluster0"
    )
    db = client["Midterm_with_User_Login"]

    print("✅ Connecting to MongoDB...")

    await init_beanie(
        database=db, document_models=[User, Application]
    )

    print("✅ MongoDB connected and Beanie initialized")
