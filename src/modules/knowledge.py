import os
import glob
from typing import Dict, List
from src.modules.mongodb_manager import MongoDBManager

class KnowledgeSystem:
    def __init__(self):
        self.collection = None
        collection = MongoDBManager.get_collection(MongoDBManager.MONGO_COLLECTION_KNOWLEDGE)
        if collection is not None:
            self.collection = collection
            print("成功连接到MongoDB知识库")
        else:
            print("警告: MongoDB连接失败，将使用内存存储")
        
        self.raw_files_dir = MongoDBManager.RAW_FILES_DIR
        os.makedirs(self.raw_files_dir, exist_ok=True)
        
        self.memory_storage = {}
        self.reset_knowledge_base()

    def _split_text(self, text: str) -> List[str]:
        return [text[i:i+MongoDBManager.CHUNK_SIZE] for i in range(0, len(text), MongoDBManager.CHUNK_SIZE)]

    def reset_knowledge_base(self):
        if self.collection is not None:
            self.collection.delete_many({})
        else:
            self.memory_storage.clear()
        
        txt_files = glob.glob(os.path.join(self.raw_files_dir, "*.txt"))
        for file_path in txt_files:
            domain = os.path.splitext(os.path.basename(file_path))[0]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    chunks = self._split_text(content)
                    if self.collection is not None:
                        self.collection.insert_many([
                            {"domain": domain, "content": chunk}
                            for chunk in chunks
                        ])
                    else:
                        if domain not in self.memory_storage:
                            self.memory_storage[domain] = []
                        self.memory_storage[domain].extend(chunks)
                    print(f"已加载 {len(chunks)} 条知识到 '{domain}'")
            except Exception as e:
                print(f"加载文件 {file_path} 失败: {e}")

    def add_knowledge(self, domain: str, knowledge: str):
        try:
            chunks = self._split_text(knowledge)
            if chunks and self.collection is not None:
                self.collection.insert_many([
                    {"domain": domain.lower(), "content": chunk}
                    for chunk in chunks
                ])
                print(f"已添加知识到 '{domain}'")
            elif chunks:
                if domain not in self.memory_storage:
                    self.memory_storage[domain] = []
                self.memory_storage[domain].extend(chunks)
                print(f"已添加知识到内存存储 '{domain}'")
        except Exception as e:
            print(f"添加知识失败: {str(e)}")

    def get_knowledge(self, domain: str = None) -> Dict[str, List[str]]:
        if self.collection is not None:
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
        else:
            if domain:
                return {domain: self.memory_storage.get(domain, [])}
            return self.memory_storage

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
        pass
