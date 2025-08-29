/**
 * 亚克力效果检测和回退机制
 * 检测浏览器是否支持backdrop-filter，如果不支持则回退到半透明效果
 */

class AcrylicEffectDetector {
    constructor() {
        this.supportsAcrylic = this.detectBackdropFilterSupport();
        this.init();
    }

    /**
     * 检测浏览器是否支持backdrop-filter
     * @returns {boolean} 是否支持亚克力效果
     */
    detectBackdropFilterSupport() {
        // 首先检测标准backdrop-filter支持
        if (CSS.supports('backdrop-filter', 'blur(10px)')) {
            return true;
        }

        // 然后检测Webkit前缀支持
        if (CSS.supports('-webkit-backdrop-filter', 'blur(10px)')) {
            return true;
        }

        // 如果CSS.supports不可靠，则返回false（现代浏览器普遍支持CSS.supports）
        return false;
    }

    /**
     * 初始化检测和回退处理
     */
    init() {
        // 如果DOM已经加载，直接应用效果
        if (document.readyState !== 'loading') {
            this.applyAcrylicEffects();
        } else {
            // 否则等待DOM加载完成
            document.addEventListener('DOMContentLoaded', () => {
                this.applyAcrylicEffects();
            });
        }
    }

    /**
     * 应用亚克力效果或回退效果
     */
    applyAcrylicEffects() {
        // 立即应用正确的样式类
        if (!this.supportsAcrylic) {
            this.fallbackToTransparent();
            this.addNoAcrylicClass();
        } else {
            this.addAcrylicClass();
        }

        // 监听性能问题导致的回退
        this.monitorPerformance();
    }

    /**
     * 回退到半透明效果
     */
    fallbackToTransparent() {
        console.log('浏览器不支持亚克力效果，已回退到半透明效果');
        
        // 移除所有亚克力效果相关的样式
        const elements = document.querySelectorAll('.acrylic-effect, .chat-header, .user-input-container, .dialog-box, .control-buttons, .modal-content, .history-content');
        elements.forEach(element => {
            element.style.backdropFilter = 'none';
            element.style.webkitBackdropFilter = 'none';
            element.style.backgroundColor = ''; // 让CSS回退机制生效
        });
    }

    /**
     * 添加支持亚克力的CSS类
     */
    addAcrylicClass() {
        document.documentElement.classList.add('acrylic-support');
    }

    /**
     * 添加不支持亚克力的CSS类
     */
    addNoAcrylicClass() {
        document.documentElement.classList.add('no-acrylic-support');
    }

    /**
     * 监控性能，在性能不足时回退
     */
    monitorPerformance() {
        // 监听帧率下降
        let lastTime = performance.now();
        let frameCount = 0;
        let lowFpsCount = 0;

        const checkPerformance = () => {
            const now = performance.now();
            frameCount++;

            if (now - lastTime >= 1000) {
                const fps = Math.round((frameCount * 1000) / (now - lastTime));
                
                if (fps < 30) {
                    lowFpsCount++;
                    if (lowFpsCount >= 3) {
                        console.warn('检测到性能不足，禁用亚克力效果以提升性能');
                        this.fallbackToTransparent();
                        this.addNoAcrylicClass();
                        document.documentElement.classList.remove('acrylic-support');
                        return; // 停止监控
                    }
                } else {
                    lowFpsCount = Math.max(0, lowFpsCount - 1);
                }

                frameCount = 0;
                lastTime = now;
            }

            if (this.supportsAcrylic) {
                requestAnimationFrame(checkPerformance);
            }
        };

        if (this.supportsAcrylic) {
            requestAnimationFrame(checkPerformance);
        }
    }


    /**
     * 手动触发回退（用于测试或其他情况）
     */
    forceFallback() {
        this.fallbackToTransparent();
        this.addNoAcrylicClass();
        document.documentElement.classList.remove('acrylic-support');
    }

    /**
     * 检查当前是否支持亚克力效果
     * @returns {boolean} 当前是否支持亚克力效果
     */
    isSupported() {
        return this.supportsAcrylic;
    }
}

// 全局初始化 - 立即创建检测器并应用样式
window.acrylicDetector = new AcrylicEffectDetector();

// 导出用于模块化使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AcrylicEffectDetector;
}

/**
 * 亚克力效果应用机制
 * 根据用户设置应用亚克力效果或半透明效果
 */

class AcrylicEffectManager {
    constructor() {
        this.init();
    }

    /**
     * 初始化效果应用处理
     */
    init() {
        // 等待DOM加载完成后再进行初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.applyEffects();
            });
        } else {
            // DOM已经加载完成
            this.applyEffects();
        }
    }

    /**
     * 应用用户选择的视觉效果
     */
    applyEffects() {
        // 从localStorage获取用户设置，如果没有设置默认使用亚克力效果
        const useAcrylic = localStorage.getItem('useAcrylic') !== 'false';
        
        if (useAcrylic) {
            this.applyAcrylicEffects();
        } else {
            this.applyTransparentEffects();
        }
    }

    /**
     * 应用亚克力效果
     */
    applyAcrylicEffects() {
        document.documentElement.classList.remove('no-acrylic-support');
        document.documentElement.classList.add('acrylic-support');
    }

    /**
     * 应用半透明效果
     */
    applyTransparentEffects() {
        document.documentElement.classList.remove('acrylic-support');
        document.documentElement.classList.add('no-acrylic-support');
    }

    /**
     * 切换到亚克力效果
     */
    switchToAcrylic() {
        this.applyAcrylicEffects();
        localStorage.setItem('useAcrylic', 'true');
    }

    /**
     * 切换到半透明效果
     */
    switchToTransparent() {
        this.applyTransparentEffects();
        localStorage.setItem('useAcrylic', 'false');
    }

    /**
     * 检查当前是否使用亚克力效果
     * @returns {boolean} 当前是否使用亚克力效果
     */
    isAcrylicEnabled() {
        return localStorage.getItem('useAcrylic') !== 'false';
    }
}

// 全局初始化
document.addEventListener('DOMContentLoaded', function() {
    window.acrylicManager = new AcrylicEffectManager();
});

// 导出用于模块化使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AcrylicEffectManager;
}
