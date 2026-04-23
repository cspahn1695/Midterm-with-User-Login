import asyncio

from pymongo import AsyncMongoClient
from beanie import init_beanie

from application_model import Application
from user_model import User


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
