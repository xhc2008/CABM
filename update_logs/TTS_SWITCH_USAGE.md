# TTS开关功能使用说明

## 功能概述
已为TTS（文本转语音）功能添加了开关控制，可以方便地启用或禁用TTS功能。

## 开关变量位置
- **文件**: `static/js/main.js`
- **变量**: `window.ttsEnabled`
- **默认值**: `true` (开启状态)

## 使用方法

### 1. 直接修改变量
```javascript
// 关闭TTS
window.ttsEnabled = false;

// 开启TTS
window.ttsEnabled = true;
```

### 2. 使用控制函数
```javascript
// 切换TTS状态（开启↔关闭）
window.toggleTTS();

// 设置TTS状态
window.setTTS(true);   // 开启
window.setTTS(false);  // 关闭
```

### 3. 在浏览器控制台中测试
1. 打开浏览器开发者工具 (F12)
2. 在控制台中输入：
   ```javascript
   window.toggleTTS()  // 切换TTS状态
   ```
3. 或者直接设置：
   ```javascript
   window.ttsEnabled = false  // 关闭TTS
   ```

## 功能效果
- **开启时**: 正常播放TTS音频，包括用户主动播放和自动播放
- **关闭时**: 
  - 跳过所有TTS请求，不向后端发送TTS API调用
  - 用户点击播放按钮时显示"TTS功能已关闭"提示
  - 自动播放被静默跳过，不显示错误信息
  - 音频预加载也会被跳过

## 日后UI集成
该开关已设计为变量形式，方便日后在UI界面中添加开关按钮：
- 可以绑定到设置页面的开关控件
- 可以添加到主界面的快捷开关
- 状态会实时生效，无需重新加载页面

## 修改的文件
1. `static/js/main.js` - 添加开关变量和控制函数
2. `static/js/audio-service.js` - 在`playAudio`和`prefetchAudio`函数中添加开关判断