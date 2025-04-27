from pymongo import MongoClient
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Optional
import math

# 孩子们这个还没写完，哈基bot的大脑还不完善
class MemorySystem:
    def __init__(self, db_name: str = "NeuroBot", host: str = "localhost", port: int = 27017):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]
        self.memories = self.db.memories
        self.conversations = self.db.conversations
        
        self.memory_thread = threading.Thread(target=self._manage_memories, daemon=True)
        self.memory_thread.start()

    def store_memory(self, content: str, tags: List[str] = None, metadata: Dict = None) -> str:
        memory = {
            "content": content,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "weight": 1.0,  
            "access_count": 1 
        }
        result = self.memories.insert_one(memory)
        return str(result.inserted_id)
        
    def retrieve_memories(self, tags: List[str] = None, limit: int = 10) -> List[Dict]:
        query = {"tags": {"$in": tags}} if tags else {}
        return list(self.memories.find(query).limit(limit))
        
    def store_conversation(self, messages: List[Dict], metadata: Dict = None) -> str:
        conversation = {
            "messages": messages,
            "metadata": metadata or {},
            "created_at": datetime.utcnow()
        }
        result = self.conversations.insert_one(conversation)
        return str(result.inserted_id)
        
    def retrieve_conversation(self, conversation_id: str) -> Optional[Dict]:
        from bson.objectid import ObjectId
        return self.conversations.find_one({"_id": ObjectId(conversation_id)})
        
    def update_memory_access(self, memory_id: str):
        from bson.objectid import ObjectId
        self.memories.update_one(
            {"_id": ObjectId(memory_id)},
            {
                "$set": {"last_accessed": datetime.utcnow()},
                "$inc": {"access_count": 1},
                "$mul": {"weight": 1.1}  #
            }
        )

    def _manage_memories(self):
        """定期管理哈基bot的大脑"""
        while True:
            try:
                old_date = datetime.utcnow() - timedelta(days=7)
                self.memories.update_many(
                    {"last_accessed": {"$lt": old_date}},
                    {"$mul": {"weight": 0.9}}
                )

                # 哈基bot鱼一般的记忆力
                self.memories.delete_many({"weight": {"$lt": 0.1}})

                all_memories = self.memories.find()
                for memory in all_memories:
                    age = (datetime.utcnow() - memory["created_at"]).days + 1
                    access_rate = memory["access_count"] / age
                    new_weight = min(1.0, access_rate * math.log10(age + 1))
                    
                    self.memories.update_one(
                        {"_id": memory["_id"]},
                        {"$set": {"weight": new_weight}}
                    )

                self._optimize_tag_relationships()

            except Exception as e:
                print(f"记忆管理错误: {e}")
            
            time.sleep(1800)  # 每30分钟对着自己大脑哈一次气

    def _optimize_tag_relationships(self):
        """优化标签之间的关系权重"""
        tags_count = {}
        tag_pairs = {}
        
        memories = self.memories.find()
        for memory in memories:
            tags = memory["tags"]
            for tag in tags:
                tags_count[tag] = tags_count.get(tag, 0) + 1
                for other_tag in tags:
                    if tag != other_tag:
                        pair = tuple(sorted([tag, other_tag]))
                        tag_pairs[pair] = tag_pairs.get(pair, 0) + 1

        for tag, count in tags_count.items():
            self.memories.update_many(
                {"tags": tag},
                {"$set": {f"tag_weights.{tag}": count / len(tags_count)}}
            )
