# Neuro-bot-recode
基于MaiBot产生灵感的神金Neuro-bot

> [!WARNING]
> 我在4月27日的更新中添加了bot可以调用系统权限的方法，谨慎使用，开发者不对AI造成的结果负任何责任

## 功能特性

- 基于deepseek-chat大语言模型的对话系统
- 可调用系统权限执行命令
- 完整的进程管理功能
- 模拟人类行为的输入控制(键盘、鼠标)
- 支持摄像头操作
- 知识库管理系统
- 内容过滤系统
- 对话历史记录

## 主要命令

- `/switch 后端` - 切换API后端
- `/model 模型` - 切换模型
- `/persona [名称 特征 背景]` - 设置人设
- `/add 领域 知识` - 添加知识
- `/clear` - 清空对话历史
- `/save` - 保存配置
- `/filter add/remove 关键词` - 添加或移除敏感词
- `/reset` - 重置知识库
- `/system` - 显示系统信息
- `/camera capture [文件名]` - 拍摄照片
- `/camera preview [秒数]` - 打开摄像头预览

## 系统权限功能

- 进程管理(查看、结束进程)
- 文件操作(打开文件和应用程序)
- 模拟输入(键盘输入、鼠标移动、点击)
- 系统监控(CPU、内存使用率等)
- 摄像头控制

## 部署方法

1. 环境要求:
   - Python 3.8+
   - MongoDB Support
   - Windows操作系统

2. 安装依赖:
```bash
python -m venv bot
bot\\Scripts\\activate
pip install -r requirements.txt
```

3. 配置文件:
   - 运行一次bot让它生成config.json
   - 编辑config.json,填入API相关配置:
```json
{
    "default_backend": "deepseek",
    "api_config": {
        "deepseek": {
            "api_key": "你的API密钥",
            "api_base": "https://api.deepseek.com/v1"
        }
    }
}
```

4. 启动bot:
```bash
python main.py
```

## 注意事项

1. 谨慎使用系统权限功能,建议在测试环境下运行
2. API调用可能产生费用,请注意控制使用量
3. 建议定期备份知识库数据
4. 确保给予足够的系统权限以执行相关操作

## 文件结构

```
.
├── main.py                 # 主程序
├── config.json            # 配置文件
├── README.md             # 说明文档
└── src/
    ├── constants.py      # 常量定义
    └── modules/
        ├── filter.py     # 内容过滤
        ├── knowledge.py  # 知识库管理
        ├── memories.py   # 记忆系统
        ├── pc_permissions.py # 系统权限
        └── prompt_builder.py # 提示词构建
```

## 开发计划

- [ ] 完善记忆系统
- [ ] 添加更多系统控制功能
- [ ] 优化知识库管理
- [ ] 添加语音交互功能
- [ ] 改进人设系统

## 许可证

本项目采用GPL-3.0 License