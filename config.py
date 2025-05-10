import os
from dotenv import load_dotenv
from pymongo import MongoClient
from llama_index.llms.openai import OpenAI

load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URl")

client = MongoClient(MONGODB_URI)
db = client['HoangHaMobile']
phone_collection = db["phone-main"]
laptop_collection = db["laptop-main"]
tablet_collection = db["tablet-main"]

collections_to_check = ["phone-main", "laptop-main", "tablet-main"]

# Lấy danh sách các collection thực tế trong database
existing_collections = db.list_collection_names()

# LLM configuration
llm = OpenAI(model="gpt-4o-mini", temperature=0)