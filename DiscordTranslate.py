import webview
import os
from groq import Groq

GROQ_API_KEY = ""  # defina sua chave de API da Groq aqui. Você pode obter uma chave gratuita em https://groq.com/signup.

client = Groq(api_key=GROQ_API_KEY)

STORAGE_PATH = os.path.join(os.path.expanduser("~"), "discord_app_session")

class Api:
    def __init__(self):
        self.translate_on = False

    def toggle_translate(self, state):
        self.translate_on = state
        print("Translate:", "ON" if state else "OFF")
        return "ok"

    def translate_message(self, text):
        if not self.translate_on:
            return text
        print(f"[Traduzindo]: {text}")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "You are a translator. Translate the user's message from Portuguese to English. "
                    "Keep the tone casual and natural, as if texting a friend. "
                    "Preserve slang, internet expressions, and the original vibe. "
                    "Do NOT translate 'mano' as 'hand' — it means 'bro' or 'dude'. "
                    "Return ONLY the translated text, nothing else. "
                    "No explanations, no quotes, no extra content."
                )},
                {"role": "user", "content": text}
            ]
        )
        translated = response.choices[0].message.content.strip()
        print(f"[Traduzido]: {translated}")
        return translated


    def log(self, msg):
        print(f"[JS] {msg}")
        return "ok"


JS_PATCH = """
(function() {
    if (window.__discordTranslatePatchDone) return;
    window.__discordTranslatePatchDone = true;

    const _open   = XMLHttpRequest.prototype.open;
    const _send   = XMLHttpRequest.prototype.send;
    const _setHdr = XMLHttpRequest.prototype.setRequestHeader;

    XMLHttpRequest.prototype.open = function(method, url) {
        this.__url     = url;
        this.__method  = method;
        this.__headers = {};
        return _open.apply(this, arguments);
    };

    XMLHttpRequest.prototype.setRequestHeader = function(key, value) {
        if (!this.__headers) this.__headers = {};
        this.__headers[key] = value;
        return _setHdr.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(body) {
        const self   = this;
        const url    = self.__url    || '';
        const method = (self.__method || '').toUpperCase();

        const isMessage = url.includes('/api/v9/channels/') &&
                          url.includes('/messages') &&
                          !url.includes('/messages/') &&
                          method === 'POST' &&
                          body;

        if (isMessage) {
            try {
                const parsed = JSON.parse(body);
                if (parsed.content && parsed.content.trim() !== '') {
                    const snapUrl     = url;
                    const snapHeaders = Object.assign({}, self.__headers);
                    const originalContent = parsed.content;

                    // Envia dummy com zero-width space
                    const dummyParsed = Object.assign({}, parsed);
                    dummyParsed.content = '\u200b';

                    // Intercepta a resposta do XHR dummy para pegar o ID e deletar
                    self.addEventListener('load', function() {
                        try {
                            const resp = JSON.parse(self.responseText);
                            const msgId = resp.id;
                            if (msgId) {
                                // Deleta a mensagem dummy imediatamente
                                const delXhr = new XMLHttpRequest();
                                _open.call(delXhr, 'DELETE', snapUrl + '/' + msgId, true);
                                for (const [k, v] of Object.entries(snapHeaders)) {
                                    _setHdr.call(delXhr, k, v);
                                }
                                _send.call(delXhr, null);
                                pywebview.api.log('Dummy deletado: ' + msgId);
                            }
                        } catch(e) {
                            pywebview.api.log('Erro ao deletar dummy: ' + e.message);
                        }
                    });

                    // Traduz e envia a mensagem real traduzida
                    pywebview.api.translate_message(originalContent).then(function(translated) {
                        const translatedParsed = Object.assign({}, parsed);
                        translatedParsed.content = translated;
                        translatedParsed.nonce   = String(BigInt(Date.now()) * BigInt(1048576));

                        const req = new XMLHttpRequest();
                        _open.call(req, 'POST', snapUrl, true);
                        for (const [k, v] of Object.entries(snapHeaders)) {
                            _setHdr.call(req, k, v);
                        }
                        _send.call(req, JSON.stringify(translatedParsed));
                        pywebview.api.log('Enviado traduzido: ' + translated);
                    }).catch(function(err) {
                        pywebview.api.log('Erro traducao: ' + err);
                        const req = new XMLHttpRequest();
                        _open.call(req, 'POST', snapUrl, true);
                        for (const [k, v] of Object.entries(snapHeaders)) {
                            _setHdr.call(req, k, v);
                        }
                        _send.call(req, body);
                    });

                    return _send.call(self, JSON.stringify(dummyParsed));
                }
            } catch(e) {
                pywebview.api.log('Erro parse: ' + e.message);
            }
        }

        return _send.apply(this, arguments);
    };

    pywebview.api.log('Patch instalado!');
})();
"""

JS_INIT = f"""
(function tryPatch() {{
    if (window.__discordTranslatePatchDone) return;
    try {{
        {JS_PATCH}
    }} catch(e) {{}}
    if (!window.__discordTranslatePatchDone) {{
        setTimeout(tryPatch, 500);
    }}
}})();
"""

def inject(window):
    window.evaluate_js(JS_INIT)

def add_button(window):
    window.evaluate_js("""
        if (!document.getElementById('translate-btn')) {
            const btn = document.createElement('div');
            btn.id = 'translate-btn';
            btn.innerHTML = 'Translate: OFF';
            btn.style.cssText = `
                position: fixed !important;
                right: 20px;
                bottom: 20px;
                background: #5865F2;
                color: white;
                padding: 8px 14px;
                border-radius: 8px;
                font-family: Arial, sans-serif;
                font-size: 14px;
                cursor: pointer;
                z-index: 999999;
                box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                user-select: none;
            `;
            btn.onclick = function() {
                const isOn = btn.innerHTML.includes('OFF');
                btn.innerHTML = isOn ? 'Translate: ON' : 'Translate: OFF';
                btn.style.background = isOn ? '#57F287' : '#5865F2';
                pywebview.api.toggle_translate(isOn);
            };
            document.body.appendChild(btn);
        }
    """)

def on_loaded(window):
    inject(window)
    add_button(window)

def main():
    api = Api()
    window = webview.create_window(
        "Discord Web + Translate",
        "https://discord.com/app",
        js_api=api,
        width=1200,
        height=700
    )
    window.events.loaded += lambda: on_loaded(window)
    webview.start(private_mode=False, storage_path=STORAGE_PATH)

if __name__ == "__main__":
    main()
