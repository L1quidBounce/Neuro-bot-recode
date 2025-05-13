from pymongo import MongoClient
from typing import Optional
import logging

class MongoDBManager:
    _instance = None
    _client: Optional[MongoClient] = None
    
    MONGO_URI = "mongodb://localhost:27017/"
    MONGO_DB = "NeuroBot"
    MONGO_COLLECTION_KNOWLEDGE = "knowledge"
    MONGO_COLLECTION_RELATIONSHIPS = "relationships"
    MONGO_COLLECTION_MEMORIES = "memories"
    MONGO_COLLECTION_CONVERSATIONS = "conversations"

    RAW_FILES_DIR = "knowledge_base"
    CHUNK_SIZE = 2000
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                self._client = MongoClient(self.MONGO_URI)
                self._client.server_info()  
                logging.info("MongoDB connection established")
            except Exception as e:
                logging.error(f"MongoDB connection failed: {e}")
                self._client = None
    
    @classmethod
    def get_db(cls):
        instance = cls.get_instance()
        if instance._client is None:
            return None
        return instance._client[cls.MONGO_DB]
    
    @classmethod
    def get_collection(cls, collection_name):
        db = cls.get_db()
        if db is None:
            return None
        return db[collection_name]
