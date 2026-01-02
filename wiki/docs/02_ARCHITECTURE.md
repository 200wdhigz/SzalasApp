# System Architecture: OAuth & User Management

## Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         SzalasApp                                │
│                    Equipment Management System                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (Templates)                        │
├─────────────────────────────────────────────────────────────────┤
│ login.html          │ OAuth login buttons                        │
│ account.html        │ User account management                    │
│ admin/users_list    │ Admin user list view                       │
│ admin/user_new      │ New user registration                      │
│ admin/user_edit     │ Edit user details                          │
│ base.html           │ Enhanced navigation                        │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Flask Application (Backend)                    │
├─────────────────────────────────────────────────────────────────┤
│ auth_bp             │ /login, /logout                            │
│ oauth_bp            │ /auth/google, /auth/microsoft, /account    │
│ admin_bp            │ /admin/users/*                             │
│ views_bp            │ /sprzet, /usterki (existing)              │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ src/auth.py         │ Login/logout, decorators                   │
│ src/oauth.py        │ OAuth flows, account linking               │
│ src/admin.py        │ User management operations                 │
│ src/db_users.py     │ User database operations                   │
│ src/db_firestore.py │ Equipment/malfunction ops (existing)       │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────┬──────────────────────┬────────────────────┐
│   Firebase Auth      │   Google OAuth       │  Microsoft OAuth   │
│   (Password)         │   (OAuth 2.0)        │  (OAuth 2.0)       │
└──────────────────────┴──────────────────────┴────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Data Storage (Firestore)                    │
├─────────────────────────────────────────────────────────────────┤
│ Collection: users   │ email, is_admin, active, google_id,        │
│                     │ microsoft_id, created_at, updated_at       │
├─────────────────────────────────────────────────────────────────┤
│ Collection: sprzet  │ Equipment data (existing)                  │
├─────────────────────────────────────────────────────────────────┤
│ Collection: usterki │ Malfunction data (existing)                │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

### 1. Password Login (Existing + Enhanced)
```
User → /login → Firebase Auth API → Token Verification
                                   ↓
                         Check/Create User in Firestore
                                   ↓
                         Check Account Active Status
                                   ↓
                         Set Session (user_id, is_admin)
                                   ↓
                         Redirect to Dashboard
```

### 2. Google OAuth Login (New)
```
User → Click Google Button → /auth/google
                                   ↓
                         Generate CSRF State
                                   ↓
                         Redirect to Google
                                   ↓
User Authorizes ← Google Login Page
                                   ↓
Google → /auth/google/callback → Validate State
                                   ↓
                         Exchange Code for Token
                                   ↓
                         Get User Info (email, id)
                                   ↓
                         Find User by google_id
                                   ↓
              ┌──────────────────┴───────────────────┐
              │                                      │
        User Found                             User Not Found
              │                                      │
    Check Active Status                    Show "Contact Admin"
              │                                      │
    Set Session & Login                    Redirect to Login
```

### 3. Microsoft OAuth Login (New)
```
User → Click Microsoft Button → /auth/microsoft
                                   ↓
                         Generate CSRF State
                                   ↓
                         Redirect to Microsoft
                                   ↓
User Authorizes ← Microsoft Login
                                   ↓
Microsoft → /auth/microsoft/callback → Validate State
                                   ↓
                         Exchange Code for Token
                                   ↓
                         Get User Info (email, id)
                                   ↓
                         Validate Domain (zhp.net.pl/zhp.pl)
                                   ↓
              ┌──────────────────┴───────────────────┐
              │                                      │
        Domain Valid                          Domain Invalid
              │                                      │
    Find User by microsoft_id                Show Error Message
              │
    ┌─────────┴──────────┐
    │                    │
User Found          User Not Found
    │                    │
Check Active      "Contact Admin"
    │
Set Session
```

### 4. OAuth Account Linking (New)
```
Logged In User → /account → Click "Połącz"
                                   ↓
                         /auth/google or /auth/microsoft
                                   ↓
                         Set oauth_linking flag in session
                                   ↓
                         OAuth Authorization Flow
                                   ↓
                         Callback with OAuth ID
                                   ↓
                         Check if ID already linked
                                   ↓
              ┌──────────────────┴───────────────────┐
              │                                      │
        Not Linked                            Already Linked
              │                                      │
    Link to Current User                    Show Error Message
              │
    Update Firestore
              │
    Show Success Message
```

## User Management Flow

### Admin User Creation (New)
```
Admin → /admin/users/new → Enter email & password
                                   ↓
                         Set admin flag (optional)
                                   ↓
                         Create in Firebase Auth
                                   ↓
                         Set custom claims (admin)
                                   ↓
                         Create in Firestore
                                   ↓
                         Redirect to User List
```

### Password Reset (New)
```
Admin → /admin/users → Click Reset Password
                                   ↓
                         Generate Random Password
                         (16 chars + special chars)
                                   ↓
                         Update Firebase Auth
                                   ↓
                         Store in Session (temp)
                                   ↓
                         Redirect to List
                                   ↓
                         Display Password (one-time)
                                   ↓
                         Clear from Session
```

### Enable/Disable User (New)
```
Admin → /admin/users → Toggle Status
                                   ↓
                         Update Firebase Auth (disabled flag)
                                   ↓
                         Update Firestore (active flag)
                                   ↓
              ┌──────────────────┴───────────────────┐
              │                                      │
        User Disabled                          User Enabled
              │                                      │
    Cannot Login                           Can Login Again
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         Request Layer                            │
├─────────────────────────────────────────────────────────────────┤
│ ✓ HTTPS (Production)                                             │
│ ✓ CSRF Token Validation                                          │
│ ✓ Session Management                                             │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Authentication Layer                        │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Firebase Authentication                                        │
│ ✓ OAuth State Parameter                                          │
│ ✓ Token Verification                                             │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Authorization Layer                         │
├─────────────────────────────────────────────────────────────────┤
│ ✓ @login_required decorator                                      │
│ ✓ @admin_required decorator                                      │
│ ✓ Account status check                                           │
│ ✓ Domain validation (Microsoft)                                  │
└─────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
├─────────────────────────────────────────────────────────────────┤
│ ✓ Firestore security rules                                       │
│ ✓ Firebase Auth management                                       │
│ ✓ No sensitive data in logs                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Navigation Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         Public Routes                            │
├─────────────────────────────────────────────────────────────────┤
│ /login                   │ Login page with OAuth buttons         │
│ /auth/google             │ Initiate Google OAuth                 │
│ /auth/microsoft          │ Initiate Microsoft OAuth              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Authenticated Routes                         │
├─────────────────────────────────────────────────────────────────┤
│ /                        │ Equipment list (existing)             │
│ /sprzet/*                │ Equipment views (existing)            │
│ /usterki/*               │ Malfunction views (existing)          │
│ /account                 │ Account management (NEW)              │
│ /account/unlink/*        │ Unlink OAuth accounts (NEW)           │
│ /logout                  │ Logout                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Admin Routes                             │
├─────────────────────────────────────────────────────────────────┤
│ /admin/users             │ List all users (NEW)                  │
│ /admin/users/new         │ Create new user (NEW)                 │
│ /admin/users/:id/edit    │ Edit user (NEW)                       │
│ /admin/users/:id/disable │ Disable user (NEW)                    │
│ /admin/users/:id/enable  │ Enable user (NEW)                     │
│ /admin/users/:id/reset-* │ Reset password (NEW)                  │
│ /sprzet/add              │ Add equipment (existing)              │
│ /sprzet/edit/*           │ Edit equipment (existing)             │
│ /usterka/edit/*          │ Edit malfunction (existing)           │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Admin-Only Registration**: Users cannot self-register. Only admins create accounts.
   - Reason: Security requirement from problem statement
   - Implementation: @admin_required on /admin/users/new

2. **OAuth Linking vs Direct Login**: Users can link OAuth to existing accounts OR login directly.
   - Reason: Flexibility for users with existing passwords
   - Implementation: Session flag 'oauth_linking' determines behavior

3. **Domain Restriction**: Microsoft OAuth limited to ZHP domains.
   - Reason: Requirement for ZHP organization
   - Implementation: Configurable via MICROSOFT_ALLOWED_DOMAINS

4. **Session-Based Password Display**: Reset passwords shown once in browser.
   - Reason: Security - don't store in flash messages or logs
   - Implementation: Store in session, display once, clear immediately

5. **Firestore + Firebase Auth**: Dual storage system.
   - Reason: Firebase Auth for authentication, Firestore for application data
   - Implementation: User document created/synced on login

## Testing Strategy

### Unit Testing (Automated)
- ✅ Module imports
- ✅ Syntax compilation
- ✅ Template syntax validation
- ✅ CodeQL security scan

### Integration Testing (Manual Required)
- OAuth flows require real credentials
- Admin operations need Firebase project
- Account linking needs OAuth setup

See OAUTH_SETUP.md for complete manual testing checklist.
