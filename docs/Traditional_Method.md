## 📦方法三：传统安装方式（适合开发者）
### 📋 环境要求
- Python 3.8+
- 500MB以上的可用存储空间
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
编辑`.env`文件，填写API_KEY（将里面所有的`your_api_key_here`替换成你的API密钥）。

需前往[硅基流动平台](https://cloud.siliconflow.cn/i/mVqMyTZk)申请你的API Key；
如果使用其他平台或模型，需要替换对应的API_BASE_URL和MODEL