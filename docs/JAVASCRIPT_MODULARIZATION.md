# JavaScript 模块化改造说明

## 改造概述

原本的 `main.js` 文件（1746行）已经按功能拆分成以下模块：

## 文件结构

### 1. `dom-elements.js` - DOM元素引用模块
**功能**: 集中管理所有DOM元素的引用
**内容**:
- 页面元素 (homePage, chatPage, 按钮等)
- 对话元素 (characterName, currentMessage, messageInput等)
- 模态框元素 (historyModal, characterModal, confirmModal等)
- 加载和错误元素

### 2. `audio-service.js` - 音频服务模块
**功能**: 处理所有音频相关功能
**主要函数**:
- `playAudio()` - 播放TTS音频
- `prefetchAudio()` - 预加载音频到缓存
- `stopCurrentAudio()` - 停止当前播放的音频
- `toggleRecording()` - 语音识别开关

**特性**:
- 音频缓存机制
- 首次播放提示
- 语音识别支持

### 3. `character-service.js` - 角色管理服务模块
**功能**: 管理角色数据和角色相关操作
**主要函数**:
- `loadCharacters()` - 加载可用角色列表
- `selectCharacter()` - 切换角色
- `switchCharacterImage()` - 切换角色图片
- `handleMoodChange()` - 处理表情变化
- `toggleCharacterModal()` - 角色选择弹窗

**数据管理**:
- 当前角色信息
- 可用角色列表
- 角色图片集合

### 4. `ui-service.js` - UI交互服务模块
**功能**: 界面状态管理和交互控制
**主要函数**:
- `updateCurrentMessage()` - 更新当前消息显示
- `addToHistory()` - 添加消息到历史记录
- `showLoading()` / `hideLoading()` - 加载状态控制
- `showError()` / `hideError()` - 错误信息显示
- `showContinuePrompt()` / `hideContinuePrompt()` - 继续提示控制
- `showOptionButtons()` / `hideOptionButtons()` - 选项按钮控制
- `disableUserInput()` / `enableUserInput()` - 用户输入控制
- 页面切换函数
- 确认对话框管理

### 5. `chat-service.js` - 聊天服务模块
**功能**: 处理消息发送和流式响应
**主要函数**:
- `sendMessage()` - 发送消息到后端
- `changeBackground()` - 更换背景
- `continueOutput()` - 继续流式输出
- `skipTyping()` - 跳过打字效果

**特性**:
- 流式响应处理
- 音频预加载
- 表情变化处理
- 选项按钮支持

### 6. `main.js` - 主入口文件
**功能**: 应用初始化和事件绑定
**内容**:
- 导入所有必要模块
- DOM事件监听器绑定
- 快捷键注册
- 全局函数暴露

### 7. `stream_processor.js` - 流式处理器（保持不变）
**功能**: 处理流式数据的分段和控制
**特性**: 独立的类，无需修改

## 模块间依赖关系

```
main.js (入口)
├── dom-elements.js (DOM引用)
├── ui-service.js (UI控制)
│   └── dom-elements.js
├── character-service.js (角色管理)
│   └── dom-elements.js
├── audio-service.js (音频处理)
│   └── dom-elements.js
└── chat-service.js (聊天功能)
    ├── ui-service.js
    ├── character-service.js
    └── audio-service.js
```

## 使用ES模块

- 所有新文件都使用ES6模块语法 (`import`/`export`)
- HTML中使用 `<script type="module">` 引入主文件
- 保持了原有的所有功能

## 优势

1. **代码组织**: 按功能分类，易于理解和维护
2. **模块化**: 每个模块职责单一，便于测试和重用
3. **可维护性**: 修改某个功能只需要关注对应模块
4. **团队协作**: 不同开发者可以同时修改不同模块
5. **代码复用**: 模块可以在其他项目中重用

## 文件备份

- 原始的 `main.js` 文件已重命名为 `main-old.js` 作为备份
- 所有原功能都得到保留和正确映射

## 注意事项

- 由于使用了ES模块，需要通过HTTP服务器访问（不能直接用file://协议）
- 保持了与原有后端API的完全兼容
- 全局变量和函数通过window对象暴露，确保兼容性
