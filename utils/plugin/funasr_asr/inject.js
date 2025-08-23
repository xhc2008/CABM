// inject.js
(function () {
  // 🔒 全局标志：FunASR 已激活
  window.__funasr_active__ = true;

  // 🚫 标记：是否正在由 FunASR 处理
  let isHandlingByFunASR = false;

  // 🚫 劫持原始 toggleRecording（无论它是否在 window 上）
  if (typeof window.toggleRecording === 'function') {
    console.warn('🟡 拦截并替换 window.toggleRecording');
    window.toggleRecording = function () {
      console.log('🚫 toggleRecording 已被 FunASR 阻止（window 层面）');
    };
  }

  // 🚫 如果未来有人定义 toggleRecording，也拦截
  Object.defineProperty(window, 'toggleRecording', {
    configurable: true,
    set: function (val) {
      if (typeof val === 'function' && !val.toString().includes('__funasr_active__')) {
        console.warn('🟡 检测到试图覆盖 toggleRecording，已阻止');
        // 可以选择不设置，或设置为空函数
      }
    }
  });

  // 🚫 拦截 fetch，防止重复提交
  const originalFetch = window.fetch;
  let micRequestLocked = false;

  window.fetch = function (input, init) {
    if (typeof input === 'string' && input.includes('/api/mic')) {
      if (micRequestLocked) {
        console.warn('🚫 阻止重复 /api/mic 请求');
        return Promise.resolve(new Response('{}'));
      }
      micRequestLocked = true;
      console.log('📤 FunASR 正在提交录音...');
      return originalFetch(input, init).finally(() => {
        setTimeout(() => {
          micRequestLocked = false;
        }, 600);
      });
    }
    return originalFetch(input, init);
  };

  // ✅ 真正接管：在捕获阶段拦截点击事件
  document.addEventListener(
    'click',
    function (e) {
      const target = e.target;
      const isMicButton =
        target.id === 'micButton' ||
        target.classList.contains('mic-button') ||
        target.closest('#micButton') ||
        target.closest('.mic-button');

      if (!isMicButton) return;

      // 🔥 阻止原事件冒泡到原始监听器
      e.stopImmediatePropagation();
      e.preventDefault();

      // 获取 input 元素
      const messageInput =
        document.getElementById('messageInput') ||
        document.querySelector('textarea') ||
        document.querySelector('.message-input');

      if (!messageInput) {
        console.error('❌ 未找到 messageInput');
        return;
      }

      const micButton = target.closest('button') || target;

      // 状态判断
      const isCurrentlyRecording = micButton.classList.contains('recording');

      if (isHandlingByFunASR) {
        console.warn('🟡 忽略：已在处理中');
        return;
      }

      if (isCurrentlyRecording) {
        // --- 停止录音 ---
        if (window.__mediaRecorder__ && window.__mediaRecorder__.state === 'recording') {
          window.__mediaRecorder__.stop();
          window.__mediaRecorder__.stream.getTracks().forEach((track) => track.stop());
          console.log('🛑 FunASR: 录音已停止');
        }
        micButton.classList.remove('recording');
      } else {
        // --- 开始录音 ---
        isHandlingByFunASR = true;

        navigator.mediaDevices.getUserMedia({ audio: true })
          .then((stream) => {
            const mediaRecorder = new MediaRecorder(stream);
            window.__mediaRecorder__ = mediaRecorder; // 挂载到全局
            const audioChunks = [];

            mediaRecorder.ondataavailable = (e) => e.data.size > 0 && audioChunks.push(e.data);

            mediaRecorder.onstop = () => {
              const blob = new Blob(audioChunks, { type: 'audio/webm' });
              const formData = new FormData();
              formData.append('audio', blob, 'recording.webm');

              fetch('/api/mic', {
                method: 'POST',
                body: formData,
              })
                .then((r) => r.json())
                .then((data) => {
                  if (data.text) {
                    messageInput.value += data.text;
                    messageInput.focus();
                    // FunASR 语音识别后更新字数统计
                    if (window.inputEnhancements && typeof window.inputEnhancements.updateCharCount === 'function') {
                      window.inputEnhancements.updateCharCount();
                    }
                  }
                })
                .catch((err) => console.error('上传失败', err));
            };

            mediaRecorder.start();
            console.log('✅ FunASR: 录音已开始');
            micButton.classList.add('recording');
          })
          .catch((err) => {
            console.error('麦克风失败', err);
            alert('无法访问麦克风: ' + err.message);
            micButton.classList.remove('recording');
          })
          .finally(() => {
            isHandlingByFunASR = false;
          });
      }
    },
    true // 🔥 在捕获阶段执行，早于任何冒泡监听器
  );

  console.log('🎙️ FunASR 插件已激活：在捕获阶段接管麦克风按钮');
})();