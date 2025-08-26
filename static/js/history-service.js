// 历史记录服务模块 - 处理历史记录的分页加载和显示
class HistoryService {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 0;
        this.totalMessages = 0;
        this.isLoading = false;
        this.hasMore = true;
        this.loadedMessages = [];
        this.isStoryMode = false;
        
        // DOM元素
        this.historyModal = null;
        this.historyMessages = null;
        this.loadMoreButton = null;
        this.loadingIndicator = null;
        
        this.init();
    }
    
    init() {
        // 获取DOM元素
        this.historyModal = document.getElementById('historyModal');
        this.historyMessages = document.getElementById('historyMessages');
        
        // 检测是否为故事模式
        this.isStoryMode = window.storyId !== undefined;
        
        // 创建加载更多按钮
        this.createLoadMoreButton();
        
        // 创建加载指示器
        this.createLoadingIndicator();
        
        // 绑定滚动事件
        this.bindScrollEvent();
    }
    
    createLoadMoreButton() {
        this.loadMoreButton = document.createElement('button');
        this.loadMoreButton.className = 'btn secondary-btn load-more-btn';
        this.loadMoreButton.textContent = '加载更多历史记录';
        this.loadMoreButton.style.display = 'none';
        this.loadMoreButton.style.width = '100%';
        this.loadMoreButton.style.marginTop = '10px';
        
        this.loadMoreButton.addEventListener('click', () => {
            this.loadMoreHistory();
        });
    }
    
    createLoadingIndicator() {
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'history-loading';
        this.loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <p>加载历史记录中...</p>
        `;
        this.loadingIndicator.style.display = 'none';
        this.loadingIndicator.style.textAlign = 'center';
        this.loadingIndicator.style.padding = '20px';
        this.loadingIndicator.style.color = 'white';
    }
    
    bindScrollEvent() {
        if (!this.historyMessages) return;
        
        this.historyMessages.addEventListener('scroll', () => {
            // 当滚动到顶部附近时，自动加载更多历史记录
            if (this.historyMessages.scrollTop < 100 && this.hasMore && !this.isLoading) {
                this.loadMoreHistory();
            }
        });
    }
    
    async loadHistory(page = 1, append = false) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const apiUrl = this.isStoryMode ? '/api/story/history' : '/api/history';
            const response = await fetch(`${apiUrl}?page=${page}&page_size=${this.pageSize}`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || '加载历史记录失败');
            }
            
            const { messages, pagination } = result.data;
            
            // 更新分页信息
            this.currentPage = pagination.current_page;
            this.totalPages = pagination.total_pages;
            this.totalMessages = pagination.total_messages;
            this.hasMore = pagination.has_more;
            
            if (append) {
                // 追加到现有消息前面（新加载的历史消息应该在前面）
                this.loadedMessages = [...messages, ...this.loadedMessages];
            } else {
                // 替换所有消息
                this.loadedMessages = messages;
            }
            
            this.renderHistory(append);
            this.updateLoadMoreButton();
            
        } catch (error) {
            console.error('加载历史记录失败:', error);
            this.showError(`加载历史记录失败: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async loadMoreHistory() {
        if (!this.hasMore || this.isLoading) return;
        
        const nextPage = this.currentPage + 1;
        await this.loadHistory(nextPage, true);
    }
    
    renderHistory(append = false) {
        if (!this.historyMessages) return;
        
        // 记录当前滚动位置
        const scrollHeight = this.historyMessages.scrollHeight;
        const scrollTop = this.historyMessages.scrollTop;
        
        if (!append) {
            // 清空现有内容
            this.historyMessages.innerHTML = '';
            
            // 添加加载指示器到顶部
            this.historyMessages.appendChild(this.loadingIndicator);
            
            // 添加加载更多按钮到顶部
            this.historyMessages.appendChild(this.loadMoreButton);
        }
        
        // 渲染消息
        const fragment = document.createDocumentFragment();
        
        if (append) {
            // 只渲染新加载的消息（最新加载的消息在数组前面）
            const newMessages = this.loadedMessages.slice(0, this.pageSize);
            newMessages.forEach(message => {
                const messageDiv = this.createMessageElement(message);
                fragment.appendChild(messageDiv);
            });
        } else {
            // 渲染所有消息
            this.loadedMessages.forEach(message => {
                const messageDiv = this.createMessageElement(message);
                fragment.appendChild(messageDiv);
            });
        }
        
        if (append) {
            // 将新消息插入到加载更多按钮之后
            const loadMoreBtn = this.historyMessages.querySelector('.load-more-btn');
            if (loadMoreBtn && loadMoreBtn.nextSibling) {
                this.historyMessages.insertBefore(fragment, loadMoreBtn.nextSibling);
            } else {
                // 如果没有找到加载更多按钮，插入到现有消息前面
                const firstMessage = this.historyMessages.querySelector('.history-message');
                if (firstMessage) {
                    this.historyMessages.insertBefore(fragment, firstMessage);
                } else {
                    this.historyMessages.appendChild(fragment);
                }
            }
            
            // 保持滚动位置
            const newScrollHeight = this.historyMessages.scrollHeight;
            this.historyMessages.scrollTop = scrollTop + (newScrollHeight - scrollHeight);
        } else {
            this.historyMessages.appendChild(fragment);
            
            // 滚动到底部
            this.historyMessages.scrollTop = this.historyMessages.scrollHeight;
        }
    }
    
    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `history-message history-${message.role}`;
        
        const roleSpan = document.createElement('div');
        roleSpan.className = 'history-role';
        
        let roleName = '';
        if (message.role === 'user') {
            roleName = '你';
        } else if (message.role === 'assistant') {
            // 尝试获取当前角色名称
            const currentCharacter = window.getCurrentCharacter ? window.getCurrentCharacter() : null;
            roleName = currentCharacter ? currentCharacter.name : 'AI助手';
        } else {
            roleName = '系统';
        }
        
        roleSpan.textContent = roleName;
        
        // 处理消息内容
        let content = message.content;
        if (message.role === 'assistant') {
            // 尝试解析JSON格式的回复
            try {
                const parsed = JSON.parse(content);
                if (parsed.content) {
                    content = parsed.content;
                }
            } catch (e) {
                // 如果不是JSON格式，可能需要清理【】标记
                content = content.replace(/【[^】]*】/g, '');
            }
        }
        
        // 使用后端提供的句子数据，如果没有则前端分割
        let sentences = [];
        if (message.sentences && Array.isArray(message.sentences)) {
            sentences = message.sentences;
        } else if (message.role === 'assistant') {
            sentences = this.splitIntoSentences(content);
        } else {
            sentences = [content];
        }
        
        // 创建内容容器
        const contentContainer = document.createElement('div');
        contentContainer.className = 'history-content-container';
        
        // 为每个句子创建一个元素
        sentences.forEach((sentence, index) => {
            if (sentence.trim()) {
                const sentenceDiv = document.createElement('div');
                sentenceDiv.className = 'history-sentence';
                sentenceDiv.textContent = sentence.trim();
                
                // 为句子添加点击事件（可以用于TTS播放等）
                sentenceDiv.addEventListener('click', () => {
                    this.onSentenceClick(sentence, roleName);
                });
                
                contentContainer.appendChild(sentenceDiv);
            }
        });
        
        // 添加时间戳
        if (message.timestamp) {
            const timestampDiv = document.createElement('div');
            timestampDiv.className = 'history-timestamp';
            timestampDiv.textContent = message.timestamp;
            messageDiv.appendChild(timestampDiv);
        }
        
        messageDiv.appendChild(roleSpan);
        messageDiv.appendChild(contentContainer);
        
        return messageDiv;
    }
    
    splitIntoSentences(text) {
        if (!text) return [];
        
        // 清理文本
        text = text.replace(/\s+/g, ' ').trim();
        if (!text) return [];
        
        // 定义句子结束标点
        const sentenceEndings = ['。', '！', '？', '!', '?', '.', '…', '♪', '...'];
        
        // 构建分割正则表达式
        const escapedEndings = sentenceEndings.map(ch => ch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('');
        const pattern = new RegExp(`([^${escapedEndings}]*[${escapedEndings}]+|[^${escapedEndings}]+(?=[${escapedEndings}]|$))`, 'g');
        
        const sentences = text.match(pattern) || [];
        
        // 清理和过滤句子
        return sentences
            .map(sentence => sentence.trim())
            .filter(sentence => sentence.length > 0);
    }
    
    onSentenceClick(sentence, characterName) {
        // 句子点击事件处理
        console.log('点击句子:', sentence, '角色:', characterName);
        
        // 如果有TTS功能，可以播放这个句子
        if (window.playTextAudio && characterName !== '你' && characterName !== '系统') {
            try {
                window.playTextAudio(sentence, false);
            } catch (error) {
                console.error('播放句子失败:', error);
            }
        }
    }
    
    updateLoadMoreButton() {
        if (!this.loadMoreButton) return;
        
        if (this.hasMore && this.totalMessages > this.pageSize) {
            this.loadMoreButton.style.display = 'block';
            this.loadMoreButton.textContent = `加载更多历史记录 (${this.totalMessages - this.loadedMessages.length} 条剩余)`;
        } else {
            this.loadMoreButton.style.display = 'none';
        }
    }
    
    showLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'block';
        }
        
        if (this.loadMoreButton) {
            this.loadMoreButton.disabled = true;
            this.loadMoreButton.textContent = '加载中...';
        }
    }
    
    hideLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
        }
        
        if (this.loadMoreButton) {
            this.loadMoreButton.disabled = false;
        }
    }
    
    showError(message) {
        if (window.showError) {
            window.showError(message);
        } else {
            console.error(message);
            alert(message);
        }
    }
    
    reset() {
        this.currentPage = 1;
        this.totalPages = 0;
        this.totalMessages = 0;
        this.hasMore = true;
        this.loadedMessages = [];
        
        if (this.historyMessages) {
            this.historyMessages.innerHTML = '';
        }
    }
    
    async openHistory() {
        // 重置状态
        this.reset();
        
        // 显示历史记录模态框
        if (this.historyModal) {
            this.historyModal.style.display = 'flex';
        }
        
        // 加载第一页历史记录
        await this.loadHistory(1);
    }
    
    closeHistory() {
        if (this.historyModal) {
            this.historyModal.style.display = 'none';
        }
    }
}

// 创建全局历史记录服务实例
let historyService = null;

// 初始化历史记录服务
function initHistoryService() {
    if (!historyService) {
        historyService = new HistoryService();
    }
    return historyService;
}

// 导出函数
export function toggleHistory() {
    const service = initHistoryService();
    
    if (service.historyModal && service.historyModal.style.display === 'flex') {
        service.closeHistory();
    } else {
        service.openHistory();
    }
}

export function getHistoryService() {
    return initHistoryService();
}

// 暴露给全局使用
window.toggleHistory = toggleHistory;
window.getHistoryService = getHistoryService;