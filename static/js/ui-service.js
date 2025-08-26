// UI服务模块 - 处理界面交互和模态框管理
import { 
    homePage, 
    chatPage, 
    characterName, 
    currentMessage, 
    messageInput, 
    sendButton, 
    micButton,
    continueButton,
    clickToContinue,
    optionButtonsContainer,
    optionButtons,
    historyModal,
    historyMessages,
    confirmModal,
    confirmMessage,
    loadingIndicator,
    errorContainer,
    errorMessage
} from './dom-elements.js';

// 状态变量
let isProcessing = false;
let isPaused = false;
let messageHistory = [];
let currentTypingTimeout = null;
let currentConfirmCallback = null;
let currentScreenClickHandler = null;

// 获取状态
export function getIsProcessing() {
    return isProcessing;
}

export function setIsProcessing(value) {
    isProcessing = value;
}

export function getIsPaused() {
    return isPaused;
}

export function setIsPaused(value) {
    isPaused = value;
}

export function getMessageHistory() {
    return messageHistory;
}

// 显示加载指示器
export function showLoading() {
    isProcessing = true;
    loadingIndicator.style.display = 'flex';
}

// 隐藏加载指示器
export function hideLoading() {
    isProcessing = false;
    loadingIndicator.style.display = 'none';
}

// 显示错误信息
export function showError(message) {
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
}

// 隐藏错误信息
export function hideError() {
    errorContainer.style.display = 'none';
}

// 更新当前消息
export function updateCurrentMessage(role, content, isStreaming = false) {
    if (!isStreaming && currentTypingTimeout) {
        clearTimeout(currentTypingTimeout);
        currentTypingTimeout = null;
    }

    // 更新角色名称
    if (role === 'user') {
        characterName.textContent = '你';
        characterName.style.color = '#90caf9';
    } else if (role === 'assistant') {
        // 需要从角色服务获取当前角色
        const currentCharacter = window.getCurrentCharacter ? window.getCurrentCharacter() : null;
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

    currentMessage.textContent = content;
}

// 添加消息到历史记录
export function addToHistory(role, content, customName = null) {
    messageHistory.push({
        role: role === 'assistant_continue' ? 'assistant' : role,
        content: content
    });

    const messageDiv = document.createElement('div');
    messageDiv.className = `history-message history-${role}`;

    const roleSpan = document.createElement('div');
    roleSpan.className = 'history-role';

    let roleName = '';
    if (role === 'user') {
        roleName = '你';
        roleSpan.textContent = roleName;
    } else if (role === 'assistant') {
        const currentCharacter = window.getCurrentCharacter ? window.getCurrentCharacter() : null;
        roleName = customName || (currentCharacter ? currentCharacter.name : 'AI');
        roleSpan.textContent = roleName;
    } else {
        roleName = '系统';
        roleSpan.textContent = roleName;
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'history-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(roleSpan);
    messageDiv.appendChild(contentDiv);
    historyMessages.appendChild(messageDiv);
}

// 切换历史记录面板（保留原有实现作为备用）
export function toggleHistoryLegacy() {
    if (historyModal.style.display === 'flex') {
        historyModal.style.display = 'none';
    } else {
        historyModal.style.display = 'flex';
        historyMessages.scrollTop = historyMessages.scrollHeight;
    }
}

// 新的历史记录切换函数（使用历史记录服务）
export function toggleHistory() {
    // 动态导入历史记录服务
    import('./history-service.js').then(module => {
        module.toggleHistory();
    }).catch(error => {
        console.error('加载历史记录服务失败，使用备用方案:', error);
        toggleHistoryLegacy();
    });
}

// 更新背景图片
export function updateBackground(url) {
    const backgroundElements = document.getElementsByClassName('background-image');
    if (backgroundElements.length > 0) {
        const backgroundElement = backgroundElements[0];
        const newBackground = document.createElement('div');
        newBackground.className = 'background-image';
        newBackground.style.backgroundImage = `url('${url}')`;
        newBackground.style.opacity = '0';

        backgroundElement.parentNode.appendChild(newBackground);

        setTimeout(() => {
            newBackground.style.opacity = '1';
            backgroundElement.style.opacity = '0';
            setTimeout(() => {
                backgroundElement.remove();
            }, 1000);
        }, 10);
    }
}

// 页面切换函数
export function showHomePage() {
    homePage.classList.add('active');
    chatPage.classList.remove('active');
}

export function showChatPage() {
    homePage.classList.remove('active');
    chatPage.classList.add('active');
}

// 确认返回主页
export function confirmBackToHome() {
    if (messageHistory.length > 0) {
        showConfirmModal('确定要返回吗？', () => {
            showHomePage();
        });
    } else {
        showHomePage();
    }
}

// 确认退出应用
export function confirmExit() {
    showConfirmModal('确定要退出应用吗？', exitApplication);
}

// 退出应用
async function exitApplication() {
    try {
        showLoading();
        
        const response = await fetch('/api/exit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        window.close();
        
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
export function showConfirmModal(message, callback) {
    confirmMessage.textContent = message;
    currentConfirmCallback = callback;
    confirmModal.style.display = 'flex';
}

// 隐藏确认对话框
export function hideConfirmModal() {
    confirmModal.style.display = 'none';
    currentConfirmCallback = null;
}

// 处理确认对话框的确定按钮
export function handleConfirmYes() {
    if (currentConfirmCallback) {
        currentConfirmCallback();
    }
    hideConfirmModal();
}

// 处理确认对话框的取消按钮
export function handleConfirmNo() {
    hideConfirmModal();
}

// 禁用用户输入
export function disableUserInput() {
    messageInput.disabled = true;
    sendButton.disabled = true;
    micButton.disabled = true;
    messageInput.placeholder = "角色正在回复中...";
}

// 启用用户输入
export function enableUserInput() {
    messageInput.disabled = false;
    sendButton.disabled = false;
    micButton.disabled = false;
    messageInput.placeholder = "输入消息...";
}

// 显示"点击屏幕继续"提示
export function showContinuePrompt(promptText = '▽') {
    continueButton.classList.add('active');

    if (clickToContinue) {
        clickToContinue.style.display = 'block';
        clickToContinue.textContent = promptText;
    }

    if (currentScreenClickHandler) {
        document.removeEventListener('click', currentScreenClickHandler);
    }

    currentScreenClickHandler = (e) => {
        const clickedElement = e.target;

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
            return;
        }

        if (clickedElement.closest('.dialog-container') ||
            clickedElement.closest('.background-container') ||
            clickedElement === document.body ||
            clickedElement.classList.contains('page')) {
            console.log('Screen clicked during pause');
            if (window.continueOutput) {
                window.continueOutput();
            }
        }
    };

    setTimeout(() => {
        document.addEventListener('click', currentScreenClickHandler);
    }, 100);
}

// 隐藏"点击屏幕继续"提示
export function hideContinuePrompt() {
    if (clickToContinue) {
        clickToContinue.style.display = 'none';
    }

    continueButton.classList.remove('active');

    if (currentScreenClickHandler) {
        document.removeEventListener('click', currentScreenClickHandler);
        currentScreenClickHandler = null;
    }
}

// 显示选项按钮
export function showOptionButtons(options) {
    optionButtons.innerHTML = '';

    options.forEach((option, index) => {
        const button = document.createElement('button');
        button.className = 'option-button';
        button.textContent = option;
        button.addEventListener('click', () => {
            selectOption(option);
        });
        optionButtons.appendChild(button);
    });

    optionButtonsContainer.classList.add('show');
}

// 隐藏选项按钮
export function hideOptionButtons() {
    optionButtonsContainer.classList.remove('show');
    optionButtons.innerHTML = '';
}

// 选择选项
function selectOption(option) {
    hideOptionButtons();
    messageInput.value = option;
    // 需要调用发送消息函数
    if (window.sendMessage) {
        window.sendMessage();
    }
}

// 暴露给全局使用
window.hideOptionButtons = hideOptionButtons;
