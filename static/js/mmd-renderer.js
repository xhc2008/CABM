/**
 * MMD渲染器核心模块
 * 基于Three.js + MMDLoader实现3D模型渲染
 */

// 全局变量
let scene, camera, renderer, mixer, clock, axesHelper;
let currentModel = null;
let currentAnimation = null;
let isInitialized = false;

// 初始化MMD渲染器
export function initMMDRenderer(containerId) {
    if (isInitialized) {
        console.warn('MMD渲染器已经初始化');
        return;
    }

    console.log('正在初始化MMD渲染器...');
    
    // 创建场景
    scene = new THREE.Scene();
    // 透明背景，仅渲染角色
    scene.background = null;
    
    // 获取容器尺寸
    const container = document.getElementById(containerId);
    const width = container ? container.clientWidth : window.innerWidth;
    const height = container ? container.clientHeight : window.innerHeight;
    
    // 创建相机
    camera = new THREE.PerspectiveCamera(
        45, 
        width / height, 
        1, 
        2000
    );
    camera.position.set(0, 10, 25);
    
    // 创建渲染器
    renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true, // 透明背景
        preserveDrawingBuffer: false
    });
    renderer.setClearColor(0x000000, 0);
    renderer.setSize(width, height);
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
    
    // 默认不显示坐标轴
    setAxesVisible(false);

    // 开始渲染循环
    animate();
}

// 设置光照
function setupLighting() {
    // 柔和环境光，整体提亮
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.25);
    scene.add(ambientLight);

    // 半球光，增强头顶亮度与面部自然光
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x222222, 0.1);
    hemiLight.position.set(0, 20, 8);
    scene.add(hemiLight);
    
    // 主方向光，从正面上方直打面部
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.3);
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
                        mats.forEach(mat => {
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
                            // 面部减少接收阴影
                            if (name.includes('face') || name.includes('skin') || name.includes('head')) {
                                node.receiveShadow = false;
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
        renderer.render(scene, camera);
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