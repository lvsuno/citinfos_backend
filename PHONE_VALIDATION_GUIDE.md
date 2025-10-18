# Phone Number Validation - Implementation Guide

## Overview
This implementation provides comprehensive phone number validation for all countries using Google's libphonenumber library (Python backend) and libphonenumber-js (React frontend).

## ✅ What's Been Set Up

### Backend (Django/Python)

1. **Dependencies Added** (`requirements.txt`):
   ```
   phonenumbers>=8.13.0
   ```

2. **Validation Functions** (`accounts/validators.py`):
   - `validate_phone_number(phone_number, country_code)` - Validates and formats phone numbers
   - `PhoneNumberValidator` - Django model field validator class

3. **Features**:
   - ✅ International phone number validation
   - ✅ Country-specific format validation
   - ✅ Automatic formatting (international + national)
   - ✅ Detailed error messages in French
   - ✅ Fallback to regex if phonenumbers not installed

### Frontend (React)

1. **Dependencies Added** (`package.json`):
   ```json
   "libphonenumber-js": "^1.10.51"
   ```

2. **Utility Functions** (`src/utils/phoneValidation.js`):
   - `validatePhoneNumber(phone, countryCode)` - Validates phone numbers
   - `formatPhoneNumber(phone, countryCode, format)` - Formats for display
   - `formatAsYouType(value, countryCode)` - Real-time formatting as user types
   - `isMobileNumber(phone, countryCode)` - Checks if mobile
   - `getCountryFromNumber(phone)` - Auto-detects country
   - `COUNTRY_PHONE_CODES` - List of countries with flags and dial codes

## 📦 Installation

### Backend
```bash
# In Docker container or virtual environment
pip install -r requirements.txt
```

### Frontend
```bash
# In project root
npm install
# or
yarn install
```

## 🔧 Usage Examples

### Frontend - SignUpPage.js

**Basic Validation**:
```javascript
import { validatePhoneNumber } from '../utils/phoneValidation';

const [formData, setFormData] = useState({
    phoneNumber: '',
    country: 'CA', // ISO 3166-1 alpha-2 code
});

const validateForm = () => {
    const newErrors = {};

    // Validate phone number
    const phoneValidation = validatePhoneNumber(
        formData.phoneNumber,
        formData.country
    );

    if (!phoneValidation.valid) {
        newErrors.phoneNumber = phoneValidation.error;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
};
```

**Real-time Formatting** (As user types):
```javascript
import { formatAsYouType } from '../utils/phoneValidation';

const handlePhoneChange = (e) => {
    const value = e.target.value;
    const formatted = formatAsYouType(value, formData.country);

    setFormData(prev => ({
        ...prev,
        phoneNumber: formatted
    }));
};
```

**Country Selector with Phone Input**:
```javascript
import { COUNTRY_PHONE_CODES, getExampleNumber } from '../utils/phoneValidation';

<div className={styles.phoneInputGroup}>
    {/* Country Selector */}
    <select
        name="country"
        value={formData.country}
        onChange={handleCountryChange}
        className={styles.countrySelect}
    >
        {COUNTRY_PHONE_CODES.map(country => (
            <option key={country.code} value={country.code}>
                {country.flag} {country.name} ({country.dialCode})
            </option>
        ))}
    </select>

    {/* Phone Input */}
    <input
        type="tel"
        name="phoneNumber"
        value={formData.phoneNumber}
        onChange={handlePhoneChange}
        placeholder={getExampleNumber(formData.country)}
        className={styles.phoneInput}
    />
</div>
```

**Complete Example with Validation**:
```javascript
import {
    validatePhoneNumber,
    formatPhoneNumber,
    isMobileNumber
} from '../utils/phoneValidation';

const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate phone number
    const phoneValidation = validatePhoneNumber(
        formData.phoneNumber,
        formData.country
    );

    if (!phoneValidation.valid) {
        setErrors({ phoneNumber: phoneValidation.error });
        return;
    }

    // Check if mobile (optional requirement)
    if (!isMobileNumber(formData.phoneNumber, formData.country)) {
        setErrors({
            phoneNumber: 'Veuillez fournir un numéro de téléphone mobile'
        });
        return;
    }

    // Send formatted international number to backend
    const userData = {
        ...formData,
        phoneNumber: phoneValidation.international, // +15141234567
    };

    // Submit to backend...
};
```

### Backend - Django Views

**Using the Validator Function**:
```python
from accounts.validators import validate_phone_number
from django.core.exceptions import ValidationError

def register_user(request):
    phone_number = request.data.get('phone_number')
    country = request.data.get('country', None)  # ISO code like 'CA', 'US'

    try:
        # Validate and get formatted number
        result = validate_phone_number(phone_number, country)

        # Save formatted international number to database
        user.phone_number = result['formatted']  # +1 514 123 4567
        user.save()

    except ValidationError as e:
        return Response({'error': str(e)}, status=400)
```

**Using as Model Field Validator**:
```python
from accounts.validators import PhoneNumberValidator
from django.db import models

class UserProfile(models.Model):
    phone_number = models.CharField(
        max_length=20,
        validators=[PhoneNumberValidator(country_code='CA')]
    )

    # Or dynamic country-based validation
    country = models.CharField(max_length=2)  # 'CA', 'US', etc.
    phone_number = models.CharField(max_length=20)

    def clean(self):
        super().clean()
        from accounts.validators import validate_phone_number
        try:
            validate_phone_number(self.phone_number, self.country)
        except ValidationError as e:
            raise ValidationError({'phone_number': e})
```

**In Serializers**:
```python
from rest_framework import serializers
from accounts.validators import validate_phone_number

class RegistrationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2, required=False)

    def validate(self, data):
        phone = data.get('phone_number')
        country = data.get('country')

        try:
            result = validate_phone_number(phone, country)
            # Replace with formatted version
            data['phone_number'] = result['formatted']
        except ValidationError as e:
            raise serializers.ValidationError({
                'phone_number': str(e)
            })

        return data
```

## 🌍 Supported Countries

All countries are supported! The library includes validation rules for 200+ countries.

**Common Countries**:
- 🇨🇦 Canada (CA): +1
- 🇺🇸 United States (US): +1
- 🇫🇷 France (FR): +33
- 🇬🇧 United Kingdom (GB): +44
- 🇩🇪 Germany (DE): +49
- 🇧🇯 Benin (BJ): +229
- 🇨🇮 Côte d'Ivoire (CI): +225
- And many more...

## 📱 Phone Number Formats

### Input Formats (All Valid):
```
+1 514 123 4567       // International with spaces
+15141234567          // International compact
(514) 123-4567        // National (Canada/US)
514-123-4567          // National alternative
01 23 45 67 89        // National (France)
```

### Output Formats:
```javascript
// International: +1 514 123 4567
formatPhoneNumber(phone, 'CA', 'international')

// National: (514) 123-4567
formatPhoneNumber(phone, 'CA', 'national')

// E.164: +15141234567 (for APIs)
formatPhoneNumber(phone, 'CA', 'e164')

// URI: tel:+15141234567 (for tel: links)
formatPhoneNumber(phone, 'CA', 'uri')
```

## 🎨 UI Components Examples

### Country Selector Dropdown:
```javascript
<select value={country} onChange={e => setCountry(e.target.value)}>
    {COUNTRY_PHONE_CODES.map(c => (
        <option key={c.code} value={c.code}>
            {c.flag} {c.name} ({c.dialCode})
        </option>
    ))}
</select>
```

### Phone Input with Real-time Formatting:
```javascript
<input
    type="tel"
    value={phone}
    onChange={e => setPhone(formatAsYouType(e.target.value, country))}
    placeholder={getExampleNumber(country)}
/>
```

### Validation Error Display:
```javascript
{errors.phoneNumber && (
    <div className={styles.errorText}>
        {errors.phoneNumber}
    </div>
)}
```

## ⚠️ Important Notes

1. **Country Code Required**: For best validation, always provide the country code. If not provided, the number must start with '+' and country code (e.g., +1514...).

2. **Store International Format**: Always store phone numbers in international E.164 format in the database (`+15141234567`).

3. **Display National Format**: Show users the national format for their country for better UX.

4. **Mobile vs Landline**: Use `isMobileNumber()` if you need to verify it's a mobile number (for SMS, etc.).

5. **Error Messages**: All error messages are in French for better user experience.

## 🔍 Testing

**Frontend Test**:
```javascript
import { validatePhoneNumber } from './utils/phoneValidation';

// Test valid numbers
console.log(validatePhoneNumber('+1 514 123 4567', 'CA'));  // ✅ Valid
console.log(validatePhoneNumber('514 123 4567', 'CA'));     // ✅ Valid
console.log(validatePhoneNumber('01 23 45 67 89', 'FR'));   // ✅ Valid

// Test invalid numbers
console.log(validatePhoneNumber('123', 'CA'));              // ❌ Too short
console.log(validatePhoneNumber('abc', 'CA'));              // ❌ Not a number
```

**Backend Test**:
```python
from accounts.validators import validate_phone_number

# Test valid
result = validate_phone_number('+1 514 123 4567', 'CA')
print(result)  # {'valid': True, 'formatted': '+1 514 123 4567', ...}

# Test invalid
try:
    validate_phone_number('123', 'CA')
except ValidationError as e:
    print(e)  # "Phone number is too short."
```

## 🚀 Next Steps

1. **Install dependencies**: Run `pip install -r requirements.txt` and `npm install`
2. **Update SignUpPage.js**: Replace basic regex with `validatePhoneNumber()`
3. **Add country selector**: Use `COUNTRY_PHONE_CODES` for dropdown
4. **Test thoroughly**: Test with different countries and formats
5. **Add to other forms**: Apply to profile edit, contact forms, etc.

## 📚 Resources

- [libphonenumber (Python)](https://github.com/daviddrysdale/python-phonenumbers)
- [libphonenumber-js (JavaScript)](https://github.com/catamphetamine/libphonenumber-js)
- [Google's libphonenumber](https://github.com/google/libphonenumber)
- [ISO 3166-1 Country Codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
