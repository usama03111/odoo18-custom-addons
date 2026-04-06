#!/usr/bin/env python3
"""
WhatsApp Webhook Test Script

This script helps you test the WhatsApp webhook functionality.
Run this script to send a test message to your webhook endpoint.
"""

import requests
import json
import sys

def test_twilio_webhook(webhook_url, from_number="+1234567890", message="Hello from test script"):
    """Test webhook with Twilio format"""
    data = {
        "From": f"whatsapp:{from_number}",
        "Body": message,
        "MessageSid": "test_message_sid_123",
        "To": "whatsapp:+1234567890"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(webhook_url, data=data, headers=headers)
        print(f"Twilio Test Response: {response.status_code}")
        print(f"Response Text: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing Twilio webhook: {e}")
        return False

def test_whatsapp_business_webhook(webhook_url, from_number="1234567890", message="Hello from test script"):
    """Test webhook with WhatsApp Business API format"""
    data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
                                "phone_number_id": "123456789"
                            },
                            "messages": [
                                {
                                    "from": from_number,
                                    "id": "test_message_id_123",
                                    "timestamp": "1234567890",
                                    "text": {
                                        "body": message
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(webhook_url, json=data, headers=headers)
        print(f"WhatsApp Business Test Response: {response.status_code}")
        print(f"Response Text: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing WhatsApp Business webhook: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_webhook.py <webhook_url> [provider] [from_number] [message]")
        print("Example: python test_webhook.py https://your-odoo-domain.com/whatsapp/webhook twilio +1234567890 'Hello from test'")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    provider = sys.argv[2] if len(sys.argv) > 2 else "twilio"
    from_number = sys.argv[3] if len(sys.argv) > 3 else "+1234567890"
    message = sys.argv[4] if len(sys.argv) > 4 else "Hello from test script"
    
    print(f"Testing webhook: {webhook_url}")
    print(f"Provider: {provider}")
    print(f"From: {from_number}")
    print(f"Message: {message}")
    print("-" * 50)
    
    success = False
    
    if provider.lower() == "twilio":
        success = test_twilio_webhook(webhook_url, from_number, message)
    elif provider.lower() == "whatsapp_business":
        success = test_whatsapp_business_webhook(webhook_url, from_number, message)
    else:
        print(f"Unknown provider: {provider}")
        print("Supported providers: twilio, whatsapp_business")
        sys.exit(1)
    
    if success:
        print("\n✅ Webhook test successful!")
        print("Check your Odoo WhatsApp Conversations to see the test message.")
    else:
        print("\n❌ Webhook test failed!")
        print("Check your webhook URL and Odoo logs for errors.")

if __name__ == "__main__":
    main() 