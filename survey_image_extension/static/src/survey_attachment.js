/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

function extendSurveyFormWidget() {
    if (!publicWidget.registry.SurveyFormWidget) {
        setTimeout(extendSurveyFormWidget, 100);
        return;
    }

    publicWidget.registry.SurveyFormWidget.include({
        start: function() {
            this._addMultipleChoiceEventDelegation();
            return this._super();
        },

        _addMultipleChoiceEventDelegation: function() {
            this.$el.off('click.survey.multiplechoice').on('click.survey.multiplechoice', '.o_survey_question_multiple_choice .o_survey_choice_btn', function(ev) {
                ev.preventDefault();
                ev.stopPropagation();
                const $choice = $(this);
                const $input = $choice.find('input[type="checkbox"]');
                if ($input.length) {
                    $input.prop('checked', !$input.prop('checked'));
                    if ($input.prop('checked')) {
                        $choice.addClass('o_survey_choice_selected');
                        $choice.find('.fa-square-o').hide();
                        $choice.find('.fa-check-square').show();
                    } else {
                        $choice.removeClass('o_survey_choice_selected');
                        $choice.find('.fa-square-o').show();
                        $choice.find('.fa-check-square').hide();
                    }
                    $input.trigger('change');
                }
            });

            this.$el.off('change.survey.multiplechoice').on('change.survey.multiplechoice', '.o_survey_question_multiple_choice input[type="checkbox"]', function() {
                const $input = $(this);
                const $choice = $input.closest('.o_survey_choice_btn');
                if ($input.prop('checked')) {
                    $choice.addClass('o_survey_choice_selected');
                    $choice.find('.fa-square-o').hide();
                    $choice.find('.fa-check-square').show();
                } else {
                    $choice.removeClass('o_survey_choice_selected');
                    $choice.find('.fa-square-o').show();
                    $choice.find('.fa-check-square').hide();
                }
            });
        },
    });
}

extendSurveyFormWidget();