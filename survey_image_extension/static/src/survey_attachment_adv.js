/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Global storage for per-question files (used by template inline handlers)
window.surveyFiles = window.surveyFiles || {};

// Expose helpers globally to match template calls
window.addFile = function (event) {
    const input = event.target;
    const qid = input.dataset.qid;
    const files = (input && input.files) ? Array.from(input.files) : [];
    if (!qid || !files.length) {
        return;
    }
    if (!window.surveyFiles[qid]) {
        window.surveyFiles[qid] = [];
    }
    // Append all selected files
    files.forEach(f => window.surveyFiles[qid].push(f));
    window.renderFileList(qid);
    // reset input to allow re-adding same file name if needed
    input.value = '';
};

window.renderFileList = function (qid) {
    const list = document.getElementById(`file_list_${qid}`);
    if (!list) return;
    list.innerHTML = '';
    (window.surveyFiles[qid] || []).forEach((file, index) => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.innerHTML = `
            <span><i class="fa fa-file text-secondary me-2"></i>${file.name}</span>
            <button type="button" class="btn btn-sm btn-danger" onclick="removeFile(${index}, '${qid}')">
              <i class=\"fa fa-times\"></i>
            </button>
        `;
        list.appendChild(li);
    });
};

window.removeFile = function (index, qid) {
    if (!window.surveyFiles[qid]) return;
    window.surveyFiles[qid].splice(index, 1);
    window.renderFileList(qid);
};

// Ensure files in window.surveyFiles are included during submission
function extendSurveySubmit() {
    if (!publicWidget.registry.SurveyFormWidget) {
        setTimeout(extendSurveySubmit, 100);
        return;
    }

    publicWidget.registry.SurveyFormWidget.include({
        start: function () {
            // Setup drag-and-drop on enhanced upload areas
            this._setupDragAndDrop();
            return this._super.apply(this, arguments);
        },

        /**
         * Extend Odoo's _validateForm to add attachment question validation
         * This adds client-side validation for attachment questions before form submission
         * @override
         */
        _validateForm: function ($form, formData) {
            // Call parent validation first (validates all Odoo default question types)
            var isValid = this._super.apply(this, arguments);

            // If parent validation failed, return early (errors already shown by parent)
            if (!isValid) {
                return false;
            }

            // Add attachment question validation
            var errors = {};
            var inactiveQuestionIds = this.options.sessionInProgress ? [] : this._getInactiveConditionalQuestionIds();

            $form.find('[data-question-type="attachment"]').each(function () {
                var $questionWrapper = $(this).closest(".js_question-wrapper");
                var questionId = $questionWrapper.attr('id');

                // If question is inactive (conditional), skip validation
                if (inactiveQuestionIds.includes(parseInt(questionId))) {
                    return;
                }

                var questionRequired = $questionWrapper.data('required');
                var constrErrorMsg = $questionWrapper.data('constrErrorMsg');

                // Check if attachment question is mandatory and has files
                if (questionRequired) {
                    var files = window.surveyFiles[questionId] || [];
                    if (!files || files.length === 0) {
                        errors[questionId] = constrErrorMsg || "This question requires an answer";
                    }
                }
            });

            // If there are attachment errors, show them and return false
            if (Object.keys(errors).length > 0) {
                // Show attachment errors using custom handler (displays below file list)
                if (window.surveyAttachmentErrorHandler) {
                    window.surveyAttachmentErrorHandler({
                        error: 'validation',
                        fields: errors
                    });
                } else {
                    // Fallback to Odoo's default error display
                    this._showErrors(errors);
                }
                return false;
            }

            return true;
        },

        _setupDragAndDrop: function () {
            const self = this;
            this.$('.border-dashed').each(function () {
                const $zone = $(this);
                const $input = $zone.find('input[type="file"]');
                const qid = $input.data('qid');
                if (!qid) return;

                $zone.on('dragover.survey.attach', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    $zone.addClass('border-primary');
                });
                $zone.on('dragleave.survey.attach dragend.survey.attach', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    $zone.removeClass('border-primary');
                });
                $zone.on('drop.survey.attach', function (e) {
                    e.preventDefault();
                    e.stopPropagation();
                    $zone.removeClass('border-primary');
                    const dt = e.originalEvent && e.originalEvent.dataTransfer;
                    if (!dt || !dt.files || !dt.files.length) return;
                    if (!window.surveyFiles[qid]) {
                        window.surveyFiles[qid] = [];
                    }
                    Array.from(dt.files).forEach(f => window.surveyFiles[qid].push(f));
                    window.renderFileList(qid);
                });
            });
        },
        _onSubmit: function (ev) {
            // If there are no attachment questions using our enhanced UI, fall back
            const enhancedQuestions = this.$('[data-question-type="attachment"]').filter(function () {
                return $(this).find('[id^="file_input_"]').length > 0;
            });

            if (enhancedQuestions.length === 0) {
                return this._super(ev);
            }

            // Prevent default and build FormData with our files
            ev.preventDefault();
            ev.stopPropagation();

            if (this._isSubmitting) {
                return false;
            }

            // Run Odoo's client-side validation first (same as Odoo's default _submitForm does)
            const $form = this.$('form');
            const tempFormData = new FormData($form[0]);

            // Call Odoo's _validateForm method if available
            if (this._validateForm && typeof this._validateForm === 'function') {
                if (!this._validateForm($form, tempFormData)) {
                    // Validation failed, errors are already shown by _validateForm
                    return false;
                }
            }

            this._isSubmitting = true;
            this.$('input, textarea, select, button').prop('disabled', true);

            // Use Odoo's _prepareSubmitValues to get correctly formatted data
            // This handles date serialization, matrix structure, etc.
            const params = {};
            this._prepareSubmitValues(tempFormData, params);

            // Build FormData with our files and the prepared params
            const formData = new FormData();

            // Add prepared params to FormData
            Object.entries(params).forEach(([key, value]) => {
                if (typeof value === 'object' && value !== null) {
                    // Complex objects (like matrix answers) need to be serialized
                    // We prefix with JSON_DATA: so the controller knows to decode it
                    formData.append(key, 'JSON_DATA:' + JSON.stringify(value));
                } else {
                    formData.append(key, value);
                }
            });

            // Add selected files per question from window.surveyFiles
            enhancedQuestions.each((_, el) => {
                const $el = $(el);
                const qid = String($el.data('questionId'));

                // Note: Text answer is NOT handled by _prepareSubmitValues because 'attachment' is a custom type
                // So we must manually add it here
                const textVal = ($el.find('textarea').val() || '').toString();
                formData.append(qid, textVal);

                const files = window.surveyFiles[qid] || [];
                for (let i = 0; i < files.length; i++) {
                    formData.append(`attachment_${qid}_${i}`, files[i]);
                }
                if (files.length) {
                    formData.append(`attachment_${qid}_count`, files.length);
                }
            });

            const currentUrl = window.location.href;
            const submitUrl = currentUrl.replace('/survey/', '/survey/submit_with_files/');

            fetch(submitUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                }
            })
                .then(resp => resp.json())
                .then(data => {
                    console.log('Survey submit response (raw):', data);

                    // 🩹 Handle array responses from backend
                    if (Array.isArray(data)) {
                        data = data.find(d => d && d.error) || data[0] || {};
                    }

                    console.log('Survey submit response (normalized):', data);

                    // ✅ Handle validation errors
                    if (data && data.error === 'validation') {
                        console.log('Validation error detected — handling errors');

                        // Separate attachment errors from regular Odoo question errors
                        const attachmentErrors = {};
                        const regularErrors = {};

                        if (data.fields) {
                            Object.entries(data.fields).forEach(([qid, msg]) => {
                                const fileList = document.getElementById(`file_list_${qid}`);
                                if (fileList) {
                                    // This is an attachment question
                                    attachmentErrors[qid] = msg;
                                } else {
                                    // This is a regular Odoo question
                                    regularErrors[qid] = msg;
                                }
                            });
                        }

                        // Handle attachment errors with custom handler
                        if (Object.keys(attachmentErrors).length > 0 && window.surveyAttachmentErrorHandler) {
                            console.log('Handling attachment errors with custom handler');
                            window.surveyAttachmentErrorHandler({
                                error: 'validation',
                                fields: attachmentErrors
                            });
                        }

                        // Handle regular Odoo question errors using Odoo's default _showErrors method
                        if (Object.keys(regularErrors).length > 0) {
                            console.log('Handling regular Odoo question errors using Odoo default _showErrors');
                            // Call Odoo's default _showErrors method to display errors properly
                            if (this._showErrors && typeof this._showErrors === 'function') {
                                this._showErrors(regularErrors);
                            } else {
                                // Fallback: try to call parent's _showErrors
                                const parentWidget = this.constructor.prototype;
                                if (parentWidget._showErrors && typeof parentWidget._showErrors === 'function') {
                                    parentWidget._showErrors.call(this, regularErrors);
                                } else {
                                    console.warn('Could not find _showErrors method, errors may not display correctly');
                                }
                            }
                        }

                        // Re-enable form elements
                        this._isSubmitting = false;
                        this.$('input, textarea, select, button').prop('disabled', false);

                        // Fade in the form content (same as Odoo does in _onNextScreenDone)
                        this.$('.o_survey_form_content').fadeIn(0);

                        // Scroll to first error (same as Odoo does)
                        if (this._scrollToFirstError && typeof this._scrollToFirstError === 'function') {
                            this._scrollToFirstError();
                        }

                        return;
                    }

                    // ✅ Fallback generic error
                    if (data && data.error) {
                        alert(data.error);
                        return;
                    }

                    // ✅ Success flow
                    if (this._handleSuccess) {
                        this._handleSuccess(data);
                    } else {
                        window.location.reload();
                    }
                })

                .catch(err => {
                    alert('Submission failed: ' + (err && err.message ? err.message : err));
                })
                .finally(() => {
                    this._isSubmitting = false;
                    this.$('input, textarea, select, button').prop('disabled', false);
                });

            return false;
        },
    });
}

extendSurveySubmit();


