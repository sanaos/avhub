// globals.js - 包含所有需要在HTML中直接调用的全局函数

// 在此处存储全局状态
let appState = {
    translations: null, // 将在初始化后从脚本中设置
    currentLang: 'zh',
    SORT_OPTIONS: null,  // 将在初始化后从脚本中设置
};

// 注册全局函数
window.switchTab = function(tabName) {
    // 调用主脚本中的函数
    window.dispatchEvent(new CustomEvent('switchTab', { detail: { tabName } }));
};

window.searchMagnet = function() {
    // 触发搜索事件
    window.dispatchEvent(new CustomEvent('searchMagnet'));
};

window.copyToClipboard = function(text) {
    // 触发复制事件
    window.dispatchEvent(new CustomEvent('copyToClipboard', { detail: { text } }));
};

window.showSortMenu = function(button) {
    // 触发排序菜单事件
    window.dispatchEvent(new CustomEvent('showSortMenu', { detail: { button } }));
};

// 添加热门搜索词点击处理函数
window.searchWithTerm = function(term) {
    // 触发热门搜索词点击事件
    window.dispatchEvent(new CustomEvent('searchWithTerm', { detail: { term } }));
};

// 添加视频页面复制URL按钮点击事件
window.copyVideoUrl = function() {
    const sourceUrlElement = document.getElementById('videoSourceUrl');
    const sourceUrl = sourceUrlElement?.textContent;
    if (!sourceUrl) return;
    
    // 使用全局copyToClipboard函数
    window.copyToClipboard(sourceUrl);
    
    // 更新按钮状态
    const copyButton = document.getElementById('copySourceUrl');
    if (copyButton) {
        copyButton.classList.add('copied');
        const textElement = copyButton.querySelector('.tab-text');
        if (textElement) {
            const originalText = textElement.textContent;
            textElement.textContent = appState.translations ? 
                appState.translations[appState.currentLang].copied : 
                '已复制';
            
            setTimeout(() => {
                copyButton.classList.remove('copied');
                textElement.textContent = originalText;
            }, 2000);
        }
    }
};

// 注册全局事件处理函数以便主脚本可以设置全局状态
window.setGlobalState = function(key, value) {
    appState[key] = value;
};

// 为主脚本提供初始化方法
window.initializeGlobals = function(data) {
    if (data.translations) appState.translations = data.translations;
    if (data.currentLang) appState.currentLang = data.currentLang;
    if (data.SORT_OPTIONS) appState.SORT_OPTIONS = data.SORT_OPTIONS;
}; 