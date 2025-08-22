// 对话页面的初始化和事件绑定
import { 
    sendMessage, 
    changeBackground, 
    continueOutput, 
    skipTyping 
} from './chat-service.js';

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
    showError,
    hideError,
    toggleHistory,
    handleConfirmYes,
    handleConfirmNo,
    hideConfirmModal
} from './ui-service.js';

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('开始初始化对话页面...');
        
        // 加载角色数据
        loadCharacters();

        // 绑定按钮事件
        const playAudioButton = document.getElementById('playaudioButton');
        const backgroundButton = document.getElementById('backgroundButton');
        const historyButton = document.getElementById('historyButton');
        const closeHistoryButton = document.getElementById('closeHistoryButton');
        const characterButton = document.getElementById('characterButton');
        const closeCharacterButton = document.getElementById('closeCharacterButton');
        const continueButton = document.getElementById('continueButton');
        const micButton = document.getElementById('micButton');
        const errorCloseButton = document.getElementById('errorCloseButton');
        const messageInput = document.getElementById('messageInput');
        const currentMessage = document.getElementById('currentMessage');
        const clickToContinue = document.getElementById('clickToContinue');

        // 绑定对话事件
        playAudioButton?.addEventListener('click', () => playAudio(getCurrentCharacter(), false));
        backgroundButton?.addEventListener('click', changeBackground);
        historyButton?.addEventListener('click', toggleHistory);
        closeHistoryButton?.addEventListener('click', toggleHistory);
        characterButton?.addEventListener('click', toggleCharacterModal);
        closeCharacterButton?.addEventListener('click', toggleCharacterModal);
        continueButton?.addEventListener('click', continueOutput);
        micButton?.addEventListener('click', () => toggleRecording(messageInput, micButton, showError));
        errorCloseButton?.addEventListener('click', hideError);

        // 绑定确认对话框事件
        const confirmYesButton = document.getElementById('confirmYesButton');
        const confirmNoButton = document.getElementById('confirmNoButton');
        const closeConfirmButton = document.getElementById('closeConfirmButton');

        confirmYesButton?.addEventListener('click', handleConfirmYes);
        confirmNoButton?.addEventListener('click', handleConfirmNo);
        closeConfirmButton?.addEventListener('click', hideConfirmModal);

        // 绑定点击事件继续输出
        currentMessage?.addEventListener('click', continueOutput);
        clickToContinue?.addEventListener('click', continueOutput);
        
        console.log('对话页面初始化完成');
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
window.ttsEnabled = true; // 默认开启TTS
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
import { showOptionButtons } from './ui-service.js';
window.showOptionButtons = showOptionButtons;
window.playAudio = (autoPlay = false) => playAudio(getCurrentCharacter(), autoPlay);
window.playTextAudio = (text, autoPlay = false) => playTextAudio(text, getCurrentCharacter(), autoPlay);
window.stopCurrentAudio = stopCurrentAudio;
window.showError = showError;
