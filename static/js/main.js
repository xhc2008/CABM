// 主入口文件 - 事件绑定和初始化

// TTS开关变量 - 控制是否启用TTS功能
window.ttsEnabled = true; // 默认开启TTS，设为false可关闭TTS功能

import { 
    startButton, 
    backButton, 
    exitButton, 
    sendButton, 
    playaudioButton, 
    backgroundButton, 
    historyButton, 
    closeHistoryButton, 
    characterButton, 
    closeCharacterButton, 
    continueButton, 
   // skipButton, 
    micButton, 
    errorCloseButton, 
    confirmYesButton, 
    confirmNoButton, 
    closeConfirmButton, 
    messageInput,
    currentMessage,
    clickToContinue
} from './dom-elements.js';

import { 
    showChatPage, 
    confirmBackToHome, 
    confirmExit, 
    toggleHistory, 
    hideError, 
    handleConfirmYes, 
    handleConfirmNo, 
    hideConfirmModal,
    showOptionButtons,
    showError
} from './ui-service.js';

import { 
    loadCharacters, 
    toggleCharacterModal, 
    getCurrentCharacter 
} from './character-service.js';

import { 
    playAudio, 
    playTextAudio,
    toggleRecording,
    stopCurrentAudio
} from './audio-service.js';

import { 
    sendMessage, 
    changeBackground, 
    continueOutput, 
    skipTyping 
} from './chat-service.js';

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
    showError(`发生错误: ${event.error.message}`);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
    showError(`请求失败: ${event.reason}`);
});

// 初始化

document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('主页初始化...');
        // 主页只需要绑定主页按钮
        // 主页按钮跳转已用<a>标签实现，无需JS跳转
        exitButton?.addEventListener('click', () => {
            window.close();
        });
        console.log('主页初始化完成');
    } catch (error) {
        console.error('主页初始化失败:', error);
    }
});

// 注册快捷键
function registrationShortcuts(config) {
    document.addEventListener('keydown', e => {
        if (e.key in config) {
            if (e.key.length === 1) {
                if (e.altKey) {
                    config[e.key]();
                }
            } else {
                config[e.key]();
            }
        }
    });
}

registrationShortcuts({
    Enter: continueOutput,
    s: skipTyping,
    h: toggleHistory,
    b: changeBackground
});

// TTS开关控制函数
window.toggleTTS = function() {
    window.ttsEnabled = !window.ttsEnabled;
    console.log(`TTS已${window.ttsEnabled ? '开启' : '关闭'}`);
    return window.ttsEnabled;
};

window.setTTS = function(enabled) {
    window.ttsEnabled = !!enabled;
    console.log(`TTS已${window.ttsEnabled ? '开启' : '关闭'}`);
    return window.ttsEnabled;
};

// 暴露必要的函数给全局使用
window.getCurrentCharacter = getCurrentCharacter;
window.showOptionButtons = showOptionButtons;
window.playAudio = (autoPlay = false) => playAudio(getCurrentCharacter(), autoPlay);
window.playTextAudio = (text, autoPlay = false) => playTextAudio(text, getCurrentCharacter(), autoPlay);
window.stopCurrentAudio = stopCurrentAudio;
window.showError = showError;
