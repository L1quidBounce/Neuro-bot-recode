import openai
import logging
from typing import Dict, Optional
import threading
import time

class APIManager:
    def __init__(self, config: Dict):
        self.logger = logging.getLogger('api_manager')
        self.config = config
        self.backend = config.get("default_backend", "deepseek")
        self.api_status = True
        self._setup_client()
        self._start_status_check()

    def _setup_client(self) -> None:
        if self.backend in self.config.get("api_config", {}):
            config = self.config["api_config"][self.backend]
            openai.api_key = config.get("api_key", "")
            openai.api_base = config.get("api_base", "https://api.deepseek.com/v1")
            self.logger.info(f"API client setup complete for {self.backend}")

    def _start_status_check(self) -> None:
        self.status_check_thread = threading.Thread(target=self._check_status, daemon=True)
        self.status_check_thread.start()

    def _check_status(self) -> None:
        while True:
            try:
                response = self.test_api()
                self.api_status = response is not None and "API当前不可用" not in str(response)
            except Exception as e:
                self.api_status = False
                self.logger.error(f"API status check failed: {e}")
            time.sleep(30)

    def test_api(self) -> Optional[str]:
        try:
            return self.call_api("test")
        except Exception:
            return None

    def call_api(self, prompt: str, system_prompt: str = "", mode: str = "chat") -> str:
        if not self.api_status:
            return "API当前不可用，请稍后重试"

        try:
            config = self.config["api_config"][self.backend]
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            response = openai.ChatCompletion.create(
                model=config.get(f"{mode}_model", "deepseek-chat"),
                messages=messages,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2000)
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            return f"API调用失败: {str(e)}"
