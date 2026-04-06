console.log('=== WHATSAPP VISIBILITY MODULE LOADED ===');

(function () {
    const ns = (window.codexWhatsApp = window.codexWhatsApp || {});

    let allowedModelsCache = null;

    async function fetchAllowedModels() {
        try {
            if (allowedModelsCache) return allowedModelsCache;
            const res = await fetch('/whatsapp/allowed_models', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {} }),
            });
            const data = await res.json();
            const arr = (data && data.result && data.result.models) || [];
            allowedModelsCache = Array.isArray(arr) ? arr : [];
            return allowedModelsCache;
        } catch (e) {
            return [];
        }
    }

    function getThreadContext(buttonEl) {
        const modelAttr = buttonEl.getAttribute('data-thread-model');
        const idAttr = buttonEl.getAttribute('data-thread-id');
        if (modelAttr && idAttr) {
            const idNum = parseInt(idAttr, 10);
            if (!Number.isNaN(idNum)) {
                return { model: modelAttr, id: idNum };
            }
        }
        try {
            const url = new URL(window.location.href);
            const modelParam = url.searchParams.get('model');
            const id = parseInt(url.searchParams.get('id'), 10) || null;
            let detectedModel = modelParam;
            if (!detectedModel) {
                if (url.pathname.includes('/crm/')) {
                    detectedModel = 'crm.lead';
                } else if (url.pathname.includes('/sale/')) {
                    detectedModel = 'sale.order';
                } else if (url.pathname.includes('/project/')) {
                    detectedModel = 'project.project';
                } else if (url.pathname.includes('/purchase/')) {
                    detectedModel = 'purchase.order';
                } else if (url.pathname.includes('/account/')) {
                    detectedModel = 'account.move';
                } else if (url.pathname.includes('/helpdesk/')) {
                    detectedModel = 'helpdesk.ticket';
                } else if (url.pathname.includes('/mrp/')) {
                    detectedModel = 'mrp.production';
                } else if (url.pathname.includes('/mail/discuss')) {
                    detectedModel = 'discuss.channel';
                }
            }
            if (detectedModel && id) {
                return { model: detectedModel, id: id };
            }
        } catch (e) {
            console.warn('URL parsing failed:', e);
        }

        const thread = buttonEl.closest('.o-mail-ThreadView, .o-mail-Thread, .o-mail-Composer');
        if (thread) {
            const model = thread.getAttribute('data-model') || null;
            const id = parseInt(thread.getAttribute('data-id') || '', 10);
            if (model && id) {
                return { model, id };
            }
        }
        return null;
    }

    async function shouldShowButtonFor(buttonEl) {
        const ctx = getThreadContext(buttonEl);
        if (!ctx || !ctx.model) return false;

        if (ctx.model === 'discuss.channel') {
            try {
                const res = await fetch('/whatsapp/is_wa_channel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { channel_id: ctx.id } }),
                });
                const data = await res.json();
                return data && data.result && data.result.is_wa;
            } catch (e) {
                console.warn('Failed to check if channel is WhatsApp:', e);
                return false;
            }
        }

        const allowed = await fetchAllowedModels();
        if (!allowed || !allowed.length) return true;
        return allowed.includes(ctx.model);
    }

    function onReady(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    }

    function initVisibilityObserver() {
        const mo = new MutationObserver(async () => {
            const models = await fetchAllowedModels();
            const restrict = models && models.length;
            if (!restrict) return;
            document.querySelectorAll('.o_whatsapp_send_btn').forEach(async (btn) => {
                try {
                    const allowed = await shouldShowButtonFor(btn);
                    btn.style.display = allowed ? '' : 'none';
                } catch (e) {
                    // ignore
                }
            });
        });
        mo.observe(document.body, { childList: true, subtree: true });
        console.log('WhatsApp button visibility observer initialized');
    }

    ns.fetchAllowedModels = fetchAllowedModels;
    ns.shouldShowButtonFor = shouldShowButtonFor;
    ns.getThreadContext = getThreadContext;
    ns.initVisibilityObserver = initVisibilityObserver;

    onReady(initVisibilityObserver);
})();


