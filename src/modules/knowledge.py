import os
import glob
from typing import Dict, List
from pymongo import MongoClient
from src.constants import MONGO_URI, MONGO_DB, MONGO_COLLECTION, RAW_FILES_DIR, CHUNK_SIZE

# 孩子们这个更是传奇半成品module

class KnowledgeSystem:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB.lower()]
        self.collection = self.db[MONGO_COLLECTION.lower()]
        self.raw_files_dir = RAW_FILES_DIR
        
        os.makedirs(self.raw_files_dir, exist_ok=True)
        
        self.reset_knowledge_base()

    def _split_text(self, text: str) -> List[str]:
        return [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]

    def reset_knowledge_base(self):
        self.collection.delete_many({})
        
        txt_files = glob.glob(os.path.join(self.raw_files_dir, "*.txt"))
        for file_path in txt_files:
            domain = os.path.splitext(os.path.basename(file_path))[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    chunks = self._split_text(content)
                    self.collection.insert_many([
                        {"domain": domain, "content": chunk}
                        for chunk in chunks
                    ])
                    print(f"已加载 {len(chunks)} 条知识到 '{domain}'")
            except Exception as e:
                print(f"加载文件 {file_path} 失败: {e}")

    def add_knowledge(self, domain: str, knowledge: str):
        try:
            chunks = self._split_text(knowledge)
            if chunks:
                self.collection.insert_many([
                    {"domain": domain.lower(), "content": chunk}
                    for chunk in chunks
                ])
                print(f"已添加知识到 '{domain}'")
        except Exception as e:
            print(f"添加知识失败: {str(e)}")

    def get_knowledge(self, domain: str = None) -> Dict[str, List[str]]:
        if domain:
            cursor = self.collection.find({"domain": domain})
            return {domain: [doc["content"] for doc in cursor]}
        else:
            result = {}
            for doc in self.collection.find():
                if doc["domain"] not in result:
                    result[doc["domain"]] = []
                result[doc["domain"]].append(doc["content"])
            return result

    def get_all_knowledge(self) -> Dict:
        return {
            "general": "通用知识库",
            "specialized": self.get_knowledge()
        }

    def learn_all(self) -> int:
        count = 0
        txt_files = glob.glob(os.path.join(self.raw_files_dir, "*.txt"))
        for file_path in txt_files:
            domain = os.path.splitext(os.path.basename(file_path))[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    chunks = self._split_text(content)
                    self.collection.insert_many([
                        {"domain": domain, "content": chunk}
                        for chunk in chunks
                    ])
                    count += len(chunks)
            except Exception as e:
                print(f"加载文件 {file_path} 失败: {e}")
        return count

    def forget_all(self):
        count = self.collection.count_documents({})
        self.collection.delete_many({})
        return count

    def __del__(self):
        self.client.close()
