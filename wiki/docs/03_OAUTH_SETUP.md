# OAuth Setup and Testing Guide

## Overview
This guide provides step-by-step instructions for configuring OAuth providers and testing the new authentication and user management features.

## Prerequisites

1. Firebase project with Authentication enabled
2. Google Cloud Console access for Google OAuth
3. Azure Portal access for Microsoft OAuth
4. Admin user account in Firebase

## Part 1: Google OAuth Setup

### Step 1: Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Configure OAuth consent screen if not done:
   - User Type: External (or Internal for G Suite)
   - App name: SzalasApp
   - Support email: Your email
   - Authorized domains: Your domain
   - Scopes: openid, email, profile

### Step 2: Configure OAuth Client

1. Application type: **Web application**
2. Name: `SzalasApp OAuth Client`
3. Authorized JavaScript origins:
   - `http://localhost:5000` (development)
   - `https://yourdomain.com` (production)
4. Authorized redirect URIs:
   - `http://localhost:5000/auth/google/callback` (development)
   - `https://yourdomain.com/auth/google/callback` (production)
5. Click **Create**
6. Save the **Client ID** and **Client Secret**

### Step 3: Update Environment Variables

Add to your `.env` file:
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

## Part 2: Microsoft OAuth Setup (for ZHP domains)

### Step 1: Register Application in Azure

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory**
3. Select **App registrations** → **New registration**
4. Configure:
   - Name: `SzalasApp`
   - Supported account types: **Accounts in any organizational directory**
   - Redirect URI:
     - Platform: **Web**
     - URI: `http://localhost:5000/auth/microsoft/callback` (development)
     - URI: `https://yourdomain.com/auth/microsoft/callback` (production)
5. Click **Register**

### Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission** → **Microsoft Graph**
3. Select **Delegated permissions**
4. Add:
   - `User.Read`
   - `email`
   - `openid`
   - `profile`
5. Click **Add permissions**
6. (Optional) Click **Grant admin consent** if you're an admin

### Step 3: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Description: `SzalasApp OAuth Secret`
4. Expires: Choose appropriate duration
5. Click **Add**
6. **Important:** Copy the secret value immediately (it won't be shown again)

### Step 4: Get Application Details

1. Go to **Overview** page
2. Copy:
   - **Application (client) ID**
   - **Directory (tenant) ID**

### Step 5: Update Environment Variables

Add to your `.env` file:
```bash
MICROSOFT_CLIENT_ID=your-application-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id-or-common
MICROSOFT_ALLOWED_DOMAINS=zhp.net.pl,zhp.pl
```

**Note:** Use `common` for TENANT_ID if you want to support multiple tenants.

## Part 3: Application Configuration

### Complete .env File Example

```bash
# Google Configuration
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_API_KEY=your-firebase-api-key
SECRET_KEY=generate-a-strong-random-key-here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_TENANT_ID=common
MICROSOFT_ALLOWED_DOMAINS=zhp.net.pl,zhp.pl

# Base URL (adjust for your environment)
BASE_URL=http://localhost:5000

# Server Configuration
PORT=5000
HOST=0.0.0.0
```

## Part 4: Manual Testing Checklist

### Test 1: Admin User Registration
- [ ] Log in as an admin user
- [ ] Navigate to **Zarządzanie Użytkownikami**
- [ ] Click **Nowy Użytkownik**
- [ ] Create a test user with a strong password
- [ ] Verify user appears in the list
- [ ] Check both admin and non-admin role creation

### Test 2: Regular Login
- [ ] Log out
- [ ] Try logging in with the newly created user credentials
- [ ] Verify successful login
- [ ] Check that non-admin users don't see admin menu

### Test 3: Google OAuth Login
- [ ] Log out
- [ ] On login page, click **Zaloguj przez Google**
- [ ] Authorize the application in Google
- [ ] Verify redirect back to application
- [ ] Check if new Google users get appropriate message
- [ ] For existing users, verify successful login

### Test 4: Microsoft OAuth Login
- [ ] Log out
- [ ] On login page, click **Zaloguj przez Microsoft (ZHP)**
- [ ] Use an account with @zhp.net.pl or @zhp.pl domain
- [ ] Authorize the application
- [ ] Verify domain validation works
- [ ] Test with non-ZHP domain (should be rejected)

### Test 5: Account Linking
- [ ] Log in with regular credentials
- [ ] Go to **Moje Konto**
- [ ] Click **Połącz** for Google
- [ ] Authorize Google account
- [ ] Verify account is linked (shows "Połączone")
- [ ] Click **Połącz** for Microsoft
- [ ] Authorize Microsoft account
- [ ] Verify both accounts are linked

### Test 6: OAuth Login After Linking
- [ ] Log out
- [ ] Try logging in via Google OAuth
- [ ] Verify successful login with linked account
- [ ] Log out and try Microsoft OAuth
- [ ] Verify successful login

### Test 7: Account Unlinking
- [ ] Go to **Moje Konto**
- [ ] Click **Rozłącz** for Google
- [ ] Confirm unlinking
- [ ] Verify account is unlinked
- [ ] Repeat for Microsoft account

### Test 8: Admin User Management
- [ ] Log in as admin
- [ ] Go to **Zarządzanie Użytkownikami**
- [ ] Test **Wyłącz** (disable) on a test user
- [ ] Try logging in as that user (should be denied)
- [ ] Re-enable the user with **Włącz**
- [ ] Verify user can log in again

### Test 9: Password Reset
- [ ] As admin, go to **Zarządzanie Użytkownikami**
- [ ] Click **Resetuj hasło** (key icon) for a test user
- [ ] Note the generated password displayed
- [ ] Log out and try logging in with new password
- [ ] Verify successful login

### Test 10: User Role Management
- [ ] As admin, edit a test user
- [ ] Toggle admin status on/off
- [ ] Log in as that user
- [ ] Verify menu changes based on role

### Test 11: CSRF Protection
- [ ] Try to submit forms without CSRF token (using browser dev tools)
- [ ] Verify all actions are rejected
- [ ] Check that legitimate form submissions work correctly

### Test 12: Security Validations
- [ ] Try accessing admin routes as regular user
- [ ] Try accessing protected routes without login
- [ ] Verify proper error messages and redirects

## Part 5: Troubleshooting

### Issue: "OAuth not configured" message
**Solution:** Ensure GOOGLE_CLIENT_ID and MICROSOFT_CLIENT_ID are set in .env

### Issue: Redirect URI mismatch
**Solution:** Ensure the redirect URIs in OAuth providers match BASE_URL in .env

### Issue: Microsoft domain validation fails
**Solution:** Check MICROSOFT_ALLOWED_DOMAINS includes the user's domain

### Issue: CSRF validation error
**Solution:** Clear browser cookies and try again

### Issue: User not found after OAuth login
**Solution:** Admin must create user account first, then user can link OAuth

## Part 6: Production Deployment Checklist

- [ ] Update BASE_URL to production domain
- [ ] Update OAuth redirect URIs in Google Console
- [ ] Update OAuth redirect URIs in Azure Portal
- [ ] Generate strong SECRET_KEY (use `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Ensure GOOGLE_PROJECT_ID points to production project
- [ ] Test all OAuth flows in production
- [ ] Monitor logs for any errors
- [ ] Set up SSL/TLS (HTTPS required for OAuth)

## Security Best Practices

1. **Never commit .env file** - Use .env.example as template
2. **Rotate secrets regularly** - Especially client secrets
3. **Use HTTPS in production** - Required for OAuth security
4. **Monitor OAuth activity** - Check logs for suspicious behavior
5. **Limit OAuth scopes** - Only request necessary permissions
6. **Keep dependencies updated** - Run `pip install -U` regularly
7. **Review admin list** - Ensure only trusted users have admin access

## Support

For issues or questions:
1. Check application logs in console output
2. Review Firebase Authentication logs
3. Check OAuth provider dashboards for errors
4. Verify all environment variables are set correctly
