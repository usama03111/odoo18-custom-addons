console.log('=== WHATSAPP MODULE LOADED ===');

(function () {
    const onReady = (fn) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    };

    function getComposerText(buttonEl) {
        const composer = buttonEl.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread');
        if (!composer) return '';
        const input = composer.querySelector('textarea, [contenteditable="true"], .o-mail-Composer-input');
        if (input) {
            return input.value || input.textContent || '';
        }
        return '';
    }

    // Check if there are any attachment elements in the composer
    function hasAttachmentElements(buttonEl) {
        const composer = buttonEl.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread');
        if (!composer) {
            // Global composer list as last resort (some UI renders outside the local subtree)
            const globalList = document.querySelector('.o-mail-AttachmentList.o-inComposer');
            if (globalList && globalList.querySelector('[data-mimetype], .o-mail-AttachmentCard-image, .o-mail-AttachmentImage, .o-mail-Attachment')) {
                return true;
            }
            return false;
        }

        // Look for the attachment list container
        const attachmentList = composer.querySelector('.o-mail-AttachmentList');
        if (attachmentList) {
            const attachmentElements = attachmentList.querySelectorAll('.o-mail-AttachmentImage, .o-mail-Attachment, [data-mimetype], .o-mail-AttachmentCard-image, .o-mail-AttachmentCard');
            if (attachmentElements.length > 0) {
                return true;
            }
        }

        // Also check for direct attachment elements
        const directAttachments = composer.querySelectorAll('.o-mail-AttachmentImage, .o-mail-Attachment, [data-mimetype], .o-mail-AttachmentCard-image, .o-mail-AttachmentCard');
        if (directAttachments.length > 0) {
            return true;
        }

        // Extra check for audio UI (voice notes) that may not expose attachment data attributes yet
        const audioUi = composer.querySelector('audio, .o-mail-Composer-audio, .o-Composer-audio, [data-mimetype^="audio/"], .o-mail-VoicePlayer');
        if (audioUi) {
            return true;
        }

        // Global fallback again
        const globalList = document.querySelector('.o-mail-AttachmentList.o-inComposer');
        if (globalList && globalList.querySelector('[data-mimetype], .o-mail-AttachmentCard-image, .o-mail-AttachmentImage, .o-mail-Attachment, .o-mail-AttachmentCard')) {
            return true;
        }

        return false;
    }

    // Show loading indicator on the button
    function showLoading(buttonEl) {
        const originalText = buttonEl.innerHTML;
        buttonEl.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Sending...';
        buttonEl.disabled = true;
        return originalText;
    }

    // Hide loading indicator
    function hideLoading(buttonEl, originalText) {
        buttonEl.innerHTML = originalText;
        buttonEl.disabled = false;
    }

    function sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    // Clear all attachments from composer
    function clearAllAttachments(composer) {
        // Clear local attachment list
            const attachmentList = composer.querySelector('.o-mail-AttachmentList');
            if (attachmentList) {
            const attachmentCards = attachmentList.querySelectorAll('.o-mail-AttachmentCard, .o-mail-AttachmentImage, [data-mimetype][role="menuitem"], .o-mail-Attachment, [data-mimetype]');
            attachmentCards.forEach(card => {
                try {
                    card.remove();
                        } catch (e) {
                    console.warn('Failed to remove attachment card:', e);
                }
            });
            
            if (attachmentList.children.length === 0) {
                attachmentList.style.display = 'none';
            }
        }

        // Clear global attachment list
        const globalAttachmentList = document.querySelector('.o-mail-AttachmentList.o-inComposer');
        if (globalAttachmentList) {
            const globalCards = globalAttachmentList.querySelectorAll('.o-mail-AttachmentCard, .o-mail-AttachmentImage, [data-mimetype][role="menuitem"], .o-mail-Attachment, [data-mimetype]');
            globalCards.forEach(card => {
                try {
                    card.remove();
                            } catch (e) {
                    console.warn('Failed to remove global attachment card:', e);
                }
            });
            
            if (globalAttachmentList.children.length === 0) {
                globalAttachmentList.style.display = 'none';
            }
        }

        // Trigger composer update events
        try {
            const composerInput = composer.querySelector('textarea, [contenteditable="true"], .o-mail-Composer-input');
            if (composerInput) {
                composerInput.dispatchEvent(new Event('input', { bubbles: true }));
                composerInput.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            } catch (e) {
            console.warn('Failed to trigger composer update events:', e);
        }
    }

    // Get the newest attachment from composer DOM by attachment id only
    async function getAttachmentFromComposer(buttonEl, ctx) {
        try {
            const composer = buttonEl.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread');
            if (!composer) return null;

            const attachmentList = composer.querySelector('.o-mail-AttachmentList');
            if (!attachmentList) return null;

            // Prefer the last attachment element (card or image)
            const candidates = attachmentList.querySelectorAll('.o-mail-AttachmentCard, .o-mail-AttachmentImage, [data-mimetype][role="menuitem"]');
            if (!candidates.length) return null;
            const lastEl = candidates[candidates.length - 1];

            // Try to resolve id from common attributes on the element or its children
            const idAttr = lastEl.getAttribute('data-attachment-id')
                || lastEl.getAttribute('data-id')
                || (lastEl.dataset && (lastEl.dataset.attachmentId || lastEl.dataset.id));
            if (idAttr) {
                const attachmentId = parseInt(idAttr, 10);
                if (!Number.isNaN(attachmentId)) {
                    return await readAttachmentFields(attachmentId);
                }
            }

            // Try child elements for data attributes
            const childWithId = lastEl.querySelector('[data-attachment-id], [data-id]');
            if (childWithId) {
                const idAttr2 = childWithId.getAttribute('data-attachment-id') || childWithId.getAttribute('data-id');
                const attachmentId2 = parseInt(idAttr2 || '', 10);
                if (!Number.isNaN(attachmentId2)) {
                    return await readAttachmentFields(attachmentId2);
                }
            }

            // Try to extract id from embedded download URL (in aside button within a card)
            const dlBtn = (lastEl.closest('.o-mail-AttachmentCard') || lastEl).querySelector('[data-download-url]');
            const dlUrl = dlBtn && (dlBtn.getAttribute('data-download-url') || dlBtn.dataset && dlBtn.dataset.downloadUrl);
            if (dlUrl) {
                // Common patterns: /web/content/<id> or query param id=<id>
                let match = dlUrl.match(/\/web\/content\/(\d+)/);
                if (!match) {
                    const urlObj = (()=>{ try { return new URL(dlUrl, window.location.origin); } catch(e){ return null; } })();
                    if (urlObj) {
                        const qId = urlObj.searchParams.get('id') || urlObj.searchParams.get('res_id') || urlObj.searchParams.get('attachment_id');
                        if (qId) match = [null, qId];
                    }
                }
                if (match && match[1]) {
                    const parsedId = parseInt(match[1], 10);
                    if (!Number.isNaN(parsedId)) {
                        return await readAttachmentFields(parsedId);
                    }
                }
            }

            // Name + mimetype based resolution (covers images/documents rendered without ids)
            const inferredName = (lastEl.getAttribute('title') || lastEl.getAttribute('aria-label')) || getLastComposerAttachmentName(buttonEl);
            const inferredMime = (lastEl.getAttribute('data-mimetype') || (lastEl.dataset && lastEl.dataset.mimetype)) || getLastComposerAttachmentMime(buttonEl) || '';
            if (ctx && inferredName) {
                // Try exact filename first, then filename+mime prefix
                const byName = await searchAttachmentByNameInContext(ctx, inferredName);
                if (byName) return byName;
                if (inferredMime) {
                    const prefix = inferredMime.toLowerCase().split('/')[0] + '/%';
                    const byNameMime = await searchAttachmentByNameAndMimeInContext(ctx, inferredName, prefix);
                    if (byNameMime) return byNameMime;
                }
            }

            // As a final step, directly query attachments by inferred mimetype within the current context
            if (ctx) {
                // Prefer exact filename match if available
                if (inferredName) {
                    const byName2 = await searchAttachmentByNameInContext(ctx, inferredName);
                    if (byName2) return byName2;
                }
                // If mimetype indicates image/video/document, search by that prefix only (never wildcard to avoid picking old audio)
                const lower = inferredMime.toLowerCase();
                if (lower.startsWith('image/')) {
                    const foundImg = await searchRecentAttachmentByMimeAndContext(ctx, 'image/%', true);
                    if (foundImg) return foundImg;
                } else if (lower.startsWith('video/')) {
                    const foundVid = await searchRecentAttachmentByMimeAndContext(ctx, 'video/%', true);
                    if (foundVid) return foundVid;
                } else if (lower.startsWith('application/')) {
                    const foundDoc = await searchRecentAttachmentByMimeAndContext(ctx, 'application/%', true);
                    if (foundDoc) return foundDoc;
                } else if (lower.startsWith('text/')) {
                    const foundTxt = await searchRecentAttachmentByMimeAndContext(ctx, 'text/%', true);
                    if (foundTxt) return foundTxt;
                }
                // As a last resort for non-audio types, pick latest non-audio in the thread
                const nonAudio = await searchLatestNonAudioInContext(ctx);
                if (nonAudio) return nonAudio;
            }

            // If we cannot resolve an id, return null (we will rely on recent-loose-audio fallback)
            return null;
        } catch (error) {
            console.error('Error reading attachment from composer:', error);
            return null;
        }
    }

    // Search most recent attachment by mime prefix for the current thread/composer context
    async function searchRecentAttachmentByMimeAndContext(ctx, mimelike, excludeAudio) {
        try {
            const domain = [
                ['mimetype', 'ilike', mimelike || '%'],
                ['res_model', 'in', [ctx.model, 'mail.compose.message', 'discuss.channel']],
                ['res_id', 'in', [ctx.id, 0]],
            ];
            if (excludeAudio) {
                domain.push(['mimetype', 'not ilike', 'audio/%']);
            }
            const payload = {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.attachment',
                    method: 'search_read',
                    args: [],
                    kwargs: {
                        domain: domain,
                        fields: ['id', 'name', 'mimetype', 'datas', 'create_date', 'res_model', 'res_id'],
                        order: 'create_date desc, id desc',
                        limit: 5,
                    },
                },
            };
            const res = await fetch('/web/dataset/call_kw/ir.attachment/search_read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            const recs = (data && data.result) || [];
            if (!recs.length) return null;
            // Prefer attachments created in last 5 minutes
            const now = new Date();
            const cutoff = new Date(now.getTime() - 5 * 60 * 1000);
            return recs.find(att => new Date(att.create_date) >= cutoff) || recs[0];
        } catch (e) {
            console.warn('searchRecentAttachmentByMimeAndContext failed', e);
            return null;
        }
    }

    // Exact filename match inside current thread/composer contexts
    async function searchAttachmentByNameInContext(ctx, filename) {
        try {
            const payload = {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.attachment',
                    method: 'search_read',
                    args: [],
                    kwargs: {
                        domain: [
                            ['name', '=', filename],
                            ['res_model', 'in', [ctx.model, 'mail.compose.message', 'discuss.channel']],
                            ['res_id', 'in', [ctx.id, 0]],
                        ],
                        fields: ['id', 'name', 'mimetype', 'datas', 'create_date', 'res_model', 'res_id'],
                        order: 'create_date desc, id desc',
                        limit: 3,
                    },
                },
            };
            const res = await fetch('/web/dataset/call_kw/ir.attachment/search_read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            const recs = (data && data.result) || [];
            if (!recs.length) return null;
                return recs[0];
        } catch (e) {
            console.warn('searchAttachmentByNameInContext failed', e);
            return null;
        }
    }

    // Filename + mime prefix match inside current context
    async function searchAttachmentByNameAndMimeInContext(ctx, filename, mimelike) {
        try {
            const payload = {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.attachment',
                    method: 'search_read',
                    args: [],
                    kwargs: {
                        domain: [
                            ['name', '=', filename],
                            ['mimetype', 'ilike', mimelike],
                            ['res_model', 'in', [ctx.model, 'mail.compose.message', 'discuss.channel']],
                            ['res_id', 'in', [ctx.id, 0]],
                        ],
                        fields: ['id', 'name', 'mimetype', 'datas', 'create_date', 'res_model', 'res_id'],
                        order: 'create_date desc, id desc',
                        limit: 3,
                    },
                },
            };
            const res = await fetch('/web/dataset/call_kw/ir.attachment/search_read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            const recs = (data && data.result) || [];
            if (!recs.length) return null;
            return recs[0];
        } catch (e) {
            console.warn('searchAttachmentByNameAndMimeInContext failed', e);
            return null;
        }
    }

    // Latest non-audio attachment in the current thread contexts
    async function searchLatestNonAudioInContext(ctx) {
        try {
            const payload = {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.attachment',
                    method: 'search_read',
                    args: [],
                    kwargs: {
                        domain: [
                            ['mimetype', 'not ilike', 'audio/%'],
                            ['res_model', 'in', [ctx.model, 'mail.compose.message', 'discuss.channel']],
                            ['res_id', 'in', [ctx.id, 0]],
                        ],
                        fields: ['id', 'name', 'mimetype', 'datas', 'create_date', 'res_model', 'res_id'],
                        order: 'create_date desc, id desc',
                        limit: 5,
                    },
                },
            };
            const res = await fetch('/web/dataset/call_kw/ir.attachment/search_read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            const recs = (data && data.result) || [];
            if (!recs.length) return null;
            return recs[0];
        } catch (e) {
            console.warn('searchLatestNonAudioInContext failed', e);
            return null;
        }
    }

    // Inspect last composer attachment card to infer its mimetype (best-effort)
    function getLastComposerAttachmentMime(buttonEl) {
        try {
        const composer = buttonEl.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread');
            if (!composer) return null;
            const attachmentList = composer.querySelector('.o-mail-AttachmentList');
            if (!attachmentList) return null;
            const cards = attachmentList.querySelectorAll('.o-mail-AttachmentCard');
            if (!cards.length) return null;
            const lastCard = cards[cards.length - 1];
            const mimeFromCard = lastCard.getAttribute('data-mimetype')
                || (lastCard.dataset && lastCard.dataset.mimetype);
            if (mimeFromCard) return mimeFromCard;
            const child = lastCard.querySelector('[data-mimetype]');
            if (child) return child.getAttribute('data-mimetype');
            // Heuristic: presence of voice player implies audio
            if (lastCard.querySelector('.o-mail-VoicePlayer, audio')) return 'audio/*';
            return null;
        } catch (e) {
            return null;
        }
    }

    // Extract last composer attachment display name (best-effort)
    function getLastComposerAttachmentName(buttonEl) {
        try {
            const composer = buttonEl.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread');
            if (!composer) return null;
            const attachmentList = composer.querySelector('.o-mail-AttachmentList');
            if (!attachmentList) return null;
            const cards = attachmentList.querySelectorAll('.o-mail-AttachmentCard');
            if (!cards.length) return null;
            const lastCard = cards[cards.length - 1];
            const name = lastCard.getAttribute('title') || lastCard.getAttribute('aria-label');
            if (name && name !== 'Preview') return name;
            const child = lastCard.querySelector('[title], [aria-label]');
            const childName = child && (child.getAttribute('title') || child.getAttribute('aria-label'));
            if (childName && childName !== 'Preview') return childName;
            return null;
        } catch (e) {
            return null;
        }
    }

    async function rpc(route, params) {
        const payload = { jsonrpc: '2.0', method: 'call', params: params || {} };
        const body = JSON.stringify(payload);
        const csrf = (window.odoo && window.odoo.csrf_token) ? window.odoo.csrf_token : (document.cookie.match(/csrftoken=([^;]+)/) || [])[1];
        const headers = { 'Content-Type': 'application/json' };
        if (csrf) headers['X-CSRFToken'] = csrf;
        const res = await fetch(route, {
            method: 'POST',
            headers,
            body,
            credentials: 'include'
        });
        const data = await res.json();
        return data;
    }

    async function readAttachmentFields(attachmentId) {
        const payload = {
            jsonrpc: '2.0',
            method: 'call',
            params: {
                model: 'ir.attachment',
                method: 'read',
                args: [[attachmentId], ['id', 'name', 'mimetype', 'datas']],
                kwargs: {},
            },
        };
        const res = await fetch('/web/dataset/call_kw/ir.attachment/read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        const recs = data && data.result;
        if (Array.isArray(recs) && recs.length) return recs[0];
        throw new Error('Could not read attachment');
    }

    // Heuristic: very recent audio attachments not yet linked to thread (single lookup)
    async function findRecentLooseAudioAttachment(sinceClickMs) {
        try {
            const payload = {
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    model: 'ir.attachment',
                    method: 'search_read',
                    args: [],
                    kwargs: {
                        domain: [
                            ['mimetype', 'ilike', 'audio/%']
                        ],
                        fields: ['id', 'name', 'mimetype', 'datas', 'create_date', 'res_model', 'res_id'],
                        order: 'create_date desc',
                        limit: 5,
                    },
                },
            };
            const res = await fetch('/web/dataset/call_kw/ir.attachment/search_read', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            const recs = (data && data.result) || [];
            if (!recs.length) return null;
            const windowStart = sinceClickMs ? new Date(sinceClickMs - 2 * 60 * 1000) : new Date(Date.now() - 10 * 60 * 1000);
            const preferred = recs.find(att => new Date(att.create_date) >= windowStart && (att.res_model === 'mail.compose.message' || att.res_model === 'discuss.channel'))
                || recs.find(att => new Date(att.create_date) >= windowStart)
                || recs[0];
            return preferred;
        } catch (error) {
            console.error('Error searching heuristic recent audio attachment:', error);
            return null;
        }
    }

    async function onClick(e) {
        const btn = e.target.closest('.o_whatsapp_send_btn');
        if (!btn) return;
        e.preventDefault();

        console.log('=== WHATSAPP BUTTON CLICKED ===');

        const ctx = (window.codexWhatsApp && window.codexWhatsApp.getThreadContext)
            ? window.codexWhatsApp.getThreadContext(btn)
            : null;
        if (!ctx) {
            console.warn('WhatsApp: cannot determine thread context');
            alert('Could not determine the record context. Please refresh the page and try again.');
            return;
        }

        const text = getComposerText(btn).trim();
        const hasAttachments = hasAttachmentElements(btn);

        // If no attachments but voice UI detected, wait briefly to let upload finalize and re-check
        if (!hasAttachments) {
            const composer = btn.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread') || document;
            const hasVoiceUi = !!composer.querySelector('.o-mail-VoicePlayer, [data-mimetype^="audio/"], .o-mail-AttachmentCard-image');
            if (hasVoiceUi) {
                await sleep(2500);
            }
        }
        const hasAttachmentsAfterWait = hasAttachmentElements(btn);
        const effectiveHasAttachments = hasAttachments || hasAttachmentsAfterWait;

        // Show loading indicator
        const originalButtonText = showLoading(btn);

        const sendText = async () => {
            return rpc('/whatsapp/send_message', { res_model: ctx.model, res_id: ctx.id, message: text });
        };

        const clickTimeMs = Date.now();

        const sendMedia = async (useTextAsCaption = false) => {
            // Try strict DOM-based attachment first
            if (effectiveHasAttachments) {
                const att = await getAttachmentFromComposer(btn, ctx);
                if (att) {
                    const filename = att.name || 'file';
                    const mimetype = att.mimetype || 'application/octet-stream';
                    const data_base64 = att.datas;
                    const caption = useTextAsCaption ? text : '';
                    return rpc('/whatsapp/send_media', { res_model: ctx.model, res_id: ctx.id, filename, mimetype, data_base64, caption });
                }
                // If we could not resolve the attachment by id, only fall back to recent voice if the last card looks like audio
                const inferredMime = getLastComposerAttachmentMime(btn) || '';
                const isLikelyAudio = inferredMime.toLowerCase().startsWith('audio/') || inferredMime === 'audio/*';
                if (isLikelyAudio) {
                    const recentLooseAudio = await findRecentLooseAudioAttachment(clickTimeMs);
                    if (recentLooseAudio) {
                        const filename = recentLooseAudio.name || 'voice.ogg';
                        const mimetype = recentLooseAudio.mimetype || 'audio/ogg';
                        const data_base64 = recentLooseAudio.datas;
                const caption = useTextAsCaption ? text : '';
                return rpc('/whatsapp/send_media', { res_model: ctx.model, res_id: ctx.id, filename, mimetype, data_base64, caption });
            }
                }
            }

            // If no attachment elements found in DOM, don't try to send media
            throw new Error('No attachment found in composer');
        };

        // Determine what to send based on what's available
        let doSend;
        if (effectiveHasAttachments && text) {
            // Send media with text as caption
            doSend = () => sendMedia(true);
        } else if (effectiveHasAttachments) {
            doSend = sendMedia;
        } else if (text) {
            doSend = sendText;
        } else {
            hideLoading(btn, originalButtonText);
            alert('Please enter a message or attach a file before sending.');
            return;
        }

        doSend()
            .then((result) => {
                if (result && result.result && result.result.success) {
                    // Clear composer only when send succeeded
                    const composer = btn.closest('.o-mail-ThreadView, .o-mail-Composer, .o-mail-Thread');
                    if (composer) {
                        const input = composer.querySelector('textarea, [contenteditable="true"], .o-mail-Composer-input');
                        if (input) {
                            if ('value' in input) input.value = '';
                            if ('textContent' in input) input.textContent = '';
                        }
                        const inputFile = composer.querySelector('input[type="file"]');
                        if (inputFile) inputFile.value = '';
                        
                        // Clear attachments
                        clearAllAttachments(composer);
                    }
                    hideLoading(btn, originalButtonText);
                    const messageType = result.result.message_type || 'message';
                    alert('WhatsApp ' + messageType + ' sent successfully!');
                } else if (result && (result.error || (result.result && result.result.error))) {
                    const error = result.error || result.result.error;
                    const errorMsg = error ? (error.message || error.data || JSON.stringify(error)) : 'Unknown error';
                    hideLoading(btn, originalButtonText);
                    alert('Failed to send WhatsApp message: ' + errorMsg);
                }
            })
            .catch((err) => {
                console.error('WhatsApp send error:', err);
                hideLoading(btn, originalButtonText);
                alert('Failed to send WhatsApp message. Check console for details.');
            });
    }

    onReady(() => {
        document.addEventListener('click', onClick, true);
        console.log('WhatsApp button handler initialized');
    });
})();
