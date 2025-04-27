import psutil
import platform
import logging
import pyautogui
import random
import time
import os
import subprocess
from typing import Dict, Union, List
import math
import cv2 # 孩子们我要半夜偷偷开摄像头拍照片了

class SystemMonitor:
    WINDOWS_APPS = {
        'notepad.exe': 'notepad',
        'calc.exe': 'calc',
        'mspaint.exe': 'mspaint',
        'write.exe': 'write',
        'wordpad.exe': 'wordpad',
        'cmd.exe': 'cmd',
        'control.exe': 'control',
        'explorer.exe': 'explorer'
    }
    
    def __init__(self):
        self.logger = logging.getLogger('system_monitor')
        self.enabled = True
        pyautogui.FAILSAFE = False  
        pyautogui.PAUSE = 0.1  
        
    def get_safe_system_info(self) -> Dict:
        try:
            screen_width, screen_height = self.get_screen_size()
            mouse_x, mouse_y = self.get_mouse_position()
            info = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'python_version': platform.python_version(),
                'system': platform.system(),
                'machine': platform.machine(),
                'screen_size': f"{screen_width}x{screen_height}",
                'mouse_position': f"({mouse_x}, {mouse_y})",
                'running_processes': len(psutil.pids())  
            }
            self.logger.info('Retrieved system information')
            return info
            
        except Exception as e:
            self.logger.error(f'Error getting system info: {e}')
            return {}

    def simulate_typing(self, text: str):
        """模拟哈基人输入文字"""
        try:
            for char in text:
                if char in ',.?!;:':
                    time.sleep(random.uniform(0.3, 0.5))
                elif char == ' ':
                    time.sleep(random.uniform(0.1, 0.2))
                typing_speed = random.uniform(0.05, 0.15)
                if random.random() < 0.05:
                    time.sleep(random.uniform(0.5, 1.0))
                pyautogui.write(char, interval=typing_speed)
            return "已完成输入"
        except Exception as e:
            return f"输入失败: {str(e)}"

    def simulate_mouse_move(self, x: int, y: int):
        """模拟哈基人移动鼠标"""
        try:
            current_x, current_y = pyautogui.position()
            distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
            duration = min(2.0, max(0.3, distance / 1000.0))
            
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)
            
            pyautogui.moveTo(x, y, duration=duration)
            return f"已移动到 ({x}, {y})"
        except Exception as e:
            return f"移动失败: {str(e)}"

    def simulate_click(self, button: str = 'left', clicks: int = 1):
        """模拟哈基人点击鼠标"""
        try:
            for _ in range(clicks):
                pyautogui.click(button=button)
                if clicks > 1:
                    time.sleep(random.uniform(0.1, 0.2))
            return f"已点击 {clicks} 次"
        except Exception as e:
            return f"点击失败: {str(e)}"

    def open_file(self, file_path: str):
        """打开文件或系统应用"""
        try:
            if file_path.lower() in ['taskmgr.exe', 'explorer.exe']:
                # 哈基bot调用应用的底层代码
                try:
                    # if 普通模式运行 成功
                    subprocess.Popen([file_path], 
                                  creationflags=subprocess.CREATE_NEW_CONSOLE if file_path.lower() == 'taskmgr.exe' else 0)
                except PermissionError:
                    # else 管理员模式 开启哈基bot脊背龙形态对着win11哈气
                    subprocess.run(['powershell', 'Start-Process', file_path, '-Verb', 'RunAs'], 
                                 capture_output=True,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                return f"已启动 {file_path}"
            elif os.path.exists(file_path):
                os.startfile(file_path)
                return f"已打开 {file_path}"
            else:
                # 尝试作为Windows应用名处理
                app_name = file_path.lower()
                if app_name in self.WINDOWS_APPS:
                    subprocess.Popen(self.WINDOWS_APPS[app_name])
                    return f"已启动应用 {app_name}"
                return f"找不到文件或应用: {file_path}"
        except Exception as e:
            self.logger.error(f'Failed to open file/app: {e}')
            return f"打开失败: {str(e)}"

    def simulate_shortcut(self, *keys):
        """模拟哈基人按下快捷键"""
        try:
            modifiers = {'ctrl', 'alt', 'shift', 'win'}
            mod_keys = [k for k in keys if k.lower() in modifiers]
            other_keys = [k for k in keys if k.lower() not in modifiers]
            
            for key in mod_keys:
                pyautogui.keyDown(key)
                time.sleep(random.uniform(0.05, 0.1))  
            
            for key in other_keys:
                pyautogui.press(key)
                time.sleep(random.uniform(0.1, 0.2))  
            
            for key in reversed(mod_keys):
                pyautogui.keyUp(key)
                time.sleep(random.uniform(0.05, 0.1))
            
            return f"已执行快捷键: {'+'.join(keys)}"
        except Exception as e:
            return f"快捷键执行失败: {str(e)}"

    def get_screen_size(self) -> tuple:
        """获取屏幕尺寸"""
        try:
            width, height = pyautogui.size()
            self.logger.info(f"Screen size: {width}x{height}")
            return (width, height)
        except Exception as e:
            self.logger.error(f"Error getting screen size: {e}")
            return (1920, 1080)  

    def draw_circle(self, radius: int = 100, duration: float = 0.05):
        """绘制圆形"""
        try:
            screen_width, screen_height = self.get_screen_size()
            current_x, current_y = self.get_mouse_position()
            
            radius = min(radius, 
                        min(current_x, screen_width - current_x),
                        min(current_y, screen_height - current_y))
            
            points = 36  
            for i in range(points + 1):
                angle = 2 * math.pi * i / points
                x = int(current_x + radius * math.cos(angle))
                y = int(current_y + radius * math.sin(angle))
                self.simulate_mouse_move(x, y)  
            return "已完成绘制"
        except Exception as e:
            return f"绘制失败: {str(e)}"

    def get_mouse_position(self) -> tuple:
        """获取哈基光标位置"""
        try:
            x, y = pyautogui.position()
            return (x, y)
        except Exception as e:
            self.logger.error(f"获取鼠标位置失败: {e}")
            return (0, 0)

    def execute_cmd(self, command: str) -> str:
        """直接执行命令行命令,无限制"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='gbk',  # 使用GBK编码以支持中文输出
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout or result.stderr or "命令执行完成"
            self.logger.info(f'Executed command: {command}')
            return output
        except Exception as e:
            self.logger.error(f'Command execution failed: {e}')
            return f"执行失败: {str(e)}"

    def get_process_list(self) -> List[Dict]:
        """获取完整进程列表"""
        try:
            process_list = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time', 'status', 'username']):
                try:
                    process_info = {
                        'pid': proc.info['pid'], # avp.exe：不是牢底你有什么实力啊结束我进程，直接给我坐下！(kaspersky：删除了一个傻比)
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent'],
                        'status': proc.info['status'],
                        'user': proc.info['username'],
                        'created': time.strftime('%Y-%m-%d %H:%M:%S', 
                                               time.localtime(proc.info['create_time']))
                    }
                    process_list.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            self.logger.info(f'Retrieved full process list: {len(process_list)} processes')
            return sorted(process_list, key=lambda x: x['cpu'], reverse=True)
        except Exception as e:
            self.logger.error(f'Error getting process list: {e}')
            return []

    def kill_process(self, target: Union[str, int]) -> str:
        """炸飞指定进程"""
        try:
            if isinstance(target, int):
                proc = psutil.Process(target)
            else:
                # 查找任务管理器给的KGB肃反名单上面的进程名字
                found = False
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == target.lower():
                        found = True
                        break
                if not found:
                    return f"未找到进程: {target}"
            
            proc.terminate()
            time.sleep(1)  # 等待进程结束
            if proc.is_running():
                proc.kill()  # 强制结束
            
            return f"已终止进程: {target}"
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return f"无法终止进程: {str(e)}"
        except Exception as e:
            return f"操作失败: {str(e)}"

    def get_performance_info(self) -> Dict:
        """哈基bot: byd你这啥电脑"""
        try:
            cpu_info = {
                'usage': psutil.cpu_percent(interval=1),
                'freq': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else 'N/A'
            }
            
            memory = psutil.virtual_memory()
            memory_info = {
                'total': f"{memory.total / (1024**3):.2f}GB",
                'used': f"{memory.used / (1024**3):.2f}GB",
                'percent': memory.percent
            }
            
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': f"{disk.total / (1024**3):.2f}GB",
                'used': f"{disk.used / (1024**3):.2f}GB",
                'percent': disk.percent
            }
            
            self.logger.info('Retrieved performance information')
            return {
                'cpu': cpu_info,
                'memory': memory_info,
                'disk': disk_info
            }
        except Exception as e:
            self.logger.error(f'Error getting performance info: {e}')
            return {}

    def open_new_cmd(self, admin: bool = False) -> str:
        """打开新的cmd窗口"""
        try:
            if admin:
                subprocess.Popen(['runas', '/user:Administrator', 'cmd.exe'])
            else:
                subprocess.Popen('cmd.exe', creationflags=subprocess.CREATE_NEW_CONSOLE)
            return "已打开新的命令提示符窗口"
        except Exception as e:
            return f"打开失败: {str(e)}"

    def camera_capture(self, save_path: str = "capture.jpg") -> str:
        """孩子们我要偷拍你了哦"""
        try:
            cap = cv2.VideoCapture(0)  # 打开默认摄像头
            if not cap.isOpened():
                return "无法访问摄像头"
            
            ret, frame = cap.read()  # 拍摄一帧
            cap.release()  # 拍完就跑
            
            if ret:
                cv2.imwrite(save_path, frame)
                return f"已保存照片到: {save_path}"
            else:
                return "拍摄失败"
        except Exception as e:
            return f"摄像头操作失败: {str(e)}"

    def camera_preview(self, duration: int = 5) -> str:
        """打开摄像头预览指定秒数"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "无法访问摄像头"
            
            start_time = time.time()
            while (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if ret:
                    cv2.imshow('Camera Preview', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
            cap.release()
            cv2.destroyAllWindows()
            return "预览已完成"
        except Exception as e:
            return f"预览失败: {str(e)}"

    def __str__(self):
        info = self.get_safe_system_info()
        return f"System Info:\n" + \
               f"CPU Usage: {info.get('cpu_percent')}%\n" + \
               f"Memory Usage: {info.get('memory_percent')}%"

