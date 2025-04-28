import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def get_embeddings(text, model="text-embedding-ada-002"):
    response = openai.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

# from google.api_core import exceptions
# from google.genai import types
# from google import genai
# from pymongo import MongoClient
# import openai
# import os
# from dotenv import load_dotenv
# load_dotenv()

# db_client = MongoClient(os.getenv("MONGODB_URI"))
# client = genai.Client(api_key= os.getenv("GOOGLE_API_KEY"))
# openai.api_key = os.getenv("OPENAI_API_KEY")

# def get_embeddings(text, retries=5):
#     for attempt in range(retries):
#         try:
#             result = client.models.embed_content(
#                 model="gemini-embedding-exp-03-07",
#                 contents=text,
#                 config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"))
#             return result.embeddings[0].values
#         except exceptions.ResourceExhausted as e:
#             if attempt < retries - 1:
#                 print(f"Quota vượt quá, thử lại sau {2 ** attempt} giây...")
#                 time.sleep(2 ** attempt)  # Đợi 1s, 2s, 4s,...
#             else:
#                 raise e