# 🔧 WhatsApp Webhook Setup & Troubleshooting Guide

## 🚨 **Problem**: Messages sent to WhatsApp but replies not received in CRM chatter

## 📋 **Step-by-Step Setup**

### **1. Check Odoo Settings**
Go to: `Settings > General Settings > WhatsApp` section

Make sure these are configured:
- ✅ **Access Token** - Your WhatsApp Business API access token
- ✅ **Phone Number ID** - Your WhatsApp phone number ID (not the actual phone number)
- ✅ **Webhook Verify Token** - A secret token you create (e.g., "mysecret123")
- ✅ **Webhook URL** - Should show: `https://yourdomain.com/whatsapp/webhook`

### **2. Configure Meta WhatsApp Business API Webhook**

1. Go to [Meta Developers Console](https://developers.facebook.com/)
2. Select your WhatsApp Business API app
3. Go to **Webhooks** section
4. Click **Add Callback URL**
5. Enter your webhook URL: `https://yourdomain.com/whatsapp/webhook`
6. Enter your **Verify Token** (same as in Odoo settings)
7. Select these fields to subscribe:
   - ✅ `messages`
   - ✅ `message_deliveries` 
   - ✅ `message_reads`

### **3. Test Webhook Endpoint**

Run the test script to verify your endpoint is accessible:

```bash
# Install requests if needed
pip install requests

# Run the test script
python test_webhook.py
```

**Expected Results:**
- ✅ GET request successful
- ✅ Verification test successful  
- ✅ POST test successful

### **4. Check Odoo Logs**

Look for webhook activity in your Odoo logs:

```bash
# Check Odoo logs for webhook activity
tail -f /var/log/odoo/odoo.log | grep -i webhook
```

**Look for these log messages:**
- "WhatsApp webhook called with method: POST"
- "Raw webhook data received: ..."
- "Processing message from ..."

## 🔍 **Troubleshooting Steps**

### **Step 1: Verify Webhook is Called**
1. Send a WhatsApp message from CRM
2. Have someone reply to your message
3. Check Odoo logs for webhook activity
4. If no logs, webhook is not being called by Meta

### **Step 2: Check Webhook URL Accessibility**
1. Your webhook URL must be accessible from the internet
2. Test: `curl https://yourdomain.com/whatsapp/webhook`
3. Should return a response (even if it's an error)

### **Step 3: Verify Phone Number Matching**
The webhook needs to find the correct CRM record. Check:

1. **Phone number format** in CRM record
2. **Phone number format** in WhatsApp message
3. **Webhook logs** showing phone number matching attempts

### **Step 4: Check Meta Webhook Status**
1. Go to Meta Developers Console
2. Check webhook status (should show "Active")
3. Check webhook logs for delivery attempts
4. Look for any error messages

## 🐛 **Common Issues & Solutions**

### **Issue 1: Webhook not being called**
**Symptoms:** No webhook logs in Odoo
**Solutions:**
- Verify webhook URL is correct in Meta
- Check webhook is subscribed to correct fields
- Ensure webhook status is "Active"

### **Issue 2: Webhook called but no messages processed**
**Symptoms:** Webhook logs show "Raw webhook data received" but no further processing
**Solutions:**
- Check webhook data structure matches expected format
- Verify phone number matching logic
- Check CRM record exists with matching phone

### **Issue 3: Phone number not found**
**Symptoms:** "No CRM record found for phone" in logs
**Solutions:**
- Ensure phone numbers are in same format
- Check both `phone` and `mobile` fields in CRM
- Verify phone number cleaning logic

### **Issue 4: Permission denied**
**Symptoms:** "Forbidden" or "Unauthorized" responses
**Solutions:**
- Check webhook verify token matches
- Ensure webhook endpoint is public (auth='public')
- Verify CSRF is disabled for webhook

## 📱 **Testing the Complete Flow**

### **Test 1: Send Message from CRM**
1. Go to a CRM lead/opportunity
2. Type a message in chatter
3. Click WhatsApp button
4. Verify message is sent to WhatsApp

### **Test 2: Receive Reply**
1. Have someone reply to your WhatsApp message
2. Check Odoo logs for webhook activity
3. Verify reply appears in CRM chatter
4. Check if new lead is created (for unknown numbers)

### **Test 3: Verify Phone Number Matching**
1. Check the phone number in your CRM record
2. Check the phone number in WhatsApp webhook data
3. Ensure they match after cleaning/formatting

## 🔧 **Debug Commands**

### **Check Webhook Route**
```bash
# Verify webhook route is registered
curl -X GET "https://yourdomain.com/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=test&hub.challenge=test"
```

### **Test with Sample Data**
```bash
# Test webhook with sample message
curl -X POST "https://yourdomain.com/whatsapp/webhook" \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"id":"test","changes":[{"value":{"messages":[{"from":"919876543210","type":"text","text":{"body":"test"}}]}}]}]}'
```

## 📞 **Need Help?**

If you're still having issues:

1. **Check Odoo logs** for detailed error messages
2. **Run the test script** to verify endpoint accessibility
3. **Verify Meta webhook configuration** is correct
4. **Check phone number formats** match between CRM and WhatsApp
5. **Ensure webhook URL** is accessible from the internet

The enhanced logging in the webhook controller should now give you much more detailed information about what's happening when messages arrive.
