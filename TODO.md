# Remove Two-Factor Authentication

## Backend Changes
- [ ] Remove 2FA fields from User model (phone_number, phone_verified, two_factor_enabled, two_factor_secret)
- [ ] Remove 2FA-related routes (/api/setup-phone, /api/verify-phone, /api/setup-2fa, /api/verify-2fa, /api/disable-2fa)
- [ ] Remove 2FA-related imports (pyotp, phonenumbers, twilio)
- [ ] Remove 2FA-related functions (get_twilio_client, get_twilio_number, validate_phone_number)
- [ ] Remove 2FA-related configuration (TWILIO_* variables)
- [ ] Remove 2FA dependencies from requirements.txt

## Frontend Changes
- [ ] Remove 2FA section from Settings.js security tab
- [ ] Remove 2FA-related state (twoFactorForm, twoFactorStep)
- [ ] Remove 2FA-related handlers (handlePhoneSetup, handlePhoneVerification, handleSetup2FA, handleVerify2FA, handleDisable2FA)

## Database Migration
- [ ] Run migration to update database schema (remove 2FA columns)
