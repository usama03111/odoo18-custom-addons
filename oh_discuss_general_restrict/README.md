# Discuss: General Channel Restrict Posting

**Category:** Discuss
**Version:** 18.0.1.0.0
**Author:** Codex

## Summary
General channel visible to all, only specific group can post

## Description
Keeps General channel visible to everyone while restricting posting rights to a defined security group.

## How It Works
This module provides the ability to make specific Odoo Discuss channels read-only for general users, while allowing designated admins or managers to post.
- **Settings Configuration**: In the general Odoo Settings, administrators can select one or more specific Discuss channels to mark as "Restricted Channels".
- **Permission Group**: A new security group named "Restricted Channel Posters" is added. 
- **Restricted Posting**: If a channel is marked as restricted, only users who belong to the "Restricted Channel Posters" group can successfully post messages in it. If a standard user attempts to send a message, they will receive an access error. This effectively keeps the channel history visible as a broadcast channel for the company.
