# WhatsApp Webhook Setup Guide

This guide explains how to set up the WhatsApp webhook integration to receive messages from customers.

## Overview

The WhatsApp integration allows you to:
1. Send messages to customers via WhatsApp
2. Receive replies from customers via webhook
3. View all conversations in a chat-like interface
4. Store message history for each customer

## Setup Instructions

### 1. Configure WhatsApp API Settings

1. Go to **Settings > General Settings > WhatsApp Integration**
2. Enable "Enable WhatsApp API Integration"
3. Select your API provider (Twilio or WhatsApp Business API)
4. Configure the provider-specific settings

### 2. Webhook URL Configuration

The webhook URL for your Odoo instance is:
```
https://your-odoo-domain.com/whatsapp/webhook
```

### 3. Twilio Setup (Recommended for testing)

1. Create a Twilio account at https://www.twilio.com
2. Get your Account SID and Auth Token from the Twilio Console
3. Purchase a WhatsApp-enabled phone number
4. Configure the webhook URL in your Twilio WhatsApp Sandbox:
   - Go to Twilio Console > Messaging > Try it out > Send a WhatsApp message
   - Set the webhook URL to: `https://your-odoo-domain.com/whatsapp/webhook`
   - Set the HTTP method to POST

### 4. WhatsApp Business API Setup

1. Apply for WhatsApp Business API access
2. Get your Business Token and Phone ID
3. Configure webhook in your WhatsApp Business API dashboard
4. Set the webhook URL to: `https://your-odoo-domain.com/whatsapp/webhook`

### 5. Testing the Integration

1. Send a message to a customer using the WhatsApp button
2. Ask the customer to reply to your message
3. Check the "WhatsApp Conversations" menu to see the received message
4. Open the conversation to view the chat interface

## Features

### Conversation Management
- **WhatsApp Conversations**: View all customer conversations
- **Chat Interface**: Real-time chat-like interface for each conversation
- **Message History**: All sent and received messages are stored
- **Customer Linking**: Automatically links conversations to customer records

### Message Types
- **Sent Messages**: Messages sent from Odoo (green bubbles)
- **Received Messages**: Messages received from customers (white bubbles)
- **Media Support**: Support for images, videos, audio, and documents

### Integration Points
- **Sales Orders**: Send order details via WhatsApp
- **Invoices**: Send invoice information via WhatsApp
- **Customer Portal**: Share documents via WhatsApp
- **Systray**: Quick access to WhatsApp messaging

## Troubleshooting

### Webhook Not Receiving Messages
1. Check if the webhook URL is correctly configured in your API provider
2. Verify that your Odoo instance is accessible from the internet
3. Check the Odoo logs for webhook errors
4. Test the webhook URL manually

### Messages Not Appearing in Conversations
1. Ensure the mobile number format is consistent
2. Check if the customer exists in your contacts
3. Verify the webhook is processing messages correctly
4. Check the conversation creation logic

### API Provider Issues
1. Verify your API credentials are correct
2. Check your API provider's documentation
3. Ensure your account has sufficient credits/access
4. Contact your API provider's support

## Security Considerations

1. **HTTPS Required**: Always use HTTPS for webhook URLs
2. **Authentication**: Consider implementing webhook authentication
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Data Privacy**: Ensure compliance with data protection regulations

## Customization

### Adding New API Providers
1. Extend the `whatsapp_api_provider` selection field
2. Add provider-specific configuration fields
3. Update the webhook processing logic in the controller
4. Test with your provider's webhook format

### Custom Message Processing
1. Override the `_process_single_message` method
2. Add custom message validation
3. Implement message filtering
4. Add custom message types

## Support

For technical support, please contact:
- Email: odoo@cybrosys.com
- Website: https://www.cybrosys.com

## License

This module is licensed under LGPL-3.0. 