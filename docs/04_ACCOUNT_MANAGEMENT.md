# Changelog: Self-Service Account Management & Enhanced Password Reset

## Summary

This update adds powerful self-service features for users and improves the password reset functionality for administrators. Users can now manage their own credentials without admin intervention, and password resets are automatically sent via email.

## New Features

### 1. 🔐 Self-Service Password Change

**Location:** `/account` → "Zmiana hasła" section

**What it does:**
- Users can change their own password anytime
- No admin intervention required
- Works for all users (including those with OAuth linked)

**How it works:**
1. User enters current password (for security verification)
2. User enters new password (minimum 6 characters)
3. User confirms new password
4. System validates current password before making change
5. Password updated in Firebase Authentication
6. User receives confirmation message

**Benefits:**
- Increased user autonomy
- Reduced admin workload
- Better security (users can update compromised passwords immediately)
- OAuth users can set a password for password-based login

**Security:**
- Current password required (prevents unauthorized changes)
- Password strength validation (min. 6 characters)
- Confirmation field prevents typos
- CSRF protection
- Secure password verification via Firebase API

---

### 2. ✉️ Self-Service Email Change

**Location:** `/account` → "Zmiana adresu email" section

**What it does:**
- Users can update their email address independently
- No admin required for email changes

**How it works:**
1. User enters new email address
2. User confirms change with current password
3. System validates password
4. System checks if new email is already in use
5. Email updated in both Firebase Auth and Firestore database
6. User receives confirmation message
7. New email required for next login

**Benefits:**
- Users can keep their contact info up-to-date
- No admin bottleneck for simple changes
- Maintains security through password verification

**Security:**
- Password confirmation required
- Duplicate email detection
- CSRF protection
- Updates across all systems (Firebase + Firestore)
- Immediate effect (prevents confusion)

---

### 3. 📧 Email Notification for Password Reset

**Location:** Admin panel → User list → Reset password button

**What's new:**
- Password automatically sent to user's email address
- Admin sees email delivery status
- Fallback to manual delivery if email fails

**How it works:**
1. Admin clicks "Reset password" for a user
2. System generates strong random password (16 characters)
3. System attempts to send email to user
4. Email contains:
   - New password (prominently displayed)
   - Login link
   - Recommendation to change password after login
5. Password displayed to admin with email status:
   - ✅ **Green success message:** "Email sent successfully"
   - ⚠️ **Yellow warning:** "Email failed, manual communication needed"
6. Admin can copy password if email delivery failed

**Email Template:**
- Professional HTML design
- Clear password display with highlighting
- Direct login link
- Security recommendations
- Both HTML and plain text versions

**Benefits:**
- Automatic password delivery to users
- Reduced admin workload
- Better user experience
- Audit trail (admin knows if email was sent)
- Fallback ensures password is never lost

**Configuration required:**
```bash
SMTP_HOST=smtp.gmail.com          # Your SMTP server
SMTP_PORT=587                     # Usually 587 for TLS
SMTP_USER=your-email@example.com  # Email account
SMTP_PASSWORD=your-app-password   # App-specific password
FROM_EMAIL=noreply@yourapp.com    # Optional sender address
```

---

### 4. 🎯 Smart Login Error Messages

**Location:** Login page

**What's new:**
- Intelligent error detection when password login fails
- Helpful guidance for OAuth-linked accounts

**How it works:**
1. User tries to login with email + password
2. If login fails AND user has OAuth accounts linked:
   - System detects the linked providers (Google/Microsoft)
   - Shows friendly message: "To konto ma powiązane logowanie przez Google/Microsoft"
   - Directs user to use the correct OAuth button
3. If login fails and no OAuth linked:
   - Shows standard error: "Nieprawidłowy email lub hasło"

**Example scenarios:**

**Scenario A:** User has Google linked, tries password login
- ❌ Old message: "Błąd logowania: Nieprawidłowe dane"
- ✅ New message: "To konto ma powiązane logowanie przez Google. Użyj odpowiedniego przycisku poniżej aby się zalogować."

**Scenario B:** User has both Google and Microsoft linked
- ✅ Message: "To konto ma powiązane logowanie przez Google i Microsoft. Użyj odpowiedniego przycisku poniżej aby się zalogować."

**Scenario C:** Invalid password, no OAuth
- ✅ Message: "Błąd logowania: Nieprawidłowy email lub hasło."

**Benefits:**
- Reduced user confusion
- Clear guidance on correct login method
- Better user experience
- Fewer support requests

---

## Technical Implementation

### Modified Files

#### `src/auth.py`
- Enhanced login error handling
- Added OAuth account detection on failed password login
- Improved error messages with provider information

#### `src/oauth.py`
- Added `change_password()` route
- Added `change_email()` route
- Added password verification logic
- Fixed request library usage (replaced OAuth2Session with requests)

#### `src/db_users.py`
- Added `update_user_email()` function

#### `src/admin.py`
- Added `send_password_reset_email()` function
- Enhanced `user_reset_password()` with email sending
- Added email status tracking in session
- Improved error handling for email failures

#### `templates/account.html`
- Added "Zmiana hasła" form section
- Added "Zmiana adresu email" form section
- Added helpful info message for OAuth users
- Improved layout and spacing

#### `templates/admin/users_list.html`
- Enhanced password reset alert
- Added email delivery status indicator
- Improved visual styling for password display
- Better highlighting of important information

### New Dependencies

None - uses existing libraries:
- `requests` (already in use)
- `smtplib` (Python standard library)
- `email.mime` (Python standard library)

### Security Considerations

#### Password Verification
- All self-service changes require current password
- Password verification via Firebase API (not local)
- Prevents unauthorized account modifications

#### CSRF Protection
- All forms include CSRF tokens
- Token validation on server side
- Protection against cross-site request forgery

#### Email Security
- SMTP connection uses TLS (STARTTLS)
- Supports app-specific passwords (e.g., Gmail)
- Password only sent to user's registered email
- Email template includes security recommendations

#### Error Handling
- No sensitive information in error messages
- Email failures handled gracefully
- Fallback to manual password communication
- Clear logging for troubleshooting

---

## User Interface Updates

### Account Management Page (`/account`)

**New sections added:**

1. **Zmiana hasła** (Change Password)
   - Current password field
   - New password field (with min length validation)
   - Confirm password field
   - Blue "Zmień hasło" button
   - Info box for OAuth users

2. **Zmiana adresu email** (Change Email)
   - New email field
   - Password confirmation field
   - Help text explaining password requirement
   - Yellow "Zmień email" button

**Visual improvements:**
- Clear section separation with horizontal rules
- Consistent styling with rest of application
- Bootstrap 5 form controls
- Helpful placeholder text
- Form validation feedback

### Admin User List Page (`/admin/users`)

**Password reset alert improvements:**
- Large, prominent password display
- Color-coded email status:
  - Green for success
  - Yellow/orange for failure
- Icons for visual clarity
- Dismissible alert (one-time view)
- Better contrast and readability

---

## Testing Checklist

### Self-Service Password Change
- [ ] User can change password with correct current password
- [ ] Change rejected with wrong current password
- [ ] New password must be at least 6 characters
- [ ] Password confirmation must match
- [ ] Success message displayed after change
- [ ] User can login with new password
- [ ] OAuth users can set password

### Self-Service Email Change
- [ ] User can change email with correct password
- [ ] Change rejected with wrong password
- [ ] Duplicate email validation works
- [ ] Email updated in Firebase Auth
- [ ] Email updated in Firestore
- [ ] User must use new email to login
- [ ] Success message displayed

### Email Password Reset
- [ ] Email sent when SMTP configured
- [ ] Email contains correct password
- [ ] Admin sees success status
- [ ] Email failure handled gracefully
- [ ] Admin sees failure status
- [ ] Password still displayed to admin on failure
- [ ] Email template displays correctly (HTML)
- [ ] Plain text fallback works

### Smart Login Errors
- [ ] OAuth-linked account shows helpful message
- [ ] Message lists correct providers (Google/Microsoft)
- [ ] Non-OAuth account shows standard error
- [ ] Error messages are user-friendly
- [ ] No sensitive information exposed

---

## Configuration Guide

### Setting up Email (for Password Reset)

#### Option 1: Gmail

1. Create a Gmail account or use existing
2. Enable 2-factor authentication
3. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated password
4. Add to `.env`:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   FROM_EMAIL=your-email@gmail.com  # Optional
   ```

#### Option 2: Other SMTP Providers

**Microsoft 365:**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-password
```

**Custom SMTP:**
```bash
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-password
```

#### Testing Email Configuration

```python
# Run in Python console
from src.admin import send_password_reset_email
send_password_reset_email("test@example.com", "TestPassword123!")
```

### Fallback Mode

If SMTP is not configured:
- Email sending will fail gracefully
- Password still displayed to admin
- Admin can manually send password to user
- No errors or crashes

---

## Migration Notes

### For Existing Users

**No migration required!**
- All new features are opt-in
- Existing authentication methods unchanged
- Users can continue using current login methods
- Self-service features available immediately

### For Administrators

**Optional setup:**
- Configure SMTP for email notifications
- Inform users about new self-service features
- Update internal documentation if needed

---

## Troubleshooting

### Email Not Sending

**Check:**
1. SMTP credentials are correct in `.env`
2. SMTP_USER has permission to send email
3. Firewall allows outbound SMTP connections
4. Using correct SMTP_HOST and SMTP_PORT
5. For Gmail: App Password generated (not regular password)

**Error messages:**
- "SMTP credentials not configured" → Set SMTP_USER and SMTP_PASSWORD
- "Authentication failed" → Check username/password
- "Connection refused" → Check SMTP_HOST and SMTP_PORT

### Password Change Not Working

**Check:**
1. User entering correct current password
2. New password meets minimum length (6 chars)
3. Confirm password matches new password
4. Firebase API key is valid

**User sees:**
- "Nieprawidłowe obecne hasło" → Current password is wrong
- "Nowe hasła nie pasują do siebie" → Confirmation mismatch
- "Nowe hasło musi mieć co najmniej 6 znaków" → Too short

### Email Change Not Working

**Check:**
1. User entering correct password
2. New email is valid format
3. New email not already in use
4. Firebase allows email updates

**User sees:**
- "Nieprawidłowe hasło" → Password verification failed
- "Ten adres email jest już używany" → Email already exists

---

## Future Enhancements

Potential improvements for future versions:

1. **Email verification:**
   - Send verification link to new email
   - Require confirmation before change takes effect

2. **Password strength meter:**
   - Visual indicator of password strength
   - Suggestions for stronger passwords

3. **Two-factor authentication:**
   - Optional 2FA for enhanced security
   - SMS or authenticator app support

4. **Password history:**
   - Prevent reuse of recent passwords
   - Track password change history

5. **Email templates:**
   - Customizable email templates
   - Multi-language support

6. **Audit log:**
   - Track all account changes
   - Admin view of user activity

---

## Support

For issues or questions:
1. Check this documentation first
2. Review error messages for specific guidance
3. Check application logs for detailed errors
4. Consult FEATURE_SUMMARY.md for architectural details

---

## Summary of Changes

✅ **Added:** Self-service password change
✅ **Added:** Self-service email change  
✅ **Added:** Email notifications for password reset
✅ **Added:** Email delivery status for admins
✅ **Improved:** Login error messages for OAuth accounts
✅ **Enhanced:** Account management UI
✅ **Enhanced:** Admin password reset workflow

**Lines of code changed:** ~300
**New routes added:** 2 (`/account/change-password`, `/account/change-email`)
**Templates modified:** 2 (`account.html`, `admin/users_list.html`)
**Backend files modified:** 4 (`auth.py`, `oauth.py`, `admin.py`, `db_users.py`)

---

**Last Updated:** 2026-01-01
**Version:** 1.1.0
**Author:** System Update

