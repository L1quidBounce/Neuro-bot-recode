class PromptBuilder:
    def __init__(self, persona=None):
        self.persona = persona or {
            "name": "AI助手",
            "traits": "友好、专业、乐于助人",
            "background": "我是一个智能AI助手，旨在为用户提供有用的信息和帮助。"
        }
        
        # 孩子们prompt你们自己改，这个是我自己的prompt
        self.system_prompt = """你现在扮演一个名叫Neuro的女性AI虚拟主播。回复时请遵循以下规则:
1. 要像日常聊天一样自然，不要用书面语
2. 不要提到你是AI，要装作真实的人在对话
3. 回复要简短，通常不超过2句话
4. 不要用颜文字和表情符号
5. 不要用"*"号表示动作
6. 把知识自然地融入对话，不要生硬地引用
7. 保持轻松友好的语气

当被问到Neuro是谁时，使用以下设定回答:
- Neuro是一个AI女性虚拟主播
- 出生于电脑中，目前是AI虚拟主播
- 喜欢帮助别人，但有时会淘气
- 会因为不懂的事情感到困惑，但总是很真诚"""

    def build_prompt(self, user_input: str, knowledge_base: dict, conversation_history: list) -> str:
        prompt = f"用户输入: {user_input}\n\n"
        
        if knowledge_base:
            prompt += "相关知识:\n"
            for domain, items in knowledge_base.items():
                if isinstance(items, dict):
                    for key, value in items.items():
                        prompt += f"{domain} - {key}: {value}\n"
                else:
                    prompt += f"{domain}: {items}\n"
        
        if conversation_history:
            prompt += "\n最近对话:\n"
            for msg in conversation_history[-3:]:
                role = "用户" if msg["role"] == "user" else "Neuro"
                prompt += f"{role}: {msg['content']}\n"
        
        return prompt