console.log('survey_attachment_error.js loaded, handler being defined');
window.surveyAttachmentErrorHandler = function (responseJson) {
    console.log('[AttachmentErrorHandler]: Handler invoked with:', responseJson);
    if (responseJson && responseJson.error === 'validation' && responseJson.fields) {
        // Remove old attachment-specific errors (file_error_*)
        document.querySelectorAll('[id^=file_error_]').forEach(n => n.remove());
        // Remove fallback/global box if present
        let topErrorBox = document.getElementById('survey_attachment_global_error_box');
        if (topErrorBox) topErrorBox.remove();

        let anyVisible = false;
        // Render new errors - ONLY for attachment questions
        Object.entries(responseJson.fields).forEach(([qid, msg]) => {
            console.log(`[AttachmentErrorHandler]: Handling qid=`, qid, 'msg=', msg);

            // Only handle attachment questions - check for file list
            const fileList = document.getElementById(`file_list_${qid}`);
            let errorNode = document.getElementById(`file_error_${qid}`);

            if (fileList) {
                // This is an attachment question - display error below file list
                console.log(`[AttachmentErrorHandler]: Found fileList #file_list_${qid} (attachment question)`);
                if (!errorNode) {
                    errorNode = document.createElement('div');
                    errorNode.id = `file_error_${qid}`;
                    errorNode.className = 'alert alert-danger mt-2';
                    errorNode.setAttribute('role', 'alert');
                    if (fileList.parentElement) {
                        fileList.parentElement.appendChild(errorNode);
                        anyVisible = true;
                        console.log(`[AttachmentErrorHandler]: Error message placed below #file_list_${qid}`);
                    }
                }
                errorNode.textContent = msg;
            } else {
                // This is NOT an attachment question - skip it, let Odoo handle it
                console.log(`[AttachmentErrorHandler]: Skipping qid ${qid} - not an attachment question, Odoo will handle it`);
            }
        });

        // Alert if no attachment errors were placed
        if (!anyVisible) {
            console.log('[AttachmentErrorHandler]: No attachment errors to display.');
        } else {
            console.log('[AttachmentErrorHandler]: Attachment error(s) displayed.');
        }
    } else {
        console.log('[AttachmentErrorHandler]: No validation error fields present, nothing to show.');
    }
};