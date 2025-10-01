// 资源管理页面JavaScript

let currentCharacters = [];
let currentCharacterDetail = null;
let currentMusicTracks = [];
let currentPlayingTrack = null;
let currentBackgrounds = {};
let currentBackgroundDetail = null;

// 防止重复提交的标志
let isSubmittingBackground = false;
let isImportingCharacter = false;

// 防止重复绑定事件的标志
let isEventsBound = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
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

    // 加载音乐列表
    loadMusicTracks();

    // 加载背景列表
    loadBackgrounds();
}

// 初始化选项卡
function initTabs() {
    const tabs = document.querySelectorAll('.resource-tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', function () {
            const targetTab = this.dataset.tab;

            // 移除所有活动状态
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            // 激活当前选项卡
            this.classList.add('active');
            document.getElementById(targetTab + '-tab').classList.add('active');

            // 如果切换到音乐选项卡，刷新音乐列表
            if (targetTab === 'music') {
                loadMusicTracks();
            }

            // 如果切换到背景选项卡，刷新背景列表
            if (targetTab === 'backgrounds') {
                loadBackgrounds();
            }
        });
    });
}

// 初始化按钮事件
function initButtons() {
    // 防止重复绑定事件
    if (isEventsBound) {
        return;
    }

    // 导入角色按钮 - 直接触发文件选择
    document.getElementById('importCharacterBtn').addEventListener('click', function () {
        document.getElementById('hiddenCharacterFileInput').click();
    });

    // 创建角色按钮
    document.getElementById('createCharacterBtn').addEventListener('click', function () {
        window.location.href = '/custom_character';
    });

    // 隐藏角色文件输入变化事件
    document.getElementById('hiddenCharacterFileInput').addEventListener('change', function (e) {
        if (e.target.files.length > 0) {
            importCharacter(e.target.files[0]);
            // 清空文件输入，允许重复选择同一文件
            e.target.value = '';
        }
    });

    // 导出角色按钮
    document.getElementById('exportCharacterBtn').addEventListener('click', exportCurrentCharacter);

    // 删除角色按钮
    document.getElementById('deleteCharacterBtn').addEventListener('click', showDeleteConfirm);

    // 确认删除按钮
    document.getElementById('confirmDeleteBtn').addEventListener('click', deleteCurrentCharacter);

    // 音乐管理按钮
    document.getElementById('addMusicBtn').addEventListener('click', function () {
        document.getElementById('hiddenMusicFileInput').click();
    });

    document.getElementById('refreshMusicBtn').addEventListener('click', loadMusicTracks);

    // 隐藏文件输入变化事件
    document.getElementById('hiddenMusicFileInput').addEventListener('change', function (e) {
        if (e.target.files.length > 0) {
            addMusic(e.target.files[0]);
            // 清空文件输入，允许重复选择同一文件
            e.target.value = '';
        }
    });

    // 背景管理按钮
    document.getElementById('addBackgroundBtn').addEventListener('click', function () {
        // 清空表单并重置为添加模式
        resetAddBackgroundModal();
        document.getElementById('addBackgroundModal').style.display = 'block';
    });

    document.getElementById('refreshBackgroundsBtn').addEventListener('click', loadBackgrounds);

    // 添加背景表单提交
    document.getElementById('addBackgroundForm').addEventListener('submit', function (e) {
        e.preventDefault();
        handleBackgroundFormSubmit();
    });

    // 标记事件已绑定
    isEventsBound = true;
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
async function importCharacter(file) {
    // 防止重复导入
    if (isImportingCharacter) {
        console.log('正在导入中，忽略重复请求');
        return;
    }

    if (!file) {
        showError('请选择要导入的文件');
        return;
    }

    if (!file.name.toLowerCase().endsWith('.zip')) {
        showError('只支持zip格式的文件');
        return;
    }

    // 设置导入标志
    isImportingCharacter = true;

    const formData = new FormData();
    formData.append('characterFile', file);

    try {
        // 显示上传进度提示
        showSuccess('正在导入角色，请稍候...');

        const response = await fetch('/api/import-character', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showSuccess('角色导入成功');
            // 清空文件输入
            document.getElementById('hiddenCharacterFileInput').value = '';
            loadCharacters(); // 重新加载角色列表
        } else {
            showError('导入失败: ' + data.error);
        }
    } catch (error) {
        console.error('导入角色失败:', error);
        showError('导入角色失败: ' + error.message);
    } finally {
        // 重置导入标志
        isImportingCharacter = false;
    }
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

// 音乐管理功能

// 加载音乐列表
async function loadMusicTracks() {
    try {
        const response = await fetch('/api/bgm-tracks');
        const tracks = await response.json();

        currentMusicTracks = tracks || [];
        renderMusicList();
    } catch (error) {
        console.error('加载音乐列表失败:', error);
        showError('加载音乐列表失败: ' + error.message);
    }
}

// 渲染音乐列表
function renderMusicList() {
    const container = document.getElementById('musicList');

    if (currentMusicTracks.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="padding: 40px; text-align: center; color: var(--text-secondary);">
                <h3>暂无音乐</h3>
                <p>请先添加音乐文件</p>
            </div>
        `;
        return;
    }

    container.innerHTML = currentMusicTracks.map(track => `
        <div class="music-item">
            <div class="music-info">
                <div class="music-icon">🎵</div>
                <div class="music-name">${track}</div>
            </div>
            <div class="music-actions">
                <button class="music-btn play-btn" onclick="playMusic('${track}')" data-track="${track}">
                    播放
                </button>
                <button class="music-btn delete-btn" onclick="deleteMusic('${track}')" data-track="${track}">
                    删除
                </button>
            </div>
        </div>
    `).join('');
}

// 播放音乐
async function playMusic(trackName) {
    try {
        // 检查BGM服务是否可用
        if (!window.bgmService) {
            showError('BGM服务未初始化，请刷新页面重试');
            return;
        }

        // 如果点击的是当前正在播放的音乐，则停止播放
        if (currentPlayingTrack === trackName) {
            console.log(`停止播放: ${trackName}`);
            window.bgmService.stop();
            currentPlayingTrack = null;
            updatePlayButtons(null);

            // 恢复页面BGM
            setTimeout(() => {
                window.bgmService.playPageBGM();
            }, 500);

            // showSuccess(`停止播放: ${trackName}`);
            return;
        }

        // 停止当前播放
        window.bgmService.stop();

        // 更新按钮状态
        updatePlayButtons(trackName);

        // 播放选中的音乐
        console.log(`开始播放: ${trackName}`);
        await window.bgmService.playTrack(trackName);
        currentPlayingTrack = trackName;

        // showSuccess(`开始播放: ${trackName}`);
    } catch (error) {
        console.error('播放音乐失败:', error);
        showError('播放音乐失败: ' + error.message);
        updatePlayButtons(null);
        currentPlayingTrack = null;
    }
}

// 更新播放按钮状态
function updatePlayButtons(playingTrack) {
    const playButtons = document.querySelectorAll('.play-btn');
    playButtons.forEach(btn => {
        const track = btn.dataset.track;
        if (track === playingTrack) {
            btn.textContent = '播放中';
            btn.classList.add('playing');
        } else {
            btn.textContent = '播放';
            btn.classList.remove('playing');
        }
    });
}

// 删除音乐
function deleteMusic(trackName) {
    const deleteBtn = document.querySelector(`.delete-btn[data-track="${trackName}"]`);

    if (deleteBtn.classList.contains('delete-confirm')) {
        // 执行删除
        confirmDeleteMusic(trackName);
    } else {
        // 显示确认状态
        deleteBtn.textContent = '确认删除';
        deleteBtn.classList.add('delete-confirm');

        // 3秒后恢复原状态
        setTimeout(() => {
            deleteBtn.textContent = '删除';
            deleteBtn.classList.remove('delete-confirm');
        }, 3000);
    }
}

// 确认删除音乐
async function confirmDeleteMusic(trackName) {
    try {
        const response = await fetch(`/api/bgm-tracks/${encodeURIComponent(trackName)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            // showSuccess('音乐删除成功');

            // 如果删除的是当前播放的音乐，停止播放
            if (currentPlayingTrack === trackName) {
                if (window.bgmService) {
                    window.bgmService.stop();
                }
                currentPlayingTrack = null;
            }

            // 刷新音乐列表
            loadMusicTracks();

            // 刷新BGM服务的曲目列表
            if (window.bgmService) {
                await window.bgmService.refreshTracks();
            }
        } else {
            showError('删除失败: ' + data.message);
        }
    } catch (error) {
        console.error('删除音乐失败:', error);
        showError('删除音乐失败: ' + error.message);
    }
}

// 添加音乐
async function addMusic(file) {
    if (!file) {
        showError('请选择要添加的音频文件');
        return;
    }

    // 检查文件类型
    const allowedTypes = ['.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(fileExt)) {
        showError('不支持的文件格式。支持的格式: ' + allowedTypes.join(', '));
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        // showSuccess('正在上传音乐文件...');

        const response = await fetch('/api/bgm-tracks/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // showSuccess('音乐添加成功');

            // 清空文件输入
            document.getElementById('hiddenMusicFileInput').value = '';

            // 刷新音乐列表
            loadMusicTracks();

            // 刷新BGM服务的曲目列表
            if (window.bgmService) {
                await window.bgmService.refreshTracks();
            }
        } else {
            showError('添加失败: ' + data.message);
        }
    } catch (error) {
        console.error('添加音乐失败:', error);
        showError('添加音乐失败: ' + error.message);
    }
}



// 背景管理功能

// 加载背景列表
async function loadBackgrounds() {
    try {
        const response = await fetch('/api/background/list');
        const data = await response.json();

        if (data.success) {
            currentBackgrounds = data.backgrounds || {};
            renderBackgroundsList();
        } else {
            console.error('加载背景列表失败:', data.error);
            showError('加载背景列表失败: ' + data.error);
        }
    } catch (error) {
        console.error('加载背景列表失败:', error);
        showError('加载背景列表失败: ' + error.message);
    }
}

// 渲染背景列表
function renderBackgroundsList() {
    const container = document.getElementById('backgroundsList');

    if (Object.keys(currentBackgrounds).length === 0) {
        container.innerHTML = `
            <div class="empty-state glass-panel">
                <h3>暂无背景</h3>
                <p>请先添加背景图片</p>
            </div>
        `;
        return;
    }

    container.innerHTML = Object.entries(currentBackgrounds).map(([filename, info]) => `
        <div class="background-item" onclick="showBackgroundDetail('${filename}')">
            <div class="background-actions">
                <button class="background-action-btn" onclick="event.stopPropagation(); editBackground('${filename}')" title="编辑">
                    ✏️
                </button>
                <button class="background-action-btn delete" onclick="event.stopPropagation(); showDeleteBackgroundConfirm('${filename}')" title="删除">
                    🗑️
                </button>
            </div>
            <img src="/static/images/backgrounds/${filename}" 
                 alt="${info.name}" 
                 class="background-thumbnail" 
                 onerror="this.src='/static/images/default.svg'">
            <div class="background-info">
                <div class="background-name">${info.name}</div>
            </div>
        </div>
    `).join('');
}

// 显示背景详情
async function showBackgroundDetail(filename) {
    try {
        const response = await fetch(`/api/background/info/${filename}`);
        const data = await response.json();

        if (data.success) {
            currentBackgroundDetail = { filename, ...data.info };

            // 填充详情信息
            document.getElementById('detailBackgroundImage').src = data.url;
            document.getElementById('detailBackgroundName').textContent = data.info.name;
            document.getElementById('detailBackgroundFilename').textContent = filename;
            document.getElementById('detailBackgroundDesc').textContent = data.info.desc || '无描述';
            document.getElementById('detailBackgroundPrompt').textContent = data.info.prompt || '无提示词';

            // 显示模态框
            document.getElementById('backgroundDetailModal').style.display = 'block';
        } else {
            showError('获取背景详情失败: ' + data.error);
        }
    } catch (error) {
        console.error('获取背景详情失败:', error);
        showError('获取背景详情失败: ' + error.message);
    }
}

// 关闭背景详情
function closeBackgroundDetail() {
    document.getElementById('backgroundDetailModal').style.display = 'none';
    currentBackgroundDetail = null;
}

// 统一的背景表单提交处理
async function handleBackgroundFormSubmit() {
    // 检查是否是编辑模式
    if (window.currentEditingFilename) {
        await updateBackground(window.currentEditingFilename);
    } else {
        await addBackground();
    }
}

// 添加背景
async function addBackground() {
    // 防止重复提交
    if (isSubmittingBackground) {
        console.log('正在提交中，忽略重复请求');
        return;
    }

    const name = document.getElementById('backgroundNameInput').value.trim();
    const desc = document.getElementById('backgroundDescInput').value.trim();
    const prompt = document.getElementById('backgroundPromptInput').value.trim();
    const fileInput = document.getElementById('backgroundFileInput');

    if (!name) {
        showError('请输入背景名称');
        return;
    }

    // 设置提交标志
    isSubmittingBackground = true;

    const submitBtn = document.getElementById('confirmAddBackgroundBtn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;

    try {
        if (fileInput.files.length > 0) {
            // 用户上传了图片文件，直接使用上传的图片
            submitBtn.textContent = '上传中...';
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('name', name);
            formData.append('desc', desc);
            formData.append('prompt', prompt);

            const response = await fetch('/api/background/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showSuccess('背景添加成功');
                closeAddBackgroundModal();
                loadBackgrounds();
            } else {
                showError('添加背景失败: ' + data.error);
            }
        } else {
            // 没有上传文件
            if (prompt.trim()) {
                // 有提示词，使用AI生成
                submitBtn.textContent = 'AI生成中...';
            } else {
                // 没有提示词，创建占位图片
                submitBtn.textContent = '创建中...';
            }
            
            const response = await fetch('/api/background/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, desc, prompt })
            });

            const data = await response.json();

            if (data.success) {
                if (prompt.trim()) {
                    showSuccess('背景添加成功（AI生成）');
                } else {
                    showSuccess('背景添加成功（占位图片）');
                }
                closeAddBackgroundModal();
                loadBackgrounds();
            } else {
                showError('添加背景失败: ' + data.error);
            }
        }
    } catch (error) {
        console.error('添加背景失败:', error);
        showError('添加背景失败: ' + error.message);
    } finally {
        // 重置提交标志和按钮状态
        isSubmittingBackground = false;
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// 关闭添加背景模态框
function closeAddBackgroundModal() {
    document.getElementById('addBackgroundModal').style.display = 'none';
    resetAddBackgroundModal();
}

// 重置添加背景模态框
function resetAddBackgroundModal() {
    // 清空表单
    document.getElementById('addBackgroundForm').reset();

    // 重置按钮文字
    document.getElementById('confirmAddBackgroundBtn').textContent = '添加背景';
    
    // 重置提交标志
    isSubmittingBackground = false;
    
    // 清除编辑状态
    window.currentEditingFilename = null;
}

// 编辑背景
function editBackground(filename) {
    const info = currentBackgrounds[filename];
    if (!info) return;

    // 填充表单
    document.getElementById('backgroundNameInput').value = info.name;
    document.getElementById('backgroundDescInput').value = info.desc || '';
    document.getElementById('backgroundPromptInput').value = info.prompt || '';

    // 显示模态框
    document.getElementById('addBackgroundModal').style.display = 'block';

    // 修改按钮文字
    document.getElementById('confirmAddBackgroundBtn').textContent = '更新背景';
    
    // 重置提交标志
    isSubmittingBackground = false;
    
    // 设置一个标志表示当前是编辑模式
    window.currentEditingFilename = filename;
}

// 更新背景
async function updateBackground(filename) {
    // 防止重复提交
    if (isSubmittingBackground) {
        console.log('正在提交中，忽略重复请求');
        return;
    }

    const name = document.getElementById('backgroundNameInput').value.trim();
    const desc = document.getElementById('backgroundDescInput').value.trim();
    const prompt = document.getElementById('backgroundPromptInput').value.trim();

    if (!name) {
        showError('请输入背景名称');
        return;
    }

    // 设置提交标志
    isSubmittingBackground = true;

    const submitBtn = document.getElementById('confirmAddBackgroundBtn');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = '更新中...';

    try {
        const response = await fetch(`/api/background/update/${filename}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, desc, prompt })
        });

        const data = await response.json();

        if (data.success) {
            // showSuccess('背景更新成功');
            closeAddBackgroundModal();
            loadBackgrounds();

            // 恢复表单提交行为
            resetAddBackgroundModal();
        } else {
            showError('更新背景失败: ' + data.error);
        }
    } catch (error) {
        console.error('更新背景失败:', error);
        showError('更新背景失败: ' + error.message);
    } finally {
        // 重置提交标志和按钮状态
        isSubmittingBackground = false;
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// 显示删除背景确认
function showDeleteBackgroundConfirm(filename) {
    const info = currentBackgrounds[filename];
    if (!info) return;

    document.getElementById('deleteBackgroundName').textContent = info.name;
    document.getElementById('deleteBackgroundFilename').textContent = filename;
    document.getElementById('deleteBackgroundConfirmModal').style.display = 'block';

    // 设置确认删除按钮的点击事件
    document.getElementById('confirmDeleteBackgroundBtn').onclick = function () {
        deleteBackground(filename);
    };
}

// 关闭删除背景确认
function closeDeleteBackgroundConfirm() {
    document.getElementById('deleteBackgroundConfirmModal').style.display = 'none';
}

// 删除背景
async function deleteBackground(filename) {
    try {
        const response = await fetch(`/api/background/delete/${filename}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showSuccess('背景删除成功');
            closeDeleteBackgroundConfirm();
            loadBackgrounds();
        } else {
            showError('删除背景失败: ' + data.error);
        }
    } catch (error) {
        console.error('删除背景失败:', error);
        showError('删除背景失败: ' + error.message);
    }
}

// 点击模态框外部关闭
window.addEventListener('click', function (event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});