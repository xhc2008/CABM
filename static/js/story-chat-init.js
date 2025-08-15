// 剧情模式聊天页面的初始化和事件绑定
import { 
    changeBackground, 
    continueOutput, 
    skipTyping 
} from './chat-service.js';

import {
    loadCharacters,
    toggleCharacterModal,
    getCurrentCharacter,
    handleMoodChange
} from './character-service.js';

import { 
    playAudio, 
    toggleRecording, 
    stopCurrentAudio,
    prefetchAndPlayAudio
} from './audio-service.js';

import {
    showError,
    hideError,
    toggleHistory,
    handleConfirmYes,
    handleConfirmNo,
    hideConfirmModal
} from './ui-service.js';

// 剧情模式专用的发送消息函数
async function sendStoryMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) {
        showError('请输入消息');
        return;
    }

    if (getIsProcessing()) {
        showError('正在处理上一条消息，请稍候');
        return;
    }

    // 创建新的流式处理器
    const streamProcessor = new StreamProcessor();

    // 跟踪已添加到历史记录的内容长度
    let addedToHistoryLength = 0;
    let lastPlayedLength = 0;
    let isFirstSentence = true;

    // 设置回调函数
    streamProcessor.setCallbacks(
        // 字符回调
        (fullContent) => {
            const newContent = fullContent.substring(addedToHistoryLength);
            window.updateCurrentMessage('assistant', newContent, true);
            
            // 检查是否有新的完整句子需要处理
            const sentences = newContent.split(/([。？！…~])/);
            let completeSentences = '';
            
            for (let i = 0; i < sentences.length - 1; i += 2) {
                if (i + 1 < sentences.length) {
                    completeSentences += sentences[i] + sentences[i + 1];
                }
            }
            
            if (completeSentences.length > lastPlayedLength) {
                const newSentenceContent = completeSentences.substring(lastPlayedLength);
                if (newSentenceContent.trim()) {
                    const currentCharacter = getCurrentCharacter();
                    const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                    
                    if (window.prefetchAndPlayAudio) {
                        window.prefetchAndPlayAudio(newSentenceContent, characterName, currentCharacter);
                    }
                    
                    lastPlayedLength = completeSentences.length;
                    isFirstSentence = false;
                }
            }
        },
        // 暂停回调
        (fullContent) => {
            window.setIsPaused(true);
            const currentCharacter = getCurrentCharacter();
            const newContent = fullContent.substring(addedToHistoryLength);
            if (newContent) {
                const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                
                const unplayedContent = newContent.substring(lastPlayedLength);
                if (unplayedContent.trim() && window.prefetchAndPlayAudio) {
                    window.prefetchAndPlayAudio(unplayedContent, characterName, currentCharacter);
                }
                
                window.addToHistory('assistant', newContent, characterName);
                window.updateCurrentMessage('assistant', newContent);
                addedToHistoryLength = fullContent.length;
            }
            window.showContinuePrompt();
            lastPlayedLength = 0;
            isFirstSentence = true;
        },
        // 完成回调
        (fullContent) => {
            const currentCharacter = getCurrentCharacter();
            const remainingContent = fullContent.substring(addedToHistoryLength);
            if (remainingContent) {
                const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                
                const unplayedContent = remainingContent.substring(lastPlayedLength);
                if (unplayedContent.trim() && window.prefetchAndPlayAudio) {
                    window.prefetchAndPlayAudio(unplayedContent, characterName, currentCharacter);
                }
                
                window.addToHistory('assistant', remainingContent, characterName);
                window.updateCurrentMessage('assistant', remainingContent);
                window.hideContinuePrompt();
                window.enableUserInput();
                window.setIsPaused(false);
                
                if (window.pendingOptions && window.pendingOptions.length > 0) {
                    if (window.showOptionButtons) {
                        window.showOptionButtons(window.pendingOptions);
                    }
                    window.pendingOptions = null;
                }
            } else {
                window.hideContinuePrompt();
                window.enableUserInput();
                window.setIsPaused(false);
                
                if (window.pendingOptions && window.pendingOptions.length > 0) {
                    if (window.showOptionButtons) {
                        window.showOptionButtons(window.pendingOptions);
                    }
                    window.pendingOptions = null;
                }
            }
            
            lastPlayedLength = 0;
            isFirstSentence = true;
        }
    );

    // 更新当前消息为用户消息
    window.updateCurrentMessage('user', message);

    // 添加到历史记录
    window.addToHistory('user', message);

    // 隐藏选项按钮
    if (window.hideOptionButtons) {
        window.hideOptionButtons();
    }

    // 清空输入框并更新状态
    messageInput.value = '';
    
    if (window.inputEnhancements) {
        window.inputEnhancements.updateCharCount();
        window.inputEnhancements.updateSendButtonState();
        window.inputEnhancements.autoResize();
    }

    // 禁用用户输入
    window.disableUserInput();

    try {
        // 发送API请求到剧情模式端点
        const response = await fetch('/api/story/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                story_id: window.storyId
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                error: `HTTP ${response.status}: ${response.statusText}`
            }));
            throw new Error(errorData.error || '请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        // 准备接收流式响应
        window.updateCurrentMessage('assistant', '\n');

        // 读取流式响应
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                break;
            }

            const chunk = decoder.decode(value, { stream: true });

            try {
                const lines = chunk.split('\n').filter(line => line.trim());

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);

                        if (jsonStr === '[DONE]') {
                            streamProcessor.markEnd();
                            break;
                        }

                        try {
                            const data = JSON.parse(jsonStr);

                            if (data.error) {
                                throw new Error(data.error);
                            }

                            // 处理mood字段
                            if (data.mood !== undefined) {
                                console.log('收到mood数据:', data.mood);
                                if (window.handleMoodChange) {
                                    window.handleMoodChange(data.mood);
                                }
                            }

                            // 处理content字段
                            if (data.content) {
                                streamProcessor.addData(data.content);
                            }

                            // 处理选项数据
                            if (data.options && Array.isArray(data.options)) {
                                console.log('收到选项数据:', data.options);
                                window.pendingOptions = data.options;
                            }
                            
                            // 处理故事结束信号
                            if (data.storyFinished) {
                                console.log('故事已结束');
                                // 触发故事结束事件
                                window.dispatchEvent(new CustomEvent('storyFinished'));
                            }
                        } catch (e) {
                            console.error('解析JSON失败:', e, jsonStr);
                        }
                    }
                }
            } catch (e) {
                console.error('解析流式响应失败:', e);
            }
        }

    } catch (error) {
        console.error('发送消息失败:', error);
        showError(`发送消息失败: ${error.message}`);
        window.hideLoading();
        window.enableUserInput();

        if (streamProcessor) {
            streamProcessor.reset();
        }
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('开始初始化剧情聊天页面...');
        
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
        const sendButton = document.getElementById('sendButton');
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
        
        // 绑定剧情模式专用的发送消息事件
        sendButton?.addEventListener('click', sendStoryMessage);

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
        
        console.log('剧情聊天页面初始化完成');
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
window.ttsEnabled = true;
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

// 导入UI服务函数
import { 
    showOptionButtons,
    updateCurrentMessage,
    addToHistory,
    disableUserInput,
    enableUserInput,
    showContinuePrompt,
    hideContinuePrompt,
    setIsPaused,
    hideLoading,
    getIsProcessing,
    setIsProcessing
} from './ui-service.js';

// 暴露必要的函数给全局使用
window.getCurrentCharacter = getCurrentCharacter;
window.showOptionButtons = showOptionButtons;
window.updateCurrentMessage = updateCurrentMessage;
window.addToHistory = addToHistory;
window.disableUserInput = disableUserInput;
window.enableUserInput = enableUserInput;
window.showContinuePrompt = showContinuePrompt;
window.hideContinuePrompt = hideContinuePrompt;
window.setIsPaused = setIsPaused;
window.hideLoading = hideLoading;
window.playAudio = (autoPlay = false) => playAudio(getCurrentCharacter(), autoPlay);
window.stopCurrentAudio = stopCurrentAudio;
window.prefetchAndPlayAudio = prefetchAndPlayAudio;
window.handleMoodChange = handleMoodChange;
window.showError = showError;
window.sendStoryMessage = sendStoryMessage;

// 重写全局的sendMessage函数为剧情模式版本
window.sendMessage = sendStoryMessage;