function BtnLoad(e, text) {
    $(e).children(".proxy-btn-loading-icon").css("display", "block");
    $(e).children(".proxy-btn-text").text(text);
}
function BtnUnLoad(e, text) {
    $(e).children(".proxy-btn-loading-icon").css("display", "none");
    $(e).children(".proxy-btn-text").text(text);
}

function Captcha(e) {
    $.getJSON('index/captcha?refresh=1', function (data) {
        $(e).attr('src', data.url);
    });
}

function Modal(e,obj,style){
    $(e).addClass('fade');
    $(e).children('.modal-dialog').addClass(style);
    $(e).modal(obj);
}

function GetQueryString(name) {
    let reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)");
    let r = window.location.search.substr(1).match(reg);
    if (r != null) return unescape(r[2]); return null;
}

// 代码编辑器
function code_init(tx,code = '') {

    let textareaNode = null;
    let lineNode = null;
    let lineCount =  0;

    tx.childNodes.forEach(element => {
        if(element.nodeName == 'TEXTAREA'){
            element.value = JSON.stringify(JSON.parse(code),null,4);
            textareaNode = element;
            line();

            element.addEventListener("scroll",function (e) {
                lineNode.style.top = -element.scrollTop + 'px';
            });

            element.addEventListener("keydown", function (event) {

                if (event.keyCode === 13) {
                    event.preventDefault();
                    insertN("\r\n");
                    line();
                }
        
                if (event.keyCode === 9) {
                    event.preventDefault();
                    insert("    ");
                }

                if (event.keyCode === 8 || event.keyCode === 46) {
                    line();
                }
        
            });

            element.addEventListener("keyup", function (event) {
                if (event.keyCode === 8 || event.keyCode === 46) {
                    line();
                }
            });

            return;
        }else if(element.nodeName == 'UL'){
            lineNode = element;
        }
    });

    function lineChildCount(){
        lineCount = 0;
        lineNode.childNodes.forEach(element=>{
            if(element.nodeName == 'li'){
                ++lineCount;
            }
        });
    }

    function line(){
        let newLen = textareaNode.value.split(/\r\n|\n|\r/gi).length - lineCount;
        if(newLen < 0){
            for (let index = 0; index > newLen; index--) {
                lineNode.removeChild(lineNode.lastElementChild);
            }
        }else if(newLen > 0){
            for (let index = 0; index < newLen; index++) {
                let li = document.createElement("li");
                lineNode.appendChild(li);
            }
        }else{
            return;
        }
        lineCount = textareaNode.value.split(/\r\n|\n|\r/gi).length;
    }

    function insert(v) {
        let txt = textareaNode.value;
        let point = textareaNode.selectionEnd;

        let s = "", e = "", c = "", hh = false;

        s = txt.substring(0, point);
        e = txt.substring(point, txt.length);

        txt = s + v + e;

        textareaNode.value = txt;
        textareaNode.setSelectionRange(point + v.length, point + v.length)
    }

    function insertN(v = '') {
        let txt = textareaNode.value;
        let point = textareaNode.selectionEnd;

        let s = "", e = "", c = "", hh = false;

        let sn = txt.lastIndexOf('\n', point - 1);
        if (sn === -1) {
            hh = true;
        }
        let x1 = txt.substring(sn, txt.length);


        let rxx = /^\n( )*/gi
        c = x1.match(rxx);
        c = c ? c[0] : '';
        s = txt.substring(0, point);
        e = txt.substring(point, txt.length);
        if (hh) {
            txt = s + c + v + e;
        } else
            txt = s + c + e;

        textareaNode.value = txt;
        if (hh) {
            textareaNode.setSelectionRange(point + c.length + 1, point + c.length + 1)
        } else {
            textareaNode.setSelectionRange(point + c.length, point + c.length)
        }

    }
}


// 格式化时间
function DateFormatYYMMDD(time = 0) {
    let d = time * 86400000;
    let date = new Date((new Date()) - d);
    let mm = (date.getMonth() + 1) < 10 ? '0' + (date.getMonth() + 1) : (date.getMonth() + 1);
    let dd = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
    return date.getFullYear() + '-' + mm + '-' + dd;
}

function DateFormatYYMMDDHHIISS(time = 0) {
    let d = time * 86400000;
    let date = new Date((new Date()) - d);
    let mm = (date.getMonth() + 1) < 10 ? '0' + (date.getMonth() + 1) : (date.getMonth() + 1);
    let dd = date.getDate() < 10 ? "0" + date.getDate() : date.getDate();
    let hh = date.getHours() < 10 ? "0" + date.getHours() : date.getHours();
    let ii = date.getMinutes() < 10 ? "0" + date.getMinutes() : date.getMinutes();
    let ss = date.getSeconds() < 10 ? "0" + date.getSeconds() : date.getSeconds();

    return date.getFullYear() + '-' + mm + '-' + dd + 'T' + hh + ':' + ii + ':' + ss;
}

// 统一拦截 301（被重定向到登录）时提示登录过期
(function () {
    let loginExpireNotified = false;

    function showLoginExpired() {
        if (loginExpireNotified) return;
        loginExpireNotified = true;
        const msg = '登录已过期，请重新登录';

        const modal = document.getElementById('model-1');
        if (modal) {
            const body = modal.querySelector('.modal-body');
            if (body) body.textContent = msg;
            // 若页面仍加载了 jQuery/Bootstrap，调用弹窗，否则回退 alert
            if (window.$ && typeof window.$(modal).modal === 'function') {
                window.$(modal).modal('show');
            } else {
                alert(msg);
            }
        } else {
            alert(msg);
        }
    }

    function handleRedirect(target) {
        // target 可能是 XMLHttpRequest 或 fetch Response
        const status = target && target.status;
        if (status !== 301) return;

        showLoginExpired();

        let redirectUrl = '';
        if (typeof target.getResponseHeader === 'function') {
            redirectUrl = target.getResponseHeader('Location') || '';
        } else if (target.headers && typeof target.headers.get === 'function') {
            redirectUrl = target.headers.get('Location') || '';
        }

        if (redirectUrl) {
            window.location.href = redirectUrl;
        }
    }

    // 拦截 XMLHttpRequest
    if (window.XMLHttpRequest) {
        const originalSend = window.XMLHttpRequest.prototype.send;
        window.XMLHttpRequest.prototype.send = function () {
            this.addEventListener('loadend', () => handleRedirect(this));
            return originalSend.apply(this, arguments);
        };
    }

    // 拦截 fetch
    if (window.fetch) {
        const originalFetch = window.fetch;
        window.fetch = function () {
            return originalFetch.apply(this, arguments).then((response) => {
                handleRedirect(response);
                return response;
            });
        };
    }
})();