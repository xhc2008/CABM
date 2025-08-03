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
- 记忆系统（使用向量数据库长期保存记忆）
- AI生成选项
- 角色的表情（后面或许会换成3D模型）
- ~~语音输入~~（问题太多了，目前几乎用不了）
- 很多的bug

**正在开发：**
- 用户画像（角色对用户的印象）
- 场景切换（让AI切换场景或生成新场景）
- 故事模式（根据大纲推动故事发展，区别于“闲聊模式”）
- 角色的自我认知
- 角色动作
- 更多的角色
- ~~记忆权重，记忆遗忘~~（意义不大，暂不考虑）
- 更多的bug


## 项目简介

CABM是一个AI对话应用，具有动态生成的背景图片功能。用户可以与AI模型进行对话交流，同时应用会使用图像生成模型创建的图片作为动态背景，提供更丰富的视觉体验。应用支持多角色系统，可以切换不同的AI角色进行对话。

~~人话：AI驱动的Galgame~~

## 声明
- 本项目为个人非营利性兴趣项目，无意且不参与任何形式的同业竞争。
- 本项目采用GNU通用公共许可证(GPL)开源协议，禁止闭源商业化改造。详见[GNU General Public License v3.0](LICENSE)
- 使用者需自行承担因调用第三方AI服务产生的API费用，此类费用与项目作者无关
- 本项目涉及人工智能生成内容，作者不对AI生成内容的准确性、合法性及可能引发的后果承担任何责任。
- 欢迎提出建设性意见或提交Pull Requests，但作者保留是否采纳的最终决定权，建议提前和作者联系。
- 作者保留对本声明条款的最终解释权及修改权。

## 功能特点

- 与AI模型进行自然对话，支持流式输出（打字机效果）
- 多角色系统，可切换不同的AI角色
- 动态生成背景图片，提供沉浸式体验
- 角色立绘显示，增强视觉效果
- 对话历史记录查看
- 响应式设计，适配不同设备

## 安装说明
>注：`点我开始使用.bat`尚未测试，可能无法使用，请按照下面的步骤操作
### 1. 安装依赖


使用 pip 安装项目依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制`.env.example`文件为`.env`，并填写API密钥和URL：

```bash
cp .env.example .env
```
编辑`.env`文件，填写API_KEY。
需前往[硅基流动平台](https://cloud.siliconflow.cn/i/mVqMyTZk)申请你的API Key；
如果使用其他平台或模型，需要替换对应的API_BASE_URL和MODEL

注意：如果使用`GPT-SoVITS`作为语音合成，请下载`GPT-SoVITS`整合包并把`api_v2.py`换成`\replace\api_v2.py`然后启动
在整合包根目录创建`role`文件夹，创建对应角色的文件夹，添加`config.json`
[示例（银狼的模型V4）](https://www.modelscope.cn/models/leletxh/Silver_Wolf_GPT-SoVITS_Model/files)
需要在环境中把`siliconflow`换成`GPT-SoVITS`
> **如果你有独立显卡，建议使用GPT-SoVITS，因为远程API很贵**
---
>## *以下内容尚未进行人工校对，如有疑问请咨询作者*

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

启动后，应用会自动在浏览器中打开。程序会智能选择最合适的本地IP地址（优先使用192.168开头的地址），确保在各种浏览器中都能正常访问。

你也可以手动访问以下地址：
- 本地访问：`http://localhost:5000` 或 `http://127.0.0.1:5000`
- 局域网访问：`http://[你的本地IP]:5000`（启动时会显示具体地址）

### 基本操作

- **发送消息**：在右上角输入框中输入消息，点击"发送"按钮或按回车键发送
- **查看历史**：点击"历史"按钮查看完整对话历史
- **切换角色**：点击"角色"按钮选择不同的AI角色
- **播放语音**：点击"播放语音"按钮再次播放语音
- **更换背景**：点击"更换背景"按钮生成新的背景图片
- **自动/手动模式**：点击"自动"按钮切换打字机效果的自动/手动模式
- **跳过打字**：在自动模式下，点击"跳过"按钮可以立即显示完整回复

## 项目结构

```
cabm/
├── .env                     # 环境变量（API密钥等）
├── .env.example             # 环境变量示例文件
├── .gitignore               # Git忽略文件
├── requirements.txt         # Python依赖包列表
├── environment.yaml         # Conda环境配置文件
├── config.py                # 配置文件
├── app.py                   # 主应用入口
├── run.py                   # 运行脚本
├── start.py                 # 启动脚本
├── start.bat                # Windows启动批处理文件
├── start.sh                 # Linux/macOS启动脚本
├── build.ps1                # PowerShell构建脚本
├── 点我开始使用.bat          # 中文启动批处理文件
├── log.txt                  # 日志文件
├── README.md                # 项目说明文档
├── CONTRIBUTING.md          # 贡献指南
├── LICENSE                  # 开源许可证
├── characters/              # 角色配置
│   ├── __init__.py          # 角色管理模块
│   ├── Silver_Wolf.py       # 银狼角色配置
│   └── lingyin.py           # 灵音角色配置
├── services/                # 服务组件
│   ├── chat_service.py      # 对话服务
│   ├── image_service.py     # 图像服务
│   ├── config_service.py    # 配置服务
│   ├── memory_service.py    # 记忆服务
│   ├── option_service.py    # 选项服务
│   ├── scene_service.py     # 场景服务
│   └── ttsapi_service.py    # TTS语音合成服务
├── utils/                   # 工具函数
│   ├── __init__.py          # 工具模块初始化
│   ├── api_utils.py         # API工具
│   ├── env_utils.py         # 环境变量工具
│   ├── history_utils.py     # 历史记录工具
│   ├── memory_utils.py      # 记忆工具
│   ├── network_utils.py     # 网络工具
│   ├── prompt_logger.py     # 提示词日志工具
│   └── RAG/                 # 检索增强生成模块
│       ├── __init__.py      # RAG模块初始化
│       ├── Retriever_all.py # 检索器
│       ├── Multi_Recall/    # 多重召回模块
│       └── Reranker/        # 重排序模块
├── static/                  # 静态资源
│   ├── css/                 # 样式文件
│   │   ├── style.css        # 主样式文件
│   │   ├── stream_styles.css # 流式输出样式
│   │   └── continue-prompt.css # 继续提示样式
│   ├── js/                  # JavaScript文件
│   │   ├── main.js          # 主脚本文件
│   │   └── stream_processor.js # 流式处理脚本
│   └── images/              # 图片资源
│       ├── default/         # 默认图片
│       ├── lingyin/         # 灵音角色图片
│       ├── Silver_Wolf/     # 银狼角色图片
│       └── cache/           # 图片缓存
├── templates/               # HTML模板
│   └── index.html           # 主页面模板
├── data/                    # 数据存储
│   ├── history/             # 对话历史记录
│   ├── images/              # 生成的背景图片存储
│   ├── memory/              # 记忆数据存储
│   ├── scenes/              # 场景数据
│   ├── audio/               # 音频文件
│   ├── ref_audio/           # 参考音频文件
│   └── logo/                # Logo相关文件
├── replace/                 # 替换文件
│   └── api_v2.py            # GPT-SoVITS API替换文件
├── backups/                 # 备份文件
├── temp/                    # 临时文件
├── update_logs/             # 更新日志
│   ├── RAG.md               # RAG功能更新日志
│   ├── TTS.md               # TTS功能更新日志
│   ├── MEMORY_MODULE_IMPLEMENTATION.md # 记忆模块实现日志
│   └── JSON_FORMAT_MIGRATION.md # JSON格式迁移日志
└── .kiro/                   # Kiro IDE配置文件
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
CHARACTER_IMAGE = "static/images/your_character/"  # 角色立绘目录
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
[![Contributors](https://img.shields.io/github/contributors/xhc2008/CABM?color=blue)](https://github.com/xhc2008/CABM/graphs/contributors) 

![Contributors](https://contrib.rocks/image?repo=xhc2008/CABM) 

欢迎提交 Pull Request 或 Issue！~~(但不一定会做)~~

具体贡献流程请参考[CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

[GNU General Public License v3.0](LICENSE)