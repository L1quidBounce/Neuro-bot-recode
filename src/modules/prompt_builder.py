class PromptBuilder:
    def __init__(self, persona=None):
        self.persona = persona or {
            "name": "AI助手",
            "traits": "友好、专业、乐于助人",
            "background": "我是一个智能AI助手，旨在为用户提供有用的信息和帮助。"
        }
        
        # 孩子们prompt你们自己改，这个是我自己的prompt
        self.system_prompt = """
        你的网名叫{name}，{background}。
        现在请你读读之前的聊天记录，然后给出日常且口语化的回复，平淡一些，
        尽量简短一些。请注意把握聊天内容，不要刻意突出自身学科背景，不要回复的太有条理，可以有接近于网友的个性。
        请回复的平淡一些，简短一些，在提到时不要过多提及自身的背景。
        """
        
        self.system_prompt = self.system_prompt.format(
            name=self.persona["name"],
            background=self.persona["background"]
        )

    def build_prompt(self, user_input: str, knowledge_base: dict, conversation_history: list) -> str:
        prompt = self.system_prompt + "\n\n"
        prompt += f"用户输入: {user_input}\n\n"
        
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
                role = "用户" if msg["role"] == "user" else self.persona["name"]
                prompt += f"{role}: {msg['content']}\n"
        
        return prompt