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
        // 检测标准backdrop-filter支持
        if (CSS.supports('backdrop-filter', 'blur(10px)')) {
            return true;
        }
        
        // 检测Webkit前缀支持
        if (CSS.supports('-webkit-backdrop-filter', 'blur(10px)')) {
            return true;
        }
        
        // 创建测试元素进行功能检测
        const testElement = document.createElement('div');
        testElement.style.backdropFilter = 'blur(10px)';
        testElement.style.webkitBackdropFilter = 'blur(10px)';
        
        // 如果样式被保留，说明支持
        const hasStandardSupport = testElement.style.backdropFilter.includes('blur');
        const hasWebkitSupport = testElement.style.webkitBackdropFilter.includes('blur');
        
        return hasStandardSupport || hasWebkitSupport;
    }

    /**
     * 初始化检测和回退处理
     */
    init() {
        if (!this.supportsAcrylic) {
            this.fallbackToTransparent();
            this.addNoAcrylicClass();
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
        const elements = document.querySelectorAll('.acrylic-effect');
        elements.forEach(element => {
            element.style.backdropFilter = 'none';
            element.style.webkitBackdropFilter = 'none';
            element.style.backgroundColor = ''; // 让CSS回退机制生效
        });
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
    }

    /**
     * 检查当前是否支持亚克力效果
     * @returns {boolean} 当前是否支持亚克力效果
     */
    isSupported() {
        return this.supportsAcrylic;
    }
}

// 全局初始化
document.addEventListener('DOMContentLoaded', function() {
    window.acrylicDetector = new AcrylicEffectDetector();
});

// 导出用于模块化使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AcrylicEffectDetector;
}