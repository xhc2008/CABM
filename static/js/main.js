// DOM元素
const characterName = document.getElementById('characterName');
const currentMessage = document.getElementById('currentMessage');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const clearButton = document.getElementById('clearButton');
const backgroundButton = document.getElementById('backgroundButton');
const historyButton = document.getElementById('historyButton');
const characterButton = document.getElementById('characterButton');
const autoButton = document.getElementById('autoButton');
const skipButton = document.getElementById('skipButton');
const historyModal = document.getElementById('historyModal');
const historyMessages = document.getElementById('historyMessages');
const closeHistoryButton = document.getElementById('closeHistoryButton');
const characterModal = document.getElementById('characterModal');
const characterList = document.getElementById('characterList');
const closeCharacterButton = document.getElementById('closeCharacterButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorContainer = document.getElementById('errorContainer');
const errorMessage = document.getElementById('errorMessage');
const errorCloseButton = document.getElementById('errorCloseButton');

// 角色数据
let availableCharacters = [];
let currentCharacter = null;

// 状态变量
let isProcessing = false;
let isAutoMode = false;
let messageHistory = [];
let typingSpeed = 50; // 打字速度（毫秒/字符）
let currentTypingTimeout = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 加载角色数据
    loadCharacters();
    
    // 绑定事件
    sendButton.addEventListener('click', sendMessage);
    clearButton.addEventListener('click', clearChat);
    backgroundButton.addEventListener('click', changeBackground);
    historyButton.addEventListener('click', toggleHistory);
    closeHistoryButton.addEventListener('click', toggleHistory);
    characterButton.addEventListener('click', toggleCharacterModal);
    closeCharacterButton.addEventListener('click', toggleCharacterModal);
    autoButton.addEventListener('click', toggleAutoMode);
    skipButton.addEventListener('click', skipTyping);
    errorCloseButton.addEventListener('click', hideError);
    
    // 绑定回车键发送消息
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

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
                            
                            // 处理讯飞星火API的流式输出格式
                            if (data.payload) {
                                let content = null;
                                
                                // 尝试不同的路径获取内容
                                if (data.payload.choices) {
                                    if (Array.isArray(data.payload.choices) && data.payload.choices.length > 0) {
                                        content = data.payload.choices[0].content;
                                    } else if (data.payload.choices.text && data.payload.choices.text.length > 0) {
                                        content = data.payload.choices.text[0].content;
                                    }
                                }
                                
                                if (content) {
                                    fullResponse += content;
                                    updateCurrentMessage('assistant', fullResponse, true);
                                }
                            }
                            // 处理标准格式
                            else if (data.choices && data.choices[0] && data.choices[0].delta) {
                                const delta = data.choices[0].delta;
                                
                                if (delta.content) {
                                    fullResponse += delta.content;
                                    updateCurrentMessage('assistant', fullResponse, true);
                                }
                            }
                            // 直接处理内容字段（如果存在）
                            else if (data.content) {
                                fullResponse += data.content;
                                updateCurrentMessage('assistant', fullResponse, true);
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
        
        // 添加完整响应到历史记录
        if (fullResponse) {
            addToHistory('assistant', fullResponse);
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        showError(`发送消息失败: ${error.message}`);
        hideLoading();
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
        currentMessage.textContent = content;
        return;
    }
    
    // 如果是自动模式或者是用户消息，使用打字机效果
    if (isAutoMode && role !== 'user') {
        typeMessage(content);
    } else {
        // 直接显示消息
        currentMessage.textContent = content;
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
    if (currentTypingTimeout) {
        clearTimeout(currentTypingTimeout);
        currentTypingTimeout = null;
        
        // 获取当前正在打字的完整消息
        const lastMessage = messageHistory[messageHistory.length - 1];
        if (lastMessage) {
            currentMessage.textContent = lastMessage.content;
        }
    }
}

// 切换自动模式
function toggleAutoMode() {
    isAutoMode = !isAutoMode;
    autoButton.textContent = isAutoMode ? '手动' : '自动';
    
    if (isAutoMode) {
        autoButton.classList.add('primary-btn');
        autoButton.classList.remove('secondary-btn');
    } else {
        autoButton.classList.remove('primary-btn');
        autoButton.classList.add('secondary-btn');
    }
}

// 添加消息到历史记录
function addToHistory(role, content) {
    // 添加到内存中的历史记录
    messageHistory.push({
        role: role,
        content: content
    });
    
    // 添加到历史记录面板
    const messageDiv = document.createElement('div');
    messageDiv.className = `history-message history-${role}`;
    
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
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'history-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(roleSpan);
    messageDiv.appendChild(contentDiv);
    historyMessages.appendChild(messageDiv);
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
}

// 隐藏加载指示器
function hideLoading() {
    isProcessing = false;
    loadingIndicator.style.display = 'none';
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
        // 显示加载指示器
        showLoading();
        
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
        hideLoading();
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
    }
}