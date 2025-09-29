// 资源管理页面JavaScript

let currentCharacters = [];
let currentCharacterDetail = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initResourceManagement();
});

// 初始化资源管理页面
function initResourceManagement() {
    // 初始化选项卡切换
    initTabs();
    
    // 初始化按钮事件
    initButtons();
    
    // 加载角色列表
    loadCharacters();
}

// 初始化选项卡
function initTabs() {
    const tabs = document.querySelectorAll('.resource-tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.dataset.tab;
            
            // 移除所有活动状态
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // 激活当前选项卡
            this.classList.add('active');
            document.getElementById(targetTab + '-tab').classList.add('active');
        });
    });
}

// 初始化按钮事件
function initButtons() {
    // 导入角色按钮
    document.getElementById('importCharacterBtn').addEventListener('click', function() {
        document.getElementById('importModal').style.display = 'block';
    });
    
    // 创建角色按钮
    document.getElementById('createCharacterBtn').addEventListener('click', function() {
        window.location.href = '/custom_character';
    });
    
    // 确认导入按钮
    document.getElementById('confirmImportBtn').addEventListener('click', importCharacter);
    
    // 导出角色按钮
    document.getElementById('exportCharacterBtn').addEventListener('click', exportCurrentCharacter);
    
    // 删除角色按钮
    document.getElementById('deleteCharacterBtn').addEventListener('click', showDeleteConfirm);
    
    // 确认删除按钮
    document.getElementById('confirmDeleteBtn').addEventListener('click', deleteCurrentCharacter);
}

// 加载角色列表
async function loadCharacters() {
    try {
        const response = await fetch('/api/characters');
        const data = await response.json();
        
        if (data.success) {
            currentCharacters = data.available_characters || [];
            renderCharactersList();
        } else {
            console.error('加载角色列表失败:', data.error);
            showError('加载角色列表失败: ' + data.error);
        }
    } catch (error) {
        console.error('加载角色列表失败:', error);
        showError('加载角色列表失败: ' + error.message);
    }
}

// 渲染角色列表
function renderCharactersList() {
    const container = document.getElementById('charactersList');
    
    if (currentCharacters.length === 0) {
        container.innerHTML = `
            <div class="empty-state glass-panel">
                <h3>暂无角色</h3>
                <p>请先创建或导入角色</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = currentCharacters.map(character => `
        <div class="character-item glass-panel">
            <div class="character-info">
                <div>
                    <div class="character-name" style="color: ${character.color || '#ffffff'};">
                        ${character.name || character.id}
                    </div>
                    <div class="character-id">ID: ${character.id}</div>
                </div>
            </div>
            <button class="character-actions-btn sci-fi-btn secondary" onclick="showCharacterDetail('${character.id}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"></path>
                </svg>
                详情
            </button>
        </div>
    `).join('');
}

// 显示角色详情
async function showCharacterDetail(characterId) {
    try {
        const response = await fetch(`/api/characters/${characterId}`);
        const data = await response.json();
        
        if (data.success) {
            currentCharacterDetail = data.character;
            
            // 填充详情信息
            document.getElementById('detailAvatar').src = data.character.avatar_url || '/static/images/default.svg';
            document.getElementById('detailName').textContent = data.character.name || characterId;
            document.getElementById('detailId').textContent = characterId;
            document.getElementById('detailEnglishName').textContent = data.character.name_en || '无';
            document.getElementById('detailDescription').textContent = data.character.description || '无描述';
            
            // 显示模态框
            document.getElementById('characterDetailModal').style.display = 'block';
        } else {
            showError('获取角色详情失败: ' + data.error);
        }
    } catch (error) {
        console.error('获取角色详情失败:', error);
        showError('获取角色详情失败: ' + error.message);
    }
}

// 关闭角色详情
function closeCharacterDetail() {
    document.getElementById('characterDetailModal').style.display = 'none';
    currentCharacterDetail = null;
}

// 导出当前角色
async function exportCurrentCharacter() {
    if (!currentCharacterDetail) return;
    
    try {
        const characterId = currentCharacterDetail.id;
        const response = await fetch(`/api/export-character/${characterId}`);
        
        if (response.ok) {
            // 创建下载链接
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${characterId}.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showSuccess('角色导出成功');
        } else {
            const data = await response.json();
            showError('导出失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('导出角色失败:', error);
        showError('导出角色失败: ' + error.message);
    }
}

// 显示删除确认
function showDeleteConfirm() {
    if (!currentCharacterDetail) return;
    
    document.getElementById('deleteCharacterName').textContent = currentCharacterDetail.name || currentCharacterDetail.id;
    document.getElementById('deleteCharacterId').textContent = currentCharacterDetail.id;
    document.getElementById('confirmDeleteInput').value = '';
    document.getElementById('deleteConfirmModal').style.display = 'block';
}

// 关闭删除确认
function closeDeleteConfirm() {
    document.getElementById('deleteConfirmModal').style.display = 'none';
}

// 删除当前角色
async function deleteCurrentCharacter() {
    if (!currentCharacterDetail) return;
    
    const inputId = document.getElementById('confirmDeleteInput').value.trim();
    const characterId = currentCharacterDetail.id;
    
    if (inputId !== characterId) {
        showError('输入的角色ID不匹配');
        return;
    }
    
    try {
        const response = await fetch(`/api/delete-character/${characterId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('角色删除成功');
            closeDeleteConfirm();
            closeCharacterDetail();
            loadCharacters(); // 重新加载角色列表
        } else {
            showError('删除失败: ' + data.error);
        }
    } catch (error) {
        console.error('删除角色失败:', error);
        showError('删除角色失败: ' + error.message);
    }
}

// 导入角色
async function importCharacter() {
    const fileInput = document.getElementById('importCharacterFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('请选择要导入的文件');
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.zip')) {
        showError('只支持zip格式的文件');
        return;
    }
    
    const formData = new FormData();
    formData.append('characterFile', file);
    
    try {
        const response = await fetch('/api/import-character', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('角色导入成功');
            closeImportModal();
            loadCharacters(); // 重新加载角色列表
        } else {
            showError('导入失败: ' + data.error);
        }
    } catch (error) {
        console.error('导入角色失败:', error);
        showError('导入角色失败: ' + error.message);
    }
}

// 关闭导入模态框
function closeImportModal() {
    document.getElementById('importModal').style.display = 'none';
    document.getElementById('importCharacterFile').value = '';
}

// 显示成功消息
function showSuccess(message) {
    // 简单的成功提示，可以根据需要改进
    alert(message);
}

// 显示错误消息
function showError(message) {
    // 简单的错误提示，可以根据需要改进
    alert('错误: ' + message);
}

// 点击模态框外部关闭
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});