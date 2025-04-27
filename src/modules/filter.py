import json
import os
from typing import Set

# Vedal987：你的意思是你写这玩意的意义就在于模仿我？
class ContentFilter:
    def __init__(self, filter_file: str = "sensitive_words.json"):
        self.filter_file = filter_file
        self.sensitive_words: Set[str] = set()
        self._load_sensitive_words()

    def _load_sensitive_words(self) -> None:
        default_words = {
            "nigger",
            "nazi",
            "习近平",
        }

        if os.path.exists(self.filter_file):
            try:
                with open(self.filter_file, 'r', encoding='utf-8') as f:
                    self.sensitive_words = set(json.load(f))
            except:
                self.sensitive_words = default_words
        else:
            self.sensitive_words = default_words
            self._save_sensitive_words()

    def _save_sensitive_words(self) -> None:
        with open(self.filter_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.sensitive_words), f, indent=4)

    def add_word(self, word: str) -> None:
        self.sensitive_words.add(word.lower())
        self._save_sensitive_words()

    def remove_word(self, word: str) -> None:
        self.sensitive_words.discard(word.lower())
        self._save_sensitive_words()

    def filter_text(self, text: str) -> str:
        filtered_text = text
        for word in self.sensitive_words:
            filtered_text = filtered_text.replace(word, "Filtered")
        return filtered_text
