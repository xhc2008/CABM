import { initMMDCharacterSystem, loadCharacter, playEmotionAnimation, dispose as disposeMMD, isCharacterSystemInitialized } from './mmd-character.js';
import { getCurrentCharacter } from './character-service.js';
import { getToonRenderer, updateToonParams, toggleToonRendering, adjustFaceBrightness, getFaceBrightnessSettings, getPostProcessor, updatePostProcessorParams, checkPostProcessorStatus, checkShaderAvailability, initializeShaders } from './mmd-renderer.js';
import { ToonControls } from './toon-controls.js';

const STORAGE_KEY = 'useMMDPortrait';

function getToggleState() {
    return localStorage.getItem(STORAGE_KEY) === 'true';
}

function setToggleState(enabled) {
    localStorage.setItem(STORAGE_KEY, enabled ? 'true' : 'false');
}

function showMMDCanvas(show) {
    const canvas = document.getElementById('mmdCanvas');
    const img = document.getElementById('characterImage');
    if (!canvas) {
        console.error('[MMD] 未找到 mmdCanvas 容器');
        return;
    }
    if (!img) {
        console.warn('[MMD] 未找到 characterImage，可能已被隐藏或模板变更');
    }
    canvas.style.display = show ? 'block' : 'none';
    if (img) img.style.display = show ? 'none' : 'block';
}

async function enableMMD() {
    try {
        console.log('[MMD] 准备启用MMD');
        if (typeof THREE === 'undefined') {
            console.error('[MMD] THREE 未加载，请检查 /static/plugin/three 路径及脚本标签顺序');
            alert('MMD依赖未加载（THREE未定义）。请检查静态脚本是否可访问。');
            return;
        }
        if (!THREE.MMDLoader) {
            console.error('[MMD] THREE.MMDLoader 未加载，请检查 MMDLoader 脚本是否正确引入');
            alert('MMD依赖未加载（MMDLoader未定义）。请检查静态脚本是否可访问。');
            return;
        }
        
        // 检查着色器可用性
        console.log('[MMD] 检查着色器可用性...');
        checkShaderAvailability();
        
        // 等待一下确保所有脚本都加载完成
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // 初始化着色器
        console.log('[MMD] 初始化着色器...');
        initializeShaders();
        
        // 再次检查着色器
        console.log('[MMD] 再次检查着色器可用性...');
        checkShaderAvailability();
        
        // 等待渲染器初始化完成后检查分辨率
        setTimeout(() => {
            console.log('[MMD] 检查渲染器分辨率...');
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                postProcessor.checkOutputResolution();
                postProcessor.forceResize();
            }
        }, 1000);

        // 确保DOM完全加载后再初始化渲染器
        await new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50; // 最多等待5秒
            
            const checkDOM = () => {
                attempts++;
                const canvas = document.getElementById('mmdCanvas');
                console.log(`[MMD] 检查DOM状态 (${attempts}/${maxAttempts}):`, {
                    canvas: !!canvas,
                    offsetWidth: canvas?.offsetWidth,
                    offsetHeight: canvas?.offsetHeight,
                    clientWidth: canvas?.clientWidth,
                    clientHeight: canvas?.clientHeight,
                    windowWidth: window.innerWidth,
                    windowHeight: window.innerHeight
                });
                
                // 检查Canvas是否存在且有有效尺寸
                if (canvas && (canvas.offsetWidth > 0 || canvas.clientWidth > 0)) {
                    console.log('[MMD] DOM检查通过，Canvas尺寸有效');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    console.warn('[MMD] DOM检查超时，使用窗口尺寸继续初始化');
                    resolve(); // 超时后强制继续，而不是失败
                } else if (attempts >= 10) {
                    // 10次检查后，如果Canvas存在但尺寸为0，直接使用窗口尺寸
                    console.log('[MMD] Canvas存在但尺寸为0，使用窗口尺寸继续');
                    resolve();
                } else {
                    console.log('[MMD] DOM检查未通过，继续等待...');
                    setTimeout(checkDOM, 100);
                }
            };
            checkDOM();
        });
        
        // 初始化渲染器
        if (!isCharacterSystemInitialized()) {
            console.log('[MMD] 初始化渲染系统...');
            try {
                initMMDCharacterSystem('mmdCanvas');
            } catch (error) {
                console.error('[MMD] 渲染系统初始化失败:', error);
                
                // 检查是否是WebGL相关错误
                if (error.message && error.message.includes('WebGL')) {
                    console.log('[MMD] 检测到WebGL错误，尝试降级方案...');
                    
                    // 尝试使用body作为容器
                    try {
                        console.log('[MMD] 尝试使用body作为容器...');
                        initMMDCharacterSystem('body');
                    } catch (error2) {
                        console.error('[MMD] 降级方案也失败:', error2);
                        
                        // 显示详细的错误信息和解决方案
                        const errorMsg = `3D角色功能初始化失败：\n\n错误：${error.message}\n\n可能的解决方案：\n1. 更新显卡驱动到最新版本\n2. 在浏览器设置中启用硬件加速\n3. 关闭可能干扰的安全软件\n4. 尝试使用Chrome或Firefox浏览器\n5. 重启浏览器或系统\n\n如果问题持续存在，请使用图片立绘模式。`;
                        alert(errorMsg);
                        
                        // 自动禁用MMD功能并切换到图片模式
                        setToggleState(false);
                        showMMDCanvas(false);
                        return;
                    }
                } else {
                    // 其他类型的错误
                    console.log('[MMD] 尝试使用body作为容器...');
                    try {
                        initMMDCharacterSystem('body');
                    } catch (error2) {
                        console.error('[MMD] 降级方案也失败:', error2);
                        alert('启用MMD失败：' + (error?.message || error));
                        showMMDCanvas(false);
                        return;
                    }
                }
            }
        }

        // 加载当前角色对应的MMD（按角色ID，缺省回退 Silver_Wolf）
        const character = getCurrentCharacter();
        const characterId = character?.id || 'Silver_Wolf';
        console.log('[MMD] 加载角色:', characterId);

        await loadCharacter(characterId);
        playEmotionAnimation('idle');
        
        // 确保MMD Canvas显示
        showMMDCanvas(true);
        console.log('[MMD] MMD Canvas已显示');
        
        // 强制刷新渲染器尺寸
        setTimeout(() => {
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                postProcessor.forceResize();
                console.log('[MMD] 强制刷新渲染器尺寸完成');
            }
        }, 100);
        
        // 初始化卡通渲染控制（包含后处理控制）
        setTimeout(() => {
            initToonControls();
            // 更新后处理UI状态
            if (window.__MMD__ && window.__MMD__.postProcessor) {
                const postProcessor = window.__MMD__.postProcessor;
                console.log('[MMD] 后处理状态:', postProcessor.params.enabled ? '启用' : '禁用');
            }
        }, 1000);
        
        console.log('[MMD] 启用完成');
    } catch (e) {
        console.error('[MMD] 启用失败:', e);
        alert('启用MMD失败：' + (e?.message || e));
        showMMDCanvas(false);
    }
}

function disableMMD() {
    console.log('[MMD] 关闭MMD并恢复图片立绘');
    try {
        disposeMMD();
    } catch (e) {
        console.warn('[MMD] 关闭时出现问题:', e);
    }
    showMMDCanvas(false);
}

function applyInitialState() {
    const enabled = getToggleState();
    console.log('[MMD] 初始化状态 useMMDPortrait =', enabled);
    if (enabled) enableMMD(); else disableMMD();
}

// 卡通渲染控制实例
let toonControls = null;

// 初始化卡通渲染控制
function initToonControls() {
    try {
        const toonRenderer = getToonRenderer();
        if (toonRenderer && !toonControls) {
            toonControls = new ToonControls(toonRenderer);
            toonControls.loadSavedPresets();
            console.log('[MMD] 卡通渲染控制面板已初始化');
        }
    } catch (error) {
        console.warn('[MMD] 卡通渲染控制面板初始化失败:', error);
    }
}

// 提供全局调试方法
window.__MMD__ = {
    enable: () => { setToggleState(true); enableMMD(); },
    disable: () => { setToggleState(false); disableMMD(); },
    state: () => getToggleState(),
    toonControls: () => toonControls,
    showToonPanel: () => toonControls?.show(),
    hideToonPanel: () => toonControls?.hide(),
    toggleToonPanel: () => toonControls?.toggle(),
    // 脸部亮度调整
    adjustFaceBrightness: (brightness = 1.2, emissiveIntensity = 0.4) => adjustFaceBrightness(brightness, emissiveIntensity),
    getFaceBrightness: () => getFaceBrightnessSettings(),
    // 快速亮度预设
    setFaceBrightness: {
        normal: () => adjustFaceBrightness(1.0, 0.0),
        subtle: () => adjustFaceBrightness(1.05, 0.08),
        bright: () => adjustFaceBrightness(1.1, 0.15),
        warm: () => adjustFaceBrightness(1.08, 0.12),
        reset: () => adjustFaceBrightness(1.0, 0.0) // 快速重置
    },
    // 后处理器控制
    postProcessor: {
        enable: () => {
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                postProcessor.enable();
            }
        },
        disable: () => {
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                postProcessor.disable();
            }
        },
        toggle: () => {
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                return postProcessor.toggle();
            }
            return false;
        },
        update: (params) => updatePostProcessorParams(params),
        status: () => checkPostProcessorStatus(),
        // 快速预设
        presets: {
            original: () => updatePostProcessorParams({
                contrastValue: 1.0,
                brightness: 1.0,
                saturation: 1.0
            }),
            performance: () => updatePostProcessorParams({
                contrastValue: 1.1,
                brightness: 1.0,
                saturation: 1.05
            })
        },
        
        // 应用渲染预设
        applyPreset: (presetName) => {
            if (presetName === 'original') {
                // 原始模式：禁用所有后处理
                const postProcessor = getPostProcessor();
                if (postProcessor) {
                    postProcessor.disable();
                }
                console.log('已应用原始渲染预设');
            } else if (presetName === 'performance') {
                // 性能模式：启用基本后处理
                const postProcessor = getPostProcessor();
                if (postProcessor) {
                    postProcessor.enable();
                    updatePostProcessorParams({
                        contrastValue: 1.1,
                        brightness: 1.0,
                        saturation: 1.05
                    });
                }
                console.log('已应用性能渲染预设');
            }
        }
    },
    
    // 着色器检查
    checkShaders: () => checkShaderAvailability(),
    
    // 着色器初始化
    initShaders: () => initializeShaders(),
    
    // 强制刷新渲染器尺寸
    forceResize: () => {
        const postProcessor = getPostProcessor();
        if (postProcessor) {
            postProcessor.forceResize();
        }
    },
    
    // 强制重新初始化
    forceReinit: async () => {
        console.log('[MMD] 强制重新初始化...');
        disableMMD();
        await new Promise(resolve => setTimeout(resolve, 500));
        await enableMMD();
        console.log('[MMD] 强制重新初始化完成');
    },
    
    // 检查MMD Canvas状态
    checkCanvasStatus: () => {
        const canvas = document.getElementById('mmdCanvas');
        const img = document.getElementById('characterImage');
        
        console.log('[MMD Canvas Status]', {
            canvas: canvas ? {
                display: canvas.style.display,
                zIndex: canvas.style.zIndex,
                position: canvas.style.position,
                width: canvas.style.width,
                height: canvas.style.height,
                offsetWidth: canvas.offsetWidth,
                offsetHeight: canvas.offsetHeight,
                clientWidth: canvas.clientWidth,
                clientHeight: canvas.clientHeight
            } : 'null',
            image: img ? {
                display: img.style.display
            } : 'null',
            mmdEnabled: getToggleState(),
            windowSize: {
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight
            }
        });
        
        return {
            canvas: canvas,
            image: img,
            mmdEnabled: getToggleState()
        };
    },
    
    // 抗锯齿信息
    antiAliasing: {
        // 获取当前抗锯齿状态
        getStatus: () => {
            const postProcessor = getPostProcessor();
            if (postProcessor && postProcessor.fxaaPass) {
                return 'fxaa'; // 使用FXAA抗锯齿
            }
            return 'renderer'; // 使用原始渲染器抗锯齿
        },
        
        // 检查分辨率
        checkResolution: () => {
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                return postProcessor.checkOutputResolution();
            }
            return null;
        },
        
        // 显示抗锯齿信息
        info: () => {
            const status = window.__MMD__.antiAliasing.getStatus();
            console.log('抗锯齿状态:', status === 'fxaa' ? 'FXAA抗锯齿' : '原始渲染器抗锯齿');
            console.log('设备像素比:', window.devicePixelRatio);
            console.log('屏幕分辨率:', window.innerWidth, 'x', window.innerHeight);
            
            // 检查渲染器分辨率
            const postProcessor = getPostProcessor();
            if (postProcessor) {
                const resolutionInfo = postProcessor.checkOutputResolution();
                if (resolutionInfo) {
                    console.log('渲染器分辨率:', resolutionInfo.canvas);
                    console.log('CSS分辨率:', resolutionInfo.css);
                    if (resolutionInfo.postProcessor) {
                        console.log('后处理器输入分辨率:', resolutionInfo.postProcessor.inputResolution);
                        console.log('后处理器输出分辨率:', resolutionInfo.postProcessor.outputResolution);
                    }
                }
                
                // 检查FXAA状态
                if (postProcessor.fxaaPass) {
                    console.log('FXAA已启用');
                    if (postProcessor.fxaaPass.material.uniforms && postProcessor.fxaaPass.material.uniforms['resolution']) {
                        console.log('FXAA分辨率参数:', postProcessor.fxaaPass.material.uniforms['resolution'].value);
                    }
                }
            }
        }
    }
};

// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    console.log('[MMD] mmd-integration.js 已加载，开始应用初始状态');
    applyInitialState();
}); 