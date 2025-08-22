// 后处理器UI控制
class PostProcessorUI {
    constructor() {
        this.button = document.getElementById('postProcessorToggle');
        this.init();
    }
    
    init() {
        if (this.button) {
            this.button.addEventListener('click', () => {
                this.togglePostProcessor();
            });
            
            // 监听MMD状态变化
            this.observeMMDState();
        }
    }
    
    togglePostProcessor() {
        if (window.__MMD__ && window.__MMD__.postProcessor) {
            const isEnabled = window.__MMD__.postProcessor.toggle();
            this.updateButtonText(isEnabled);
            console.log('后处理器状态已切换:', isEnabled ? '启用' : '禁用');
        }
    }
    
    updateButtonText(enabled) {
        if (this.button) {
            this.button.textContent = `后处理: ${enabled ? '开' : '关'}`;
        }
    }
    
    show() {
        if (this.button) {
            this.button.style.display = 'inline-block';
        }
    }
    
    hide() {
        if (this.button) {
            this.button.style.display = 'none';
        }
    }
    
    observeMMDState() {
        // 检查MMD是否启用
        const checkMMDState = () => {
            if (window.__MMD__ && window.__MMD__.state()) {
                this.show();
                // 获取当前后处理器状态
                if (window.__MMD__.postProcessor) {
                    const postProcessor = window.__MMD__.postProcessor;
                    // 这里可以添加获取当前状态的逻辑
                    this.updateButtonText(true); // 默认显示为开启状态
                }
            } else {
                this.hide();
            }
        };
        
        // 初始检查
        checkMMDState();
        
        // 定期检查状态变化
        setInterval(checkMMDState, 1000);
    }
}

// 初始化后处理器UI
let postProcessorUI = null;

document.addEventListener('DOMContentLoaded', () => {
    postProcessorUI = new PostProcessorUI();
});

// 导出供其他模块使用
export { PostProcessorUI }; 