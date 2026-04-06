# Survey Image Extension

This module extends the Odoo Survey module to add image support for multiple-choice questions in the portal.

## Features

- Uses existing `value_image` field from survey question suggested answers
- Display images in portal for multiple-choice questions
- Images are displayed alongside text options in both internal and portal views
- Support for both single and multiple choice questions
- Images are also displayed in survey results/print mode
- **NEW**: Automatically stores selected answer images in survey responses
- **NEW**: Displays images in survey results and user input lines
- **NEW**: Support for multiple file attachments per question
- **NEW**: Each uploaded file is stored as a separate answer line for easy management
- **NEW**: Download functionality for individual files

## Installation

1. Copy this module to your Odoo addons directory
2. Update the app list in Odoo
3. Install the "Survey Image Extension" module

## Usage

1. Go to Surveys > Configuration > Surveys
2. Create or edit a survey
3. Add a multiple choice or simple choice question
4. In the suggested answers section, you'll now see the "Value Image" field (which was already available but not displayed in the portal)
5. Upload images for each answer option using the existing value_image field
6. The images will now be displayed in the portal when users take the survey

## Technical Details

- Uses existing `value_image` field from `survey.question.answer` model
- Extends `survey.user_input.line` model to store answer images (`answer_image` field)
- Inherits survey question templates to display images in portal
- Automatically copies images from suggested answers to user input lines when answers are selected
- Uses base64 encoding for image storage
- Images are displayed with responsive styling (max-width: 200px, max-height: 150px)
- Survey results now show both text answers and associated images

## Files Structure

```
survey_image_extension/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── survey_question_suggested_answer.py
│   └── survey_user_input_line.py
├── views/
│   ├── survey_question_views.xml
│   └── survey_templates.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Dependencies

- survey (Odoo Survey module)

## License

LGPL-3
