// 聊天服务模块 - 处理消息发送和背景更换
import { 
    messageInput, 
    currentMessage 
} from './dom-elements.js';
import { 
    showLoading, 
    hideLoading, 
    showError, 
    updateCurrentMessage, 
    addToHistory, 
    disableUserInput, 
    enableUserInput, 
    showContinuePrompt, 
    hideContinuePrompt, 
    updateBackground,
    getIsProcessing,
    setIsProcessing,
    setIsPaused
} from './ui-service.js';
import { getCurrentCharacter, handleMoodChange } from './character-service.js';
import { prefetchAudio } from './audio-service.js';

// 流式处理器实例
let streamProcessor = null;

// 发送消息
export async function sendMessage() {
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
    streamProcessor = new StreamProcessor();

    // 跟踪已添加到历史记录的内容长度
    let addedToHistoryLength = 0;

    // 设置回调函数
    streamProcessor.setCallbacks(
        // 字符回调
        (fullContent) => {
            const newContent = fullContent.substring(addedToHistoryLength);
            updateCurrentMessage('assistant', newContent, true);
        },
        // 暂停回调
        (fullContent) => {
            setIsPaused(true);
            const currentCharacter = getCurrentCharacter();
            const newContent = fullContent.substring(addedToHistoryLength);
            if (newContent) {
                const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                prefetchAudio(newContent, characterName, () => {
                    addToHistory('assistant', newContent, characterName);
                    updateCurrentMessage('assistant', newContent);
                    addedToHistoryLength = fullContent.length;
                    showContinuePrompt();
                    // 自动播放，不显示错误
                    if (window.playAudio) window.playAudio(true);
                });
            } else {
                showContinuePrompt();
                // 自动播放，不显示错误
                if (window.playAudio) window.playAudio(true);
            }
        },
        // 完成回调
        (fullContent) => {
            const currentCharacter = getCurrentCharacter();
            const remainingContent = fullContent.substring(addedToHistoryLength);
            if (remainingContent) {
                const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                prefetchAudio(remainingContent, characterName, () => {
                    addToHistory('assistant', remainingContent, characterName);
                    updateCurrentMessage('assistant', remainingContent);
                    hideContinuePrompt();
                    enableUserInput();
                    setIsPaused(false);
                    if (window.pendingOptions && window.pendingOptions.length > 0) {
                        if (window.showOptionButtons) {
                            window.showOptionButtons(window.pendingOptions);
                        }
                        window.pendingOptions = null;
                    }
                    // 自动播放，不显示错误
                    if (window.playAudio) window.playAudio(true);
                });
            } else {
                hideContinuePrompt();
                enableUserInput();
                setIsPaused(false);
                if (window.pendingOptions && window.pendingOptions.length > 0) {
                    if (window.showOptionButtons) {
                        window.showOptionButtons(window.pendingOptions);
                    }
                    window.pendingOptions = null;
                }
                // 自动播放，不显示错误
                if (window.playAudio) window.playAudio(true);
            }
        }
    );

    // 更新当前消息为用户消息
    updateCurrentMessage('user', message);

    // 添加到历史记录
    addToHistory('user', message);

    // 隐藏选项按钮
    if (window.hideOptionButtons) {
        window.hideOptionButtons();
    }

    // 清空输入框
    messageInput.value = '';

    // 禁用用户输入
    disableUserInput();

    try {
        // 发送API请求
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
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
        updateCurrentMessage('assistant', '\n');

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
                                handleMoodChange(data.mood);
                            }

                            // 处理content字段
                            if (data.content) {
                                streamProcessor.addData(data.content);
                            }

                            // 处理选项数据
                            if (data.options) {
                                window.pendingOptions = data.options;
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
        hideLoading();
        enableUserInput();

        if (streamProcessor) {
            streamProcessor.reset();
        }
    }
}

// 更换背景
export async function changeBackground() {
    if (getIsProcessing()) {
        showError('正在处理请求，请稍候');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/background', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }

        if (data.background_url) {
            updateBackground(data.background_url);

            const promptMessage = data.prompt ?
                `背景已更新，提示词: "${data.prompt}"` :
                '背景已更新';

            updateCurrentMessage('system', promptMessage);
        }

    } catch (error) {
        console.error('更换背景失败:', error);
        showError(`更换背景失败: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// 继续输出
export function continueOutput() {
    // 自动中断正在播放的语音
    if (window.stopCurrentAudio) {
        window.stopCurrentAudio();
    }
    
    console.log('continueOutput called, streamProcessor:', streamProcessor);

    if (streamProcessor) {
        hideContinuePrompt();
        streamProcessor.continue();
    }
}

// 跳过打字效果
export function skipTyping() {
    if (streamProcessor && streamProcessor.isProcessing()) {
        streamProcessor.skip();
        hideContinuePrompt();
        enableUserInput();
    }
}

// 暴露给全局使用
window.sendMessage = sendMessage;
window.continueOutput = continueOutput;
