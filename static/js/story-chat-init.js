// 剧情模式聊天页面的初始化和事件绑定
import {
    changeBackground,
    continueOutput,
    skipTyping
} from './chat-service.js';

// 保存原始的continueOutput函数作为备用
window.originalContinueOutput = continueOutput;

// 直接设置当前角色的函数（用于剧情模式）
function setCurrentCharacterDirect(character) {
    console.log('直接设置角色:', character);

    // 更新角色名称显示
    const characterNameElement = document.getElementById('characterName');
    if (characterNameElement && character.name) {
        characterNameElement.textContent = character.name;
        characterNameElement.style.color = character.color || '#ffeb3b';
        console.log('设置角色名称:', character.name, '颜色:', character.color);
    }

    // 更新角色图片
    const characterImage = document.getElementById('characterImage');
    if (characterImage && character.image) {
        // 确保路径格式正确
        let imagePath = character.image;
        if (!imagePath.startsWith('/')) {
            imagePath = '/' + imagePath;
        }
        if (!imagePath.endsWith('/1.png')) {
            imagePath = imagePath + '/1.png';
        }

        console.log('设置角色图片路径:', imagePath);
        characterImage.src = imagePath;
        characterImage.alt = character.name;

        // 处理图片加载失败的情况
        characterImage.onerror = () => {
            console.log('角色图片加载失败，使用默认图片');
            characterImage.src = '/static/images/default.svg';
        };

        // 添加加载成功的回调
        characterImage.onload = () => {
            console.log('角色图片加载成功:', imagePath);
        };
    }

    // 更新全局角色状态（让getCurrentCharacter能返回正确的角色）
    setCurrentCharacter(character);

    if (window.updateCurrentCharacter) {
        window.updateCurrentCharacter(character);
    }
}

// 更新当前角色状态的函数
function updateCurrentCharacter(character) {
    // 这个函数会被角色服务导入并使用
    console.log('更新当前角色状态:', character);
    // 这里可以添加更多的角色状态更新逻辑
}

// 更新故事进度的函数
function updateStoryProgress(progress) {
    console.log('=== 更新故事进度 ===');
    console.log('进度数据:', progress);

    // 更新当前章节显示
    const currentChapterElement = document.getElementById('currentChapter');
    if (currentChapterElement && progress.currentChapter) {
        const newText = `当前章节: ${progress.currentChapter}`;
        console.log('更新章节显示:', newText);
        currentChapterElement.textContent = newText;
    } else {
        console.log('未找到章节元素或章节数据');
    }

    // 更新偏移值显示
    const currentOffsetElement = document.getElementById('currentOffset');
    if (currentOffsetElement && progress.offset !== undefined) {
        const newText = `偏移值: ${progress.offset}`;
        console.log('更新偏移值显示:', newText);
        currentOffsetElement.textContent = newText;
    } else {
        console.log('未找到偏移值元素或偏移值数据');
    }

    // 更新全局故事数据
    if (window.storyData && window.storyData.progress) {
        window.storyData.progress.current = progress.current;
        window.storyData.progress.offset = progress.offset;
        console.log('更新全局故事数据完成');
    } else {
        console.log('未找到全局故事数据');
    }

    console.log('=== 故事进度更新完成 ===');
}

// 暴露给全局使用
window.setCurrentCharacterDirect = setCurrentCharacterDirect;
window.updateCurrentCharacter = updateCurrentCharacter;
window.updateStoryProgress = updateStoryProgress;

import {
    loadCharacters,
    toggleCharacterModal,
    getCurrentCharacter,
    handleMoodChange,
    setCurrentCharacter
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
    handleConfirmYes,
    handleConfirmNo,
    hideConfirmModal
} from './ui-service.js';

import { toggleHistory } from './history-service.js';

// 全局流式处理器实例
let globalStreamProcessor = null;

// 剧情模式专用的继续输出函数
function storyContinueOutput() {
    console.log('=== storyContinueOutput called ===');

    // 自动中断正在播放的语音
    if (window.stopCurrentAudio) {
        window.stopCurrentAudio();
    }

    // 尝试从多个位置获取流式处理器
    const processor = globalStreamProcessor || window.globalStreamProcessor;

    console.log('processor:', processor);
    console.log('processor isPaused:', processor ? processor.isPaused : 'N/A');
    console.log('processor isProcessing:', processor ? processor.isProcessing() : 'N/A');

    if (processor) {
        console.log('Hiding continue prompt...');
        hideContinuePrompt();

        console.log('Calling continue() on processor...');
        processor.continue();

        console.log('Continue() called successfully');
    } else {
        console.error('No stream processor found');

        // 尝试备用方案：直接调用原始的continueOutput
        if (window.originalContinueOutput) {
            console.log('Trying fallback to originalContinueOutput');
            window.originalContinueOutput();
        }
    }

    console.log('=== storyContinueOutput finished ===');
}

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
    globalStreamProcessor = new StreamProcessor();

    // 立即暴露给全局作用域
    window.globalStreamProcessor = globalStreamProcessor;

    // 初始化角色状态
    window.currentSpeakingCharacterId = null;
    window.pendingCharacterSwitch = null;

    // 跟踪已添加到历史记录的内容长度
    let addedToHistoryLength = 0;
    let lastPlayedLength = 0;
    let isFirstSentence = true;

    // 设置回调函数
    globalStreamProcessor.setCallbacks(
        // 字符回调
        (fullContent) => {
            const newContent = fullContent.substring(addedToHistoryLength);
            // 在多角色模式下，使用当前说话角色的ID
            const isMultiCharacter = window.storyData?.characters?.list?.length > 1 ||
                window.storyData?.characters?.length > 1;
            const roleToUse = isMultiCharacter && window.currentSpeakingCharacterId ?
                window.currentSpeakingCharacterId : 'assistant';
            console.log("》》》》》》》》》聊天框更新：", roleToUse)
            updateCurrentMessage(roleToUse, newContent, true);

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
                    let currentCharacter = getCurrentCharacter();
                    let characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                    
                    if(roleToUse=='assistant')
                    {
                        if (prefetchAndPlayAudio) {
                            prefetchAndPlayAudio(newSentenceContent, characterName, currentCharacter);
                        }
                    }
                    else
                    {
                        // 异步获取角色信息
                        getCharacterById(roleToUse).then(newCharacter => {
                            const newCharacterName = newCharacter ? newCharacter.name : 'AI助手';
                            console.log("TTS角色名", newCharacterName)
                            if (prefetchAndPlayAudio) {
                                prefetchAndPlayAudio(newSentenceContent, newCharacterName, newCharacter);
                            }
                        }).catch(error => {
                            console.error("获取角色信息失败:", error);
                            // 如果获取失败，使用旧版角色信息
                            if (prefetchAndPlayAudio) {
                                prefetchAndPlayAudio(newSentenceContent, characterName, currentCharacter);
                            }
                        });
                    }
                   
                    lastPlayedLength = completeSentences.length;
                    isFirstSentence = false;
                }
            }
        },
        // 暂停回调
        (fullContent) => {
            setIsPaused(true);
            const newContent = fullContent.substring(addedToHistoryLength);
            if (newContent) {
                // 在多角色模式下，使用当前说话角色的ID
                const isMultiCharacter = window.storyData?.characters?.list?.length > 1 ||
                    window.storyData?.characters?.length > 1;
                const roleToUse = isMultiCharacter && window.currentSpeakingCharacterId ?
                    window.currentSpeakingCharacterId : 'assistant';

                if (roleToUse === 'assistant') {
                    const currentCharacter = getCurrentCharacter();
                    const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                    
                    const unplayedContent = newContent.substring(lastPlayedLength);
                    if (unplayedContent.trim() && prefetchAndPlayAudio) {
                        prefetchAndPlayAudio(unplayedContent, characterName, currentCharacter);
                    }
                    
                    addToHistory(roleToUse, newContent, characterName);
                    updateCurrentMessage(roleToUse, newContent);
                } else {
                    // 异步获取角色信息
                    getCharacterById(roleToUse).then(newCharacter => {
                        const newCharacterName = newCharacter ? newCharacter.name : 'AI助手';
                        console.log("TTS角色名", newCharacterName);
                        
                        const unplayedContent = newContent.substring(lastPlayedLength);
                        if (unplayedContent.trim() && prefetchAndPlayAudio) {
                            prefetchAndPlayAudio(unplayedContent, newCharacterName, newCharacter);
                        }
                        
                        addToHistory(roleToUse, newContent, newCharacterName);
                        updateCurrentMessage(roleToUse, newContent);
                    }).catch(error => {
                        console.error("获取角色信息失败:", error);
                        // 如果获取失败，使用默认角色信息
                        const currentCharacter = getCurrentCharacter();
                        const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                        
                        const unplayedContent = newContent.substring(lastPlayedLength);
                        if (unplayedContent.trim() && prefetchAndPlayAudio) {
                            prefetchAndPlayAudio(unplayedContent, characterName, currentCharacter);
                        }
                        
                        addToHistory(roleToUse, newContent, characterName);
                        updateCurrentMessage(roleToUse, newContent);
                    });
                }
                
                addedToHistoryLength = fullContent.length;
            }
            showContinuePrompt();
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
                if (unplayedContent.trim() && prefetchAndPlayAudio) {
                    prefetchAndPlayAudio(unplayedContent, characterName, currentCharacter);
                }

                // 在多角色模式下，使用当前说话角色的ID
                const isMultiCharacter = window.storyData?.characters?.list?.length > 1 ||
                    window.storyData?.characters?.length > 1;
                const roleToUse = isMultiCharacter && window.currentSpeakingCharacterId ?
                    window.currentSpeakingCharacterId : 'assistant';
                addToHistory(roleToUse, remainingContent, characterName);
                updateCurrentMessage(roleToUse, remainingContent);
                hideContinuePrompt();
                enableUserInput();
                setIsPaused(false);

                // 检查是否启用选项生成
                const optionGenerationEnabled = localStorage.getItem('optionGenerationEnabled') !== 'false';
                if (optionGenerationEnabled && window.pendingOptions && window.pendingOptions.length > 0) {
                    if (showOptionButtons) {
                        showOptionButtons(window.pendingOptions);
                    }
                    window.pendingOptions = null;
                }
            } else {
                hideContinuePrompt();
                enableUserInput();
                setIsPaused(false);

                // 检查是否启用选项生成
                const optionGenerationEnabled = localStorage.getItem('optionGenerationEnabled') !== 'false';
                if (optionGenerationEnabled && window.pendingOptions && window.pendingOptions.length > 0) {
                    if (showOptionButtons) {
                        showOptionButtons(window.pendingOptions);
                    }
                    window.pendingOptions = null;
                }
            }

            lastPlayedLength = 0;
            isFirstSentence = true;
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

    // 清空输入框并更新状态
    messageInput.value = '';

    if (window.inputEnhancements) {
        window.inputEnhancements.updateCharCount();
        window.inputEnhancements.updateSendButtonState();
        window.inputEnhancements.autoResize();
    }

    // 禁用用户输入
    disableUserInput();
    try {
        // 发送API请求到剧情模式端点
        const isMultiCharacter = window.storyData?.characters?.list?.length > 1 ||
            window.storyData?.characters?.length > 1;
        const endpoint = isMultiCharacter ?
            '/api/multi-character/chat/stream' :
            '/api/story/chat/stream';

        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                story_id: window.storyId,
                optionGenerationEnabled: localStorage.getItem('optionGenerationEnabled') !== 'false'
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
        updateCurrentMessage('assistant', '...\n');

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
                            globalStreamProcessor.markEnd();
                            break;
                        }

                        try {
                            const data = JSON.parse(jsonStr);

                            if (data.error) {
                                throw new Error(data.error);
                            }

                            // 处理角色回复开始信号（仅记录，不立即切换）
                            if (data.characterResponse) {
                                console.log('角色开始回复2:', data.characterName);
                                // 记录待切换的角色信息，但不立即添加切换标记
                                window.pendingCharacterSwitch = {
                                    characterID: data.characterID,
                                    characterName: data.characterName
                                };
                                
                                if (window.showCharacterResponse) {
                                    window.showCharacterResponse(data.characterName);
                                }
                            }

                            // 处理多角色对话的特定字段
                            if (data.characterContent) {
                                // 这是角色自动回复的内容
                                // console.log('收到角色回复内容:', data.characterContent);
                                
                                // 如果有待切换的角色，先添加切换标记
                                if (window.pendingCharacterSwitch) {
                                    const switchMarker = `<SWITCH_CHARACTER:${window.pendingCharacterSwitch.characterID}:${window.pendingCharacterSwitch.characterName}>`;
                                    globalStreamProcessor.addData(switchMarker);
                                    window.pendingCharacterSwitch = null; // 清除待切换状态
                                }
                                
                                globalStreamProcessor.addData(data.characterContent);
                            }

                            // 处理角色回复完成信号
                            if (data.characterResponseComplete) {
                                console.log('角色回复完成2');
                                if (window.completeCharacterResponse) {
                                    window.completeCharacterResponse();
                                }
                            }

                            // 处理下一个说话者信息
                            if (data.nextSpeaker) {
                                console.log('下一个说话者:', data.nextSpeaker);
                                if (data.nextSpeakerName) {
                                    console.log('下一个说话者名称:', data.nextSpeakerName);
                                    // 可以在这里更新UI提示下一个说话者
                                }
                            }

                            // 处理mood字段
                            if (data.mood !== undefined) {
                                console.log('收到mood数据:', data.mood);
                                if (handleMoodChange) {
                                    handleMoodChange(data.mood);
                                }
                            }

                            // 处理普通content字段（单角色模式）
                            if (data.content) {
                                globalStreamProcessor.addData(data.content);
                            }

                            // 处理选项数据
                            if (data.options && Array.isArray(data.options)) {
                                console.log('收到选项数据:', data.options);
                                const optionGenerationEnabled = localStorage.getItem('optionGenerationEnabled') !== 'false';
                                if (optionGenerationEnabled) {
                                    window.pendingOptions = data.options;
                                }
                            }

                            // 处理故事进度更新
                            if (data.storyProgress) {
                                console.log('收到故事进度更新:', data.storyProgress);
                                updateStoryProgress(data.storyProgress);
                            }

                            // 处理故事结束信号
                            if (data.storyFinished) {
                                console.log('故事已结束');
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
        hideLoading();
        enableUserInput();

        if (globalStreamProcessor) {
            globalStreamProcessor.reset();
        }
        // 清除角色状态
        window.currentSpeakingCharacterId = null;
        window.pendingCharacterSwitch = null;
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('开始初始化剧情聊天页面...');

        // 如果有当前角色信息，直接设置
        if (window.currentCharacter) {
            console.log('剧情模式 - 当前角色信息:', window.currentCharacter);
            // 直接设置当前角色，不需要通过API加载
            window.setCurrentCharacterDirect(window.currentCharacter);
        } else {
            console.log('剧情模式 - 未找到当前角色信息');
        }

        // 加载角色数据（用于角色选择模态框）
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
        continueButton?.addEventListener('click', storyContinueOutput);
        micButton?.addEventListener('click', () => toggleRecording(messageInput, micButton, showError));
        errorCloseButton?.addEventListener('click', hideError);

        // 绑定剧情模式专用的发送消息事件
        sendButton?.addEventListener('click', sendStoryMessage);

        // 绑定返回按钮事件，退出剧情模式
        const backButtons = document.querySelectorAll('.back-btn, .back-to-story');
        backButtons.forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();

                try {
                    // 调用退出剧情模式API
                    const response = await fetch('/api/story/exit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });

                    const data = await response.json();
                    if (data.success) {
                        console.log('已退出剧情模式');
                        // 跳转到故事列表页面
                        window.location.href = '/story';
                    } else {
                        console.error('退出剧情模式失败:', data.error);
                        // 即使失败也跳转，避免卡在剧情模式
                        window.location.href = '/story';
                    }
                } catch (error) {
                    console.error('退出剧情模式时发生错误:', error);
                    // 发生错误时也跳转
                    window.location.href = '/story';
                }
            });
        });

        // 绑定确认对话框事件
        const confirmYesButton = document.getElementById('confirmYesButton');
        const confirmNoButton = document.getElementById('confirmNoButton');
        const closeConfirmButton = document.getElementById('closeConfirmButton');

        confirmYesButton?.addEventListener('click', handleConfirmYes);
        confirmNoButton?.addEventListener('click', handleConfirmNo);
        closeConfirmButton?.addEventListener('click', hideConfirmModal);

        // 绑定点击事件继续输出
        currentMessage?.addEventListener('click', storyContinueOutput);
        clickToContinue?.addEventListener('click', storyContinueOutput);

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
    Enter: storyContinueOutput,
    s: skipTyping,
    h: toggleHistory,
    b: changeBackground
});

// TTS开关控制函数
window.ttsEnabled = true;
window.toggleTTS = function () {
    window.ttsEnabled = !window.ttsEnabled;
    console.log(`TTS已${window.ttsEnabled ? '开启' : '关闭'}`);
    return window.ttsEnabled;
};

window.setTTS = function (enabled) {
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
window.storyContinueOutput = storyContinueOutput;

// 重写全局的sendMessage和continueOutput函数为剧情模式版本
window.sendMessage = sendStoryMessage;
window.continueOutput = storyContinueOutput;

// 确保全局流式处理器可访问
window.globalStreamProcessor = globalStreamProcessor;