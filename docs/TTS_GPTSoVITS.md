# TTS更换GPT-SoVITS指南

## 📋 概述

本文讲述了TTS如何更换GPT-SoVITS以及一些注意事项

## 🛠️ 环境准备
### 系统要求

- GPU GeForceMX330以上或CPU i5 10代以上
- conda 环境管理GPT-SoVITS的python版本不同

如果你的电脑不行，也可以考虑租卡
这家组卡支持租Windows系统[看看~~腿~~](https://gpu.spacehpc.com/user/register?inviteCode=83929273)
### 安装 GPT-SoVITS

接着看什么，去官方仓库！
[GPT-SoVITS官方仓库](https://github.com/RVC-Boss/GPT-SoVITS)

### 启用 API服务

进入环境，启动API服务


```bash
python api_v2.py
```

这就是官方的API服务

但是由于软件特殊所以我修改了API的代码

所以你需要把`api_v2.py`换成本项目里面的`replace\api_v2.py`

替换之后，启动API服务，允许使用原版API相同的方式更改端口

```bash
python api_v2.py
```

### 配置角色

你需要手动创建`role`文件夹存放参考音频

我配置的[银狼的模型V4](https://www.modelscope.cn/models/leletxh/Silver_Wolf_GPT-SoVITS_Model/files)为例

在`role`文件夹下创建`银狼`文件夹

文件夹内必须包含两个文件`config.json`与`xxx.wav`

config.json
```json
{
    "ref_audio":"n6azcsya5ds8jnuvq1ijslpi09hzbde.wav",//参考音频名字
    "ref_text":"骇入空间站的时候，我随手改了下螺丝咕姆的画像，不过…最后还是改回去了",//参考音频的文本
    "ref_lang":"zh"//参考文本的语言
}
```

当然有能力的你也可以炼制模型增加声音的还原程度

config.json
```json
{
    "ref_audio":"n6azcsya5ds8jnuvq1ijslpi09hzbde.wav",//参考音频名字
    "ref_text":"骇入空间站的时候，我随手改了下螺丝咕姆的画像，不过…最后还是改回去了",//参考音频的文本
    "ref_lang":"zh",//参考文本的语言
    "gpt":"银狼-V4-e30.ckpt",//GPT模型
    "sovits":"银狼-V4_e8_s688_l32.pth"//SoVITS模型
}
```

### 配置环境

最后你需要在`.env`配置好环境

如下

```base
TTS_SERVICE_URL_GPTSoVITS=http://127.0.0.1:9880 #API地址/端口
TTS_SERVICE_URL_SiliconFlow= 不用写/删掉
TTS_SERVICE_API_KEY=不用写/删掉
TTS_SERVICE_METHOD=GPT-SoVITS
```