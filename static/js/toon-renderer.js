/**
 * 卡通渲染管线 (Toon Renderer)
 * 实现Cel Shading、边缘检测、颜色分级等卡通渲染效果
 */

// 卡通渲染器类
class ToonRenderer {
    constructor(renderer, scene, camera) {
        this.renderer = renderer;
        this.scene = scene;
        this.camera = camera;
        this.composer = null;
        this.toonPass = null;
        this.outlinePass = null;
        this.fxaaPass = null;
        this.bloomPass = null;
        this.colorGradingPass = null;
        
        // 卡通渲染参数
        this.params = {
            // 基础卡通效果
            celShading: true,
            celLevels: 3, // 色阶数量
            celThreshold: 0.5, // 色阶阈值
            
            // 边缘检测
            outline: true,
            outlineColor: 0x000000,
            outlineThickness: 0.003,
            outlineAlpha: 1.0,
            
            // 颜色分级
            colorGrading: true,
            saturation: 1.2,
            contrast: 1.1,
            brightness: 1.0,
            gamma: 1.0,
            
            // 泛光效果
            bloom: true,
            bloomThreshold: 0.8,
            bloomStrength: 0.5,
            bloomRadius: 0.5,
            
            // 抗锯齿
            fxaa: true,
            
            // 性能设置
            pixelRatio: window.devicePixelRatio || 1
        };
        
        this.init();
    }
    
    init() {
        // 检查是否支持WebGL2
        if (!this.renderer.capabilities.isWebGL2) {
            console.warn('WebGL2 not supported, falling back to basic toon shader');
            this.initBasicToonShader();
            return;
        }
        
        try {
            this.initAdvancedToonPipeline();
        } catch (error) {
            console.warn('Advanced toon pipeline failed, falling back to basic:', error);
            this.initBasicToonShader();
        }
    }
    
    // 初始化高级卡通渲染管线
    initAdvancedToonPipeline() {
        // 创建渲染目标
        const renderTarget = new THREE.WebGLRenderTarget(
            window.innerWidth * this.params.pixelRatio,
            window.innerHeight * this.params.pixelRatio,
            {
                minFilter: THREE.LinearFilter,
                magFilter: THREE.LinearFilter,
                format: THREE.RGBAFormat,
                encoding: THREE.sRGBEncoding
            }
        );
        
        // 创建后处理合成器
        this.composer = new THREE.EffectComposer(this.renderer, renderTarget);
        
        // 基础渲染通道
        const renderPass = new THREE.RenderPass(this.scene, this.camera);
        this.composer.addPass(renderPass);
        
        // 卡通着色通道
        if (this.params.celShading) {
            this.toonPass = new THREE.ShaderPass(ToonShader);
            this.toonPass.uniforms.celLevels.value = this.params.celLevels;
            this.toonPass.uniforms.celThreshold.value = this.params.celThreshold;
            this.composer.addPass(this.toonPass);
        }
        
        // 边缘检测通道
        if (this.params.outline) {
            try {
                if (typeof THREE.OutlinePass === 'undefined') {
                    console.warn('THREE.OutlinePass not available, outline disabled');
                } else {
                    this.outlinePass = new THREE.OutlinePass(
                        new THREE.Vector2(window.innerWidth, window.innerHeight),
                        this.scene,
                        this.camera
                    );
                    this.outlinePass.edgeStrength = this.params.outlineThickness;
                    this.outlinePass.edgeGlow = 0.0;
                    this.outlinePass.edgeThickness = 1.0;
                    this.outlinePass.pulsePeriod = 0;
                    this.outlinePass.visibleEdgeColor.setHex(this.params.outlineColor);
                    this.outlinePass.hiddenEdgeColor.setHex(this.params.outlineColor);
                    this.composer.addPass(this.outlinePass);
                    console.log('边缘检测通道已启用');
                }
            } catch (error) {
                console.warn('边缘检测通道初始化失败:', error.message);
            }
        }
        
        // 泛光效果
        if (this.params.bloom) {
            this.bloomPass = new THREE.UnrealBloomPass(
                new THREE.Vector2(window.innerWidth, window.innerHeight),
                this.params.bloomStrength,
                this.params.bloomRadius,
                this.params.bloomThreshold
            );
            this.composer.addPass(this.bloomPass);
        }
        
        // 颜色分级
        if (this.params.colorGrading) {
            this.colorGradingPass = new THREE.ShaderPass(ColorGradingShader);
            this.colorGradingPass.uniforms.saturation.value = this.params.saturation;
            this.colorGradingPass.uniforms.contrast.value = this.params.contrast;
            this.colorGradingPass.uniforms.brightness.value = this.params.brightness;
            this.colorGradingPass.uniforms.gamma.value = this.params.gamma;
            this.composer.addPass(this.colorGradingPass);
        }
        
        // FXAA抗锯齿
        if (this.params.fxaa) {
            this.fxaaPass = new THREE.ShaderPass(THREE.FXAAShader);
            this.fxaaPass.material.uniforms['resolution'].value.x = 1 / (window.innerWidth * this.params.pixelRatio);
            this.fxaaPass.material.uniforms['resolution'].value.y = 1 / (window.innerHeight * this.params.pixelRatio);
            this.composer.addPass(this.fxaaPass);
        }
        
        console.log('高级卡通渲染管线初始化完成');
    }
    
    // 初始化基础卡通着色器
    initBasicToonShader() {
        // 为场景中的所有材质应用卡通着色
        this.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                this.applyToonMaterial(object);
            }
        });
        
        console.log('基础卡通着色器初始化完成');
    }
    
    // 应用卡通材质
    applyToonMaterial(mesh) {
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        
        materials.forEach((material, index) => {
            if (material.isMeshToonMaterial) {
                // 已经是卡通材质，优化参数
                this.optimizeToonMaterial(material);
            } else {
                // 转换为卡通材质
                const toonMaterial = this.convertToToonMaterial(material);
                if (Array.isArray(mesh.material)) {
                    mesh.material[index] = toonMaterial;
                } else {
                    mesh.material = toonMaterial;
                }
            }
        });
    }
    
    // 转换为卡通材质
    convertToToonMaterial(originalMaterial) {
        const toonMaterial = new THREE.MeshToonMaterial({
            map: originalMaterial.map,
            color: originalMaterial.color,
            transparent: originalMaterial.transparent,
            opacity: originalMaterial.opacity,
            side: originalMaterial.side,
            alphaTest: originalMaterial.alphaTest,
            depthWrite: originalMaterial.depthWrite,
            depthTest: originalMaterial.depthTest
        });
        
        // 设置卡通渐变贴图
        this.setupToonGradient(toonMaterial);
        
        return toonMaterial;
    }
    
    // 设置卡通渐变贴图
    setupToonGradient(material) {
        // 创建卡通渐变贴图
        const gradientMap = this.createToonGradientMap();
        material.gradientMap = gradientMap;
        material.needsUpdate = true;
    }
    
    // 创建卡通渐变贴图
    createToonGradientMap() {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 1;
        const ctx = canvas.getContext('2d');
        
        const gradient = ctx.createLinearGradient(0, 0, 256, 0);
        const levels = this.params.celLevels;
        
        for (let i = 0; i <= levels; i++) {
            const pos = i / levels;
            const intensity = Math.pow(pos, 1.5); // 非线性渐变
            gradient.addColorStop(pos, `rgb(${Math.floor(intensity * 255)}, ${Math.floor(intensity * 255)}, ${Math.floor(intensity * 255)})`);
        }
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 256, 1);
        
        const texture = new THREE.CanvasTexture(canvas);
        texture.needsUpdate = true;
        return texture;
    }
    
    // 优化卡通材质
    optimizeToonMaterial(material) {
        if (material.gradientMap) {
            // 更新渐变贴图
            this.setupToonGradient(material);
        }
        
        // 优化渲染参数
        material.transparent = false;
        material.alphaTest = 0.5;
        material.depthWrite = true;
        material.depthTest = true;
    }
    
    // 渲染
    render() {
        if (this.composer) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }
    
    // 更新参数
    updateParams(newParams) {
        Object.assign(this.params, newParams);
        
        // 更新着色器参数
        if (this.toonPass) {
            this.toonPass.uniforms.celLevels.value = this.params.celLevels;
            this.toonPass.uniforms.celThreshold.value = this.params.celThreshold;
        }
        
        if (this.outlinePass) {
            this.outlinePass.edgeStrength = this.params.outlineThickness;
            this.outlinePass.visibleEdgeColor.setHex(this.params.outlineColor);
            this.outlinePass.hiddenEdgeColor.setHex(this.params.outlineColor);
        }
        
        if (this.bloomPass) {
            this.bloomPass.strength = this.params.bloomStrength;
            this.bloomPass.radius = this.params.bloomRadius;
            this.bloomPass.threshold = this.params.bloomThreshold;
        }
        
        if (this.colorGradingPass) {
            this.colorGradingPass.uniforms.saturation.value = this.params.saturation;
            this.colorGradingPass.uniforms.contrast.value = this.params.contrast;
            this.colorGradingPass.uniforms.brightness.value = this.params.brightness;
            this.colorGradingPass.uniforms.gamma.value = this.params.gamma;
        }
        
        // 重新应用材质
        this.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                this.applyToonMaterial(object);
            }
        });
    }
    
    // 窗口大小调整
    onWindowResize(width, height) {
        if (this.composer) {
            this.composer.setSize(width, height);
            
            if (this.fxaaPass) {
                this.fxaaPass.material.uniforms['resolution'].value.x = 1 / (width * this.params.pixelRatio);
                this.fxaaPass.material.uniforms['resolution'].value.y = 1 / (height * this.params.pixelRatio);
            }
        }
    }
    
    // 清理资源
    dispose() {
        if (this.composer) {
            this.composer.dispose();
        }
        
        // 清理材质
        this.scene.traverse((object) => {
            if (object.isMesh && object.material) {
                const materials = Array.isArray(object.material) ? object.material : [object.material];
                materials.forEach(material => {
                    if (material.gradientMap) {
                        material.gradientMap.dispose();
                    }
                    material.dispose();
                });
            }
        });
    }
}

// 卡通着色器
const ToonShader = {
    uniforms: {
        'tDiffuse': { value: null },
        'celLevels': { value: 3 },
        'celThreshold': { value: 0.5 }
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
        uniform float celLevels;
        uniform float celThreshold;
        varying vec2 vUv;
        
        void main() {
            vec4 texColor = texture2D(tDiffuse, vUv);
            vec3 color = texColor.rgb;
            
            // 计算亮度
            float brightness = dot(color, vec3(0.299, 0.587, 0.114));
            
            // 卡通化处理
            float cel = floor(brightness * celLevels) / celLevels;
            cel = smoothstep(0.0, celThreshold, cel);
            
            // 应用卡通效果
            color = color * cel;
            
            gl_FragColor = vec4(color, texColor.a);
        }
    `
};

// 颜色分级着色器
const ColorGradingShader = {
    uniforms: {
        'tDiffuse': { value: null },
        'saturation': { value: 1.0 },
        'contrast': { value: 1.0 },
        'brightness': { value: 1.0 },
        'gamma': { value: 1.0 }
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
        uniform float saturation;
        uniform float contrast;
        uniform float brightness;
        uniform float gamma;
        varying vec2 vUv;
        
        vec3 adjustSaturation(vec3 color, float saturation) {
            float luminance = dot(color, vec3(0.299, 0.587, 0.114));
            return mix(vec3(luminance), color, saturation);
        }
        
        vec3 adjustContrast(vec3 color, float contrast) {
            return 0.5 + (contrast * (color - 0.5));
        }
        
        vec3 adjustBrightness(vec3 color, float brightness) {
            return color * brightness;
        }
        
        vec3 adjustGamma(vec3 color, float gamma) {
            return pow(color, vec3(1.0 / gamma));
        }
        
        void main() {
            vec4 texColor = texture2D(tDiffuse, vUv);
            vec3 color = texColor.rgb;
            
            // 应用颜色分级
            color = adjustSaturation(color, saturation);
            color = adjustContrast(color, contrast);
            color = adjustBrightness(color, brightness);
            color = adjustGamma(color, gamma);
            
            // 限制颜色范围
            color = clamp(color, 0.0, 1.0);
            
            gl_FragColor = vec4(color, texColor.a);
        }
    `
};

// 导出卡通渲染器
export { ToonRenderer }; 