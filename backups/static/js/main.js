// DOM元素
// 页面元素
let homePage, chatPage, startButton, exitButton, backButton, dialogBox;

// 在DOMContentLoaded事件中初始化DOM元素
function initDOMElements() {
    console.log('初始化DOM元素');
    homePage = document.getElementById('homePage');
    chatPage = document.getElementById('chatPage');
    startButton = document.getElementById('startButton');
    exitButton = document.getElementById('exitButton');
    backButton = document.getElementById('backButton');
    dialogBox = document.getElementById('dialogBox');
    
    // 初始化其他DOM元素
    initDialogElements();
    initOtherElements();
    
    console.log('DOM元素初始化完成:');
    console.log('homePage:', homePage);
    console.log('chatPage:', chatPage);
    console.log('startButton:', startButton);
}

// 对话元素
let characterName, currentMessage, messageInput, sendButton, clearButton;
let backgroundButton, historyButton, characterButton, continueButton, skipButton;
let historyModal, historyMessages, closeHistoryButton;
let characterModal, characterList, closeCharacterButton;

// 在initDOMElements函数中初始化这些元素
function initDialogElements() {
    characterName = document.getElementById('characterName');
    currentMessage = document.getElementById('currentMessage');
    messageInput = document.getElementById('messageInput');
    sendButton = document.getElementById('sendButton');
    clearButton = document.getElementById('clearButton');
    backgroundButton = document.getElementById('backgroundButton');
    historyButton = document.getElementById('historyButton');
    characterButton = document.getElementById('characterButton');
    continueButton = document.getElementById('continueButton');
    skipButton = document.getElementById('skipButton');
    historyModal = document.getElementById('historyModal');
    historyMessages = document.getElementById('historyMessages');
    closeHistoryButton = document.getElementById('closeHistoryButton');
    characterModal = document.getElementById('characterModal');
    characterList = document.getElementById('characterList');
    closeCharacterButton = document.getElementById('closeCharacterButton');
}

// 确认对话框
let confirmModal, confirmMessage, confirmYesButton, confirmNoButton, closeConfirmButton;

// 加载和错误元素
let loadingIndicator, errorContainer, errorMessage, errorCloseButton;

// 在initDOMElements函数中初始化这些元素
function initOtherElements() {
    // 确认对话框
    confirmModal = document.getElementById('confirmModal');
    confirmMessage = document.getElementById('confirmMessage');
    confirmYesButton = document.getElementById('confirmYesButton');
    confirmNoButton = document.getElementById('confirmNoButton');
    closeConfirmButton = document.getElementById('closeConfirmButton');
    
    // 加载和错误元素
    loadingIndicator = document.getElementById('loadingIndicator');
    errorContainer = document.getElementById('errorContainer');
    errorMessage = document.getElementById('errorMessage');
    errorCloseButton = document.getElementById('errorCloseButton');
}

// 角色数据
let availableCharacters = [];
let currentCharacter = null;

// 状态变量
let isProcessing = false;
let isPaused = false;
let messageHistory = [];
let typingSpeed = 50; // 打字速度（毫秒/字符）
let currentTypingTimeout = null;
let currentConfirmCallback = null;
let streamController = {
    buffer: '',
    currentParagraph: '',
    paragraphs: [],
    isComplete: false,
    isPaused: false
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM加载完成');
    
    // 初始化DOM元素
    initDOMElements();
    
    // 确保输入框在初始状态下是启用的
    enableInput();
    
    // 加载角色数据
    loadCharacters();
    
    // 绑定页面切换事件
    if (startButton) {
        console.log('绑定startButton点击事件');
        startButton.addEventListener('click', function() {
            console.log('startButton被点击');
            showChatPage();
        });
    } else {
        console.error('startButton元素不存在');
    }
    
    backButton.addEventListener('click', confirmBackToHome);
    exitButton.addEventListener('click', confirmExit);
    
    // 绑定对话事件
    sendButton.addEventListener('click', sendMessage);
    clearButton.addEventListener('click', clearChat);
    backgroundButton.addEventListener('click', changeBackground);
    historyButton.addEventListener('click', toggleHistory);
    closeHistoryButton.addEventListener('click', toggleHistory);
    characterButton.addEventListener('click', toggleCharacterModal);
    closeCharacterButton.addEventListener('click', toggleCharacterModal);
    continueButton.addEventListener('click', continueOutput);
    skipButton.addEventListener('click', skipTyping);
    errorCloseButton.addEventListener('click', hideError);
    
    // 绑定确认对话框事件
    confirmYesButton.addEventListener('click', handleConfirmYes);
    confirmNoButton.addEventListener('click', handleConfirmNo);
    closeConfirmButton.addEventListener('click', hideConfirmModal);
    
    // 绑定回车键发送消息
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 绑定点击事件继续输出 - 整个对话框可点击
    dialogBox.addEventListener('click', continueOutput);
    // 绑定点击事件继续输出 - 消息内容可点击
    currentMessage.addEventListener('click', continueOutput);
});

// 禁用输入框
function disableInput() {
    console.log('禁用输入框');
    if (messageInput && sendButton) {
        messageInput.disabled = true;
        sendButton.disabled = true;
        messageInput.placeholder = "AI正在回复中...";
        sendButton.classList.add('disabled');
    }
}

// 启用输入框
function enableInput() {
    console.log('启用输入框');
    if (messageInput && sendButton) {
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.placeholder = "输入消息...";
        sendButton.classList.remove('disabled');
    }
}

// 发送消息
async function sendMessage() {
    // 获取消息内容
    const message = messageInput.value.trim();
    
    // 检查消息是否为空
    if (!message) {
        showError('请输入消息');
        return;
    }
    
    // 检查是否正在处理请求
    if (isProcessing) {
        showError('正在处理上一条消息，请稍候');
        return;
    }
    
    // 禁用输入框，防止用户在AI回复过程中发送新消息
    disableInput();
    
    // 重置流控制器状态
    streamController = {
        buffer: '',
        currentParagraph: '',
        paragraphs: [],
        isComplete: false,
        isPaused: false,
        currentIndex: 0  // 添加当前段落索引
    };
    
    // 更新当前消息为用户消息
    updateCurrentMessage('user', message);
    
    // 添加到历史记录
    addToHistory('user', message);
    
    // 清空输入框
    messageInput.value = '';
    
    // 显示加载指示器
    showLoading();
    
    try {
        // 准备接收流式响应
        let fullResponse = '';
        let currentParagraphResponse = '';
        
        // 发送API请求
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        // 检查响应状态
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '请求失败');
        }
        
        // 获取响应的读取器
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        // 隐藏加载指示器，因为我们将开始接收流式响应
        hideLoading();
        
        // 准备接收流式响应
        updateCurrentMessage('assistant', '');
        
        // 读取流式响应
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                break;
            }
            
            // 解码响应数据
            const chunk = decoder.decode(value, { stream: true });
            
            try {
                // 尝试解析JSON
                const lines = chunk.split('\n').filter(line => line.trim());
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        
                        if (jsonStr === '[DONE]') {
                            continue;
                        }
                        
                        try {
                            const data = JSON.parse(jsonStr);
                            
                            // 处理流式控制信息
                            if (data.stream_control) {
                                // 如果段落完成且需要暂停
                                if (data.stream_control.paragraph_complete && data.stream_control.pause) {
                                    isPaused = true;
                                    
                                    // 添加完整段落到当前显示
                                    if (data.stream_control.paragraph) {
                                        // 只显示当前段落，不是累积的全部内容
                                        currentParagraphResponse = data.stream_control.paragraph;
                                        streamController.paragraphs.push(currentParagraphResponse);
                                        streamController.currentIndex = streamController.paragraphs.length - 1;
                                        console.log(`添加段落 ${streamController.currentIndex}: ${currentParagraphResponse}`);
                                        
                                        // 更新当前显示的消息为当前段落
                                        updateCurrentMessage('assistant', currentParagraphResponse, true);
                                    }
                                    
                                    // 等待用户点击继续
                                    continueButton.classList.add('active');
                                    
                                    // 移除之前的点击提示（如果有）
                                    const existingPrompt = document.querySelector('.click-prompt');
                                    if (existingPrompt) {
                                        existingPrompt.remove();
                                    }
                                    
                                    // 添加提示信息到对话框右上角
                                    const clickPrompt = document.createElement('div');
                                    clickPrompt.className = 'click-prompt';
                                    clickPrompt.textContent = '点击屏幕继续...';
                                    
                                    // 添加到对话框容器而不是消息内容
                                    dialogBox.appendChild(clickPrompt);
                                    
                                    // 如果不是第一段，将当前段落添加到历史记录
                                    if (streamController.paragraphs.length > 1) {
                                        // 获取当前段落索引
                                        const currentIndex = streamController.paragraphs.length - 1;
                                        // 添加上一段到历史记录
                                        const previousIndex = currentIndex - 1;
                                        const previousParagraph = streamController.paragraphs[previousIndex];
                                        addParagraphToHistory('assistant', previousParagraph, previousIndex === 0);
                                    }
                                    
                                    // 暂停流式响应处理，等待用户点击
                                    // 不使用await，而是直接跳出循环，让用户点击后重新开始流式响应
                                    return;
                                }
                                
                                // 处理继续命令返回的下一段内容
                                if (data.stream_control.next_paragraph) {
                                    currentParagraphResponse = data.stream_control.next_paragraph;
                                    updateCurrentMessage('assistant', currentParagraphResponse, true);
                                    continue;
                                }
                                
                                // 如果是结束标记
                                if (data.stream_control.is_complete) {
                                    streamController.isComplete = true;
                                    console.log('收到完成标记，启用输入框');
                                    
                                    // 如果有段落信息，更新完整响应
                                    if (data.stream_control.paragraphs) {
                                        fullResponse = data.stream_control.paragraphs.join('');
                                        
                                        // 保存所有段落到streamController
                                        streamController.paragraphs = data.stream_control.paragraphs;
                                        
                                        // 如果只有一段，直接显示
                                        if (data.stream_control.paragraphs.length === 1) {
                                            updateCurrentMessage('assistant', data.stream_control.paragraphs[0], true);
                                        } 
                                        // 如果有多段，显示第一段
                                        else if (data.stream_control.paragraphs.length > 1) {
                                            updateCurrentMessage('assistant', data.stream_control.paragraphs[0], true);
                                            // 设置暂停状态，等待用户点击继续
                                            isPaused = true;
                                            // 显示继续按钮
                                            continueButton.classList.add('active');
                                            // 添加点击提示
                                            const clickPrompt = document.createElement('div');
                                            clickPrompt.className = 'click-prompt';
                                            clickPrompt.textContent = '点击屏幕继续...';
                                            dialogBox.appendChild(clickPrompt);
                                            // 不启用输入框，等待用户查看完所有段落
                                            return;
                                        }
                                    }
                                    
                                    // 启用输入框
                                    enableInput();
                                    
                                    continue;
                                }
                                
                                // 处理增量内容
                                if (data.stream_control.content) {
                                    currentParagraphResponse += data.stream_control.content;
                                    updateCurrentMessage('assistant', currentParagraphResponse, true);
                                }
                            }
                            // 处理标准格式（兼容旧格式）
                            else if (data.choices && data.choices[0] && data.choices[0].delta) {
                                const delta = data.choices[0].delta;
                                
                                if (delta.content) {
                                    currentParagraphResponse += delta.content;
                                    updateCurrentMessage('assistant', currentParagraphResponse, true);
                                }
                            }
                            // 直接处理内容字段（如果存在）
                            else if (data.content) {
                                currentParagraphResponse += data.content;
                                updateCurrentMessage('assistant', currentParagraphResponse, true);
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
        
        // 添加第一段到历史记录
        if (streamController.paragraphs.length > 0) {
            // 获取第一段
            const firstParagraph = streamController.paragraphs[0];
            
            // 添加第一段到历史记录
            addParagraphToHistory('assistant', firstParagraph, true);
            
            // 保存完整响应到内存中的历史记录
            fullResponse = streamController.paragraphs.join('');
            
            // 更新或添加完整响应到内存历史
            const lastHistoryMessage = messageHistory[messageHistory.length - 1];
            if (lastHistoryMessage && lastHistoryMessage.role === 'assistant') {
                lastHistoryMessage.content = fullResponse;
            } else {
                messageHistory.push({
                    role: 'assistant',
                    content: fullResponse
                });
            }
            
            // 如果有多段，设置暂停状态，等待用户点击继续
            if (streamController.paragraphs.length > 1) {
                isPaused = true;
                // 显示继续按钮
                continueButton.classList.add('active');
                // 添加点击提示
                const clickPrompt = document.createElement('div');
                clickPrompt.className = 'click-prompt';
                clickPrompt.textContent = '点击屏幕继续...';
                dialogBox.appendChild(clickPrompt);
                // 设置当前段落索引为0
                streamController.currentIndex = 0;
            } else {
                // 如果只有一段，启用输入框
                enableInput();
            }
        } else if (currentParagraphResponse) {
            addToHistory('assistant', currentParagraphResponse);
            // 启用输入框
            enableInput();
        }
        
        // 重置暂停状态
        isPaused = false;
        continueButton.classList.remove('active');
        
        // 移除点击提示（如果有）
        const existingPrompt = document.querySelector('.click-prompt');
        if (existingPrompt) {
            existingPrompt.remove();
        }
        
        // 如果流式输出已完成，启用输入框
        if (streamController.isComplete) {
            console.log('流式输出已完成，启用输入框');
            enableInput();
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        showError(`发送消息失败: ${error.message}`);
        hideLoading();
        // 出错时也要启用输入框
        enableInput();
    }
}

// 清空对话
async function clearChat() {
    // 检查是否正在处理请求
    if (isProcessing) {
        showError('正在处理请求，请稍候');
        return;
    }
    
    // 显示加载指示器
    showLoading();
    // 临时禁用输入框
    disableInput();
    
    try {
        // 发送API请求
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt_type: 'friendly' })
        });
        
        // 解析响应
        const data = await response.json();
        
        // 检查响应是否成功
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        // 清空历史记录
        messageHistory = [];
        historyMessages.innerHTML = '';
        
        // 更新当前消息
        updateCurrentMessage('assistant', '对话已重置。有什么我可以帮助您的？');
        
    } catch (error) {
        console.error('清空对话失败:', error);
        showError(`清空对话失败: ${error.message}`);
    } finally {
        // 隐藏加载指示器
        hideLoading();
        // 重新启用输入框
        enableInput();
    }
}

// 更换背景
async function changeBackground() {
    // 检查是否正在处理请求
    if (isProcessing) {
        showError('正在处理请求，请稍候');
        return;
    }
    
    // 显示加载指示器
    showLoading();
    // 临时禁用输入框
    disableInput();
    
    try {
        // 发送API请求
        const response = await fetch('/api/background', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        // 解析响应
        const data = await response.json();
        
        // 检查响应是否成功
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        // 更新背景图片
        if (data.background_url) {
            updateBackground(data.background_url);
            
            // 添加系统消息
            const promptMessage = data.prompt ? 
                `背景已更新，提示词: "${data.prompt}"` : 
                '背景已更新';
            
            updateCurrentMessage('system', promptMessage);
        }
        
    } catch (error) {
        console.error('更换背景失败:', error);
        showError(`更换背景失败: ${error.message}`);
    } finally {
        // 隐藏加载指示器
        hideLoading();
        // 重新启用输入框
        enableInput();
    }
}

// 更新当前消息
function updateCurrentMessage(role, content, isStreaming = false) {
    // 如果不是流式输出，停止当前正在进行的打字效果
    if (!isStreaming && currentTypingTimeout) {
        clearTimeout(currentTypingTimeout);
        currentTypingTimeout = null;
    }
    
    // 更新角色名称
    if (role === 'user') {
        characterName.textContent = '你';
        characterName.style.color = '#90caf9';
    } else if (role === 'assistant') {
        // 使用当前角色名称
        if (currentCharacter) {
            characterName.textContent = currentCharacter.name;
            characterName.style.color = currentCharacter.color;
        } else {
            characterName.textContent = '时雨绮罗';
            characterName.style.color = '#ffeb3b';
        }
    } else if (role === 'system') {
        characterName.textContent = '系统';
        characterName.style.color = '#4caf50';
    }
    
    // 如果是流式输出，直接更新内容
    if (isStreaming) {
        // 更新主要内容
        currentMessage.textContent = content;
        return;
    }
    
    // 直接显示消息
    currentMessage.textContent = content;
    
    // 如果不是流式输出，移除点击提示
    const existingPrompt = document.querySelector('.click-prompt');
    if (existingPrompt) {
        existingPrompt.remove();
    }
}

// 打字机效果
function typeMessage(content) {
    let i = 0;
    currentMessage.textContent = '';
    
    function type() {
        if (i < content.length) {
            currentMessage.textContent += content.charAt(i);
            i++;
            currentTypingTimeout = setTimeout(type, typingSpeed);
        }
    }
    
    type();
}

// 跳过打字效果
function skipTyping() {
    if (isPaused) {
        // 发送跳过命令
        fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ control_action: 'skip' })
        }).catch(error => {
            console.error('发送跳过命令失败:', error);
        });
        
        // 重置暂停状态
        isPaused = false;
        continueButton.classList.remove('active');
    } else if (currentTypingTimeout) {
        clearTimeout(currentTypingTimeout);
        currentTypingTimeout = null;
        
        // 获取当前正在打字的完整消息
        const lastMessage = messageHistory[messageHistory.length - 1];
        if (lastMessage) {
            currentMessage.textContent = lastMessage.content;
        }
    }
}

// 添加消息到历史记录
function addToHistory(role, content) {
    // 添加到内存中的历史记录
    messageHistory.push({
        role: role,
        content: content
    });
    
    // 如果是助手消息且有多个段落，分段显示
    if (role === 'assistant' && streamController.paragraphs.length > 0) {
        // 清空之前可能添加的段落
        const existingMessages = historyMessages.querySelectorAll(`.history-message.history-${role}.paragraph`);
        existingMessages.forEach(msg => msg.remove());
        
        // 添加每个段落
        streamController.paragraphs.forEach((paragraph, index) => {
            addParagraphToHistory(role, paragraph, index === 0);
        });
    } else {
        // 常规添加（用户消息或单段落助手消息）
        addParagraphToHistory(role, content, true);
    }
}

// 添加段落到历史记录
function addParagraphToHistory(role, content, isFirstParagraph) {
    // 创建消息容器
    const messageDiv = document.createElement('div');
    messageDiv.className = `history-message history-${role} paragraph`;
    
    // 只在第一段显示角色名称
    if (isFirstParagraph) {
        const roleSpan = document.createElement('div');
        roleSpan.className = 'history-role';
        
        // 使用当前角色名称
        if (role === 'user') {
            roleSpan.textContent = '你';
        } else if (role === 'assistant') {
            roleSpan.textContent = currentCharacter ? currentCharacter.name : '时雨绮罗';
        } else {
            roleSpan.textContent = '系统';
        }
        
        messageDiv.appendChild(roleSpan);
    }
    
    // 添加内容
    const contentDiv = document.createElement('div');
    contentDiv.className = 'history-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(contentDiv);
    historyMessages.appendChild(messageDiv);
    
    // 滚动到底部
    historyMessages.scrollTop = historyMessages.scrollHeight;
}

// 切换历史记录面板
function toggleHistory() {
    if (historyModal.style.display === 'flex') {
        historyModal.style.display = 'none';
    } else {
        historyModal.style.display = 'flex';
        // 滚动到底部
        historyMessages.scrollTop = historyMessages.scrollHeight;
    }
}

// 更新背景图片
function updateBackground(url) {
    // 获取背景元素
    const backgroundElements = document.getElementsByClassName('background-image');
    
    if (backgroundElements.length > 0) {
        const backgroundElement = backgroundElements[0];
        
        // 创建新背景元素
        const newBackground = document.createElement('div');
        newBackground.className = 'background-image';
        newBackground.style.backgroundImage = `url('${url}')`;
        newBackground.style.opacity = '0';
        
        // 添加新背景
        backgroundElement.parentNode.appendChild(newBackground);
        
        // 淡入新背景
        setTimeout(() => {
            newBackground.style.opacity = '1';
            
            // 淡出旧背景
            backgroundElement.style.opacity = '0';
            
            // 移除旧背景
            setTimeout(() => {
                backgroundElement.remove();
            }, 1000);
        }, 10);
    }
}

// 显示加载指示器
function showLoading() {
    isProcessing = true;
    loadingIndicator.style.display = 'flex';
    // 禁用输入框，但只在发送消息时
    // 其他操作（如加载角色、更换背景等）不应禁用输入框
    // disableInput() 应该在需要的地方显式调用
}

// 隐藏加载指示器
function hideLoading() {
    isProcessing = false;
    loadingIndicator.style.display = 'none';
    // 不要在这里启用输入框，因为可能还在流式输出中
    // enableInput() 应该在适当的地方显式调用
}

// 显示错误信息
function showError(message) {
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
}

// 隐藏错误信息
function hideError() {
    errorContainer.style.display = 'none';
}

// 加载角色数据
async function loadCharacters() {
    try {
        // 显示加载指示器（不禁用输入框）
        isProcessing = true;
        loadingIndicator.style.display = 'flex';
        
        // 发送API请求
        const response = await fetch('/api/characters');
        
        // 解析响应
        const data = await response.json();
        
        // 检查响应是否成功
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        // 更新角色数据
        availableCharacters = data.available_characters;
        currentCharacter = data.current_character;
        
        // 更新角色图片
        updateCharacterImage();
        
        // 更新当前消息
        if (currentCharacter && currentCharacter.welcome) {
            updateCurrentMessage('assistant', currentCharacter.welcome);
        } else {
            updateCurrentMessage('assistant', '欢迎使用CABM！我是您的AI助手，请输入消息开始对话。');
        }
        
    } catch (error) {
        console.error('加载角色数据失败:', error);
        showError(`加载角色数据失败: ${error.message}`);
        
        // 设置默认消息
        updateCurrentMessage('assistant', '欢迎使用CABM！我是您的AI助手，请输入消息开始对话。');
    } finally {
        // 隐藏加载指示器
        isProcessing = false;
        loadingIndicator.style.display = 'none';
    }
}

// 更新角色图片
function updateCharacterImage() {
    // 获取角色图片元素
    const characterImage = document.getElementById('characterImage');
    
    // 如果有当前角色，更新图片
    if (currentCharacter && characterImage) {
        characterImage.src = currentCharacter.image;
    }
}

// 切换角色选择弹窗
function toggleCharacterModal() {
    if (characterModal.style.display === 'flex') {
        characterModal.style.display = 'none';
    } else {
        // 显示角色选择弹窗
        characterModal.style.display = 'flex';
        
        // 渲染角色列表
        renderCharacterList();
    }
}

// 渲染角色列表
function renderCharacterList() {
    // 清空角色列表
    characterList.innerHTML = '';
    
    // 遍历可用角色
    availableCharacters.forEach(character => {
        // 创建角色卡片
        const card = document.createElement('div');
        card.className = `character-card ${currentCharacter && character.id === currentCharacter.id ? 'active' : ''}`;
        card.dataset.characterId = character.id;
        
        // 创建角色图片
        const imageContainer = document.createElement('div');
        imageContainer.className = 'character-card-image';
        
        const image = document.createElement('img');
        image.src = character.image;
        image.alt = character.name;
        
        imageContainer.appendChild(image);
        
        // 创建角色名称
        const name = document.createElement('div');
        name.className = 'character-card-name';
        name.textContent = character.name;
        name.style.color = character.color;
        
        // 创建角色描述
        const description = document.createElement('div');
        description.className = 'character-card-description';
        description.textContent = character.description;
        
        // 组装角色卡片
        card.appendChild(imageContainer);
        card.appendChild(name);
        card.appendChild(description);
        
        // 添加点击事件
        card.addEventListener('click', () => {
            selectCharacter(character.id);
        });
        
        // 添加到角色列表
        characterList.appendChild(card);
    });
}

// 选择角色
async function selectCharacter(characterId) {
    try {
        // 显示加载指示器
        showLoading();
        // 临时禁用输入框
        disableInput();
        
        // 发送API请求
        const response = await fetch(`/api/characters/${characterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // 解析响应
        const data = await response.json();
        
        // 检查响应是否成功
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        // 更新当前角色
        currentCharacter = data.character;
        
        // 更新角色图片
        updateCharacterImage();
        
        // 更新角色列表
        renderCharacterList();
        
        // 更新当前消息
        if (currentCharacter.welcome) {
            updateCurrentMessage('assistant', currentCharacter.welcome);
        }
        
        // 关闭角色选择弹窗
        toggleCharacterModal();
        
    } catch (error) {
        console.error('选择角色失败:', error);
        showError(`选择角色失败: ${error.message}`);
    } finally {
        // 隐藏加载指示器
        hideLoading();
        // 重新启用输入框
        enableInput();
    }
}

// 页面切换函数
function showHomePage() {
    homePage.classList.add('active');
    chatPage.classList.remove('active');
}

function showChatPage() {
    console.log('showChatPage 函数被调用');
    console.log('homePage:', homePage);
    console.log('chatPage:', chatPage);
    
    homePage.classList.remove('active');
    chatPage.classList.add('active');
    
    // 确保输入框在切换到聊天页面时是启用的
    enableInput();
    
    console.log('页面切换完成');
}

// 确认返回主页
function confirmBackToHome() {
    // 如果有未完成的对话，显示确认对话框
    if (messageHistory.length > 0) {
        showConfirmModal('返回主页将清空当前对话，确定要返回吗？', () => {
            // 清空对话历史
            messageHistory = [];
            historyMessages.innerHTML = '';
            
            // 返回主页
            showHomePage();
        });
    } else {
        // 直接返回主页
        showHomePage();
    }
}

// 确认退出应用
function confirmExit() {
    showConfirmModal('确定要退出应用吗？', exitApplication);
}

// 退出应用
async function exitApplication() {
    try {
        // 显示加载指示器
        showLoading();
        // 临时禁用输入框
        disableInput();
        
        // 发送API请求
        const response = await fetch('/api/exit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // 解析响应
        const data = await response.json();
        
        // 检查响应是否成功
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        // 关闭窗口
        window.close();
        
        // 如果window.close()不起作用（大多数浏览器会阻止），显示提示
        setTimeout(() => {
            showError('请手动关闭浏览器窗口');
        }, 1000);
        
    } catch (error) {
        console.error('退出应用失败:', error);
        showError(`退出应用失败: ${error.message}`);
        hideLoading();
        // 重新启用输入框
        enableInput();
    }
}

// 显示确认对话框
function showConfirmModal(message, callback) {
    confirmMessage.textContent = message;
    currentConfirmCallback = callback;
    confirmModal.style.display = 'flex';
}

// 隐藏确认对话框
function hideConfirmModal() {
    confirmModal.style.display = 'none';
    currentConfirmCallback = null;
}

// 处理确认对话框的确定按钮
function handleConfirmYes() {
    if (currentConfirmCallback) {
        currentConfirmCallback();
    }
    hideConfirmModal();
}

// 处理确认对话框的取消按钮
function handleConfirmNo() {
    hideConfirmModal();
}

// 继续输出
async function continueOutput() {
    if (isPaused) {
        isPaused = false;
        continueButton.classList.remove('active');
        
        // 移除点击提示
        const clickPrompt = document.querySelector('.click-prompt');
        if (clickPrompt) {
            clickPrompt.remove();
        }
        
        // 保存当前段落到历史记录
        if (currentMessage.textContent) {
            if (streamController.currentIndex >= 0) {
                // 添加当前段落到历史记录
                addParagraphToHistory('assistant', currentMessage.textContent, streamController.currentIndex === 0);
            }
        }
        
        // 增加当前段落索引
        streamController.currentIndex++;
        console.log(`继续输出，当前段落索引: ${streamController.currentIndex}`);
        
        // 清空当前消息，准备接收下一段
        currentMessage.textContent = '';
        
        // 显示加载指示器
        const loadingDots = document.createElement('div');
        loadingDots.className = 'loading-dots';
        loadingDots.textContent = '...';
        currentMessage.appendChild(loadingDots);
        
        // 继续流式响应处理
        try {
            // 如果有下一段，直接显示
            if (streamController.currentIndex < streamController.paragraphs.length) {
                console.log(`显示已有的下一段: ${streamController.paragraphs[streamController.currentIndex]}`);
                // 移除加载指示器
                currentMessage.innerHTML = '';
                updateCurrentMessage('assistant', streamController.paragraphs[streamController.currentIndex], true);
            } else {
                console.log('没有更多段落，启用输入框');
                // 移除加载指示器
                currentMessage.innerHTML = '';
                // 显示完成消息
                updateCurrentMessage('assistant', '回复已完成', true);
                // 启用输入框
                enableInput();
            }
        } catch (error) {
            console.error('继续流式响应失败:', error);
            // 移除加载指示器
            currentMessage.innerHTML = '';
            // 启用输入框
            enableInput();
        }
    }
}

// 继续流式响应处理
async function continueStreamResponse() {
    try {
        console.log('发送继续命令...');
        
        // 发送继续命令
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ control_action: 'continue' })
        });
        
        if (!response.ok) {
            throw new Error('继续命令失败');
        }
        
        // 解析JSON响应
        const data = await response.json();
        console.log('继续命令响应:', data);
        
        // 如果没有下一段，则启用输入框并返回
        if (!streamController.paragraphs[streamController.currentIndex]) {
            console.log('没有更多段落，启用输入框');
            // 移除加载指示器
            currentMessage.innerHTML = '';
            // 显示完成消息
            updateCurrentMessage('assistant', '回复已完成', true);
            // 启用输入框
            enableInput();
            return;
        }
        
        // 显示下一段
        console.log(`显示下一段: ${streamController.paragraphs[streamController.currentIndex]}`);
        // 移除加载指示器
        currentMessage.innerHTML = '';
        // 显示下一段内容
        updateCurrentMessage('assistant', streamController.paragraphs[streamController.currentIndex], true);
            
            try {
                // 尝试解析JSON
                const lines = chunk.split('\n').filter(line => line.trim());
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        
                        if (jsonStr === '[DONE]') {
                            console.log('收到[DONE]标记');
                            // 启用输入框
                            enableInput();
                            continue;
                        }
                        
                        try {
                            const data = JSON.parse(jsonStr);
                            console.log('解析的JSON数据:', data);
                            
                            // 处理流式控制信息
                            if (data.stream_control) {
                                // 如果段落完成且需要暂停
                                if (data.stream_control.paragraph_complete && data.stream_control.pause) {
                                    isPaused = true;
                                    console.log('段落完成，需要暂停');
                                    
                                    // 添加完整段落到当前显示
                                    if (data.stream_control.paragraph) {
                                        currentParagraphResponse = data.stream_control.paragraph;
                                        streamController.paragraphs.push(currentParagraphResponse);
                                        updateCurrentMessage('assistant', currentParagraphResponse, true);
                                    }
                                    
                                    // 等待用户点击继续
                                    continueButton.classList.add('active');
                                    
                                    // 添加提示信息到对话框右上角
                                    const clickPrompt = document.createElement('div');
                                    clickPrompt.className = 'click-prompt';
                                    clickPrompt.textContent = '点击屏幕继续...';
                                    dialogBox.appendChild(clickPrompt);
                                    
                                    // 暂停处理，等待用户点击
                                    return;
                                }
                                
                                // 如果是结束标记
                                if (data.stream_control.is_complete) {
                                    streamController.isComplete = true;
                                    console.log('收到完成标记');
                                    
                                    // 添加最后一段到历史记录
                                    if (currentParagraphResponse) {
                                        const lastIndex = streamController.paragraphs.length - 1;
                                        addParagraphToHistory('assistant', currentParagraphResponse, lastIndex === 0);
                                    }
                                    
                                    // 启用输入框
                                    enableInput();
                                    return;
                                }
                                
                                // 处理增量内容
                                if (data.stream_control.content) {
                                    currentParagraphResponse += data.stream_control.content;
                                    updateCurrentMessage('assistant', currentParagraphResponse, true);
                                }
                            }
                            // 处理标准格式（兼容旧格式）
                            else if (data.choices && data.choices[0] && data.choices[0].delta) {
                                const delta = data.choices[0].delta;
                                
                                if (delta.content) {
                                    currentParagraphResponse += delta.content;
                                    updateCurrentMessage('assistant', currentParagraphResponse, true);
                                }
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
        
        // 如果到这里说明流式响应结束，启用输入框
        console.log('流式响应处理完成，启用输入框');
        enableInput();
        
    } catch (error) {
        console.error('继续流式响应失败:', error);
        enableInput();
    }
}