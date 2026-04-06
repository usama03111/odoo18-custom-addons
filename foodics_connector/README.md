# Foodics Connector

**Category:** Tools
**Version:** 18.0.1.0.0
**Author:** usama

## Summary
Foodics OAuth 2.0 Integration

## Description
Foodics OAuth 2.0 Connector
===========================
This module handles the OAuth 2.0 Authorization Code flow for Foodics.
It captures the authorization code from the redirect URL and exchanges it for access and refresh tokens.

## How It Works
This module seamlessly integrates the Foodics API authorization flow into Odoo. 
- **Configuration Setup**: In Odoo settings, you can define your Foodics Client ID, Client Secret, choose between Sandbox or Production environments, and set an optional Redirect URI.
- **OAuth Callback Handled**: The module overrides the default Odoo `/web/login` route to act as the OAuth callback. When Foodics redirects back to Odoo with an OAuth `code` parameter in the URL, the module temporarily captures and stores this code in the current session.
- **Token Exchange**: As soon as the user finishes logging into Odoo (or if immediately redirected as an already logged-in user), the module securely communicates with the Foodics `/oauth/token` API endpoint, exchanging the captured `code` for fully authorized access tokens.
- **Token Persistence**: Finally, the received OAuth tokens and environment types are stored automatically in a new `foodics.connector` record, effectively authenticating Odoo to make subsequent API calls to Foodics securely.
