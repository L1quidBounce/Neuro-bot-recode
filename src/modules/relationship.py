from src.modules.mongodb_manager import MongoDBManager
import logging
from datetime import datetime

class RelationshipSystem:
    def __init__(self):
        self.relationships = None
        try:
            collection = MongoDBManager.get_collection(MongoDBManager.MONGO_COLLECTION_RELATIONSHIPS)
            if collection is not None:
                self.relationships = collection
                self.relationships.create_index("user_id", unique=True)
            else:
                print("警告: MongoDB连接失败，将使用默认好感度系统")
        except Exception as e:
            logging.error(f"MongoDB连接失败: {e}")

    def get_relationship(self, user_id: str) -> dict:
        if self.relationships is None:
            return {"level": 50, "status": "normal"}
        
        result = self.relationships.find_one({"user_id": user_id})
        if not result:
            default_data = {
                "user_id": user_id,
                "level": 50,  
                "status": "normal",
                "last_interaction": datetime.now(),
                "interaction_count": 0
            }
            self.relationships.insert_one(default_data)
            return default_data
        return result

    def update_relationship(self, user_id: str, delta: int, interaction_type: str = "chat"):
        """更新好感度"""
        if self.relationships is None:
            return
        
        current = self.get_relationship(user_id)
        new_level = max(0, min(100, current["level"] + delta))
        
        if new_level >= 80:
            status = "friendly"
        elif new_level >= 50:
            status = "normal"
        else:
            status = "cold"

        self.relationships.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "level": new_level,
                    "status": status,
                    "last_interaction": datetime.now()
                },
                "$inc": {"interaction_count": 1}
            }
        )
    
    def get_interaction_style(self, user_id: str) -> dict:
        """根据好感度返回互动风格"""
        relationship = self.get_relationship(user_id)
        level = relationship["level"]
        status = relationship["status"]
        
        styles = {
            "friendly": {
                "honorifics": ["亲爱的", "可爱的", "最好的"],
                "emoticons": ["❤️", "✨", "💕"],
                "tone": "热情",
                "response_length": "详细"
            },
            "normal": {
                "honorifics": ["", "您"],
                "emoticons": ["😊", "👍"],
                "tone": "礼貌",
                "response_length": "适中"
            },
            "cold": {
                "honorifics": ["先生", "女士"],
                "emoticons": [],
                "tone": "正式",
                "response_length": "简短"
            }
        }
        
        return {
            "level": level,
            "status": status,
            **styles[status]
        }
