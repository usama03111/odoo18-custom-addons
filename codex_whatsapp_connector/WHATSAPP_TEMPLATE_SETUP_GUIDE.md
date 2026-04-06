# WhatsApp Template Setup Guide

## Problem Description
When sending the **first message** to a customer via WhatsApp Business API:
- The message appears to be sent successfully (200 response)
- But the customer doesn't receive it
- After the customer sends a message first, both parties can send/receive messages normally

## Root Cause
This happens due to Meta's **24-hour messaging window** policy:
- Businesses can only send **free-form messages** to customers who have:
  1. **Messaged you first** within the last 24 hours, OR
  2. **Opted in** to receive messages from you
- For the first contact, you **MUST** use an **approved message template**

## Solution Implemented
The system now automatically:
1. **Checks conversation status** before sending messages
2. **Uses templates** for first contact (when customer hasn't messaged within 24 hours)
3. **Uses free-form messages** for ongoing conversations (within 24-hour window)

## Setup Steps

### 1. Create WhatsApp Template in Meta Business Manager
1. Go to [Meta Business Manager](https://business.facebook.com/)
2. Navigate to **WhatsApp > Message Templates**
3. Click **Create Template**
4. Choose template type (usually **Text** or **Interactive**)
5. Design your template with placeholders for dynamic content
6. Submit for approval (usually takes 24-48 hours)

**Example Template:**
```
Template Name: customer_support
Language: English (US)
Category: Customer Care
Content: Hello! Thank you for contacting us. How can we help you today? {{1}}

Parameters:
- {{1}}: Your custom message (limited to 100 characters)
```

### 2. Configure Template in Odoo Settings
1. Go to **Settings > WhatsApp**
2. In **Message Template Configuration** section:
   - **Template Name**: Enter your approved template name (e.g., `customer_support`)
   - **Template Language**: Enter language code (e.g., `en_US`)

### 3. Test the Solution
1. **First Contact**: Send message to a new customer
   - System will automatically use the template
   - Customer will receive the message
   - Message will be marked as "(Sent as template: template_name)"

2. **Ongoing Conversation**: Send message within 24 hours
   - System will use free-form messages
   - Customer will receive messages normally

## Template Requirements

### Meta Template Approval Criteria
- **Clear purpose**: Customer service, order updates, etc.
- **Professional language**: No spam or promotional content
- **Opt-out option**: Include unsubscribe instructions
- **Relevant content**: Must be related to customer's inquiry

### Template Types
1. **Text Templates**: Simple text messages
2. **Interactive Templates**: Buttons, quick replies
3. **Media Templates**: Images, documents, videos

## Troubleshooting

### Common Issues
1. **Template Not Approved**
   - Check approval status in Meta Business Manager
   - Ensure template meets Meta's guidelines
   - Wait for approval (24-48 hours typical)

2. **Template Name Mismatch**
   - Verify template name exactly matches Meta's approval
   - Check for typos or extra spaces
   - Ensure language code matches

3. **Customer Still Not Receiving Messages**
   - Verify phone number format (remove +, spaces, etc.)
   - Check if customer has blocked your number
   - Ensure customer's phone supports WhatsApp

### Debug Information
The system now provides:
- **Message type indication**: Shows if message was sent as template or free-form
- **Conversation status check**: New endpoint `/whatsapp/check_conversation_status`
- **Detailed logging**: All API calls and responses are logged

## API Endpoints

### Send Message
```
POST /whatsapp/send_message
{
    "res_model": "crm.lead",
    "res_id": 123,
    "message": "Hello, how can I help you?"
}
```

### Check Conversation Status
```
POST /whatsapp/check_conversation_status
{
    "phone_number": "1234567890",
    "partner_id": 456
}
```

## Best Practices

1. **Template Design**
   - Keep messages concise and professional
   - Use clear call-to-action
   - Include your business name

2. **Customer Experience**
   - Respond quickly to customer messages
   - Use templates only when necessary
   - Provide value in every interaction

3. **Monitoring**
   - Check delivery status regularly
   - Monitor customer responses
   - Track template effectiveness

## Support
If you continue experiencing issues:
1. Check Meta Business Manager for template status
2. Verify all configuration settings
3. Test with Meta's WhatsApp Business API testing tools
4. Contact Meta support for API-related issues

## Technical Notes
- Template messages are limited to 100 characters for dynamic content
- Free-form messages have no character limit
- 24-hour window resets after each customer message
- System automatically detects conversation status 