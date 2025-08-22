/**
 * 卡通渲染控制UI管理
 * 处理卡通渲染控制按钮的显示和交互
 */

// 卡通渲染控制按钮管理
class ToonControlsUI {
    constructor() {
        this.controlButton = null;
        this.isVisible = false;
        this.init();
    }
    
    init() {
        // 查找控制按钮
        this.controlButton = document.getElementById('toon-controls-btn');
        
        if (this.controlButton) {
            // 绑定点击事件
            this.controlButton.addEventListener('click', () => {
                this.toggleToonPanel();
            });
            
            // 监听MMD状态变化
            this.observeMMDState();
            
            console.log('[ToonControlsUI] 卡通渲染控制UI已初始化');
        } else {
            console.warn('[ToonControlsUI] 未找到卡通渲染控制按钮');
        }
    }
    
    // 监听MMD状态变化
    observeMMDState() {
        // 定期检查MMD状态
        const checkMMDState = () => {
            if (window.__MMD__ && window.__MMD__.state) {
                const isMMDEnabled = window.__MMD__.state();
                this.updateButtonVisibility(isMMDEnabled);
            }
        };
        
        // 初始检查
        checkMMDState();
        
        // 定期检查（每秒检查一次）
        setInterval(checkMMDState, 1000);
        
        // 监听MMD状态变化事件
        window.addEventListener('mmd-state-changed', (event) => {
            this.updateButtonVisibility(event.detail.enabled);
        });
    }
    
    // 更新按钮可见性
    updateButtonVisibility(show) {
        if (this.controlButton) {
            this.controlButton.style.display = show ? 'inline-block' : 'none';
        }
    }
    
    // 切换卡通渲染面板
    toggleToonPanel() {
        if (window.__MMD__ && window.__MMD__.toggleToonPanel) {
            window.__MMD__.toggleToonPanel();
        } else {
            console.warn('[ToonControlsUI] 卡通渲染面板功能不可用');
        }
    }
    
    // 显示控制按钮
    show() {
        this.isVisible = true;
        if (this.controlButton) {
            this.controlButton.style.display = 'inline-block';
        }
    }
    
    // 隐藏控制按钮
    hide() {
        this.isVisible = false;
        if (this.controlButton) {
            this.controlButton.style.display = 'none';
        }
    }
    
    // 设置按钮文本
    setButtonText(text) {
        if (this.controlButton) {
            this.controlButton.textContent = text;
        }
    }
    
    // 添加按钮样式
    addButtonStyle(className) {
        if (this.controlButton) {
            this.controlButton.classList.add(className);
        }
    }
    
    // 移除按钮样式
    removeButtonStyle(className) {
        if (this.controlButton) {
            this.controlButton.classList.remove(className);
        }
    }
}

// 创建全局实例
let toonControlsUI = null;

// 初始化函数
function initToonControlsUI() {
    if (!toonControlsUI) {
        toonControlsUI = new ToonControlsUI();
    }
    return toonControlsUI;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化，确保MMD相关脚本已加载
    setTimeout(() => {
        initToonControlsUI();
    }, 2000);
});

// 导出
export { ToonControlsUI, initToonControlsUI }; 