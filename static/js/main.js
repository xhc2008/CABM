// DOM元素

// 页面元素

const homePage = document.getElementById('homePage');

const chatPage = document.getElementById('chatPage');

const startButton = document.getElementById('startButton');

const exitButton = document.getElementById('exitButton');

const backButton = document.getElementById('backButton');



// 对话元素

const characterName = document.getElementById('characterName');

const currentMessage = document.getElementById('currentMessage');

const messageInput = document.getElementById('messageInput');

const sendButton = document.getElementById('sendButton');

// const clearButton = document.getElementById('clearButton'); // 已禁用：清空对话按钮

const backgroundButton = document.getElementById('backgroundButton');

const historyButton = document.getElementById('historyButton');

const characterButton = document.getElementById('characterButton');

const continueButton = document.getElementById('continueButton');

const skipButton = document.getElementById('skipButton');

const micButton = document.getElementById('micButton');

const clickToContinue = document.getElementById('clickToContinue');
const optionButtonsContainer = document.getElementById('optionButtonsContainer');
const optionButtons = document.getElementById('optionButtons');

const historyModal = document.getElementById('historyModal');

const historyMessages = document.getElementById('historyMessages');

const closeHistoryButton = document.getElementById('closeHistoryButton');

const characterModal = document.getElementById('characterModal');

const characterList = document.getElementById('characterList');

const closeCharacterButton = document.getElementById('closeCharacterButton');



// 确认对话框

const confirmModal = document.getElementById('confirmModal');

const confirmMessage = document.getElementById('confirmMessage');

const confirmYesButton = document.getElementById('confirmYesButton');

const confirmNoButton = document.getElementById('confirmNoButton');

const closeConfirmButton = document.getElementById('closeConfirmButton');



// 加载和错误元素

const loadingIndicator = document.getElementById('loadingIndicator');

const errorContainer = document.getElementById('errorContainer');

const errorMessage = document.getElementById('errorMessage');

const errorCloseButton = document.getElementById('errorCloseButton');



// 角色数据

let availableCharacters = [];

let currentCharacter = null;



// 状态变量

let isProcessing = false;

let isPaused = false;

let messageHistory = [];
let currentTypingTimeout = null;

let currentConfirmCallback = null;


// 初始化

document.addEventListener('DOMContentLoaded', () => {

    // 加载角色数据

    loadCharacters();

    // 绑定页面切换事件

    startButton.addEventListener('click', showChatPage);

    backButton.addEventListener('click', confirmBackToHome);

    exitButton.addEventListener('click', confirmExit);

    // 绑定对话事件

    sendButton.addEventListener('click', sendMessage);

    // clearButton.addEventListener('click', clearChat); // 已禁用：清空对话按钮事件

    backgroundButton.addEventListener('click', changeBackground);

    historyButton.addEventListener('click', toggleHistory);

    closeHistoryButton.addEventListener('click', toggleHistory);

    characterButton.addEventListener('click', toggleCharacterModal);

    closeCharacterButton.addEventListener('click', toggleCharacterModal);

    continueButton.addEventListener('click', continueOutput);

    skipButton.addEventListener('click', skipTyping);

    micButton.addEventListener('click', toggleRecording);

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

    // 绑定点击事件继续输出

    currentMessage.addEventListener('click', continueOutput);

    clickToContinue.addEventListener('click', continueOutput);

});

// 流式处理器实例
let streamProcessor = null;

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

    // 创建新的流式处理器
    streamProcessor = new StreamProcessor();

    // 跟踪已添加到历史记录的内容长度
    let addedToHistoryLength = 0;

    // 设置回调函数
    streamProcessor.setCallbacks(
        // 字符回调 - 每个字符输出时调用
        (fullContent) => {
            updateCurrentMessage('assistant', fullContent.substring(addedToHistoryLength), true);
        },
        // 暂停回调 - 遇到标点符号暂停时调用
        (fullContent) => {
            // 设置暂停状态
            isPaused = true;

            // 只添加新的内容段落到历史记录
            const newContent = fullContent.substring(addedToHistoryLength);
            if (newContent) {
                const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                addToHistory('assistant', newContent, characterName);
                addedToHistoryLength = fullContent.length;
            }

            // 显示继续提示（不传递文字参数，避免添加到聊天内容）
            showContinuePrompt();
        },
        // 完成回调 - 所有内容处理完成时调用
        (fullContent) => {
            // 添加任何剩余的未添加到历史记录的内容
            const remainingContent = fullContent.substring(addedToHistoryLength);
            if (remainingContent) {
                const characterName = currentCharacter ? currentCharacter.name : 'AI助手';
                addToHistory('assistant', remainingContent, characterName);
            }

            // **获取提取的【】内容并处理**
            const extractedContents = streamProcessor.getExtractedBracketContents();
            if (extractedContents.length > 0) {
                console.log('提取的【】内容:', extractedContents); // **这里可以看到提取的内容**
                // 在这里可以对提取的内容进行进一步处理
                // 例如：解析心情状态、系统指令等
                handleExtractedBracketContents(extractedContents);
            }

            // 隐藏继续提示
            hideContinuePrompt();

            // 启用用户输入
            enableUserInput();

            // 重置暂停状态
            isPaused = false;
            
            // 显示选项按钮（如果有的话）
            if (window.pendingOptions && window.pendingOptions.length > 0) {
                showOptionButtons(window.pendingOptions);
                window.pendingOptions = null; // 清空待处理的选项
            }
        }
    );

    // 更新当前消息为用户消息
    updateCurrentMessage('user', message);

    // 添加到历史记录
    addToHistory('user', message);

    // 隐藏选项按钮
    hideOptionButtons();
    
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

        // 检查响应状态
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '请求失败');
        }

        // 获取响应的读取器
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

            // 解码响应数据
            const chunk = decoder.decode(value, { stream: true });

            try {
                // 解析流式数据
                const lines = chunk.split('\n').filter(line => line.trim());

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);

                        if (jsonStr === '[DONE]') {
                            // 标记流式处理结束
                            streamProcessor.markEnd();
                            break;
                        }

                        try {
                            const data = JSON.parse(jsonStr);

                            // 处理错误
                            if (data.error) {
                                throw new Error(data.error);
                            }

                            // 处理内容
                            if (data.content) {
                                // 将数据添加到流式处理器
                                streamProcessor.addData(data.content);
                            }
                            
                            // 处理选项数据
                            if (data.options) {
                                // 存储选项数据，等待输出完成后显示
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

        // 重置流式处理器
        if (streamProcessor) {
            streamProcessor.reset();
        }
    }

}



// 清空对话 - 已禁用但保留功能代码
/*
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
*/



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
            characterName.textContent = 'AI';
            characterName.style.color = '#ffeb3b';

        }

    } else if (role === 'system') {

        characterName.textContent = '系统';

        characterName.style.color = '#4caf50';

    }

    // 如果是流式输出，直接更新内容（【】内容已在流式处理器中过滤）

    if (isStreaming) {

        currentMessage.textContent = content;

        return;

    }

    // 对于非流式输出，需要手动过滤【】内容
    const filteredContent = content.replace(/【[^】]*】/g, '');
    currentMessage.textContent = filteredContent;

}









// 添加消息到历史记录
function addToHistory(role, content, customName = null) {
    // 过滤内容中的【】标记
    const filteredContent = content.replace(/【[^】]*】/g, '');

    // 添加到内存中的历史记录

    messageHistory.push({

        role: role === 'assistant_continue' ? 'assistant' : role,

        content: filteredContent

    });

    // 添加到历史记录面板

    const messageDiv = document.createElement('div');

    messageDiv.className = `history-message history-${role}`;

    const roleSpan = document.createElement('div');

    roleSpan.className = 'history-role';

    // 使用当前角色名称或自定义名称
    let roleName = '';
    if (role === 'user') {
        roleName = '你';
        roleSpan.textContent = roleName;
    } else if (role === 'assistant') {
        roleName = customName || (currentCharacter ? currentCharacter.name : 'AI');
        roleSpan.textContent = roleName;
    } else {
        roleName = '系统';
        roleSpan.textContent = roleName;
    }

    const contentDiv = document.createElement('div');

    contentDiv.className = 'history-content';

    // 为每个段落添加角色名称前缀
    if (role === 'assistant') {
        contentDiv.textContent = filteredContent;
    } else {
        contentDiv.textContent = filteredContent;
    }

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

        // 调试：输出角色信息
        console.log('当前角色信息:', currentCharacter);

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
    // 获取角色图片元素和容器
    const characterImage = document.getElementById('characterImage');
    const characterContainer = document.querySelector('.character-container');

    // 如果有当前角色，更新图片
    if (currentCharacter && characterImage) {
        characterImage.src = currentCharacter.image;
        
        // 根据CALIB值调整位置
        if (characterContainer && typeof currentCharacter.calib !== 'undefined') {
            // 基准值为50%，根据CALIB值进行调整
            const baseTop = 50;
            const adjustedTop = baseTop + currentCharacter.calib;
            console.log(`角色位置调整: CALIB=${currentCharacter.calib}, 调整后位置=${adjustedTop}%`);
            characterContainer.style.top = `${adjustedTop}%`;
        } else if (characterContainer) {
            // 如果没有CALIB值，使用默认位置
            console.log('使用默认位置: 50%');
            characterContainer.style.top = '50%';
        }
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

        // 调试：输出角色信息
        console.log('切换后的角色信息:', currentCharacter);

        // 更新角色图片

        updateCharacterImage();

        // 更新角色列表

        renderCharacterList();

        // 更新当前消息

        if (currentCharacter.welcome) {

            updateCurrentMessage('assistant', currentCharacter.welcome);

        }
        
        // 隐藏选项按钮
        hideOptionButtons();

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



// 页面切换函数

function showHomePage() {

    homePage.classList.add('active');

    chatPage.classList.remove('active');

}



function showChatPage() {

    homePage.classList.remove('active');

    chatPage.classList.add('active');

}



// 确认返回主页

function confirmBackToHome() {

    // 如果有未完成的对话，显示确认对话框

    if (messageHistory.length > 0) {

        showConfirmModal('确定要返回吗？', () => {

            // 清空对话历史

            // messageHistory = [];

            // historyMessages.innerHTML = '';

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

function continueOutput() {
    console.log('continueOutput called, isPaused:', isPaused, 'streamProcessor:', streamProcessor);

    if (isPaused && streamProcessor) {
        isPaused = false;
        hideContinuePrompt();

        // 继续流式处理
        streamProcessor.continue();
    } else if (streamProcessor) {
        // 如果没有暂停但有流式处理器，也尝试继续
        hideContinuePrompt();
        streamProcessor.continue();
    }
}

// 跳过打字效果
function skipTyping() {
    if (streamProcessor && streamProcessor.isProcessing()) {
        // 跳过当前流式处理
        streamProcessor.skip();

        // 重置状态
        isPaused = false;
        hideContinuePrompt();
        enableUserInput();
    }
}

let recognition; // 全局变量存储语音识别实例

function toggleRecording() {
    let isRecording = micButton.classList.toggle('recording');
    if (isRecording) {
        if (!recognition) {
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'zh-CN'; // 设置语言为中文
            recognition.interimResults = false; // 不需要中间结果
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript.trim();
                if (transcript) {
                    // 将识别到的文本设置到输入框
                    messageInput.value += transcript;
                }
            };
            recognition.onerror = (event) => {
                console.error('语音识别错误:', event.error);
                showError(`语音识别错误: ${event.error}`);
            };
            recognition.onend = () => {
                micButton.classList.remove('recording');
            }
        }
        recognition.start();
    } else {
        // 停止语音识别
        if (recognition) {
            recognition.stop();
        }
    }
}

// 禁用用户输入
function disableUserInput() {
    messageInput.disabled = true;
    sendButton.disabled = true;
    micButton.disabled = true;
    messageInput.placeholder = "AI正在回复中...";
}

// 启用用户输入
function enableUserInput() {
    messageInput.disabled = false;
    sendButton.disabled = false;
    micButton.disabled = false;
    messageInput.placeholder = "输入消息...";
}

// 显示"点击屏幕继续"提示
function showContinuePrompt(promptText = '▽') {
    // 激活继续按钮来显示提示
    continueButton.classList.add('active');

    // 如果有clickToContinue元素，显示它
    if (clickToContinue) {
        clickToContinue.style.display = 'block';
        clickToContinue.textContent = promptText;
    }

    // 移除之前的监听器（如果存在）
    if (currentScreenClickHandler) {
        document.removeEventListener('click', currentScreenClickHandler);
    }

    // 创建新的点击监听器
    currentScreenClickHandler = (e) => {
        // 检查点击的目标是否是按钮或其他交互元素
        const clickedElement = e.target;

        // 如果点击的是按钮、输入框或其他交互元素，不触发继续
        if (clickedElement.tagName === 'BUTTON' ||
            clickedElement.tagName === 'INPUT' ||
            clickedElement.tagName === 'TEXTAREA' ||
            clickedElement.tagName === 'IMG' ||
            clickedElement.classList.contains('modal') ||
            clickedElement.classList.contains('btn') ||
            clickedElement.classList.contains('continue-prompt') ||
            clickedElement.closest('button') ||
            clickedElement.closest('.btn') ||
            clickedElement.closest('.modal') ||
            clickedElement.closest('.history-modal') ||
            clickedElement.closest('.character-modal') ||
            clickedElement.closest('.confirm-modal') ||
            clickedElement.closest('.control-buttons') ||
            clickedElement.closest('.user-input-container') ||
            clickedElement.closest('.chat-header') ||
            clickedElement.closest('.character-container') ||
            clickedElement.closest('.continue-prompt')) {
            return; // 不处理按钮等元素的点击
        }

        // 只有点击对话区域或背景区域才触发继续
        if (clickedElement.closest('.dialog-container') ||
            clickedElement.closest('.background-container') ||
            clickedElement === document.body ||
            clickedElement.classList.contains('page')) {
            console.log('Screen clicked during pause');
            continueOutput();
        }
    };

    // 延迟添加监听器，避免立即触发
    setTimeout(() => {
        document.addEventListener('click', currentScreenClickHandler);
    }, 100);
}

// 全局变量来存储当前的点击监听器
let currentScreenClickHandler = null;

// 显示选项按钮
function showOptionButtons(options) {
    // 清空现有选项
    optionButtons.innerHTML = '';
    
    // 创建选项按钮
    options.forEach((option, index) => {
        const button = document.createElement('button');
        button.className = 'option-button';
        button.textContent = option;
        button.addEventListener('click', () => {
            selectOption(option);
        });
        optionButtons.appendChild(button);
    });
    
    // 显示选项容器
    optionButtonsContainer.classList.add('show');
}

// 隐藏选项按钮
function hideOptionButtons() {
    optionButtonsContainer.classList.remove('show');
    optionButtons.innerHTML = '';
}

// 选择选项
function selectOption(option) {
    // 隐藏选项按钮
    hideOptionButtons();
    
    // 将选项内容设置到输入框
    messageInput.value = option;
    
    // 自动发送消息
    sendMessage();
}

// **处理提取的【】内容的函数**
function handleExtractedBracketContents(contents) {
    // 这里是处理提取内容的地方，你可以在这里添加自定义逻辑
    console.log('处理提取的【】内容:', contents);
    
    // 示例：解析心情状态
    contents.forEach((content, index) => {
        console.log(`第${index + 1}个【】内容:`, content);
        
        // 如果内容是数字，可能是心情状态
        if (/^\d+$/.test(content.trim())) {
            const moodNumber = parseInt(content.trim());
            const moods = ['', '平静', '兴奋', '愤怒', '失落'];
            if (moodNumber >= 1 && moodNumber <= 4) {
                console.log(`检测到心情状态: ${moodNumber} - ${moods[moodNumber]}`);
                // 在这里可以根据心情状态做相应处理，比如改变UI样式等
            }
        }
    });
    
    // 你可以在这里添加更多的处理逻辑
    // 例如：存储到全局变量、发送到服务器、更新UI等
}

// 隐藏"点击屏幕继续"提示
function hideContinuePrompt() {
    // 隐藏点击继续提示
    if (clickToContinue) {
        clickToContinue.style.display = 'none';
    }

    // 取消激活继续按钮
    continueButton.classList.remove('active');

    // 移除全屏点击监听器
    if (currentScreenClickHandler) {
        document.removeEventListener('click', currentScreenClickHandler);
        currentScreenClickHandler = null;
    }
}


function registrationShortcuts(config) {
    document.addEventListener('keydown', e => { 
        if (e.key in config) {
            // For single-letter keys, require Alt to be pressed
            if (e.key.length === 1) {
                if (e.altKey) {
                    config[e.key]();
                }
            }
            else {
                config[e.key]();
            }
        }
    });
}

registrationShortcuts({
    Enter: continueOutput,
    s: skipTyping,
    h: toggleHistory,
    b: changeBackground,
    // c: clearChat, // 已禁用：清空对话快捷键
    // ç: clearChat // 已禁用：清空对话快捷键（为了解决部分快捷键冲突）
});
