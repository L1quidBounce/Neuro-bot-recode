import json
import logging
import os
import sys
import threading
import time
from typing import Dict, List

import openai
from colorama import init, Fore, Style

from src.modules.filter import ContentFilter
from src.modules.knowledge import KnowledgeSystem
from src.modules.pc_permissions import SystemMonitor
from src.modules.prompt_builder import PromptBuilder
from src.modules.relationship import RelationshipSystem
import math
import random
import concurrent.futures
from concurrent.futures import TimeoutError
from src.modules.api_manager import APIManager

"""
    TODO:
    1.修复任务管理器调用权限问题
    2.添加视觉模型
    3.修复资源管理器问题
    4.修复偶现bug
    5.完善记忆系统
    6.完善知识库系统
    7.临时上下文记忆
"""

class ChatBot:
    def __init__(self, config_path: str = "config.json", knowledge_dir: str = "knowledge_base"):
        init()  

        logger = logging.getLogger('mylogger')
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - '
            f'{Fore.GREEN}%(name)s{Style.RESET_ALL} - '
            f'{Fore.YELLOW}%(levelname)s{Style.RESET_ALL} - '
            f'%(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        # 移除了没用的傻比注释
        print(Fore.GREEN + "多年以后，面对找上门的Neuro,Fedal987会想起当年重写她的那个晚上" + Style.RESET_ALL)

        logger.info('[Neuro-bot] 正在初始化系统...')
        logger.info('[Neuro-bot] 正在加载配置文件...')
        
        self.config = self._load_config(config_path)
        self.api_manager = APIManager(self.config)
        
        logger.info('[Neuro-bot] 已加载config')
        
        self.backend = self.config.get("default_backend", "deepseek")
        logger.info('[Neuro-bot] 模型设置为 deepseek-chat')
        
        self.persona = self.config.get("persona", {})
        self.prompt_builder = PromptBuilder(self.persona)
        logger.info('[Neuro-bot] 人格加载成功')
        
        self.knowledge_system = KnowledgeSystem()
        self.knowledge_base = self.knowledge_system.get_all_knowledge()
        logger.info('[Neuro-bot] 知识库加载成功')
        
        self.conversation_history = []
        logger.info('[Neuro-bot] 检查对话历史')
        
        self.knowledge_dir = knowledge_dir
        self.api_config = self.config.get("api_config", {})

        if os.path.exists(knowledge_dir):
            self.load_knowledge_from_files()
        
        logger.info('[Neuro-bot] 聊天机器人已初始化，当前模型: deepseek-chat')
        self._print_current_model()
        self.content_filter = ContentFilter()
        logger.debug('[Neuro-bot] 内容过滤系统已初始化')
        
        self.system_monitor = SystemMonitor()
        logger.debug('[Neuro-bot] 系统权限已开放至大模型')
        self.relationship_system = RelationshipSystem()
        logger.debug('[Neuro-bot] 好感度系统已初始化')

    def _call_api(self, prompt: str, mode: str = "chat") -> str:
        return self.api_manager.call_api(
            prompt, 
            system_prompt=self.prompt_builder.system_prompt,
            mode=mode
        )

    def _print_current_model(self):
        if self.backend in self.api_config:
            config = self.api_config[self.backend]
            print(Fore.GREEN + f"当前模型: {config.get('default_model', '未指定')}" + Style.RESET_ALL)
            print(Fore.GREEN + f"API端点: {getattr(openai, 'api_base', '未设置')}" + Style.RESET_ALL)
        else:
            print(Fore.RED + "当前后端配置不完整" + Style.RESET_ALL)

    # 默认参数生成器
    def _load_config(self, config_path: str) -> Dict:
        default_config = {
            "default_backend": "deepseek",
            "persona": {
                "name": "AI助手",
                "traits": "友好、专业、乐于助人",
                "background": "我是一个智能AI助手，旨在为用户提供有用的信息和帮助。"
            },
            "knowledge_base": {
                "general": "通用知识库",
                "specialized": {}
            },
            "api_config": {
                "deepseek": {
                    "api_key": "",
                    "api_base": "https://api.deepseek.com/v1",
                    "chat_model": "deepseek-chat",
                    "vision_model": "deepseek-vision",
                    "tts_model": "deepseek-tts",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return self._deep_merge(default_config, json.load(f))
            # 666参数拉太大了
            except Exception as e:
                print(f"加载配置失败: {e}, 使用默认配置")
        else:
            print("配置文件不存在，创建默认配置")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config

    def _deep_merge(self, default: Dict, custom: Dict) -> Dict:
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _split_text(self, text: str, chunk_size: int = 512) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    # 没写完的知识库系统，好像还写炸了
    def load_knowledge_from_files(self):
        pass

    def reset_knowledge(self):
        self.knowledge_system.reset_knowledge_base()
        self.knowledge_base = self.knowledge_system.get_all_knowledge()
        print("知识库已重置")

    # 参数保存
    def save_config(self, config_path: str = "config.json"):
        self.config.update({
            "default_backend": self.backend,
            "persona": self.persona,
            "knowledge_base": self.knowledge_base
        })
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        print("配置已保存")

    def switch_backend(self, backend: str):
        if backend in self.api_config:
            self.backend = backend
            self.api_manager.setup_api_client()
            print(f"已切换到 {backend}")
            self._print_current_model()
        else:
            print(f"无效后端，可用: {', '.join(self.api_config.keys())}")

    def switch_model(self, model: str):
        if self.backend in self.api_config:
            self.api_config[self.backend]["default_model"] = model
            print(f"{self.backend} 模型已切换为 {model}")
        else:
            print("请先选择有效后端")

    def update_persona(self, name: str = None, traits: str = None, background: str = None):
        self.prompt_builder.update_persona(name, traits, background)
        self.persona = self.prompt_builder.persona
        print("人设已更新")

    def add_knowledge(self, domain: str, knowledge: str):
        self.knowledge_system.add_knowledge(domain, knowledge)
        self.knowledge_base = self.knowledge_system.get_all_knowledge()
        print(f"已添加知识到 '{domain}'")

    def get_knowledge(self, domain: str = None) -> Dict[str, List[str]]:
        return self.knowledge_system.get_knowledge(domain)

    # 我其实更应该给这段prompt塞进prompt_builder或者是pc_permissions里面
    def _build_prompt(self, user_input: str) -> str:
        system_control_context = """你需要将用户的自然语言指令转换为具体的系统操作。不需要做出额外的对话回应。

鼠标控制说明：
用户的位置描述对应的坐标：
- "中间/中央": (screen_width//2, screen_height//2)
- "左上": (0, 0)
- "右上": (screen_width-1, 0)  
- "左下": (0, screen_height-1)
- "右下": (screen_width-1, screen_height-1)
- "左边": (0, screen_height//2)
- "右边": (screen_width-1, screen_height//2)

示例：
用户说"把鼠标移到中间"：
<execute>
screen_width, screen_height = self.system_monitor.get_screen_size()
self.system_monitor.simulate_mouse_move(screen_width//2, screen_height//2)
</execute>

用户说"右键点击":
<execute>
self.system_monitor.simulate_click('right')
</execute>

注意事项:
1. 所有命令必须用<execute>标签包装
2. 不要返回任何额外的文本信息
3. 准确理解用户描述的位置并转换为对应坐标
4. 命令执行完后不需要额外确认"""

        interaction_style = self.relationship_system.get_interaction_style("default_user")
        
        if (interaction_style["status"] == "friendly"):
            self.prompt_builder.system_prompt += f"\n请以{interaction_style['tone']}的语气回复，可以使用{','.join(interaction_style['emoticons'])}等表情。"
        elif (interaction_style["status"] == "cold"):
            self.prompt_builder.system_prompt += "\n请保持正式和简短的回复。"
        
        return self.prompt_builder.build_prompt(
            user_input,
            {**self.knowledge_base, "system_control": system_control_context},
            self.conversation_history
        )

    def chat(self, user_input: str) -> str:
        if not user_input.strip():
            return "请输入有效内容"
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._call_api, self._build_prompt(user_input), "chat")
                try:
                    response = future.result(timeout=120)
                except TimeoutError:
                    future.cancel()
                    return "Someone tell Vedal there is a problem with my AI"
        except AttributeError as e:
            return "API配置错误,请检查配置文件"
        except Exception as e:
            return f"对话出现错误: {str(e)}"

        try:
            if "<execute>" in response:
                parts = response.split("<execute>")
                command_part = parts[1].split("</execute>")[0].strip()
                
                try:
                    namespace = {
                        'self': self,
                        'random': random,
                        'time': time,
                        'math': math,
                        'os': os
                    }
                    exec(command_part, namespace)
                    return "命令已执行"
                except Exception as e:
                    return f"执行失败: {str(e)}"
            return response

        except Exception:
            return "命令执行失败"
        
        """
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        if isinstance(user_input, str):
            if "谢谢" in user_input or "感谢" in user_input:
                self.relationship_system.update_relationship("default_user", 2)
            elif "笨蛋" in user_input or "废物" in user_input:
                self.relationship_system.update_relationship("default_user", -3)
        
        return response
        """

    def clear_history(self):
        self.conversation_history = []
        print("对话历史已清空")

    def get_system_info(self):
        return self.system_monitor.get_safe_system_info()

    def handle_command(self, cmd: str, args: List[str]):
        """处理命令"""
        if cmd == "tasklist":
            processes = self.system_monitor.get_process_list()
            result = "\n进程列表（按CPU使用率排序）:\n"
            result += "PID".ljust(8) + "名称".ljust(20) + "CPU".ljust(10) + "内存".ljust(10)
            result += "状态".ljust(10) + "用户".ljust(15) + "创建时间".ljust(20) + "\n"
            result += "-" * 90 + "\n"
            
            for proc in processes:
                result += f"{str(proc['pid']).ljust(8)}"
                result += f"{proc['name'][:18].ljust(20)}"
                result += f"{f'{proc['cpu']:.1f}%'.ljust(10)}"
                result += f"{f'{proc['memory']:.1f}%'.ljust(10)}"
                result += f"{proc['status'][:8].ljust(10)}"
                result += f"{str(proc['user'])[:13].ljust(15)}"
                result += f"{proc['created']}\n"
            print(result)
        elif cmd == "taskinfo":
            info = self.system_monitor.get_performance_info()
            result = "\n系统性能信息:\n"
            result += f"CPU使用率: {info['cpu']['usage']}% | 频率: {info['cpu']['freq']}MHz\n"
            result += f"内存: {info['memory']['used']}/{info['memory']['total']} ({info['memory']['percent']}%)\n"
            result += f"磁盘: {info['disk']['used']}/{info['disk']['total']} ({info['disk']['percent']}%)"
            print(result)
        elif cmd == "taskkill" and args:
            target = int(args[0]) if args[0].isdigit() else args[0]
            result = self.system_monitor.kill_process(target)
            print(result)
        elif cmd == "type" and args:
            text = " ".join(args)
            result = self.system_monitor.simulate_keyboard_input(text)
            print(result)
        elif cmd == "move" and len(args) == 2:
            try:
                x, y = map(int, args)
                result = self.system_monitor.simulate_mouse_move(x, y)
                print(result)
            except ValueError:
                print("用法: /move x y (x和y必须是整数)")
        elif cmd == "click":
            button = args[0] if args else 'left'
            clicks = int(args[1]) if len(args) > 1 else 1
            result = self.system_monitor.simulate_click(button, clicks)
            print(result)
        elif cmd == "shortcut" and args:
            result = self.system_monitor.simulate_shortcut(*args)
            print(result)
        elif cmd == "open" and args:
            result = self.system_monitor.open_file(args[0])
            print(result)
        elif cmd == "cmd" and args:
            result = self.system_monitor.execute_cmd(" ".join(args))
            print(result)
        elif cmd == "camera":
            if not args:
                print("用法: /camera capture [文件名] 或 /camera preview [秒数]")
            elif args[0] == "capture":
                save_path = args[1] if len(args) > 1 else "capture.jpg"
                result = self.system_monitor.camera_capture(save_path)
                print(result)
            elif args[0] == "preview":
                duration = int(args[1]) if len(args) > 1 else 5
                result = self.system_monitor.camera_preview(duration)
                print(result)
        elif cmd == "help":
            print("可用命令:")
            print("/switch 后端 - 切换API后端")
            print("/model 模型 - 切换模型")
            print("/persona [名称 特征 背景] - 设置人设")
            print("/add 领域 知识 - 添加知识")
            print("/clear - 清空对话历史")
            print("/save - 保存配置")
            print("/filter add/remove 关键词 - 添加或移除敏感词")
            print("/reset - 重置知识库")
            print("/learn - 学习知识库文件夹中的所有文本")
            print("/forget - 遗忘所有已学习的知识")
            print("/system - 显示系统信息")
            print("/exit - 退出")
            print("/camera capture [文件名] - 拍摄照片")
            print("/camera preview [秒数] - 打开摄像头预览")
        else:
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}抱歉,我不太理解这个命令。输入 /help 可以查看所有支持的命令哦！")

    def main_loop(self):
        print(Fore.CYAN + "\n欢迎使用Neuro-bot! 输入/help查看命令" + Style.RESET_ALL)
        while True:
            try:
                user_input = input(Fore.GREEN + "\n你: " + Style.RESET_ALL).strip()
                
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    cmd, *args = user_input[1:].split(" ")
                    self.handle_command(cmd, args)  
                else:
                    start_time = time.time()
                    print("\n" + Fore.YELLOW + "思考中..." + Style.RESET_ALL, end="", flush=True)
                    timer_stop = threading.Event()
                    
                    def update_timer():
                        while not timer_stop.is_set():
                            print("\r" + Fore.YELLOW + f"思考中... {time.time() - start_time:.1f}s" + 
                                  Style.RESET_ALL, end="", flush=True)
                            time.sleep(1)
                    
                    timer_thread = threading.Thread(target=update_timer)
                    timer_thread.daemon = True
                    timer_thread.start()
                    
                    response = self.chat(user_input)  
                    timer_stop.set()
                    timer_thread.join()  
                    
                    elapsed_time = time.time() - start_time
                    print("\r" + " " * 30 + "\r", end="")  
                    print(f"{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}{response}")
                    print(Fore.YELLOW + f" 思考时间: {elapsed_time:.2f}秒" + Style.RESET_ALL)
                    
            except (KeyboardInterrupt, EOFError):
                print(Fore.YELLOW + "\n使用/exit退出程序" + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"错误: {e}" + Style.RESET_ALL)

def main():
    bot = ChatBot()
    print(Fore.CYAN + "\n欢迎使用Neuro-bot! 输入/help查看命令" + Style.RESET_ALL)
    while True:
        try:
            user_input = input(Fore.GREEN + "\n你: " + Style.RESET_ALL).strip()
            if not user_input:
                continue
            if user_input.startswith("/"):
                cmd, *args = user_input[1:].split(" ", 1)
                if cmd == "exit":
                    bot.save_config()
                    print("再见!")
                    break
                elif cmd == "switch" and args:
                    bot.switch_backend(args[0])
                elif cmd == "model" and args:
                    bot.switch_model(args[0])
                elif cmd == "persona":
                    if args:
                        parts = args[0].split(" ", 2)
                        bot.update_persona(
                            parts[0] if len(parts) > 0 else None,
                            parts[1] if len(parts) > 1 else None,
                            parts[2] if len(parts) > 2 else None
                        )
                    else:
                        print("当前人设:", json.dumps(bot.persona, indent=2, ensure_ascii=False))
                elif cmd == "add" and args:
                    if " " in args[0]:
                        domain, knowledge = args[0].split(" ", 1)
                        bot.add_knowledge(domain, knowledge)
                    else:
                        print("用法: /add 领域 知识内容")
                elif cmd == "clear":
                    bot.clear_history()
                elif cmd == "save":
                    bot.save_config()
                elif cmd == "filter":
                    if not args:
                        print("用法: /filter add/remove 关键词")
                    else:
                        action, word = args[0].split(" ", 1)
                        if action == "add":
                            bot.content_filter.add_word(word)
                            print(f"已添加敏感词: {word}")
                        elif action == "remove":
                            bot.content_filter.remove_word(word)
                            print(f"已移除敏感词: {word}")
                elif cmd == "reset":
                    bot.reset_knowledge()
                elif cmd == "system":
                    sys_info = bot.get_system_info()
                    print("\n系统信息:")
                    for key, value in sys_info.items():
                        print(f"{key}: {value}")
                elif cmd == "help":
                    print("可用命令:")
                    print("/switch 后端 - 切换API后端")
                    print("/model 模型 - 切换模型")
                    print("/persona [名称 特征 背景] - 设置人设")
                    print("/add 领域 知识 - 添加知识")
                    print("/clear - 清空对话历史")
                    print("/save - 保存配置")
                    print("/filter add/remove 关键词 - 添加或移除敏感词")
                    print("/reset - 重置知识库")
                    print("/learn - 学习知识库文件夹中的所有文本")
                    print("/forget - 遗忘所有已学习的知识")
                    print("/system - 显示系统信息")
                    print("/exit - 退出")
                    print("/camera capture [文件名] - 拍摄照片")
                    print("/camera preview [秒数] - 打开摄像头预览")
                elif cmd == "learn":
                    count = bot.knowledge_system.learn_all()
                    bot.knowledge_base = bot.knowledge_system.get_all_knowledge()
                    print(f"已学习 {count} 条新知识")
                elif cmd == "forget":
                    count = bot.knowledge_system.forget_all()
                    bot.knowledge_base = bot.knowledge_system.get_all_knowledge()
                    print(f"已遗忘 {count} 条知识")
                else:
                    print("未知命令，输入/help查看帮助")
            else:
                start_time = time.time()
                print("\n" + Fore.YELLOW + "思考中..." + Style.RESET_ALL, end="", flush=True)
                timer_stop = threading.Event()
                
                def update_timer():
                    while not timer_stop.is_set():
                        print("\r" + Fore.YELLOW + f"思考中... {time.time() - start_time:.1f}s" + 
                              Style.RESET_ALL, end="", flush=True)
                        time.sleep(1)
                
                timer_thread = threading.Thread(target=update_timer)
                timer_thread.daemon = True
                timer_thread.start()
                
                response = bot.chat(user_input)
                timer_stop.set()
                timer_thread.join()
                
                elapsed_time = time.time() - start_time
                print("\r" + " " * 30 + "\r", end="")
                print(f"{Fore.BLUE}{bot.persona.get('name','AI')}: {Style.RESET_ALL}{response}")
                print(Fore.YELLOW + f"思考时间: {elapsed_time:.2f}秒" + Style.RESET_ALL)
                
        except (KeyboardInterrupt, EOFError):
            print(Fore.YELLOW + "\n使用/exit退出程序" + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"错误: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()

