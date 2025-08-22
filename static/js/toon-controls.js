/**
 * 卡通渲染控制面板
 * 提供实时参数调整和预设管理
 */

class ToonControls {
    constructor(toonRenderer) {
        this.toonRenderer = toonRenderer;
        this.panel = null;
        this.isVisible = false;
        
        // 预设配置
        this.presets = {
            '原始': {
                celShading: false,
                outline: false,
                colorGrading: false,
                bloom: false,
                fxaa: false
            },
            '性能': {
                celShading: true,
                celLevels: 3,
                celThreshold: 0.5,
                outline: false,
                colorGrading: false,
                bloom: false,
                fxaa: false
            }
        };
        
        this.createPanel();
    }
    
    // 创建控制面板
    createPanel() {
        // 创建面板容器
        this.panel = document.createElement('div');
        this.panel.id = 'toon-controls-panel';
        this.panel.className = 'toon-controls-panel';
        this.panel.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 320px;
            max-height: 80vh;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid #00ffff;
            border-radius: 8px;
            padding: 15px;
            color: white;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            z-index: 1000;
            overflow-y: auto;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
            display: none;
        `;
        
        // 创建面板内容
        this.panel.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="margin: 0; color: #00ffff; font-size: 14px;">渲染控制面板</h3>
                <button id="close-toon-panel" style="background: none; border: none; color: #00ffff; cursor: pointer; font-size: 16px;">×</button>
            </div>
            
            <!-- 预设选择 -->
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; color: #00ffff;">预设风格:</label>
                <select id="toon-preset" style="width: 100%; padding: 5px; background: rgba(0, 0, 0, 0.5); border: 1px solid #00ffff; color: white; border-radius: 4px;">
                    <option value="">自定义</option>
                    <option value="经典卡通">经典卡通</option>
                    <option value="柔和卡通">柔和卡通</option>
                    <option value="强烈卡通">强烈卡通</option>
                    <option value="动漫风格">动漫风格</option>
                    <option value="性能模式">性能模式</option>
                </select>
            </div>
            
            <!-- 基础卡通效果 -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #00ffff; font-size: 13px;">基础卡通效果</h4>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" id="cel-shading" checked style="margin-right: 5px;">
                        <span>Cel Shading</span>
                    </label>
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">色阶数量: <span id="cel-levels-value">3</span></label>
                    <input type="range" id="cel-levels" min="2" max="8" value="3" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">色阶阈值: <span id="cel-threshold-value">0.5</span></label>
                    <input type="range" id="cel-threshold" min="0.1" max="1.0" step="0.1" value="0.5" style="width: 100%;">
                </div>
            </div>
            
            <!-- 边缘检测 -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #00ffff; font-size: 13px;">边缘检测</h4>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" id="outline" checked style="margin-right: 5px;">
                        <span>启用边缘</span>
                    </label>
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">边缘颜色:</label>
                    <input type="color" id="outline-color" value="#000000" style="width: 100%; height: 30px; border: 1px solid #00ffff; border-radius: 4px;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">边缘粗细: <span id="outline-thickness-value">0.003</span></label>
                    <input type="range" id="outline-thickness" min="0.001" max="0.01" step="0.001" value="0.003" style="width: 100%;">
                </div>
            </div>
            
            <!-- 颜色分级 -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #00ffff; font-size: 13px;">颜色分级</h4>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" id="color-grading" checked style="margin-right: 5px;">
                        <span>启用颜色分级</span>
                    </label>
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">饱和度: <span id="saturation-value">1.2</span></label>
                    <input type="range" id="saturation" min="0.5" max="2.0" step="0.1" value="1.2" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">对比度: <span id="contrast-value">1.1</span></label>
                    <input type="range" id="contrast" min="0.5" max="2.0" step="0.1" value="1.1" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">亮度: <span id="brightness-value">1.0</span></label>
                    <input type="range" id="brightness" min="0.5" max="1.5" step="0.1" value="1.0" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">伽马: <span id="gamma-value">1.0</span></label>
                    <input type="range" id="gamma" min="0.5" max="1.5" step="0.1" value="1.0" style="width: 100%;">
                </div>
            </div>
            
            <!-- 泛光效果 -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #00ffff; font-size: 13px;">泛光效果</h4>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" id="bloom" style="margin-right: 5px;">
                        <span>启用泛光</span>
                    </label>
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">泛光强度: <span id="bloom-strength-value">0.5</span></label>
                    <input type="range" id="bloom-strength" min="0.1" max="1.0" step="0.1" value="0.5" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">泛光半径: <span id="bloom-radius-value">0.5</span></label>
                    <input type="range" id="bloom-radius" min="0.1" max="1.0" step="0.1" value="0.5" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">泛光阈值: <span id="bloom-threshold-value">0.8</span></label>
                    <input type="range" id="bloom-threshold" min="0.1" max="1.0" step="0.1" value="0.8" style="width: 100%;">
                </div>
            </div>
            
            <!-- 抗锯齿 -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #00ffff; font-size: 13px;">抗锯齿</h4>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" id="fxaa" checked style="margin-right: 5px;">
                        <span>FXAA抗锯齿</span>
                    </label>
                </div>
            </div>
            
            <!-- 后处理效果 -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #00ffff; font-size: 13px;">后处理效果</h4>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: flex; align-items: center;">
                        <input type="checkbox" id="post-processor" checked style="margin-right: 5px;">
                        <span>启用后处理</span>
                    </label>
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">对比度: <span id="post-contrast-value">1.1</span></label>
                    <input type="range" id="post-contrast" min="0.5" max="2.0" step="0.1" value="1.1" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">亮度: <span id="post-brightness-value">1.0</span></label>
                    <input type="range" id="post-brightness" min="0.5" max="1.5" step="0.1" value="1.0" style="width: 100%;">
                </div>
                
                <div style="margin-bottom: 8px;">
                    <label style="display: block; margin-bottom: 3px;">饱和度: <span id="post-saturation-value">1.05</span></label>
                    <input type="range" id="post-saturation" min="0.5" max="2.0" step="0.05" value="1.05" style="width: 100%;">
                </div>
            </div>
            
            <!-- 操作按钮 -->
            <div style="display: flex; gap: 10px;">
                <button id="reset-toon" style="flex: 1; padding: 8px; background: rgba(255, 0, 0, 0.3); border: 1px solid #ff0000; color: white; border-radius: 4px; cursor: pointer;">重置</button>
                <button id="save-toon-preset" style="flex: 1; padding: 8px; background: rgba(0, 255, 0, 0.3); border: 1px solid #00ff00; color: white; border-radius: 4px; cursor: pointer;">保存预设</button>
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(this.panel);
        
        // 绑定事件
        this.bindEvents();
    }
    
    // 绑定事件
    bindEvents() {
        // 关闭按钮
        document.getElementById('close-toon-panel').addEventListener('click', () => {
            this.hide();
        });
        
        // 预设选择
        document.getElementById('toon-preset').addEventListener('change', (e) => {
            const presetName = e.target.value;
            if (presetName && this.presets[presetName]) {
                this.applyPreset(presetName);
            }
        });
        
        // 基础卡通效果
        document.getElementById('cel-shading').addEventListener('change', (e) => {
            this.updateParam('celShading', e.target.checked);
        });
        
        document.getElementById('cel-levels').addEventListener('input', (e) => {
            const value = parseInt(e.target.value);
            document.getElementById('cel-levels-value').textContent = value;
            this.updateParam('celLevels', value);
        });
        
        document.getElementById('cel-threshold').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('cel-threshold-value').textContent = value.toFixed(1);
            this.updateParam('celThreshold', value);
        });
        
        // 边缘检测
        document.getElementById('outline').addEventListener('change', (e) => {
            this.updateParam('outline', e.target.checked);
        });
        
        document.getElementById('outline-color').addEventListener('change', (e) => {
            const color = e.target.value;
            const hexColor = parseInt(color.replace('#', ''), 16);
            this.updateParam('outlineColor', hexColor);
        });
        
        document.getElementById('outline-thickness').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('outline-thickness-value').textContent = value.toFixed(3);
            this.updateParam('outlineThickness', value);
        });
        
        // 颜色分级
        document.getElementById('color-grading').addEventListener('change', (e) => {
            this.updateParam('colorGrading', e.target.checked);
        });
        
        document.getElementById('saturation').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('saturation-value').textContent = value.toFixed(1);
            this.updateParam('saturation', value);
        });
        
        document.getElementById('contrast').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('contrast-value').textContent = value.toFixed(1);
            this.updateParam('contrast', value);
        });
        
        document.getElementById('brightness').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('brightness-value').textContent = value.toFixed(1);
            this.updateParam('brightness', value);
        });
        
        document.getElementById('gamma').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('gamma-value').textContent = value.toFixed(1);
            this.updateParam('gamma', value);
        });
        
        // 泛光效果
        document.getElementById('bloom').addEventListener('change', (e) => {
            this.updateParam('bloom', e.target.checked);
        });
        
        document.getElementById('bloom-strength').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('bloom-strength-value').textContent = value.toFixed(1);
            this.updateParam('bloomStrength', value);
        });
        
        document.getElementById('bloom-radius').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('bloom-radius-value').textContent = value.toFixed(1);
            this.updateParam('bloomRadius', value);
        });
        
        document.getElementById('bloom-threshold').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('bloom-threshold-value').textContent = value.toFixed(1);
            this.updateParam('bloomThreshold', value);
        });
        
        // 抗锯齿
        document.getElementById('fxaa').addEventListener('change', (e) => {
            this.updateParam('fxaa', e.target.checked);
        });
        
        // 后处理效果
        document.getElementById('post-processor').addEventListener('change', (e) => {
            this.updatePostProcessor('enabled', e.target.checked);
        });
        
        document.getElementById('post-contrast').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('post-contrast-value').textContent = value.toFixed(1);
            this.updatePostProcessor('contrastValue', value);
        });
        
        document.getElementById('post-brightness').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('post-brightness-value').textContent = value.toFixed(1);
            this.updatePostProcessor('brightness', value);
        });
        
        document.getElementById('post-saturation').addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            document.getElementById('post-saturation-value').textContent = value.toFixed(2);
            this.updatePostProcessor('saturation', value);
        });
        
        // 操作按钮
        document.getElementById('reset-toon').addEventListener('click', () => {
            this.resetToDefault();
        });
        
        document.getElementById('save-toon-preset').addEventListener('click', () => {
            this.saveCurrentPreset();
        });
    }
    
    // 更新参数
    updateParam(key, value) {
        if (this.toonRenderer) {
            this.toonRenderer.updateParams({ [key]: value });
        }
    }
    
    // 更新后处理器参数
    updatePostProcessor(param, value) {
        if (window.__MMD__ && window.__MMD__.postProcessor) {
            const postProcessor = window.__MMD__.postProcessor;
            
            switch (param) {
                case 'enabled':
                    if (value) {
                        postProcessor.enable();
                    } else {
                        postProcessor.disable();
                    }
                    break;
                case 'contrastValue':
                    postProcessor.params.contrastValue = value;
                    postProcessor.updateParams();
                    break;
                case 'brightness':
                    postProcessor.params.brightness = value;
                    postProcessor.updateParams();
                    break;
                case 'saturation':
                    postProcessor.params.saturation = value;
                    postProcessor.updateParams();
                    break;
            }
            
            console.log(`[ToonControls] 后处理器参数更新: ${param} = ${value}`);
        }
    }
    
    // 初始化后处理UI状态
    initPostProcessorUI() {
        if (window.__MMD__ && window.__MMD__.postProcessor) {
            const postProcessor = window.__MMD__.postProcessor;
            
            // 更新后处理开关
            const postProcessorCheckbox = document.getElementById('post-processor');
            if (postProcessorCheckbox) {
                postProcessorCheckbox.checked = postProcessor.params.enabled;
            }
            
            // 更新后处理滑块
            const contrastSlider = document.getElementById('post-contrast');
            const brightnessSlider = document.getElementById('post-brightness');
            const saturationSlider = document.getElementById('post-saturation');
            
            if (contrastSlider) {
                contrastSlider.value = postProcessor.params.contrastValue;
                document.getElementById('post-contrast-value').textContent = postProcessor.params.contrastValue.toFixed(1);
            }
            
            if (brightnessSlider) {
                brightnessSlider.value = postProcessor.params.brightness;
                document.getElementById('post-brightness-value').textContent = postProcessor.params.brightness.toFixed(1);
            }
            
            if (saturationSlider) {
                saturationSlider.value = postProcessor.params.saturation;
                document.getElementById('post-saturation-value').textContent = postProcessor.params.saturation.toFixed(2);
            }
            
            console.log('[ToonControls] 后处理UI状态已初始化');
        }
    }
    
    // 应用预设
    applyPreset(presetName) {
        const preset = this.presets[presetName];
        if (preset) {
            this.toonRenderer.updateParams(preset);
            this.updateUIFromParams(preset);
        }
    }
    
    // 从参数更新UI
    updateUIFromParams(params) {
        // 更新复选框
        if (params.celShading !== undefined) {
            document.getElementById('cel-shading').checked = params.celShading;
        }
        if (params.outline !== undefined) {
            document.getElementById('outline').checked = params.outline;
        }
        if (params.colorGrading !== undefined) {
            document.getElementById('color-grading').checked = params.colorGrading;
        }
        if (params.bloom !== undefined) {
            document.getElementById('bloom').checked = params.bloom;
        }
        if (params.fxaa !== undefined) {
            document.getElementById('fxaa').checked = params.fxaa;
        }
        
        // 更新滑块和数值
        if (params.celLevels !== undefined) {
            document.getElementById('cel-levels').value = params.celLevels;
            document.getElementById('cel-levels-value').textContent = params.celLevels;
        }
        if (params.celThreshold !== undefined) {
            document.getElementById('cel-threshold').value = params.celThreshold;
            document.getElementById('cel-threshold-value').textContent = params.celThreshold.toFixed(1);
        }
        if (params.outlineColor !== undefined) {
            const colorHex = '#' + params.outlineColor.toString(16).padStart(6, '0');
            document.getElementById('outline-color').value = colorHex;
        }
        if (params.outlineThickness !== undefined) {
            document.getElementById('outline-thickness').value = params.outlineThickness;
            document.getElementById('outline-thickness-value').textContent = params.outlineThickness.toFixed(3);
        }
        if (params.saturation !== undefined) {
            document.getElementById('saturation').value = params.saturation;
            document.getElementById('saturation-value').textContent = params.saturation.toFixed(1);
        }
        if (params.contrast !== undefined) {
            document.getElementById('contrast').value = params.contrast;
            document.getElementById('contrast-value').textContent = params.contrast.toFixed(1);
        }
        if (params.brightness !== undefined) {
            document.getElementById('brightness').value = params.brightness;
            document.getElementById('brightness-value').textContent = params.brightness.toFixed(1);
        }
        if (params.gamma !== undefined) {
            document.getElementById('gamma').value = params.gamma;
            document.getElementById('gamma-value').textContent = params.gamma.toFixed(1);
        }
        if (params.bloomStrength !== undefined) {
            document.getElementById('bloom-strength').value = params.bloomStrength;
            document.getElementById('bloom-strength-value').textContent = params.bloomStrength.toFixed(1);
        }
        if (params.bloomRadius !== undefined) {
            document.getElementById('bloom-radius').value = params.bloomRadius;
            document.getElementById('bloom-radius-value').textContent = params.bloomRadius.toFixed(1);
        }
        if (params.bloomThreshold !== undefined) {
            document.getElementById('bloom-threshold').value = params.bloomThreshold;
            document.getElementById('bloom-threshold-value').textContent = params.bloomThreshold.toFixed(1);
        }
        
        // 更新后处理参数
        if (window.__MMD__ && window.__MMD__.postProcessor) {
            const postProcessor = window.__MMD__.postProcessor;
            
            // 更新后处理开关
            document.getElementById('post-processor').checked = postProcessor.params.enabled;
            
            // 更新后处理滑块
            document.getElementById('post-contrast').value = postProcessor.params.contrastValue;
            document.getElementById('post-contrast-value').textContent = postProcessor.params.contrastValue.toFixed(1);
            
            document.getElementById('post-brightness').value = postProcessor.params.brightness;
            document.getElementById('post-brightness-value').textContent = postProcessor.params.brightness.toFixed(1);
            
            document.getElementById('post-saturation').value = postProcessor.params.saturation;
            document.getElementById('post-saturation-value').textContent = postProcessor.params.saturation.toFixed(2);
        }
    }
    
    // 重置为默认值
    resetToDefault() {
        this.applyPreset('经典卡通');
    }
    
    // 保存当前预设
    saveCurrentPreset() {
        const presetName = prompt('请输入预设名称:');
        if (presetName) {
            const currentParams = { ...this.toonRenderer.params };
            this.presets[presetName] = currentParams;
            
            // 保存到localStorage
            localStorage.setItem('toonPresets', JSON.stringify(this.presets));
            
            // 更新预设选择器
            this.updatePresetSelector();
            
            alert(`预设 "${presetName}" 已保存`);
        }
    }
    
    // 更新预设选择器
    updatePresetSelector() {
        const selector = document.getElementById('toon-preset');
        const currentValue = selector.value;
        
        // 清空选项
        selector.innerHTML = '<option value="">自定义</option>';
        
        // 添加预设选项
        Object.keys(this.presets).forEach(presetName => {
            const option = document.createElement('option');
            option.value = presetName;
            option.textContent = presetName;
            selector.appendChild(option);
        });
        
        // 恢复当前选择
        if (currentValue) {
            selector.value = currentValue;
        }
    }
    
    // 显示面板
    show() {
        if (this.panel) {
            this.panel.style.display = 'block';
            this.isVisible = true;
            
            // 初始化后处理UI状态
            this.initPostProcessorUI();
        }
    }
    
    // 隐藏面板
    hide() {
        if (this.panel) {
            this.panel.style.display = 'none';
            this.isVisible = false;
        }
    }
    
    // 切换面板显示
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    // 加载保存的预设
    loadSavedPresets() {
        const saved = localStorage.getItem('toonPresets');
        if (saved) {
            try {
                const savedPresets = JSON.parse(saved);
                this.presets = { ...this.presets, ...savedPresets };
                this.updatePresetSelector();
            } catch (error) {
                console.warn('Failed to load saved presets:', error);
            }
        }
    }
    
    // 清理资源
    dispose() {
        if (this.panel) {
            document.body.removeChild(this.panel);
            this.panel = null;
        }
    }
}

// 导出控制面板
export { ToonControls }; 