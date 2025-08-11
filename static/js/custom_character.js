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
                <input type="text" name="mood_name[]" placeholder="心情名称" value="${defaultMood}" required>
            </div>
            <div class="mood-cell">
                <input type="file" name="mood_image[]" accept="image/*" required>
            </div>
            <div class="mood-cell">
                <input type="file" name="mood_audio[]" accept="audio/*">
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

        // 验证必填字段
        const requiredFields = [
            { name: 'characterName', label: '角色名' },
            { name: 'themeColorText', label: '主题颜色' },
            { name: 'imageOffset', label: '角色立绘校准' },
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

        // 验证心情设置
        const moodNames = formData.getAll('mood_name[]');
        const moodImages = formData.getAll('mood_image[]');
        
        if (moodNames.length === 0) {
            errors.push('至少需要添加一个心情设置');
        }

        moodNames.forEach((name, index) => {
            if (!name || name.trim() === '') {
                errors.push(`第${index + 1}个心情的名称不能为空`);
            }
        });

        // 验证文件上传
        // const detailFiles = document.getElementById('characterDetails').files;
        // if (detailFiles.length === 0) {
        //     errors.push('必须上传至少一个角色详细信息文件');
        // }

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

        try {
            // 显示加载指示器
            this.showLoading(true);

            const response = await fetch('/api/custom-character', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                alert(`自定义角色创建成功！\n角色ID: ${result.character_id}`);
                // 清除草稿
                localStorage.removeItem('customCharacterDraft');
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
}

// 初始化自定义角色管理器
let customCharacterManager;

document.addEventListener('DOMContentLoaded', () => {
    customCharacterManager = new CustomCharacterManager();
});