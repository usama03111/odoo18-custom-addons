(function () {
    const onReady = (fn) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    };

    function setWhatsappOpen(enabled) {
        document.body.classList.toggle('o-wa-open', !!enabled);
    }

    function isWhatsappChannel(el) {
        return el.classList.contains('o-wa-channel') || el.querySelector('.o-wa-channel');
    }

    function countWhatsapp() {
        return document.querySelectorAll('.o-mail-DiscussSidebarChannel.o-wa-channel, .o-wa-channel-container .o-mail-DiscussSidebarChannel').length;
    }

    function refreshBadge() {
        const count = countWhatsapp();
        document.querySelectorAll('.o-wa-badge-count').forEach((el) => el.textContent = String(count));
    }

    async function fetchWaIds(ids) {
        const waIds = [];
        await Promise.all((ids || []).map(async (id) => {
            try {
                const res = await fetch('/whatsapp/is_wa_channel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { channel_id: id } }),
                });
                const data = await res.json();
                const isWa = data && data.result && data.result.is_wa;
                if (isWa) {
                    waIds.push(id);
                }
            } catch (e) {
                console.warn('WA sidebar: cannot check WA id', e);
            }
        }));
        return waIds;
    }

    async function moveWhatsappChannels() {
        const waList = document.querySelector('.o-wa-list');
        if (!waList) return;
        // First move any elements already marked as WA
        document.querySelectorAll('.o-wa-channel-container').forEach((container) => {
            if (!container.closest('.o-wa-list')) waList.appendChild(container);
        });
        // For unmarked ones, query the server by thread id
        const candidates = Array.from(document.querySelectorAll('.o-mail-DiscussSidebarChannel[data-thread-id]'))
            .filter((btn) => !btn.classList.contains('o-wa-channel'));
        if (candidates.length) {
            const ids = candidates.map((btn) => parseInt(btn.getAttribute('data-thread-id') || '0', 10)).filter((n) => n > 0);
            if (ids.length) {
                const waIds = await fetchWaIds(ids);
                candidates.forEach((btn) => {
                    const tid = parseInt(btn.getAttribute('data-thread-id') || '0', 10);
                    if (waIds.includes(tid)) {
                        btn.classList.add('o-wa-channel');
                        const cont = btn.closest('.o-mail-DiscussSidebarChannel-container');
                        if (cont && !cont.closest('.o-wa-list')) waList.appendChild(cont);
                    }
                });
            }
        }
    }

    function applyFilter() {
        moveWhatsappChannels();
        const open = document.body.classList.contains('o-wa-open');
        const waList = document.querySelector('.o-wa-list');
        if (waList) waList.style.display = open ? '' : 'none';
        document.querySelectorAll('.o-mail-DiscussSidebarChannel').forEach((btn) => {
            const container = btn.closest('.o-mail-DiscussSidebarChannel-container');
            if (container && !container.closest('.o-wa-list')) {
                container.classList.remove('o-wa-hidden');
            }
        });
        document.querySelectorAll('.o-wa-sidebar-toggle .o-mail-DiscussSidebarCategory-icon').forEach((icon) => {
            const closing = !document.body.classList.contains('o-wa-open');
            icon.classList.toggle('oi-chevron-right', closing);
            icon.classList.toggle('oi-chevron-down', !closing);
            icon.classList.toggle('opacity-50', closing);
            icon.classList.toggle('opacity-100', !closing);
        });
        refreshBadge();
    }

    function bindToggle(root) {
        const btn = root.querySelector('.o-wa-sidebar-toggle .o-mail-DiscussSidebarCategory-toggler');
        if (!btn || btn._waBound) return;
        btn._waBound = true;
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const open = !document.body.classList.contains('o-wa-open');
            setWhatsappOpen(open);
            applyFilter();
        });
    }

    function observe() {
        const mo = new MutationObserver((mutations) => {
            let needsApply = false;
            mutations.forEach((m) => {
                (m.addedNodes || []).forEach((n) => {
                    if (!(n instanceof HTMLElement)) return;
                    bindToggle(n);
                    if (n.matches && (n.matches('.o-wa-channel-container') || n.querySelector?.('.o-wa-channel-container'))) {
                        needsApply = true;
                    }
                    // If a new discuss sidebar channel is added, check if it's WA and move it
                    if (n.matches && (n.matches('.o-mail-DiscussSidebarChannel-container') || n.querySelector?.('.o-mail-DiscussSidebarChannel-container'))) {
                        needsApply = true;
                    }
                });
            });
            if (needsApply) applyFilter();
        });
        mo.observe(document.body, { childList: true, subtree: true });
    }

    onReady(() => {
        bindToggle(document);
        applyFilter();
        observe();
        window.addEventListener('hashchange', applyFilter);
    });
})(); 