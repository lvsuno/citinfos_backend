# 🧪 Quick Testing Guide - Phone Country Auto-Detection

## 🚀 Quick Start

### Test 1: Verify Auto-Detection Works

1. **Open browser console** (F12)
2. **Navigate to** `/signup`
3. **Check console output:**

```javascript
// Expected output:
🌍 Detecting user country for phone validation...
✅ User country detected: {
  name: 'Canada',  // or your actual country
  iso3: 'CAN',
  city: 'Montreal'
}
📱 Setting phone country: CA (from CAN)
```

4. **Check the country selector:**
   - Should show your country's flag and dial code
   - Example: If in Canada → 🇨🇦 +1
   - Example: If in Benin → 🇧🇯 +229

### Test 2: Verify 120+ Countries Available

1. **Click the country dropdown**
2. **Scroll through the list**
3. **Verify you see regional groupings:**
   - North America (3 countries)
   - West Africa (13 countries)
   - Central Africa (6 countries)
   - East Africa (6 countries)
   - And many more...

### Test 3: Test Phone Validation

#### For Canadian Users (🇨🇦):
```
1. Country selector: 🇨🇦 +1 (should be auto-selected)
2. Enter: 514-123-4567
3. See real-time format: (514) 123-4567
4. Submit: Sends +15141234567
```

#### For Benin Users (🇧🇯):
```
1. Country selector: 🇧🇯 +229 (should be auto-selected)
2. Enter: 97123456
3. See real-time format: 97 12 34 56
4. Submit: Sends +22997123456
```

#### For French Users (🇫🇷):
```
1. Country selector: 🇫🇷 +33 (should be auto-selected)
2. Enter: 123456789
3. See real-time format: 1 23 45 67 89
4. Submit: Sends +33123456789
```

## 🔍 Console Commands for Testing

### Test ISO3 to ISO2 Conversion

Open browser console and run:

```javascript
// Import the function (if module available in console)
// Or check network tab for API responses

// Check what the backend returns
fetch('/auth/location-data/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ip_address: null })
})
.then(r => r.json())
.then(data => {
  console.log('Backend country:', data.country);
  console.log('ISO3 code:', data.country?.iso3);
});
```

### Check Current Form State

```javascript
// If React DevTools installed:
// 1. Open React DevTools
// 2. Select SignUpPage component
// 3. Check formData state
// 4. Verify phoneCountry is set to correct ISO2 code

// Example expected state:
// formData: {
//   phoneCountry: 'BJ',  // for Benin
//   phoneNumber: '',
//   ...
// }
```

## 📋 Test Scenarios Checklist

### ✅ Auto-Detection Tests

- [ ] **Test from Canada**
  - Navigate to `/signup`
  - Verify 🇨🇦 +1 is auto-selected
  - Check console shows "ISO3: CAN" → "ISO2: CA"

- [ ] **Test from Benin** (or use VPN)
  - Navigate to `/signup`
  - Verify 🇧🇯 +229 is auto-selected
  - Check console shows "ISO3: BEN" → "ISO2: BJ"

- [ ] **Test from France** (or use VPN)
  - Navigate to `/signup`
  - Verify 🇫🇷 +33 is auto-selected
  - Check console shows "ISO3: FRA" → "ISO2: FR"

### ✅ Fallback Tests

- [ ] **Test with VPN blocking geolocation**
  - Should fall back to CA
  - Console shows: "⚠️ Could not detect user country, using default CA"

- [ ] **Test with unknown country**
  - Manually test ISO3 code not in mapping
  - Should fall back to CA with warning

### ✅ Phone Validation Tests

- [ ] **Test Canadian number**
  - Country: CA
  - Input: 514-123-4567
  - Expected format: (514) 123-4567
  - Expected submit: +15141234567

- [ ] **Test Benin number**
  - Country: BJ
  - Input: 97123456
  - Expected format: 97 12 34 56
  - Expected submit: +22997123456

- [ ] **Test French number**
  - Country: FR
  - Input: 123456789
  - Expected format: 1 23 45 67 89
  - Expected submit: +33123456789

- [ ] **Test invalid number**
  - Country: Any
  - Input: 123
  - Expected: Error message "Le numéro de téléphone est invalide pour..."

### ✅ UI Tests

- [ ] **Dropdown shows all countries**
  - Open dropdown
  - Scroll to bottom
  - Verify 120+ countries visible

- [ ] **Regional grouping visible**
  - Countries organized by region
  - Flags display correctly
  - Dial codes show correctly

- [ ] **Country change works**
  - Select different country
  - Phone input placeholder updates
  - Format changes for new country

## 🐛 Common Issues & Solutions

### Issue 1: Country Not Auto-Detected
```
Symptom: Always shows Canada (CA)
Check:
1. Open console - any errors?
2. Check network tab - /auth/location-data/ called?
3. Check response - country.iso3 present?
4. Check ISO3_TO_ISO2_MAP - mapping exists?

Fix:
- Verify backend geolocation service is running
- Check GeoLite2 database is loaded
- Verify ISO3 code has mapping in phoneValidation.js
```

### Issue 2: Wrong Country Selected
```
Symptom: Shows wrong country (e.g., shows US instead of CA)
Check:
1. Console log - what ISO3 was detected?
2. ISO3_TO_ISO2_MAP - correct mapping?
3. COUNTRY_PHONE_CODES - ISO2 code exists?

Fix:
- Verify ISO3_TO_ISO2_MAP has correct mapping
- Check backend returns correct country data
- Clear cache and reload
```

### Issue 3: Phone Validation Fails
```
Symptom: Valid numbers show as invalid
Check:
1. Correct country selected?
2. Using ISO2 code (not ISO3)?
3. Number format valid for that country?

Fix:
- Double-check ISO2 code in dropdown
- Test with example number for that country
- Check libphonenumber-js supports country
```

### Issue 4: Dropdown Shows Old Country List
```
Symptom: Only 17 countries visible
Check:
1. Clear browser cache
2. Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
3. Check phoneValidation.js loaded new version

Fix:
- Stop frontend container
- Rebuild: docker compose build frontend
- Start: docker compose up -d frontend
```

## 📊 Expected Console Output Examples

### Successful Detection (Benin):
```
🌍 Detecting user country for phone validation...
✅ User country detected: {
  name: "Benin",
  iso3: "BEN",
  city: "Cotonou"
}
📱 Setting phone country: BJ (from BEN)
```

### Successful Detection (Canada):
```
🌍 Detecting user country for phone validation...
✅ User country detected: {
  name: "Canada",
  iso3: "CAN",
  city: "Montreal"
}
📱 Setting phone country: CA (from CAN)
```

### Successful Detection (Nigeria - newly supported):
```
🌍 Detecting user country for phone validation...
✅ User country detected: {
  name: "Nigeria",
  iso3: "NGA",
  city: "Lagos"
}
📱 Setting phone country: NG (from NGA)
```

### Failed Detection (Fallback):
```
🌍 Detecting user country for phone validation...
⚠️ Could not detect user country, using default CA
```

### Unknown Country (Warning):
```
🌍 Detecting user country for phone validation...
✅ User country detected: {
  name: "Antarctica",
  iso3: "ATA",
  city: "McMurdo Station"
}
⚠️ No ISO2 mapping found for ISO3 code: ATA. Using default 'CA'.
📱 Setting phone country: CA (from ATA)
```

## 🎯 Quick Verification Checklist

Before considering this feature complete, verify:

- [ ] `/signup` page loads without errors
- [ ] Console shows country detection logs
- [ ] Country selector shows detected country
- [ ] Dropdown contains 120+ countries
- [ ] Countries are grouped by region
- [ ] Flags and dial codes display correctly
- [ ] Phone number formats in real-time
- [ ] Validation works for detected country
- [ ] Fallback to CA works if detection fails
- [ ] No JavaScript errors in console
- [ ] No TypeScript errors (if using TS)

## 🎉 Success Indicators

You'll know it's working when:

1. **Console shows detection:**
   ```
   ✅ User country detected: { name: "Your Country", iso3: "XXX" }
   📱 Setting phone country: XX (from XXX)
   ```

2. **UI shows your country:**
   - Dropdown pre-selected with your flag
   - Dial code matches your country
   - Placeholder shows local format

3. **Validation works:**
   - Enter local phone number
   - Formats correctly
   - No validation errors
   - Submits in E.164 format (+XXXXXXXXXXXX)

## 📞 Support

If issues persist:
1. Check both documentation files created
2. Review console logs for specific errors
3. Test with different countries/VPNs
4. Verify backend geolocation service is working
5. Check ISO3_TO_ISO2_MAP for your country

---

**Happy Testing! 🚀**

The auto-detection should now work seamlessly for users from 120+ countries worldwide!
