// 横幅悬停显示/隐藏功能
(function() {
    'use strict';
    
    // 只在chat和story_chat页面启用
    const chatPage = document.getElementById('chatPage');
    if (!chatPage) return;
    
    const header = document.querySelector('.chat-header');
    if (!header) return;
    
    let hideTimeout = null;
    const HIDE_DELAY = 500; // 鼠标离开后延迟隐藏的时间（毫秒）
    const TRIGGER_HEIGHT = 80; // 触发区域的高度（像素）
    
    // 显示横幅
    function showHeader() {
        if (hideTimeout) {
            clearTimeout(hideTimeout);
            hideTimeout = null;
        }
        header.classList.add('show');
    }
    
    // 隐藏横幅
    function hideHeader() {
        hideTimeout = setTimeout(() => {
            header.classList.remove('show');
        }, HIDE_DELAY);
    }
    
    // 监听鼠标移动
    document.addEventListener('mousemove', (e) => {
        // 如果鼠标在顶部触发区域内
        if (e.clientY <= TRIGGER_HEIGHT) {
            showHeader();
        } else if (!header.matches(':hover')) {
            // 如果鼠标不在触发区域且不在横幅上，隐藏横幅
            hideHeader();
        }
    });
    
    // 鼠标进入横幅时保持显示
    header.addEventListener('mouseenter', () => {
        showHeader();
    });
    
    // 鼠标离开横幅时延迟隐藏
    header.addEventListener('mouseleave', (e) => {
        // 检查鼠标是否还在触发区域内
        if (e.clientY > TRIGGER_HEIGHT) {
            hideHeader();
        }
    });
    
    // 初始状态：隐藏横幅
    header.classList.remove('show');
})();
