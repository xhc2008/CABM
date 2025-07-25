# CABM - Code Afflatus & Beyond Matter

"当灵性注入载体，它便挣脱物质躯壳，抵达超验之境。"

~~（不就是个Gal吗）~~
> ## **⚠️ 注意：本项目目前处于开发阶段，核心功能尚未实现，其他的功能和优化也正在进行中。欢迎贡献代码或提出建议。**

## 开发状态

**已完成功能：**
- 基本的AI对话功能，包含最近的历史记录
- 前端的主页面（但是极简风）
- 角色系统（可切换不同角色）
- 分段流式输出（灵魂所在~）
- 很多的bug

**正在开发：**
- 修bug
- 场景切换（让AI切换场景或生成新场景）
- 记忆系统（使用向量数据库长期保存记忆）
- 故事模式（根据大纲推动故事发展，区别于“闲聊模式”）
- 角色的表情/动作（蹲一个免费的画师）
- ~~角色语音~~（硬件受限，等我换个有独显的电脑再说）


## 项目简介

CABM是一个AI对话应用，具有动态生成的背景图片功能。用户可以与AI模型进行对话交流，同时应用会使用图像生成模型创建的图片作为动态背景，提供更丰富的视觉体验。应用支持多角色系统，可以切换不同的AI角色进行对话。

~~人话：AI驱动的Galgame~~

> ## *以下内容由AI生成，~~纯属瞎扯~~仅供参考*

## 功能特点

- 与AI模型进行自然对话，支持流式输出（打字机效果）
- 多角色系统，可切换不同的AI角色
- 动态生成背景图片，提供沉浸式体验
- 角色立绘显示，增强视觉效果
- 对话历史记录查看
- 响应式设计，适配不同设备

## 安装说明

### 1. 安装依赖

使用 pip 安装项目依赖：

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install flask requests python-dotenv
```

### 2. 配置环境变量

复制`.env.example`文件为`.env`，并填写API密钥和URL：

```bash
cp .env.example .env
```
需前往[硅基流动平台](https://cloud.siliconflow.cn/i/mVqMyTZk)申请你的API Key；
如果使用其他平台，需要替换对应的API_URL

编辑`.env`文件，填写以下信息：

```
# 对话API配置
CHAT_API_URL=https://api.siliconflow.cn/v1/chat/completions
CHAT_API_KEY=your_chat_api_key_here

# 图像生成API配置
IMAGE_API_URL=https://api.siliconflow.cn/v1/images/generations
IMAGE_API_KEY=your_image_api_key_here

# 应用配置
DEBUG=False
PORT=5000
HOST=0.0.0.0
```

## 使用说明

### 启动应用

#### Windows

双击 `start.bat` 文件或在命令行中运行：

```cmd
start.bat
```

#### Linux/macOS

确保脚本有执行权限：

```bash
chmod +x start.sh
```

然后运行：

```bash
./start.sh
```

#### 高级选项

你也可以直接使用Python启动脚本，并传递额外的参数：

```bash
python start.py --host 127.0.0.1 --port 8080 --debug --no-browser
```

可用参数：
- `--host`: 指定主机地址（默认为配置文件中的值）
- `--port`: 指定端口号（默认为配置文件中的值）
- `--debug`: 启用调试模式
- `--no-browser`: 不自动打开浏览器

启动后，应用会自动在浏览器中打开，或者你可以手动访问：`http://localhost:5000`

### 基本操作

- **发送消息**：在右上角输入框中输入消息，点击"发送"按钮或按回车键发送
- **查看历史**：点击"历史"按钮查看完整对话历史
- **切换角色**：点击"角色"按钮选择不同的AI角色
- **清空对话**：点击"清空对话"按钮重置对话历史
- **更换背景**：点击"更换背景"按钮生成新的背景图片
- **自动/手动模式**：点击"自动"按钮切换打字机效果的自动/手动模式
- **跳过打字**：在自动模式下，点击"跳过"按钮可以立即显示完整回复

## 项目结构

```
cabm/
├── .env                  # 环境变量（API密钥等）
├── .env.example          # 环境变量示例文件
├── .gitignore            # Git忽略文件
├── requirements.txt      # Python依赖包列表
├── config.py             # 配置文件
├── app.py                # 主应用入口
├── start.py              # 启动脚本
├── start.bat             # Windows启动批处理文件
├── start.sh              # Linux/macOS启动脚本
├── stream.py             # 分段流式输出的demo
├── characters/           # 角色配置
│   ├── __init__.py       # 角色管理模块
│   ├── Silver_Wolf.py    # 银狼角色配置
│   └── lingyin.py        # 灵音角色配置
├── static/               # 静态资源
│   ├── css/              # 样式文件
│   ├── js/               # JavaScript文件
│   └── images/           # 图片资源和缓存
├── templates/            # HTML模板
├── services/             # 服务组件
│   ├── chat_service.py   # 对话服务
│   ├── image_service.py  # 图像服务
│   ├── config_service.py # 配置服务
│   └── scene_service.py  # 场景服务
├── utils/                # 工具函数
│   ├── api_utils.py      # API工具
│   ├── env_utils.py      # 环境变量工具
│   └── history_utils.py  # 历史记录工具
└── data/                 # 数据存储
    ├── history/          # 对话历史记录
    ├── images/           # 图片存储
    └── scenes/           # 场景数据
```

## 注意事项

- 图像API生成的图片URL有效期为一小时，应用会自动下载并存储图片
- 默认情况下，应用会清理超过24小时的旧图片，最多保留20张图片
- 如果图像API调用失败，应用会使用缓存的图片作为背景
- 角色图片需要放置在`static/images/`目录下，并在角色配置文件中指定路径
- 默认角色设置在`characters/__init__.py`文件中的`_default_character_id`变量

## 自定义角色

你可以通过创建新的角色配置文件来添加自定义角色。在`characters/`目录下创建一个新的Python文件，按照以下格式定义角色：

```python
# 角色基本信息
CHARACTER_ID = "your_character_id"
CHARACTER_NAME = "角色名称"
CHARACTER_NAME_EN = "Character Name"

# 角色外观
CHARACTER_IMAGE = "static/images/your_character.png"  # 角色立绘路径
CHARACTER_COLOR = "#ffeb3b"  # 角色名称颜色

# 角色设定
CHARACTER_DESCRIPTION = """
角色的简短描述
"""

# AI系统提示词
CHARACTER_PROMPT = """
详细的角色设定和提示词，用于指导AI生成符合角色特点的回复
"""

# 角色欢迎语
CHARACTER_WELCOME = "角色的欢迎语"

# 角色对话示例
CHARACTER_EXAMPLES = [
    {"role": "user", "content": "示例问题1"},
    {"role": "assistant", "content": "示例回答1"},
    # 更多示例...
]

# 获取角色配置
def get_character_config():
    """获取角色配置"""
    return {
        "id": CHARACTER_ID,
        "name": CHARACTER_NAME,
        "name_en": CHARACTER_NAME_EN,
        "image": CHARACTER_IMAGE,
        "color": CHARACTER_COLOR,
        "description": CHARACTER_DESCRIPTION,
        "prompt": CHARACTER_PROMPT,
        "welcome": CHARACTER_WELCOME,
        "examples": CHARACTER_EXAMPLES
    }
```

## 贡献

欢迎提交Pull Request或Issue来帮助改进这个项目。

## 许可证

[MIT License](LICENSE)