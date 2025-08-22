/**
 * MMD渲染器核心模块
 * 基于Three.js + MMDLoader实现3D模型渲染
 * 集成卡通渲染管线
 */

// 导入卡通渲染器
import { ToonRenderer } from './toon-renderer.js';

// 全局变量
let scene, camera, renderer, mixer, clock, axesHelper;
let currentModel = null;
let currentAnimation = null;
let isInitialized = false;
let toonRenderer = null; // 卡通渲染器实例
let postProcessor = null; // 后处理器实例

// 检查WebGL支持
function checkWebGLSupport() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) {
            throw new Error('WebGL not supported');
        }
        return true;
    } catch (error) {
        console.error('WebGL支持检查失败:', error);
        return false;
    }
}

// 尝试创建WebGL渲染器，带降级方案
function createWebGLRenderer(fallbackOptions = {}) {
    const options = {
        antialias: true,
        alpha: true,
        powerPreference: "default",
        failIfMajorPerformanceCaveat: false,
        ...fallbackOptions
    };

    try {
        console.log('尝试创建WebGL渲染器，选项:', options);
        return new THREE.WebGLRenderer(options);
    } catch (error) {
        console.warn('WebGL渲染器创建失败，尝试降级选项:', error);
        
        // 降级方案1：禁用抗锯齿
        if (options.antialias) {
            try {
                const fallbackOptions1 = { ...options, antialias: false };
                console.log('尝试降级方案1：禁用抗锯齿');
                return new THREE.WebGLRenderer(fallbackOptions1);
            } catch (error1) {
                console.warn('降级方案1失败:', error1);
            }
        }
        
        // 降级方案2：使用软件渲染
        try {
            const fallbackOptions2 = { 
                ...options, 
                antialias: false,
                powerPreference: "low-power"
            };
            console.log('尝试降级方案2：使用低功耗模式');
            return new THREE.WebGLRenderer(fallbackOptions2);
        } catch (error2) {
            console.warn('降级方案2失败:', error2);
        }
        
        throw new Error('所有WebGL渲染器创建方案都失败了');
    }
}

// 初始化MMD渲染器
export function initMMDRenderer(containerId) {
    if (isInitialized) {
        console.warn('MMD渲染器已经初始化');
        return;
    }

    console.log('正在初始化MMD渲染器...');
    
    // 检查WebGL支持
    if (!checkWebGLSupport()) {
        const errorMsg = '您的浏览器或系统不支持WebGL，无法启用3D角色功能。请尝试：\n1. 更新显卡驱动\n2. 启用硬件加速\n3. 使用Chrome或Firefox浏览器\n4. 检查安全软件设置';
        console.error(errorMsg);
        alert(errorMsg);
        throw new Error('WebGL not supported');
    }
    
    // 创建场景
    scene = new THREE.Scene();
    // 透明背景，仅渲染角色
    scene.background = null;
    
    // 获取容器尺寸
    const container = document.getElementById(containerId);
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    // 创建相机
    camera = new THREE.PerspectiveCamera(
        45, 
        width / height, 
        1, 
        2000
    );
    camera.position.set(0, 10, 25);
    
    // 创建渲染器（带降级方案）
    try {
        renderer = createWebGLRenderer();
    } catch (error) {
        console.error('WebGL渲染器创建失败:', error);
        const errorMsg = '无法创建WebGL渲染器。可能的原因：\n1. 显卡驱动过旧或有问题\n2. 硬件加速被禁用\n3. 安全软件阻止了WebGL\n4. 系统资源不足\n\n请尝试重启浏览器或更新显卡驱动。';
        alert(errorMsg);
        throw error;
    }
    renderer.setClearColor(0x000000, 0);
    renderer.setSize(width, height);
    // 使用原始渲染器的抗锯齿
    renderer.setPixelRatio(window.devicePixelRatio);
    // 使用sRGB输出，贴图颜色更接近Blender
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // 添加到容器
    if (container) {
        container.appendChild(renderer.domElement);
    } else {
        document.body.appendChild(renderer.domElement);
    }
    
    // 创建时钟
    clock = new THREE.Clock();
    
    // 添加光源
    setupLighting();
    
    // 添加地面
    setupGround();
    
    // 设置窗口大小调整
    window.addEventListener('resize', onWindowResize);
    
    isInitialized = true;
    console.log('MMD渲染器初始化完成');
    
    // 初始化卡通渲染器
    try {
        toonRenderer = new ToonRenderer(renderer, scene, camera);
        console.log('卡通渲染器初始化完成');
    } catch (error) {
        console.warn('卡通渲染器初始化失败:', error);
    }
    
    // 初始化后处理器
    try {
        console.log('开始初始化后处理器...');
        postProcessor = new PostProcessor(renderer, scene, camera);
        
        // 检查初始化结果
        if (postProcessor && postProcessor.composer) {
            console.log('后处理器初始化完成，合成器已创建');
        } else {
            console.warn('后处理器初始化完成，但合成器未创建');
        }
    } catch (error) {
        console.error('后处理器初始化失败:', error);
        console.error('错误详情:', error.stack);
    }
    
    // 默认不显示坐标轴
    setAxesVisible(false);

    // 如果后处理器已初始化，确保其尺寸也正确
    if (postProcessor && postProcessor.composer) {
        postProcessor.onWindowResize(width, height);
    }

    // 开始渲染循环
    animate();
}

// 设置光照
function setupLighting() {
    // 柔和环境光，整体提亮
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.35);
    scene.add(ambientLight);

    // 半球光，增强头顶亮度与面部自然光
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x222222, 0.1);
    hemiLight.position.set(0, 10, 8);
    scene.add(hemiLight);
    
    // 主方向光，从正面上方直打面部
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.15);
    directionalLight.position.set(0, 12, 6);
    directionalLight.target.position.set(0, 12, 0);
    scene.add(directionalLight.target);
    directionalLight.castShadow = true;
    directionalLight.shadow.bias = -0.0005;
    directionalLight.shadow.normalBias = 0.02;
    directionalLight.shadow.camera.near = 0.1;
    directionalLight.shadow.camera.far = 30;
    directionalLight.shadow.camera.left = -10;
    directionalLight.shadow.camera.right = 10;
    directionalLight.shadow.camera.top = 10;
    directionalLight.shadow.camera.bottom = -10;
    scene.add(directionalLight);
    

    // 侧前方补光，丰富面部细节
    const fillLight = new THREE.PointLight(0xffffff, 0.12);
    fillLight.position.set(0, 6, 6);
    scene.add(fillLight);
}

// 移除地面（仅渲染角色）
function setupGround() {
    // 不创建任何地面，保持透明背景
}

// 加载MMD模型
export function loadMMDModel(modelPath, callback) {
    if (!isInitialized) {
        console.error('MMD渲染器未初始化');
        return;
    }
    
    console.log('正在加载MMD模型:', modelPath);
    
    // 创建MMDLoader
    const loader = new THREE.MMDLoader();
    
    // 加载模型
    loader.load(
        modelPath,
        (object) => {
            console.log('MMD模型加载成功');
            
            // 清理当前模型
            if (currentModel) {
                scene.remove(currentModel);
                if (mixer) {
                    mixer.stopAllAction();
                }
            }
            
            // 设置新模型
            currentModel = object;
            currentModel.position.set(0, 0, 0);
            currentModel.scale.set(0.1, 0.1, 0.1);
            currentModel.castShadow = true;
            currentModel.receiveShadow = true;

            // 调整材质与阴影，缓解脸部偏暗（发丝半透明贴图常见问题）
            currentModel.traverse(node => {
                if (node.isMesh) {
                    if (node.material) {
                        const mats = Array.isArray(node.material) ? node.material : [node.material];
                        mats.forEach((mat, index) => {
                            // 面部材质常用命名包含 'face' / 'skin' / 'head'
                            const name = (mat.name || node.name || '').toLowerCase();
                            
                            // 启用sRGB
                            if (mat.map && mat.map.encoding !== THREE.sRGBEncoding) {
                                mat.map.encoding = THREE.sRGBEncoding;
                                mat.map.needsUpdate = true;
                            }
                            
                            // 半透明发丝：避免阴影过暗压脸
                            if (mat.transparent || mat.alphaTest > 0) {
                                mat.alphaTest = Math.max(mat.alphaTest || 0.5, 0.5);
                                node.castShadow = false; // 发丝不投影
                            }
                            
                            // 手动提高脸部贴图亮度 - 使用emissive属性
                            if (name.includes('face') || name.includes('skin') || name.includes('head') || name.includes('脸')) {
                                // 设置自发光颜色和强度
                                mat.emissive = new THREE.Color(0.15, 0.12, 0.1); // 暖色调自发光
                                mat.emissiveIntensity = 0.4; // 发光强度40%
                                
                                // 确保材质支持发光
                                // if (mat.isMeshToonMaterial) {
                                //     // 对于卡通材质，调整渐变贴图
                                //     if (mat.gradientMap) {
                                //         // 创建更亮的渐变贴图
                                //         const brightGradientMap = createBrightGradientMap();
                                //         mat.gradientMap = brightGradientMap;
                                //     }
                                // }
                                
                                // 轻微调整材质颜色
                                if (mat.color) {
                                    const originalColor = mat.color.clone();
                                    mat.color.multiplyScalar(1.50); // 调亮50%
                                    console.log(`[MMD] 已为 ${name} 应用发光效果: 颜色 ${originalColor.getHexString()} -> ${mat.color.getHexString()}`);
                                }
                                
                                console.log(`[MMD] 已为 ${name} 添加自发光效果: emissive=${mat.emissive.getHexString()}, intensity=${mat.emissiveIntensity}`);
                            }
                            
                            mat.needsUpdate = true;
                        });
                    }
                }
            });
            
            // 创建动画混合器
            mixer = new THREE.AnimationMixer(currentModel);
            
            scene.add(currentModel);
            
            if (callback) {
                callback(object);
            }
        },
        (progress) => {
            console.log('加载进度:', (progress.loaded / progress.total * 100) + '%');
        },
        (error) => {
            console.error('MMD模型加载失败:', error);
        }
    );
}

// 加载动画
export function loadAnimation(animationPath, callback) {
    if (!currentModel || !mixer) {
        console.error('没有加载的模型或动画混合器');
        return;
    }
    
    console.log('正在加载动画:', animationPath);
    
    const loader = new THREE.MMDLoader();
    
    loader.loadAnimation(
        animationPath,
        currentModel,
        (animation) => {
            console.log('动画加载成功');
            
            // 停止当前动画
            if (currentAnimation) {
                mixer.stopAllAction();
            }
            
            // 播放新动画
            currentAnimation = mixer.clipAction(animation);
            currentAnimation.play();
            
            if (callback) {
                callback(animation);
            }
        },
        (progress) => {
            console.log('动画加载进度:', (progress.loaded / progress.total * 100) + '%');
        },
        (error) => {
            console.error('动画加载失败:', error);
        }
    );
}

// 播放表情动画
export function playExpression(expressionName) {
    if (!currentModel) {
        console.error('没有加载的模型');
        return;
    }
    
    // 这里可以添加表情控制逻辑
    console.log('播放表情:', expressionName);
}

// 设置相机位置
export function setCameraPosition(x, y, z) {
    if (camera) {
        camera.position.set(x, y, z);
    }
}

// 设置相机目标
export function setCameraTarget(x, y, z) {
    if (camera) {
        camera.lookAt(x, y, z);
    }
}

// 窗口大小调整
function onWindowResize() {
    if (camera && renderer) {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
        
        // 更新后处理器尺寸
        if (postProcessor) {
            postProcessor.onWindowResize(window.innerWidth, window.innerHeight);
        }
    }
}

// 控制坐标轴显示
export function setAxesVisible(visible = true) {
    if (!scene) return;
    if (visible) {
        if (!axesHelper) {
            axesHelper = new THREE.AxesHelper(1.0); // 1单位轴
            axesHelper.position.set(0, 0, 0);
        }
        if (!scene.children.includes(axesHelper)) {
            scene.add(axesHelper);
        }
    } else if (axesHelper) {
        scene.remove(axesHelper);
    }
}

// 渲染循环
function animate() {
    requestAnimationFrame(animate);
    
    if (mixer && clock) {
        const delta = clock.getDelta();
        mixer.update(delta);
    }
    
    if (renderer && scene && camera) {
        // 使用后处理器进行渲染（如果可用）
        if (postProcessor && postProcessor.composer) {
            postProcessor.render();
            // 调试信息（只在第一次渲染时显示）
            if (!window._postProcessorDebugShown) {
                console.log('[PostProcessor] 正在使用后处理器渲染');
                window._postProcessorDebugShown = true;
            }
        } else {
            // 使用卡通渲染器进行渲染
            if (toonRenderer) {
                toonRenderer.render();
            } else {
                renderer.render(scene, camera);
            }
            // 调试信息
            if (!window._rendererDebugShown) {
                console.log('[PostProcessor] 后处理器不可用，使用标准渲染');
                window._rendererDebugShown = true;
            }
        }
    }
}

// 清理资源
export function dispose() {
    if (mixer) {
        mixer.stopAllAction();
    }
    
    if (currentModel) {
        scene.remove(currentModel);
        currentModel.geometry.dispose();
        currentModel.material.dispose();
    }
    
    if (toonRenderer) {
        toonRenderer.dispose();
        toonRenderer = null;
    }
    
    if (postProcessor) {
        postProcessor.dispose();
        postProcessor = null;
    }
    
    if (renderer) {
        renderer.dispose();
    }
    
    isInitialized = false;
    console.log('MMD渲染器已清理');
}

// 获取当前模型
export function getCurrentModel() {
    return currentModel;
}

// 获取当前动画
export function getCurrentAnimation() {
    return currentAnimation;
}

// 检查是否已初始化
export function isRendererInitialized() {
    return isInitialized;
}

// 创建更亮的渐变贴图
function createBrightGradientMap() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 1;
    const ctx = canvas.getContext('2d');
    
    const gradient = ctx.createLinearGradient(0, 0, 256, 0);
    
    // 创建更亮的渐变，减少暗部
    gradient.addColorStop(0, 'rgb(40, 40, 40)');   // 暗部提高
    gradient.addColorStop(0.3, 'rgb(80, 80, 80)'); // 中间调提高
    gradient.addColorStop(0.7, 'rgb(180, 180, 180)'); // 亮部
    gradient.addColorStop(1, 'rgb(255, 255, 255)');   // 最亮
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 256, 1);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
}

// 卡通渲染相关函数
export function getToonRenderer() {
    return toonRenderer;
}

export function updateToonParams(params) {
    if (toonRenderer) {
        toonRenderer.updateParams(params);
    }
}

export function toggleToonRendering(enabled) {
    if (toonRenderer) {
        toonRenderer.updateParams({
            celShading: enabled,
            outline: enabled,
            colorGrading: enabled
        });
    }
}

// 后处理器相关函数
export function getPostProcessor() {
    return postProcessor;
}

export function updatePostProcessorParams(params) {
    if (postProcessor) {
        postProcessor.updateParams(params);
    }
}

export function togglePostProcessing(enabled) {
    if (postProcessor) {
        postProcessor.updateParams({
            contrast: enabled,
            shadowEnhancement: enabled,
            bloom: enabled,
            fxaa: enabled
        });
    }
}

// 初始化着色器
export function initializeShaders() {
    // 确保LuminosityHighPassShader的defaultColor正确初始化
    if (typeof THREE.LuminosityHighPassShader !== 'undefined' && 
        THREE.LuminosityHighPassShader.uniforms.defaultColor.value === null) {
        THREE.LuminosityHighPassShader.uniforms.defaultColor.value = new THREE.Color(0x000000);
        console.log('[Shader Init] LuminosityHighPassShader defaultColor 已初始化');
    }
}

// 检查着色器可用性
export function checkShaderAvailability() {
    // 先尝试初始化着色器
    initializeShaders();
    
    const shaders = {
        'THREE.FXAAShader': typeof THREE.FXAAShader !== 'undefined',
        'THREE.LuminosityHighPassShader': typeof THREE.LuminosityHighPassShader !== 'undefined',
        'THREE.CopyShader': typeof THREE.CopyShader !== 'undefined',
        'THREE.EffectComposer': typeof THREE.EffectComposer !== 'undefined',
        'THREE.RenderPass': typeof THREE.RenderPass !== 'undefined',
        'THREE.ShaderPass': typeof THREE.ShaderPass !== 'undefined',
        'THREE.OutlinePass': typeof THREE.OutlinePass !== 'undefined'
    };
    
    console.log('[Shader Check] 着色器可用性检查:');
    Object.entries(shaders).forEach(([name, available]) => {
        console.log(`[Shader Check] ${name}: ${available ? '✓' : '✗'}`);
        if (!available) {
            console.warn(`[Shader Check] ${name} 未定义，可能需要检查脚本加载顺序`);
        }
    });
    
    // 检查THREE对象本身
    console.log('[Shader Check] THREE对象状态:', {
        'THREE': typeof THREE !== 'undefined',
        'THREE.Color': typeof THREE.Color !== 'undefined',
        'THREE.Vector2': typeof THREE.Vector2 !== 'undefined',
        'THREE.ShaderMaterial': typeof THREE.ShaderMaterial !== 'undefined'
    });
    
    return shaders;
}

// 检查后处理器状态
export function checkPostProcessorStatus() {
    if (!postProcessor) {
        console.log('[PostProcessor] 后处理器未初始化');
        return false;
    }
    
    if (!postProcessor.params.enabled) {
        console.log('[PostProcessor] 后处理器已禁用');
        return false;
    }
    
    if (!postProcessor.composer) {
        console.log('[PostProcessor] 后处理器合成器未创建');
        return false;
    }
    
    console.log('[PostProcessor] 后处理器状态正常');
    console.log('[PostProcessor] 当前参数:', postProcessor.params);
    
    // 检查FXAA状态
    if (postProcessor.fxaaPass) {
        console.log('[PostProcessor] FXAA抗锯齿已启用');
        if (postProcessor.fxaaPass.material.uniforms && postProcessor.fxaaPass.material.uniforms['resolution']) {
            console.log('[PostProcessor] FXAA分辨率参数:', 
                postProcessor.fxaaPass.material.uniforms['resolution'].value.x, 
                postProcessor.fxaaPass.material.uniforms['resolution'].value.y);
        }
    } else {
        console.log('[PostProcessor] FXAA抗锯齿未启用');
    }
    
    return true;
}

// 动态调整脸部亮度
export function adjustFaceBrightness(brightness = 1.2, emissiveIntensity = 0.4) {
    if (!currentModel) {
        console.warn('没有加载的模型');
        return;
    }
    
    currentModel.traverse(node => {
        if (node.isMesh && node.material) {
            const mats = Array.isArray(node.material) ? node.material : [node.material];
            mats.forEach(mat => {
                const name = (mat.name || node.name || '').toLowerCase();
                
                if (name.includes('face') || name.includes('skin') || name.includes('head') || name.includes('脸')) {
                    // 调整自发光强度
                    mat.emissiveIntensity = emissiveIntensity;
                    
                    // 调整颜色亮度
                    if (mat.color) {
                        const originalColor = mat.color.clone();
                        mat.color.multiplyScalar(brightness);
                        console.log(`[MMD] 已调整 ${name} 亮度: emissiveIntensity=${emissiveIntensity}, color=${originalColor.getHexString()} -> ${mat.color.getHexString()}`);
                    }
                    
                    // 更新着色器材质的亮度参数（如果存在）
                    if (mat.uniforms && mat.uniforms.brightness) {
                        mat.uniforms.brightness.value = brightness;
                        console.log(`[MMD] 已更新 ${name} 着色器亮度参数: ${brightness}`);
                    }
                    
                    mat.needsUpdate = true;
                }
            });
        }
    });
}

// 获取当前脸部亮度设置
export function getFaceBrightnessSettings() {
    if (!currentModel) return null;
    
    let settings = null;
    currentModel.traverse(node => {
        if (node.isMesh && node.material && !settings) {
            const mats = Array.isArray(node.material) ? node.material : [node.material];
            mats.forEach(mat => {
                const name = (mat.name || node.name || '').toLowerCase();
                
                if (name.includes('face') || name.includes('skin') || name.includes('head') || name.includes('脸')) {
                    settings = {
                        name: name,
                        emissiveIntensity: mat.emissiveIntensity || 0,
                        emissiveColor: mat.emissive ? mat.emissive.getHexString() : '000000',
                        color: mat.color ? mat.color.getHexString() : 'ffffff',
                        shaderBrightness: mat.uniforms?.brightness?.value || null
                    };
                }
            });
        }
    });
    
    return settings;
}

// 后处理器类 - 为最终渲染结果添加对比度和阴影增强
class PostProcessor {
    constructor(renderer, scene, camera) {
        this.renderer = renderer;
        this.scene = scene;
        this.camera = camera;
        this.composer = null;
        this.contrastPass = null;
        this.shadowPass = null;
        this.bloomPass = null;
        this.fxaaPass = null;
        
        // 后处理参数
        this.params = {
            // 后处理器开关
            enabled: true,
            
            // 对比度增强
            contrast: true,
            contrastValue: 1.65,
            brightness: 0.8,
            saturation: 1.1,
            
            // 阴影增强
            // shadowEnhancement: true,
            // shadowIntensity: 0.5,
            // shadowRadius: 0.5,
            
            // 泛光效果
            // bloom: true,
            // bloomThreshold: 0.7,
            // bloomStrength: 0.3,
            // bloomRadius: 0.4,
            
            // 抗锯齿已禁用，使用原始渲染器抗锯齿
            
            // 性能设置
            pixelRatio: window.devicePixelRatio || 1
        };
        
        this.init();
    }
    
    init() {
        // 检查是否启用后处理器
        if (!this.params.enabled) {
            console.log('后处理器已禁用');
            return;
        }
        
        // 检查Three.js后处理库是否可用
        if (typeof THREE.EffectComposer === 'undefined') {
            console.warn('THREE.EffectComposer not available, post-processing disabled');
            return;
        }
        
        // 检查是否支持WebGL2
        if (!this.renderer.capabilities.isWebGL2) {
            console.warn('WebGL2 not supported, post-processing disabled');
            return;
        }
        
        try {
            console.log('开始初始化后处理管线...');
            this.initPostProcessingPipeline();
            console.log('后处理管线初始化成功');
        } catch (error) {
            console.error('Post-processing pipeline failed:', error);
            console.error('错误详情:', error.stack);
        }
    }
    
    // 初始化后处理管线
    initPostProcessingPipeline() {
        // 确保渲染器尺寸正确设置
        const screenWidth = window.innerWidth;
        const screenHeight = window.innerHeight;
        
        // 如果渲染器尺寸不正确，先设置一次
        if (this.renderer.domElement.width !== screenWidth * window.devicePixelRatio || 
            this.renderer.domElement.height !== screenHeight * window.devicePixelRatio) {
            this.renderer.setSize(screenWidth, screenHeight);
        }
        
        // 使用原始渲染器的实际分辨率
        const rendererCanvas = this.renderer.domElement;
        const renderWidth = rendererCanvas.width;
        const renderHeight = rendererCanvas.height;
        
        console.log('后处理器渲染目标分辨率:', {
            screen: `${screenWidth}x${screenHeight}`,
            renderer: `${renderWidth}x${renderHeight}`,
            pixelRatio: this.params.pixelRatio,
            devicePixelRatio: window.devicePixelRatio
        });
        
        // 创建渲染目标，使用原始渲染器的分辨率
        const renderTarget = new THREE.WebGLRenderTarget(
            renderWidth,
            renderHeight,
            {
                minFilter: THREE.LinearFilter,
                magFilter: THREE.LinearFilter,
                format: THREE.RGBAFormat,
                encoding: THREE.sRGBEncoding,
                stencilBuffer: false,
                depthBuffer: true
            }
        );
        
        // 创建后处理合成器
        this.composer = new THREE.EffectComposer(this.renderer, renderTarget);
        
        // 基础渲染通道
        const renderPass = new THREE.RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);
        
        // 对比度增强通道
        if (this.params.contrast) {
            this.contrastPass = new THREE.ShaderPass(ContrastEnhancementShader);
            this.contrastPass.uniforms.contrast.value = this.params.contrastValue;
            this.contrastPass.uniforms.brightness.value = this.params.brightness;
            this.contrastPass.uniforms.saturation.value = this.params.saturation;
            this.composer.addPass(this.contrastPass);
        }
        
        // 阴影增强通道
        if (this.params.shadowEnhancement) {
            this.shadowPass = new THREE.ShaderPass(ShadowEnhancementShader);
            this.shadowPass.uniforms.intensity.value = this.params.shadowIntensity;
            this.shadowPass.uniforms.radius.value = this.params.shadowRadius;
            this.composer.addPass(this.shadowPass);
        }
        
        // 泛光效果
        if (this.params.bloom) {
            try {
                // 检查必要的着色器是否可用
                if (typeof THREE.LuminosityHighPassShader === 'undefined') {
                    console.warn('THREE.LuminosityHighPassShader not available, bloom disabled');
                } else if (typeof THREE.CopyShader === 'undefined') {
                    console.warn('THREE.CopyShader not available, bloom disabled');
                } else {
                    this.bloomPass = new THREE.UnrealBloomPass(
                        new THREE.Vector2(window.innerWidth, window.innerHeight),
                        this.params.bloomStrength,
                        this.params.bloomRadius,
                        this.params.bloomThreshold
                    );
                    this.composer.addPass(this.bloomPass);
                    console.log('泛光效果已启用');
                }
            } catch (error) {
                console.warn('泛光效果初始化失败:', error);
                console.warn('错误详情:', error.message);
            }
        }
        
        // 添加FXAA抗锯齿
        try {
            if (typeof THREE.FXAAShader !== 'undefined') {
                this.fxaaPass = new THREE.ShaderPass(THREE.FXAAShader);
                
                // 检查着色器是否成功创建
                if (this.fxaaPass.material && this.fxaaPass.material.uniforms) {
                    // 使用渲染目标的实际分辨率
                    const renderTarget = this.composer.renderTarget1;
                    const renderWidth = renderTarget ? renderTarget.width : window.innerWidth;
                    const renderHeight = renderTarget ? renderTarget.height : window.innerHeight;
                    
                    this.fxaaPass.material.uniforms['resolution'].value.x = 1 / renderWidth;
                    this.fxaaPass.material.uniforms['resolution'].value.y = 1 / renderHeight;
                    
                    // 检查uniforms是否正确设置
                    if (this.fxaaPass.material.uniforms['resolution'].value.x !== 0 && 
                        this.fxaaPass.material.uniforms['resolution'].value.y !== 0) {
                        this.composer.addPass(this.fxaaPass);
                        console.log('FXAA抗锯齿已启用，渲染分辨率:', renderWidth, 'x', renderHeight);
                        console.log('FXAA分辨率参数:', this.fxaaPass.material.uniforms['resolution'].value);
                    }
                }
            } else {
                console.warn('THREE.FXAAShader not available, FXAA disabled');
            }
        } catch (error) {
            console.warn('FXAA抗锯齿初始化失败:', error.message);
        }
        
        console.log('后处理管线初始化完成');
    }
    
    // 渲染
    render() {
        if (this.composer && this.params.enabled) {
            this.composer.render();
        } else {
            // 如果后处理器禁用，使用原始渲染器
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    // 更新参数
    updateParams(newParams) {
        Object.assign(this.params, newParams);
        
        // 更新着色器参数
        if (this.contrastPass) {
            this.contrastPass.uniforms.contrast.value = this.params.contrastValue;
            this.contrastPass.uniforms.brightness.value = this.params.brightness;
            this.contrastPass.uniforms.saturation.value = this.params.saturation;
        }
        
        if (this.shadowPass) {
            this.shadowPass.uniforms.intensity.value = this.params.shadowIntensity;
            this.shadowPass.uniforms.radius.value = this.params.shadowRadius;
        }
        
        if (this.bloomPass) {
            this.bloomPass.strength = this.params.bloomStrength;
            this.bloomPass.radius = this.params.bloomRadius;
            this.bloomPass.threshold = this.params.bloomThreshold;
        }
        
        // 抗锯齿参数更新已移除，使用原始渲染器抗锯齿
    }
    
    // 窗口大小调整
    onWindowResize(width, height) {
        if (this.composer) {
            // 使用原始渲染器的实际分辨率
            const rendererCanvas = this.renderer.domElement;
            const renderWidth = rendererCanvas.width;
            const renderHeight = rendererCanvas.height;
            
            this.composer.setSize(renderWidth, renderHeight);
            
            // 更新FXAA分辨率参数
            if (this.fxaaPass && this.fxaaPass.material.uniforms['resolution']) {
                this.fxaaPass.material.uniforms['resolution'].value.x = 1 / renderWidth;
                this.fxaaPass.material.uniforms['resolution'].value.y = 1 / renderHeight;
            }
            
            console.log('后处理器窗口大小调整:', {
                screen: `${width}x${height}`,
                renderer: `${renderWidth}x${renderHeight}`,
                fxaaUpdated: !!this.fxaaPass
            });
        }
    }
    
    // 强制刷新尺寸
    forceResize() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        this.onWindowResize(width, height);
        console.log('后处理器尺寸已强制刷新');
    }
    
    // 检查输出分辨率
    checkOutputResolution() {
        if (this.renderer) {
            const canvas = this.renderer.domElement;
            const actualWidth = canvas.width;
            const actualHeight = canvas.height;
            const cssWidth = canvas.clientWidth;
            const cssHeight = canvas.clientHeight;
            
            // 检查后处理器渲染目标
            let postProcessorInfo = null;
            if (this.composer) {
                const renderTarget1 = this.composer.renderTarget1;
                const renderTarget2 = this.composer.renderTarget2;
                postProcessorInfo = {
                    renderTarget1: renderTarget1 ? `${renderTarget1.width}x${renderTarget1.height}` : 'null',
                    renderTarget2: renderTarget2 ? `${renderTarget2.width}x${renderTarget2.height}` : 'null',
                    passes: this.composer.passes.length,
                    inputResolution: `${actualWidth}x${actualHeight}`,
                    outputResolution: `${cssWidth}x${cssHeight}`
                };
            }
            
            console.log('渲染器输出分辨率检查:', {
                canvas: `${actualWidth}x${actualHeight}`,
                css: `${cssWidth}x${cssHeight}`,
                screen: `${window.innerWidth}x${window.innerHeight}`,
                pixelRatio: window.devicePixelRatio,
                rendererPixelRatio: this.renderer.getPixelRatio(),
                postProcessor: postProcessorInfo
            });
            
            return {
                canvas: { width: actualWidth, height: actualHeight },
                css: { width: cssWidth, height: cssHeight },
                screen: { width: window.innerWidth, height: window.innerHeight },
                postProcessor: postProcessorInfo
            };
        }
        return null;
    }
    
    // 启用后处理器
    enable() {
        this.params.enabled = true;
        if (!this.composer) {
            this.init();
        }
        console.log('后处理器已启用');
    }
    
    // 禁用后处理器
    disable() {
        this.params.enabled = false;
        console.log('后处理器已禁用');
    }
    
    // 切换后处理器状态
    toggle() {
        if (this.params.enabled) {
            this.disable();
        } else {
            this.enable();
        }
        return this.params.enabled;
    }
    
    // 清理资源
    dispose() {
        if (this.composer) {
            this.composer.dispose();
        }
    }
}

// 对比度增强着色器
const ContrastEnhancementShader = {
    uniforms: {
        'tDiffuse': { value: null },
        'contrast': { value: 1.15 },
        'brightness': { value: 1.0 },
        'saturation': { value: 1.1 }
    },
    
    vertexShader: `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    
    fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform float contrast;
        uniform float brightness;
        uniform float saturation;
        varying vec2 vUv;
        
        vec3 adjustContrast(vec3 color, float contrast) {
            return 0.5 + (contrast * (color - 0.5));
        }
        
        vec3 adjustBrightness(vec3 color, float brightness) {
            return color * brightness;
        }
        
        vec3 adjustSaturation(vec3 color, float saturation) {
            float luminance = dot(color, vec3(0.299, 0.587, 0.114));
            return mix(vec3(luminance), color, saturation);
        }
        
        void main() {
            vec4 texColor = texture2D(tDiffuse, vUv);
            vec3 color = texColor.rgb;
            
            // 应用对比度增强
            color = adjustContrast(color, contrast);
            
            // 应用亮度调整
            color = adjustBrightness(color, brightness);
            
            // 应用饱和度调整
            color = adjustSaturation(color, saturation);
            
            // 限制颜色范围
            color = clamp(color, 0.0, 1.0);
            
            gl_FragColor = vec4(color, texColor.a);
        }
    `
};

// 阴影增强着色器
const ShadowEnhancementShader = {
    uniforms: {
        'tDiffuse': { value: null },
        'intensity': { value: 0.3 },
        'radius': { value: 0.5 }
    },
    
    vertexShader: `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    
    fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform float intensity;
        uniform float radius;
        varying vec2 vUv;
        
        void main() {
            vec4 texColor = texture2D(tDiffuse, vUv);
            vec3 color = texColor.rgb;
            
            // 计算亮度
            float luminance = dot(color, vec3(0.299, 0.587, 0.114));
            
            // 增强暗部
            if (luminance < 0.5) {
                float shadowFactor = pow(1.0 - luminance, 2.0) * intensity;
                color = color * (1.0 - shadowFactor * radius);
            }
            
            // 限制颜色范围
            color = clamp(color, 0.0, 1.0);
            
            gl_FragColor = vec4(color, texColor.a);
        }
    `
};

// 简单抗锯齿着色器（备选方案）
const SimpleAntiAliasingShader = {
    uniforms: {
        'tDiffuse': { value: null },
        'resolution': { value: new THREE.Vector2(1, 1) }
    },
    
    vertexShader: `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    
    fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform vec2 resolution;
        varying vec2 vUv;
        
        void main() {
            vec2 texelSize = 1.0 / resolution;
            vec2 uv = vUv;
            
            // 9x采样抗锯齿，正确处理alpha通道
            vec4 color = vec4(0.0);
            float weight = 1.0 / 9.0;
            
            // 中心点
            vec4 centerColor = texture2D(tDiffuse, uv);
            color += centerColor * weight;
            
            // 周围8个点
            color += texture2D(tDiffuse, uv + vec2(-texelSize.x, -texelSize.y)) * weight;
            color += texture2D(tDiffuse, uv + vec2( 0.0, -texelSize.y)) * weight;
            color += texture2D(tDiffuse, uv + vec2( texelSize.x, -texelSize.y)) * weight;
            color += texture2D(tDiffuse, uv + vec2(-texelSize.x,  0.0)) * weight;
            color += texture2D(tDiffuse, uv + vec2( texelSize.x,  0.0)) * weight;
            color += texture2D(tDiffuse, uv + vec2(-texelSize.x,  texelSize.y)) * weight;
            color += texture2D(tDiffuse, uv + vec2( 0.0,  texelSize.y)) * weight;
            color += texture2D(tDiffuse, uv + vec2( texelSize.x,  texelSize.y)) * weight;
            
            // 确保alpha通道正确
            // 计算alpha通道的加权平均
            float alphaSum = 0.0;
            float alphaWeight = 0.0;
            
            // 重新计算alpha通道，只考虑非透明像素
            vec4 samples[9];
            samples[0] = texture2D(tDiffuse, uv);
            samples[1] = texture2D(tDiffuse, uv + vec2(-texelSize.x, -texelSize.y));
            samples[2] = texture2D(tDiffuse, uv + vec2( 0.0, -texelSize.y));
            samples[3] = texture2D(tDiffuse, uv + vec2( texelSize.x, -texelSize.y));
            samples[4] = texture2D(tDiffuse, uv + vec2(-texelSize.x,  0.0));
            samples[5] = texture2D(tDiffuse, uv + vec2( texelSize.x,  0.0));
            samples[6] = texture2D(tDiffuse, uv + vec2(-texelSize.x,  texelSize.y));
            samples[7] = texture2D(tDiffuse, uv + vec2( 0.0,  texelSize.y));
            samples[8] = texture2D(tDiffuse, uv + vec2( texelSize.x,  texelSize.y));
            
            for (int i = 0; i < 9; i++) {
                if (samples[i].a > 0.1) {
                    alphaSum += samples[i].a * weight;
                    alphaWeight += weight;
                }
            }
            
            // 如果中心点透明，则保持透明
            if (centerColor.a < 0.1) {
                color.a = 0.0;
            } else {
                // 使用加权平均的alpha值
                color.a = alphaWeight > 0.0 ? alphaSum / alphaWeight : centerColor.a;
                color.a = clamp(color.a, 0.0, 1.0);
            }
            
            gl_FragColor = color;
        }
    `
};

// 导出卡通渲染器和后处理器
export { ToonRenderer, PostProcessor };
 