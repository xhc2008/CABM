/**
 * 科幻视觉效果管理器
 * 轻量级实现，注重性能优化
 */

class SciFiEffects {
    constructor() {
        this.particles = [];
        this.maxParticles = 15; // 限制粒子数量以保持性能
        this.animationId = null;
        this.isActive = false;
        this.init();
    }

    init() {
        // 检查用户是否偏好减少动画
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        // 检查设备性能（简单的启发式检查）
        if (this.isLowPerformanceDevice()) {
            this.maxParticles = 8;
        }

        this.createParticleContainer();
        this.startParticleSystem();
    }

    isLowPerformanceDevice() {
        // 简单的性能检测
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!gl) return true;
        
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
            const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
            // 检测集成显卡或低端设备
            if (renderer.includes('Intel') || renderer.includes('Mali') || renderer.includes('Adreno')) {
                return true;
            }
        }
        
        // 检查内存（如果可用）
        if (navigator.deviceMemory && navigator.deviceMemory < 4) {
            return true;
        }
        
        return false;
    }

    createParticleContainer() {
        // 只在主页创建粒子容器
        const homePage = document.getElementById('homePage');
        if (!homePage) return;

        this.particleContainer = document.createElement('div');
        this.particleContainer.className = 'sci-fi-particles';
        this.particleContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: hidden;
            z-index: 1;
        `;
        
        homePage.appendChild(this.particleContainer);
    }

    createParticle() {
        if (!this.particleContainer || this.particles.length >= this.maxParticles) {
            return;
        }

        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 3 + 1;
        const startX = Math.random() * window.innerWidth;
        const duration = Math.random() * 8 + 6; // 6-14秒
        const delay = Math.random() * 2;
        
        // 随机颜色（青色系）
        const colors = ['#00ffff', '#0080ff', '#40e0d0', '#00bfff'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        
        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            left: ${startX}px;
            bottom: -10px;
            opacity: 0;
            box-shadow: 0 0 ${size * 2}px ${color};
            animation: particleFloat ${duration}s linear ${delay}s infinite;
        `;
        
        this.particleContainer.appendChild(particle);
        this.particles.push(particle);
        
        // 清理过期粒子
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
                const index = this.particles.indexOf(particle);
                if (index > -1) {
                    this.particles.splice(index, 1);
                }
            }
        }, (duration + delay + 1) * 1000);
    }

    startParticleSystem() {
        if (this.isActive) return;
        
        this.isActive = true;
        
        // 创建粒子的间隔（降低频率以提升性能）
        this.particleInterval = setInterval(() => {
            if (document.getElementById('homePage')?.classList.contains('active')) {
                this.createParticle();
            }
        }, 2000); // 每2秒创建一个粒子
    }

    stopParticleSystem() {
        this.isActive = false;
        
        if (this.particleInterval) {
            clearInterval(this.particleInterval);
            this.particleInterval = null;
        }
        
        // 清理现有粒子
        this.particles.forEach(particle => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        });
        this.particles = [];
    }

    // 添加鼠标跟随光效（可选，性能友好版本）
    addMouseGlow() {
        if (this.isLowPerformanceDevice()) return;
        
        let mouseGlow = null;
        let glowTimeout = null;
        
        document.addEventListener('mousemove', (e) => {
            // 节流处理，避免过度更新
            if (glowTimeout) return;
            
            glowTimeout = setTimeout(() => {
                glowTimeout = null;
            }, 50);
            
            if (!mouseGlow) {
                mouseGlow = document.createElement('div');
                mouseGlow.style.cssText = `
                    position: fixed;
                    width: 20px;
                    height: 20px;
                    background: radial-gradient(circle, rgba(0, 255, 255, 0.3) 0%, transparent 70%);
                    border-radius: 50%;
                    pointer-events: none;
                    z-index: 9999;
                    transition: opacity 0.3s ease;
                `;
                document.body.appendChild(mouseGlow);
            }
            
            mouseGlow.style.left = (e.clientX - 10) + 'px';
            mouseGlow.style.top = (e.clientY - 10) + 'px';
            mouseGlow.style.opacity = '1';
        });
        
        document.addEventListener('mouseleave', () => {
            if (mouseGlow) {
                mouseGlow.style.opacity = '0';
            }
        });
    }

    // 页面切换时的处理
    handlePageSwitch() {
        // 监听页面切换
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const homePage = document.getElementById('homePage');
                    if (homePage?.classList.contains('active')) {
                        this.startParticleSystem();
                    } else {
                        this.stopParticleSystem();
                    }
                }
            });
        });
        
        const homePage = document.getElementById('homePage');
        if (homePage) {
            observer.observe(homePage, { attributes: true });
        }
    }

    // 清理资源
    destroy() {
        this.stopParticleSystem();
        if (this.particleContainer && this.particleContainer.parentNode) {
            this.particleContainer.parentNode.removeChild(this.particleContainer);
        }
    }
}

// 初始化科幻效果
let sciFiEffects = null;

document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化以避免阻塞页面加载
    setTimeout(() => {
        sciFiEffects = new SciFiEffects();
        sciFiEffects.handlePageSwitch();
        
        // 可选：添加鼠标光效（仅在高性能设备上）
        if (!sciFiEffects.isLowPerformanceDevice()) {
            sciFiEffects.addMouseGlow();
        }
    }, 1000);
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', () => {
    if (sciFiEffects) {
        sciFiEffects.destroy();
    }
});