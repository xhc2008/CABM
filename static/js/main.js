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
        console.log('开始初始化CABM应用...');
        
        // 加载角色数据
        loadCharacters();

        // 绑定页面切换事件
        startButton.addEventListener('click', showChatPage);
        backButton.addEventListener('click', confirmBackToHome);
        exitButton.addEventListener('click', confirmExit);

        // 绑定对话事件
        // sendButton 的点击事件已经在 input-enhancements.js 中处理
        playaudioButton.addEventListener('click', () => playAudio(getCurrentCharacter(), false)); // 用户主动播放
        backgroundButton.addEventListener('click', changeBackground);
        historyButton.addEventListener('click', toggleHistory);
        closeHistoryButton.addEventListener('click', toggleHistory);
        characterButton.addEventListener('click', toggleCharacterModal);
        closeCharacterButton.addEventListener('click', toggleCharacterModal);
        continueButton.addEventListener('click', continueOutput);
        //skipButton.addEventListener('click', skipTyping);
        micButton.addEventListener('click', () => toggleRecording(messageInput, micButton, showError));
        errorCloseButton.addEventListener('click', hideError);

        // 绑定确认对话框事件
        confirmYesButton.addEventListener('click', handleConfirmYes);
        confirmNoButton.addEventListener('click', handleConfirmNo);
        closeConfirmButton.addEventListener('click', hideConfirmModal);

        // 键盘快捷键已经在 input-enhancements.js 中处理

        // 绑定点击事件继续输出
        currentMessage.addEventListener('click', continueOutput);
        clickToContinue.addEventListener('click', continueOutput);
        
        console.log('CABM应用初始化完成');
    } catch (error) {
        console.error('初始化失败:', error);
        showError(`初始化失败: ${error.message}`);
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
window.stopCurrentAudio = stopCurrentAudio;
window.showError = showError;
