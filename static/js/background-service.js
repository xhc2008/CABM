// 背景选择器服务模块
class BackgroundService {
    constructor() {
        this.backgrounds = {};
        this.isLoading = false;

        // DOM元素
        this.backgroundModal = null;
        this.backgroundList = null;
        this.addBackgroundModal = null;
        this.addBackgroundForm = null;
        this.loadingIndicator = null;

        this.init();
    }

    init() {
        // 创建背景选择模态框
        this.createBackgroundModal();
        
        // 创建添加背景模态框
        this.createAddBackgroundModal();
        
        // 绑定事件
        this.bindEvents();
    }

    createBackgroundModal() {
        // 创建主模态框
        this.backgroundModal = document.createElement('div');
        this.backgroundModal.id = 'backgroundModal';
        this.backgroundModal.className = 'background-modal';

        this.backgroundModal.innerHTML = `
            <div class="background-content">
                <div class="background-header">
                    <h3>选择背景</h3>
                    <button class="add-background-btn" id="addBackgroundBtn">添加背景</button>
                </div>
                <div class="background-list" id="backgroundList">
                    <!-- 背景列表将通过JavaScript动态加载 -->
                </div>
            </div>
        `;

        document.body.appendChild(this.backgroundModal);

        // 获取DOM元素引用
        this.backgroundList = document.getElementById('backgroundList');

        // 创建加载指示器
        this.createLoadingIndicator();
    }

    createAddBackgroundModal() {
        // 创建添加背景模态框
        this.addBackgroundModal = document.createElement('div');
        this.addBackgroundModal.id = 'addBackgroundModal';
        this.addBackgroundModal.className = 'add-background-modal';

        this.addBackgroundModal.innerHTML = `
            <div class="add-background-content">
                <h3>添加新背景</h3>
                <form id="addBackgroundForm">
                    <div class="form-group">
                        <label for="backgroundName">名称 *</label>
                        <input type="text" id="backgroundName" required placeholder="请输入背景名称">
                    </div>
                    
                    <div class="form-group">
                        <label for="backgroundDesc">描述</label>
                        <textarea id="backgroundDesc" placeholder="可选，描述这个背景的特点"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="backgroundPrompt">提示词</label>
                        <textarea id="backgroundPrompt" placeholder="留空则随机生成，或输入自定义提示词"></textarea>
                    </div>
                    
                    <div class="form-buttons">
                        <button type="button" class="form-btn form-btn-secondary" id="cancelAddBtn">取消</button>
                        <button type="submit" class="form-btn form-btn-primary" id="submitAddBtn">生成并保存</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(this.addBackgroundModal);

        // 获取表单引用
        this.addBackgroundForm = document.getElementById('addBackgroundForm');
    }

    createLoadingIndicator() {
        this.loadingIndicator = document.createElement('div');
        this.loadingIndicator.className = 'background-loading';
        this.loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <p>加载背景列表中...</p>
        `;
        this.loadingIndicator.style.display = 'none';
    }

    bindEvents() {
        // 点击模态框外部关闭
        this.backgroundModal.addEventListener('click', (e) => {
            if (e.target === this.backgroundModal) {
                this.closeBackgroundSelector();
            }
        });

        this.addBackgroundModal.addEventListener('click', (e) => {
            if (e.target === this.addBackgroundModal) {
                this.hideAddBackgroundModal();
            }
        });

        // 添加背景按钮
        document.getElementById('addBackgroundBtn').addEventListener('click', () => {
            this.showAddBackgroundModal();
        });

        // 取消添加按钮
        document.getElementById('cancelAddBtn').addEventListener('click', () => {
            this.hideAddBackgroundModal();
        });

        // 表单提交
        this.addBackgroundForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAddBackground();
        });

        // ESC键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.addBackgroundModal.style.display === 'flex') {
                    this.hideAddBackgroundModal();
                } else if (this.backgroundModal.style.display === 'flex') {
                    this.closeBackgroundSelector();
                }
            }
        });
    }

    async loadBackgrounds() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading();

        try {
            const response = await fetch('/api/backgrounds');
            const data = await response.json();

            if (data.success) {
                this.backgrounds = data.backgrounds;
                this.renderBackgrounds();
            } else {
                this.showError('加载背景列表失败: ' + data.error);
            }
        } catch (error) {
            console.error('加载背景失败:', error);
            this.showError('加载背景列表失败');
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }

    renderBackgrounds() {
        if (!this.backgroundList) return;

        // 清空现有内容
        this.backgroundList.innerHTML = '';

        // 添加加载指示器
        this.backgroundList.appendChild(this.loadingIndicator);

        // 检查是否有背景
        if (Object.keys(this.backgrounds).length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.className = 'background-empty';
            emptyDiv.innerHTML = `
                <div class="background-empty-icon">&#128444;</div>
                <p>暂无背景，点击"添加背景"创建第一个背景</p>
            `;
            this.backgroundList.appendChild(emptyDiv);
            return;
        }

        // 渲染背景列表
        Object.entries(this.backgrounds).forEach(([filename, info]) => {
            const item = this.createBackgroundItem(filename, info);
            this.backgroundList.appendChild(item);
        });
    }

    createBackgroundItem(filename, info) {
        const item = document.createElement('div');
        item.className = 'background-item';
        
        // 使用addEventListener而不是onclick，确保事件正确绑定
        item.addEventListener('click', () => {
            console.log('点击背景项:', filename);
            this.selectBackground(filename);
        });

        item.innerHTML = `
            <img src="/static/images/backgrounds/${filename}" 
                 alt="${info.name}" 
                 class="background-thumbnail" 
                 onerror="this.src='/static/images/default.svg'">
            <div class="background-info">
                <div class="background-name">${info.name}</div>
                <div class="background-desc">${info.desc || '无描述'}</div>
                <div class="background-prompt">${info.prompt || '无提示词'}</div>
            </div>
        `;

        return item;
    }

    async selectBackground(filename) {
        console.log('选择背景:', filename);
        try {
            const response = await fetch('/api/background/select', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename })
            });

            const data = await response.json();
            console.log('背景选择响应:', data);

            if (data.success) {
                // 更新背景
                console.log('updateBackground函数存在:', !!window.updateBackground);
                if (window.updateBackground) {
                    console.log('调用updateBackground:', data.background_url);
                    window.updateBackground(data.background_url);
                } else {
                    console.error('updateBackground函数不存在');
                }

                // 显示系统消息
                const promptMessage = data.prompt ?
                    `背景已更新，提示词: "${data.prompt}"` :
                    '背景已更新';

                console.log('updateCurrentMessage函数存在:', !!window.updateCurrentMessage);
                if (window.updateCurrentMessage) {
                    console.log('调用updateCurrentMessage:', promptMessage);
                    window.updateCurrentMessage('system', promptMessage);
                } else {
                    console.error('updateCurrentMessage函数不存在');
                }

                // 关闭选择器
                this.closeBackgroundSelector();
            } else {
                this.showError('切换背景失败: ' + data.error);
            }
        } catch (error) {
            console.error('切换背景失败:', error);
            this.showError('切换背景失败');
        }
    }

    showAddBackgroundModal() {
        this.addBackgroundModal.style.display = 'flex';
        // 清空表单
        this.addBackgroundForm.reset();
        // 聚焦到名称输入框
        document.getElementById('backgroundName').focus();
    }

    hideAddBackgroundModal() {
        this.addBackgroundModal.style.display = 'none';
    }

    async handleAddBackground() {
        const name = document.getElementById('backgroundName').value.trim();
        const desc = document.getElementById('backgroundDesc').value.trim();
        const prompt = document.getElementById('backgroundPrompt').value.trim();

        if (!name) {
            this.showError('请输入背景名称');
            return;
        }

        const submitBtn = document.getElementById('submitAddBtn');
        const originalText = submitBtn.textContent;
        
        submitBtn.disabled = true;
        submitBtn.textContent = '生成中...';

        try {
            const response = await fetch('/api/background/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, desc, prompt })
            });

            const data = await response.json();

            if (data.success) {
                this.hideAddBackgroundModal();
                // 重新加载背景列表
                await this.loadBackgrounds();
                this.showSuccess('背景添加成功');
            } else {
                this.showError('添加背景失败: ' + data.error);
            }
        } catch (error) {
            console.error('添加背景失败:', error);
            this.showError('添加背景失败');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    showLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'block';
        }
    }

    hideLoading() {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
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

    showSuccess(message) {
        if (window.showSuccess) {
            window.showSuccess(message);
        } else {
            console.log(message);
            // 可以添加一个简单的成功提示
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4CAF50;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                z-index: 2000;
                font-size: 14px;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 3000);
        }
    }

    async openBackgroundSelector() {
        // 显示背景选择模态框
        this.backgroundModal.style.display = 'flex';

        // 加载背景列表
        await this.loadBackgrounds();
    }

    closeBackgroundSelector() {
        this.backgroundModal.style.display = 'none';
        // 同时关闭添加背景模态框
        this.hideAddBackgroundModal();
    }
}

// 创建全局背景服务实例
let backgroundService = null;

// 初始化背景服务
function initBackgroundService() {
    if (!backgroundService) {
        backgroundService = new BackgroundService();
    }
    return backgroundService;
}

// 导出函数
export function openBackgroundSelector() {
    const service = initBackgroundService();
    service.openBackgroundSelector();
}

export function getBackgroundService() {
    return initBackgroundService();
}

// 暴露给全局使用
window.openBackgroundSelector = openBackgroundSelector;
window.getBackgroundService = getBackgroundService;