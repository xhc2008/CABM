/**
 * 用户输入框增强功能
 */

class InputEnhancements {
    constructor() {
        this.messageInput = null;
        this.sendButton = null;
        this.charCount = null;
        this.maxLength = 2000;
        this.init();
    }

    init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupElements());
        } else {
            this.setupElements();
        }
    }

    setupElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.charCount = document.getElementById('charCount');

        if (!this.messageInput || !this.sendButton || !this.charCount) {
            return; // 如果元素不存在，可能不在聊天页面
        }

        this.bindEvents();
        this.updateCharCount();
        this.updateSendButtonState();
    }

    bindEvents() {
        // 字符计数更新
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateSendButtonState();
        });

        // 键盘快捷键
        this.messageInput.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });

        // 自动调整高度
        this.messageInput.addEventListener('input', () => {
            this.autoResize();
        });

        // 粘贴事件处理
        this.messageInput.addEventListener('paste', (e) => {
            setTimeout(() => {
                this.updateCharCount();
                this.updateSendButtonState();
                this.autoResize();
            }, 0);
        });

        // 发送按钮点击
        this.sendButton.addEventListener('click', () => {
            this.handleSend();
        });

        // 焦点事件
        this.messageInput.addEventListener('focus', () => {
            this.onFocus();
        });

        this.messageInput.addEventListener('blur', () => {
            this.onBlur();
        });
    }

    updateCharCount() {
        const currentLength = this.messageInput.value.length;
        this.charCount.textContent = `${currentLength}/${this.maxLength}`;
        
        // 根据字符数改变颜色
        if (currentLength > this.maxLength * 0.9) {
            this.charCount.style.color = '#ff6b6b';
        } else if (currentLength > this.maxLength * 0.7) {
            this.charCount.style.color = '#ffa726';
        } else {
            this.charCount.style.color = 'rgba(255, 255, 255, 0.6)';
        }
    }

    updateSendButtonState() {
        const hasContent = this.messageInput.value.trim().length > 0;
        const withinLimit = this.messageInput.value.length <= this.maxLength;
        
        if (hasContent && withinLimit) {
            this.sendButton.disabled = false;
            this.sendButton.classList.add('ready');
            this.sendButton.title = '发送消息 (Enter)';
        } else {
            this.sendButton.disabled = true;
            this.sendButton.classList.remove('ready');
            if (!hasContent) {
                this.sendButton.title = '请输入消息';
            } else {
                this.sendButton.title = '消息过长，请缩短';
            }
        }
    }

    handleKeydown(e) {
        // Ctrl+Enter 发送消息
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            this.handleSend();
            return;
        }

        // Shift+Enter 换行（默认行为）
        if (e.shiftKey && e.key === 'Enter') {
            return;
        }

        // Enter 发送消息（可选，根据用户偏好）
        if (e.key === 'Enter' && !e.shiftKey) {
            // 检查是否启用了Enter发送
            const enterToSend = localStorage.getItem('enterToSend') !== 'false';
            if (enterToSend) {
                e.preventDefault();
                this.handleSend();
            }
        }

        // Escape 清空输入框
        if (e.key === 'Escape') {
            this.messageInput.value = '';
            this.updateCharCount();
            this.updateSendButtonState();
            this.autoResize();
        }
    }

    autoResize() {
        // 自动调整textarea高度
        this.messageInput.style.height = 'auto';
        const scrollHeight = this.messageInput.scrollHeight;
        const minHeight = 80;
        const maxHeight = 200;
        
        const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
        this.messageInput.style.height = newHeight + 'px';
    }

    handleSend() {
        if (this.sendButton.disabled) {
            return;
        }

        const message = this.messageInput.value.trim();
        if (!message) {
            return;
        }

        // 直接调用全局的sendMessage函数
        if (window.sendMessage) {
            window.sendMessage();
        }

        // 注意：不在这里清空输入框，让sendMessage函数自己处理
        // 因为sendMessage函数需要从输入框获取内容
    }

    onFocus() {
        // 输入框获得焦点时的处理
        this.messageInput.parentElement.parentElement.classList.add('focused');
    }

    onBlur() {
        // 输入框失去焦点时的处理
        this.messageInput.parentElement.parentElement.classList.remove('focused');
    }

    // 公共方法：设置输入框内容
    setMessage(message) {
        if (this.messageInput) {
            this.messageInput.value = message;
            this.updateCharCount();
            this.updateSendButtonState();
            this.autoResize();
            this.messageInput.focus();
        }
    }

    // 公共方法：获取输入框内容
    getMessage() {
        return this.messageInput ? this.messageInput.value : '';
    }

    // 公共方法：清空输入框
    clearMessage() {
        if (this.messageInput) {
            this.messageInput.value = '';
            this.updateCharCount();
            this.updateSendButtonState();
            this.autoResize();
        }
    }

    // 公共方法：聚焦到输入框
    focus() {
        if (this.messageInput) {
            this.messageInput.focus();
        }
    }
}

// 初始化输入框增强功能
let inputEnhancements = null;

// 确保在聊天页面才初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在聊天页面
    if (document.getElementById('messageInput')) {
        inputEnhancements = new InputEnhancements();
    }
});

// 页面切换时重新初始化
document.addEventListener('pageSwitch', (e) => {
    if (e.detail && e.detail.page === 'chat') {
        setTimeout(() => {
            if (!inputEnhancements && document.getElementById('messageInput')) {
                inputEnhancements = new InputEnhancements();
            }
        }, 100);
    }
});

// 导出给其他脚本使用
window.InputEnhancements = InputEnhancements;
window.inputEnhancements = inputEnhancements;