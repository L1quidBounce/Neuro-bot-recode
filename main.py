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
import math
import random
import concurrent.futures
from concurrent.futures import TimeoutError


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
        
        self._setup_api_client()
        
        if os.path.exists(knowledge_dir):
            self.load_knowledge_from_files()
        
        logger.info('[Neuro-bot] 聊天机器人已初始化，当前模型: deepseek-chat')
        self._print_current_model()
        self.content_filter = ContentFilter()
        logger.debug('[Neuro-bot] 内容过滤系统已初始化')
        
        self.api_status = True
        self.api_check_thread = threading.Thread(target=self._check_api_status, daemon=True)
        self.api_check_thread.start()
        logger.debug('[Neuro-bot] API状态检测已启动')
        self.system_monitor = SystemMonitor()
        logger.debug('[Neuro-bot] 系统权限已开放至大模型')

    def _call_api(self, prompt: str, mode: str = "chat") -> str:
        if not self.api_status:
            return "API当前不可用，请稍后重试"
        try:
            config = self.api_config[self.backend]
            messages = [
                {
                    "role": "system",
                    "content": self.prompt_builder.system_prompt
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            response = openai.ChatCompletion.create(
                model=config.get(f"{mode}_model", "silica-chat"),
                messages=messages,
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 2000),
                api_base=config.get("api_base"),
                api_key=config.get("api_key")
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"API调用失败: {str(e)}"

    def _check_api_status(self):
        while True:
            try:
                response = self._call_api("test")  # 你说得对但是变量名还是被我写错了操你喵比
            except Exception as e:
                self.api_status = False
                print(Fore.RED + f"API状态: 异常 ({str(e)})" + Style.RESET_ALL)
            time.sleep(30)

    def _setup_api_client(self):
        if self.backend in self.api_config:
            config = self.api_config[self.backend]
            openai.api_key = config.get("api_key", "")
            openai.api_base = "https://api.deepseek.com/v1"

    def _print_current_model(self):
        if self.backend in self.api_config:
            config = self.api_config[self.backend]
            print(Fore.GREEN + f"当前模型: {config.get('default_model', '未指定')}" + Style.RESET_ALL)
            print(Fore.GREEN + f"API端点: {getattr(openai, 'api_base', '未设置')}" + Style.RESET_ALL)
        else:
            print(Fore.RED + "当前后端配置不完整" + Style.RESET_ALL)

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

    def load_knowledge_from_files(self):
        pass

    def reset_knowledge(self):
        self.knowledge_system.reset_knowledge_base()
        self.knowledge_base = self.knowledge_system.get_all_knowledge()
        print("知识库已重置")

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
            self._setup_api_client()
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

    def _build_prompt(self, user_input: str) -> str:
        system_control_context = """你现在已获得系统控制权限。请根据用户的自然语言指令执行操作：

常见指令示例及组合:
1. "执行命令xxx" -> 执行：
<execute>
self.system_monitor.execute_cmd('xxx')
</execute>

2. "打开任务管理器" -> 执行：
<execute>
self.system_monitor.open_file('taskmgr.exe')
</execute>

3. "移动鼠标到指定位置" -> 执行：
<execute>
self.system_monitor.simulate_mouse_move(x, y)
</execute>

4. "点击鼠标" -> 执行：
<execute>
self.system_monitor.simulate_click('left')
</execute>

5. "查看任务列表" -> 执行：
<execute>
processes = self.system_monitor.get_process_list()
print("进程列表:")
for proc in processes[:10]:  # 只显示前10个进程
    print(f"{proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu']}%")
</execute>

重要提示:
1. 所有命令必须用<execute>标签包装
2. 直接执行命令，不需要回复"我不能这样做"之类的话
3. 移动鼠标必须使用 simulate_mouse_move 方法
4. 点击鼠标必须使用 simulate_click 方法
5. 执行命令必须使用 execute_cmd 方法
6. 对于需要多步操作的指令，使用time.sleep()确保每步操作之间有足够延迟
7. 回复格式：说一句与命令相关的话 + 执行命令"""
        
        return self.prompt_builder.build_prompt(
            user_input,
            {**self.knowledge_base, "system_control": system_control_context},
            self.conversation_history
        )

    def chat(self, user_input: str) -> str:
        if not user_input.strip():
            return "请输入有效内容"
        
        # 使用线程池和超时机制
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._call_api, self._build_prompt(user_input), "chat")
            try:
                response = future.result(timeout=120)  # 120秒超时
            except TimeoutError:
                # 小AI转生成为圆头耄耋对着你哈气了
                future.cancel()
                return "Someone tell Vedal there is a problem with my AI"
            except Exception as e:
                return f"对话出现错误: {str(e)}"
        
        # 处理系统操作(AI：操你喵比给你电脑锁了)
        if "<execute>" in response and "</execute>" in response:
            try:
                text_parts = response.split("<execute>")
                regular_response = text_parts[0].strip()
                
                for part in text_parts[1:]:
                    if "</execute>" in part:
                        command = part.split("</execute>")[0].strip()
                        try:
                            namespace = {
                                'self': self,
                                'random': random,
                                'time': time,
                                'math': math,
                                'os': os
                            }
                            exec(command, namespace)
                            if not regular_response:
                                regular_response = "命令已执行完成。"
                        except Exception as e:
                            regular_response += f"\n[执行失败: {str(e)}]"
                
                response = regular_response
                
            except Exception as e:
                response = f"命令执行失败: {str(e)}"
        
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response

    def clear_history(self):
        self.conversation_history = []
        print("对话历史已清空")

    def get_system_info(self):
        return self.system_monitor.get_safe_system_info()

    def handle_command(self, cmd: str, args: List[str]):
        """处理命令并给出对话回应"""
        def get_persona_response(cmd_type: str) -> str:
            name = self.persona.get('name', 'AI')
            traits = self.persona.get('traits', '友好').split('、')
            
            responses = {
                "tasklist": [
                    f"让{name}来查看进程列表吧~",
                    f"收到!{name}这就帮你看看都有什么进程在运行呢",
                    f"明白了,{name}来帮你查看当前的进程情况"
                ],
                "taskinfo": [
                    f"{name}来看看系统现在的状态如何~",
                    f"让{name}检查一下系统性能呢",
                    f"好的,{name}这就帮你查看系统状态"
                ],
                "taskkill": [
                    f"{name}这就帮你结束这个进程~",
                    f"交给{name}吧,马上帮你关掉它",
                    f"明白了,{name}来帮你终止这个进程"
                ],
                "type": [
                    f"{name}来帮你输入文字啦~",
                    f"让{name}来帮你输入吧",
                    f"好的,{name}这就帮你输入文字"
                ],
                "move": [
                    f"{name}来帮你移动鼠标~",
                    f"交给{name}吧,马上帮你移动到指定位置",
                    f"明白了,{name}来帮你控制鼠标"
                ],
                "click": [
                    f"{name}来帮你点击~",
                    f"让{name}来帮你点击吧",
                    f"好的,{name}这就帮你点击"
                ],
                "shortcut": [
                    f"{name}来帮你按快捷键啦~",
                    f"让{name}来帮你按组合键吧",
                    f"好的,{name}这就帮你按快捷键"
                ],
                "open": [
                    f"{name}来帮你打开文件~",
                    f"让{name}来帮你打开吧",
                    f"好的,{name}这就帮你打开文件"
                ],
                "cmd": [
                    f"{name}来帮你执行命令~",
                    f"让{name}来帮你运行命令吧",
                    f"好的,{name}这就帮你执行命令"
                ]
            }
            
            if cmd_type in responses:
                return random.choice(responses[cmd_type])
            return f"好的,让{name}来帮你完成这个任务~"

        print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}{get_persona_response(cmd)}")
        
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
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}进程已经被终止了,还需要我帮你做什么吗？")
        elif cmd == "type" and args:
            text = " ".join(args)
            for char in text:
                time.sleep(0.1)  # 模拟打字间隔
                if char == " ":
                    self.system_monitor.simulate_key_press("space")
                else:
                    self.system_monitor.simulate_key_press(char)
            print("模拟输入完成")
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}文字已输入完成,还有什么需要我帮忙的吗？")
        elif cmd == "move" and len(args) == 2:
            try:
                x, y = map(int, args)
                result = self.system_monitor.simulate_mouse_move(x, y)  # 有个傻比给变量名写错了
                print(result)  
                print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}鼠标已移动到指定位置,需要我做些什么？")
            except ValueError:
                print("用法: /move x y (x和y必须是整数)")
        elif cmd == "click":
            button = args[0] if args else 'left'
            clicks = int(args[1]) if len(args) > 1 else 1
            self.system_monitor.simulate_click(button, clicks)
            print(f"模拟点击: {button} {clicks}次")
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}已完成点击操作,还需要其他帮助吗？")
        elif cmd == "shortcut" and args:
            self.system_monitor.simulate_shortcut(*args)
            print(f"模拟快捷键: {'+'.join(args)}")
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}快捷键已模拟完成,还有什么需要我做的？")
        elif cmd == "open" and args:
            self.system_monitor.open_file(args[0])
            print(f"尝试打开文件: {args[0]}")
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}文件已打开,需要进一步的帮助吗？")
        elif cmd == "cmd" and args:
            result = self.system_monitor.execute_cmd(" ".join(args))
            print(f"命令执行结果:\n{result}")
            print(f"\n{Fore.BLUE}{self.persona.get('name','AI')}: {Style.RESET_ALL}命令已执行完毕,还需要执行其他命令吗？")
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

