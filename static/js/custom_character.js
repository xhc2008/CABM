/**
 * 自定义角色页面JavaScript
 */

class CustomCharacterManager {
    constructor() {
        this.moodRowCount = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.addInitialMoodRow();
        this.loadDraft();
    }

    bindEvents() {
        // 页面切换
        document.getElementById('customCharacterButton')?.addEventListener('click', () => {
            this.showCustomCharacterPage();
        });

        document.getElementById('backToHomeButton')?.addEventListener('click', () => {
            this.showHomePage();
        });

        document.getElementById('cancelButton')?.addEventListener('click', () => {
            this.showHomePage();
        });

        // 表单验证
        document.getElementById('characterId')?.addEventListener('input', (e) => {
            this.validateCharacterId(e.target);
            this.checkCharacterExists(e.target.value);
        });

        // 加载角色按钮
        document.getElementById('loadCharacterButton')?.addEventListener('click', () => {
            this.loadExistingCharacter();
        });

        // 颜色选择器同步
        document.getElementById('themeColor')?.addEventListener('change', (e) => {
            document.getElementById('themeColorText').value = e.target.value;
        });

        document.getElementById('themeColorText')?.addEventListener('input', (e) => {
            const color = e.target.value;
            if (/^#[0-9A-F]{6}$/i.test(color)) {
                document.getElementById('themeColor').value = color;
            }
        });

        // 头像上传
        document.getElementById('avatarImage')?.addEventListener('change', (e) => {
            this.handleAvatarUpload(e);
        });

        document.getElementById('cropAvatarButton')?.addEventListener('click', () => {
            this.showCropModal();
        });

        // 裁剪相关事件
        document.getElementById('closeCropButton')?.addEventListener('click', () => {
            this.hideCropModal();
        });

        document.getElementById('cancelCropButton')?.addEventListener('click', () => {
            this.hideCropModal();
        });

        document.getElementById('confirmCropButton')?.addEventListener('click', () => {
            this.confirmCrop();
        });

        // 添加心情行
        document.getElementById('addMoodButton')?.addEventListener('click', () => {
            this.addMoodRow();
        });

        // 文件选择显示
        document.getElementById('characterDetails')?.addEventListener('change', (e) => {
            this.displaySelectedFiles(e.target);
        });

        // 表单提交
        document.getElementById('customCharacterForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });

        // 存草稿
        document.getElementById('saveDraftButton')?.addEventListener('click', () => {
            this.saveDraft();
        });
    }

    showCustomCharacterPage() {
        document.getElementById('homePage').classList.remove('active');
        document.getElementById('customCharacterPage').classList.add('active');
    }

    showHomePage() {
        const customPage = document.getElementById('customCharacterPage');
        const homePage = document.getElementById('homePage');
        
        if (customPage) {
            customPage.classList.remove('active');
        }
        
        if (homePage) {
            homePage.classList.add('active');
        } else {
            // 如果没有主页，则重定向到根路径
            window.location.href = '/';
        }
    }

    validateCharacterId(input) {
        const value = input.value;
        const isValid = /^[a-zA-Z0-9_]*$/.test(value);
        const description = document.getElementById('characterIdDesc');
        
        if (value && !isValid) {
            description.classList.add('error');
            description.textContent = '⚠只能包含英文字母、数字或下划线';
        } else {
            description.classList.remove('error');
            description.textContent = '只能包含英文字母、数字或下划线';
        }
    }

    async checkCharacterExists(characterId) {
        if (!characterId || !/^[a-zA-Z0-9_]+$/.test(characterId)) {
            document.getElementById('loadCharacterButton').style.display = 'none';
            return;
        }

        try {
            const response = await fetch(`/api/check-character/${characterId}`);
            const result = await response.json();
            
            const loadButton = document.getElementById('loadCharacterButton');
            if (result.exists) {
                loadButton.style.display = 'inline-block';
            } else {
                loadButton.style.display = 'none';
            }
        } catch (error) {
            console.error('检查角色存在失败:', error);
            document.getElementById('loadCharacterButton').style.display = 'none';
        }
    }

    async loadExistingCharacter() {
        const characterId = document.getElementById('characterId').value;
        if (!characterId) return;

        try {
            this.showLoading(true);
            
            const response = await fetch(`/api/load-character/${characterId}`);
            const result = await response.json();
            
            if (result.success) {
                this.fillFormWithCharacterData(result.character);
                alert(`角色 "${result.character.name}" 已加载！\n文件需要重新手动上传（浏览器安全限制，没办法）\n请注意，角色详细信息是追加写入\n如果希望覆写请删除data/details/${result.character.id}.json并重启程序`);
            } else {
                alert('加载角色失败：' + result.error);
            }
        } catch (error) {
            console.error('加载角色失败:', error);
            alert('加载角色失败：' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    fillFormWithCharacterData(character) {
        // 填充基本角色信息
        document.getElementById('characterName').value = character.name || '';
        document.getElementById('characterEnglishName').value = character.name_en || '';
        document.getElementById('themeColorText').value = character.color || '#000000';
        document.getElementById('themeColor').value = character.color || '#000000';
        document.getElementById('imageOffset').value = character.calib || 0;
        document.getElementById('scaleRate').value = character.scale_rate || 100;
        document.getElementById('characterIntro').value = character.description || '';
        document.getElementById('characterDescription').value = character.prompt || '';

        // 加载头像预览
        if (character.avatar_url) {
            this.showAvatarPreview(character.avatar_url);
            this.croppedAvatarData = character.avatar_url;
        }

        // 清空并重新填充心情设置
        const tableBody = document.getElementById('moodTableBody');
        tableBody.innerHTML = '';
        this.moodRowCount = 0;

        if (character.moods && character.moods.length > 0) {
            character.moods.forEach(mood => {
                this.addMoodRow(mood.name || mood);
            });
        } else {
            this.addInitialMoodRow();
        }

        // 显示已加载的详细信息文件
        if (character.detail_files && character.detail_files.length > 0) {
            this.displayLoadedDetailFiles(character.detail_files);
            this.markFileInputAsFilled();
        } else {
           this.clearFileDisplay();
        }
    }

    displayLoadedDetailFiles(files) {
        const container = document.getElementById('selectedFiles');
        container.innerHTML = '<div class="loaded-files-info">已加载的文件：</div>';
        
        files.forEach(file => {
            const fileTag = document.createElement('span');
            fileTag.className = 'selected-file loaded-file';
            fileTag.textContent = file;
            container.appendChild(fileTag);
        });
    }

    markFileInputAsFilled() {
        // 标记文件输入为已填写状态
        const fileInput = document.getElementById('characterDetails');
        if (fileInput) {
            fileInput.setAttribute('data-has-files', 'true');
            fileInput.setAttribute('data-existing-files', 'true');
        }
    }

    clearFileDisplay() {
        const container = document.getElementById('selectedFiles');
        container.innerHTML = '';
        const fileInput = document.getElementById('characterDetails');
        if (fileInput) {
            fileInput.removeAttribute('data-has-files');
            fileInput.removeAttribute('data-existing-files');
        }
    }

    addInitialMoodRow() {
        // 添加默认的心情行
        const defaultMoods = ['开心', '生气', '悲伤', '惊讶'];
        defaultMoods.forEach(mood => {
            this.addMoodRow(mood);
        });
    }

    addMoodRow(defaultMood = '') {
        const tableBody = document.getElementById('moodTableBody');
        const rowId = `mood-row-${this.moodRowCount++}`;
        
        const row = document.createElement('div');
        row.className = 'mood-row';
        row.id = rowId;
        
        row.innerHTML = `
            <div class="mood-cell">
                <input type="text" name="mood_name[]" placeholder="心情名称" value="${defaultMood}" required style="width: 80px;">
            </div>
            <div class="mood-cell">
                <input type="file" name="mood_image[]" accept="image/*" required>
            </div>
            <div class="mood-cell">
                <input type="file" name="mood_audio[]" accept="audio/*">
            </div>
            <div class="mood-cell">
                <input type="text" name="mood_ref_text[]" placeholder="音频的内容">
            </div>
            <div class="mood-cell">
                <button type="button" class="remove-mood-btn" onclick="customCharacterManager.removeMoodRow('${rowId}')">×</button>
            </div>
        `;
        
        tableBody.appendChild(row);
    }

    removeMoodRow(rowId) {
        const row = document.getElementById(rowId);
        if (row) {
            // 确保至少保留一行
            const tableBody = document.getElementById('moodTableBody');
            if (tableBody.children.length > 1) {
                row.remove();
            } else {
                alert('至少需要保留一个心情设置');
            }
        }
    }

    displaySelectedFiles(input) {
        const container = document.getElementById('selectedFiles');
        container.innerHTML = '';
        
        if (input.files.length > 0) {
            // 创建一个新的文件列表，用于支持删除功能
            this.selectedFilesList = Array.from(input.files);
            
            this.selectedFilesList.forEach((file, index) => {
                const fileTag = document.createElement('span');
                fileTag.className = 'selected-file';
                
                const fileName = document.createElement('span');
                fileName.textContent = file.name;
                
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'remove-file-btn';
                removeBtn.innerHTML = '×';
                removeBtn.onclick = () => this.removeSelectedFile(index);
                
                fileTag.appendChild(fileName);
                fileTag.appendChild(removeBtn);
                container.appendChild(fileTag);
            });
        }
    }

    removeSelectedFile(index) {
        // 从文件列表中移除指定文件
        this.selectedFilesList.splice(index, 1);
        
        // 创建新的FileList对象
        const dt = new DataTransfer();
        this.selectedFilesList.forEach(file => {
            dt.items.add(file);
        });
        
        // 更新input的files属性
        const input = document.getElementById('characterDetails');
        input.files = dt.files;
        
        // 重新显示文件列表
        this.displaySelectedFiles(input);
    }

    validateForm() {
        const form = document.getElementById('customCharacterForm');
        const formData = new FormData(form);
        const errors = [];

        // 验证角色ID
        const characterId = formData.get('characterId');
        if (!characterId || !/^[a-zA-Z0-9_]+$/.test(characterId)) {
            errors.push('角色ID必须填写且只能包含英文字母、数字或下划线');
        }

        // 验证头像
        if (!this.croppedAvatarData && !formData.get('avatarImage')) {
            errors.push('必须上传并裁剪角色头像');
        }

        // 验证必填字段
        const requiredFields = [
            { name: 'characterName', label: '角色名' },
            { name: 'themeColorText', label: '主题颜色' },
            { name: 'imageOffset', label: '角色立绘校准' },
            { name: 'scaleRate', label: '立绘缩放率' },
            { name: 'characterIntro', label: '角色简介' },
            { name: 'characterDescription', label: '角色描述' }
        ];

        requiredFields.forEach(field => {
            const value = formData.get(field.name);
            if (!value || value.trim() === '') {
                errors.push(`${field.label}不能为空`);
            }
        });

        // 验证颜色格式
        const themeColor = formData.get('themeColorText');
        if (themeColor && !/^#[0-9A-F]{6}$/i.test(themeColor)) {
            errors.push('主题颜色格式不正确，请使用十六进制格式（如：#FF0000）');
        }

        // 验证立绘校准范围
        const imageOffset = parseInt(formData.get('imageOffset'));
        if (isNaN(imageOffset) || imageOffset < -100 || imageOffset > 100) {
            errors.push('角色立绘校准必须是-100到100之间的整数');
        }

        // 验证缩放率范围
        const scaleRate = parseInt(formData.get('scaleRate'));
        if (isNaN(scaleRate) || scaleRate < 1 || scaleRate > 300) {
            errors.push('立绘缩放率必须是1到300之间的整数');
        }

        // 验证心情设置
        const moodNames = formData.getAll('mood_name[]');
        
        if (moodNames.length === 0) {
            errors.push('至少需要添加一个心情设置');
        }

        moodNames.forEach((name, index) => {
            if (!name || name.trim() === '') {
                errors.push(`第${index + 1}个心情的名称不能为空`);
            }
        });

        // 验证角色详细信息文件（可选）
        // 检查是否有现有文件或新上传的文件
        const fileInput = document.getElementById('characterDetails');
        const hasExistingFiles = fileInput.getAttribute('data-existing-files') === 'true';
        const detailFiles = fileInput.files;
        
        // 如果有新上传的文件，验证文件格式和大小
        if (detailFiles.length > 0) {
            for (let i = 0; i < detailFiles.length; i++) {
                const file = detailFiles[i];
                if (!file.name.toLowerCase().endsWith('.txt')) {
                    errors.push(`文件 "${file.name}" 不是txt格式，请只上传纯文本文件`);
                }
                if (file.size > 5 * 1024 * 1024) { // 5MB限制
                    errors.push(`文件 "${file.name}" 过大，请确保文件小于5MB`);
                }
            }
        }

        return errors;
    }

    async handleFormSubmit() {
        const errors = this.validateForm();
        
        if (errors.length > 0) {
            alert('表单验证失败：\n' + errors.join('\n'));
            return;
        }

        const form = document.getElementById('customCharacterForm');
        const formData = new FormData(form);

        // 添加裁剪后的头像数据
        if (this.croppedAvatarData) {
            // 将base64数据转换为blob
            const response = await fetch(this.croppedAvatarData);
            const blob = await response.blob();
            formData.set('avatarImage', blob, 'avatar.png');
        }

        try {
            // 显示加载指示器
            this.showLoading(true);

            const response = await fetch('/api/custom-character', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                alert(`自定义角色创建成功！\n角色ID: ${result.character_id}\n如未成功加载请重启程序`);
                // 清除草稿
                localStorage.removeItem('customCharacterDraft');
                // 清空表单
                this.clearForm();
                // 重新加载角色列表
                await this.reloadCharacterList();
                this.showHomePage();
            } else {
                alert('创建失败：' + result.error);
            }
            
        } catch (error) {
            console.error('提交失败：', error);
            alert('提交失败：' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    saveDraft() {
        const form = document.getElementById('customCharacterForm');
        const formData = new FormData(form);
        const draftData = Object.fromEntries(formData.entries());
        
        // 保存到localStorage作为草稿
        localStorage.setItem('customCharacterDraft', JSON.stringify(draftData));
        alert('草稿已保存！');
    }

    loadDraft() {
        const draftData = localStorage.getItem('customCharacterDraft');
        if (draftData) {
            try {
                const data = JSON.parse(draftData);
                const form = document.getElementById('customCharacterForm');
                
                // 填充表单数据
                Object.keys(data).forEach(key => {
                    const element = form.querySelector(`[name="${key}"]`);
                    if (element && element.type !== 'file') {
                        element.value = data[key];
                    }
                });
                
                // 同步颜色选择器
                const themeColor = data.themeColorText;
                if (themeColor) {
                    document.getElementById('themeColor').value = themeColor;
                }
                
            } catch (error) {
                console.error('加载草稿失败：', error);
            }
        }
    }

    showLoading(show) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = show ? 'flex' : 'none';
        }
    }

    clearForm() {
        const form = document.getElementById('customCharacterForm');
        if (form) {
            // 重置表单
            form.reset();
            
            // 清空心情表格，重新添加默认心情
            const tableBody = document.getElementById('moodTableBody');
            if (tableBody) {
                tableBody.innerHTML = '';
                this.moodRowCount = 0;
                this.addInitialMoodRow();
            }
            
            // 清空文件选择显示
            const selectedFiles = document.getElementById('selectedFiles');
            if (selectedFiles) {
                selectedFiles.innerHTML = '';
            }
            
            // 重置颜色选择器
            const themeColor = document.getElementById('themeColor');
            const themeColorText = document.getElementById('themeColorText');
            if (themeColor && themeColorText) {
                themeColor.value = '#ffffff';
                themeColorText.value = '#ffffff';
            }
        }
    }

    async reloadCharacterList() {
        try {
            const response = await fetch('/api/reload-characters');
            const result = await response.json();
            
            if (result.success) {
                // 如果页面有角色选择器，更新它
                const characterSelect = document.getElementById('characterSelect');
                if (characterSelect) {
                    // 清空现有选项
                    characterSelect.innerHTML = '';
                    
                    // 添加新的角色选项
                    result.characters.forEach(character => {
                        const option = document.createElement('option');
                        option.value = character.id;
                        option.textContent = character.name;
                        characterSelect.appendChild(option);
                    });
                }
                
                // 触发自定义事件，通知其他组件角色列表已更新
                window.dispatchEvent(new CustomEvent('charactersReloaded', {
                    detail: { characters: result.characters }
                }));
                
                console.log('角色列表已重新加载');
            } else {
                console.error('重新加载角色列表失败:', result.error);
            }
        } catch (error) {
            console.error('重新加载角色列表时发生错误:', error);
        }
    }

    // 头像上传处理
    handleAvatarUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            alert('请选择图片文件');
            return;
        }

        // 验证文件大小 (10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('图片文件不能超过10MB');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            this.originalAvatarData = e.target.result;
            this.showAvatarPreview(e.target.result);
        };
        reader.readAsDataURL(file);
    }

    showAvatarPreview(imageSrc) {
        const preview = document.getElementById('avatarPreview');
        const previewImg = document.getElementById('avatarPreviewImg');
        
        previewImg.src = imageSrc;
        preview.style.display = 'flex';
    }

    showCropModal() {
        if (!this.originalAvatarData) {
            alert('请先选择头像图片');
            return;
        }

        // 检查Cropper.js是否已加载
        if (typeof Cropper === 'undefined') {
            alert('裁剪功能加载失败，请检查网络连接后刷新页面');
            return;
        }

        const modal = document.getElementById('cropModal');
        modal.style.display = 'flex';
        
        // 初始化Cropper.js
        this.initCropper();
    }

    hideCropModal() {
        const modal = document.getElementById('cropModal');
        modal.style.display = 'none';
        
        // 销毁cropper实例
        if (this.cropper) {
            this.cropper.destroy();
            this.cropper = null;
        }
    }

    initCropper() {
        const image = document.getElementById('cropImage');
        image.src = this.originalAvatarData;
        
        // 等待图片加载完成后初始化cropper
        image.onload = () => {
            try {
                // 如果已存在cropper实例，先销毁
                if (this.cropper) {
                    this.cropper.destroy();
                }
                
                // 初始化Cropper.js
                this.cropper = new Cropper(image, {
                    aspectRatio: 1, // 1:1 正方形裁剪
                    viewMode: 1, // 限制裁剪框不超出画布
                    dragMode: 'move', // 拖拽模式
                    autoCropArea: 0.8, // 初始裁剪区域占比
                    restore: false, // 不恢复裁剪状态
                    guides: true, // 显示网格线
                    center: true, // 显示中心指示器
                    highlight: true, // 高亮裁剪区域
                    cropBoxMovable: true, // 裁剪框可移动
                    cropBoxResizable: true, // 裁剪框可调整大小
                    toggleDragModeOnDblclick: false, // 禁用双击切换拖拽模式
                    responsive: true, // 响应式
                    modal: true, // 显示遮罩
                    background: true, // 显示网格背景
                    minContainerWidth: 300,
                    minContainerHeight: 300,
                    ready: function () {
                        console.log('Cropper.js 初始化完成');
                    }
                });
            } catch (error) {
                console.error('初始化Cropper.js失败:', error);
                alert('初始化裁剪器失败，请刷新页面重试');
            }
        };
        
        // 添加图片加载错误处理
        image.onerror = () => {
            console.error('图片加载失败');
            alert('图片加载失败，请重新选择图片');
            this.hideCropModal();
        };
    }

    confirmCrop() {
        if (!this.cropper) {
            alert('裁剪器未初始化');
            return;
        }
        
        // 获取裁剪后的canvas
        const canvas = this.cropper.getCroppedCanvas({
            width: 200,
            height: 200,
            minWidth: 200,
            minHeight: 200,
            maxWidth: 200,
            maxHeight: 200,
            fillColor: '#fff',
            imageSmoothingEnabled: true,
            imageSmoothingQuality: 'high'
        });
        
        if (canvas) {
            // 获取裁剪后的数据
            this.croppedAvatarData = canvas.toDataURL('image/png', 0.9);
            
            // 更新预览
            this.showAvatarPreview(this.croppedAvatarData);
            
            // 隐藏裁剪模态框
            this.hideCropModal();
        } else {
            alert('裁剪失败，请重试');
        }
    }
}

// 初始化自定义角色管理器
let customCharacterManager;

document.addEventListener('DOMContentLoaded', () => {
    customCharacterManager = new CustomCharacterManager();
});
