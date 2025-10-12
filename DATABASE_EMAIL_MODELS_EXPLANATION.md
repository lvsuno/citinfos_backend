# Django Email Models Explanation

## 📧 Email-Related Tables in Your Database

You have these email-related tables:
1. `account_emailaddress` - Stores email addresses for users
2. `account_emailconfirmation` - Stores email verification tokens

These come from **Django-allauth**, not Django core.

---

## 🔍 What is Django-allauth?

**Django-allauth** is a popular Django package that provides:
- Email verification
- Social authentication (Google, Facebook, GitHub, Twitter)
- Multiple email addresses per user
- Email confirmation workflow
- Password reset via email

### Your Current Setup

From your `settings.py`:
```python
INSTALLED_APPS = [
    # Django AllAuth for social authentication
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.twitter',
]
```

---

## 📊 Database Tables Breakdown

### 1. `auth_user` (Django Core User Table) ✅

**Purpose**: The main user table from Django
**Location**: `django.contrib.auth`

**Structure**:
```
auth_user
├── id (primary key)
├── username
├── first_name
├── last_name
├── email (single email field)
├── password (hashed)
├── is_staff
├── is_active
├── is_superuser
├── date_joined
└── last_login
```

**Why you might not see it easily**:
- It's the standard Django user table
- Many database tools show it as `auth_user` not "django user"
- It's in the `auth` app namespace

---

### 2. `account_emailaddress` (Django-allauth) 📨

**Purpose**: Stores multiple email addresses per user with verification status
**Why it exists**: Allows users to have multiple emails and verify them

**Structure**:
```
account_emailaddress
├── id (primary key)
├── user_id (foreign key to auth_user)
├── email (email address)
├── verified (boolean - is this email verified?)
├── primary (boolean - is this the primary email?)
└── Constraints:
    ├── One primary email per user
    ├── Unique verified emails
    └── Unique (user_id, email) combination
```

**Example Data**:
```
id | user_id | email              | verified | primary
---+---------+--------------------+----------+---------
1  | 5       | john@example.com   | true     | true
2  | 5       | john@work.com      | false    | false
3  | 7       | sarah@example.com  | true     | true
```

**Use Cases**:
- ✅ User signs up with email → creates unverified email entry
- ✅ User clicks verification link → sets `verified = true`
- ✅ User adds secondary email → creates additional row
- ✅ User changes primary email → updates `primary` flag

---

### 3. `account_emailconfirmation` (Django-allauth) 🔐

**Purpose**: Stores email verification tokens (confirmation keys)
**Why it exists**: Manages the email confirmation workflow

**Structure**:
```
account_emailconfirmation
├── id (primary key)
├── email_address_id (foreign key to account_emailaddress)
├── created (timestamp when token was created)
├── sent (timestamp when email was sent)
└── key (unique verification token/key)
```

**Example Data**:
```
id | email_address_id | key                              | created             | sent
---+------------------+----------------------------------+---------------------+---------------------
1  | 2                | a3f8d9e7c2b1... (64 char hash)   | 2025-10-09 10:00:00 | 2025-10-09 10:00:01
```

**Workflow**:
```
┌────────────────────────────────────────────────────────────┐
│                  Email Verification Flow                   │
└────────────────────────────────────────────────────────────┘

1. User signs up with email: john@example.com
   ↓
2. Django-allauth creates:
   - account_emailaddress (verified=false, primary=true)
   - account_emailconfirmation (unique key generated)
   ↓
3. Sends email to user:
   "Click this link: https://site.com/verify?key=a3f8d9e7..."
   ↓
4. User clicks link
   ↓
5. Django-allauth verifies key:
   - Finds matching account_emailconfirmation
   - Updates account_emailaddress (verified=true)
   - Deletes used confirmation token
   ↓
6. User email is now verified ✅
```

---

## 🤔 Why Do You Need These Tables?

### Without Django-allauth:
```python
# Django's built-in User model
auth_user
├── email: "john@example.com"  # Just one field
└── No email verification ❌
```

**Problems**:
- ❌ No email verification
- ❌ Can't have multiple emails
- ❌ No "resend verification email" feature
- ❌ Manual implementation needed for social auth

### With Django-allauth:
```python
# Django-allauth provides:
auth_user (Django core)
└── Linked to: account_emailaddress (allauth)
    ├── email: "john@example.com" (verified ✅, primary ✅)
    ├── email: "john@work.com" (verified ❌, primary ❌)
    └── Linked to: account_emailconfirmation
        └── key: "a3f8d9e7..." (verification token)
```

**Benefits**:
- ✅ Automatic email verification
- ✅ Multiple emails per user
- ✅ Social authentication (Google, Facebook, etc.)
- ✅ Email change workflow
- ✅ Resend verification email
- ✅ Primary email management

---

## 📋 Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Structure                       │
└─────────────────────────────────────────────────────────────┘

auth_user (Django Core)
    ├── id: 5
    ├── username: "john_doe"
    ├── email: "john@example.com"
    └── password: "hashed..."
         │
         │ user_id (FK)
         ↓
account_emailaddress (Django-allauth)
    ├── id: 10
    ├── user_id: 5 ──────────────┐
    ├── email: "john@example.com" │
    ├── verified: false           │
    └── primary: true             │
         │                        │
         │ email_address_id (FK)  │
         ↓                        │
account_emailconfirmation          │
    ├── id: 20                    │
    ├── email_address_id: 10 ─────┘
    ├── key: "a3f8d9e7c2b1..."
    ├── created: 2025-10-09 10:00:00
    └── sent: 2025-10-09 10:00:01
```

---

## 🛠️ Common Queries

### Check User's Emails
```sql
SELECT
    u.id,
    u.username,
    e.email,
    e.verified,
    e.primary
FROM auth_user u
LEFT JOIN account_emailaddress e ON u.id = e.user_id
WHERE u.username = 'john_doe';
```

### Find Pending Email Verifications
```sql
SELECT
    u.username,
    e.email,
    c.key,
    c.created,
    c.sent
FROM account_emailconfirmation c
JOIN account_emailaddress e ON c.email_address_id = e.id
JOIN auth_user u ON e.user_id = u.id
WHERE e.verified = false;
```

### Count Users by Email Verification Status
```sql
SELECT
    e.verified,
    COUNT(DISTINCT e.user_id) as user_count
FROM account_emailaddress e
WHERE e.primary = true
GROUP BY e.verified;
```

---

## ⚙️ Configuration in Your Project

Your allauth settings (from `settings.py`):
```python
# AllAuth Settings
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Allow both
ACCOUNT_EMAIL_REQUIRED = True                     # Email mandatory
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'          # Must verify email
ACCOUNT_UNIQUE_EMAIL = True                       # Emails must be unique
ACCOUNT_USERNAME_REQUIRED = True                  # Username mandatory
```

This means:
- ✅ Users must provide email on signup
- ✅ Users must verify email before logging in (if `mandatory`)
- ✅ Each email can only be used once
- ✅ Username is required

---

## 🎯 Summary

| Table | From | Purpose |
|-------|------|---------|
| `auth_user` | Django Core | Main user data (username, password, etc.) |
| `account_emailaddress` | Django-allauth | Multiple emails per user with verification |
| `account_emailconfirmation` | Django-allauth | Email verification tokens |

**You have the Django user table!** It's called `auth_user`.

The email models are **additional features** from Django-allauth that enhance Django's basic user system with:
- Email verification workflow
- Multiple emails per user
- Social authentication support

---

## 🚀 Next Steps

If you want to see the Django user table in your database tool, search for:
- Table name: `auth_user`
- Or filter by schema: `public.auth_user`

If you want to manage allauth email verification:
```python
# In Django shell
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()
user = User.objects.get(username='john_doe')

# Get user's emails
emails = EmailAddress.objects.filter(user=user)

# Verify an email manually
email = EmailAddress.objects.get(user=user, primary=True)
email.verified = True
email.save()
```

---

## 📚 References

- [Django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Django User Model](https://docs.djangoproject.com/en/stable/ref/contrib/auth/)
- Email verification explained: Django-allauth sends a unique token via email, user clicks link, token verified, email marked as verified.
