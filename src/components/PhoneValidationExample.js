/**
 * Example Phone Validation Component
 * Demonstrates how to use the phone validation utilities
 */

import React, { useState } from 'react';
import {
    validatePhoneNumber,
    formatPhoneNumber,
    formatAsYouType,
    isMobileNumber,
    getCountryFromNumber,
    COUNTRY_PHONE_CODES
} from '../utils/phoneValidation';

const PhoneValidationExample = () => {
    const [phone, setPhone] = useState('');
    const [country, setCountry] = useState('CA');
    const [validationResult, setValidationResult] = useState(null);

    const handlePhoneChange = (e) => {
        const value = e.target.value;
        // Format as user types
        const formatted = formatAsYouType(value, country);
        setPhone(formatted);

        // Validate in real-time
        const result = validatePhoneNumber(formatted, country);
        setValidationResult(result);
    };

    const handleCountryChange = (e) => {
        setCountry(e.target.value);
        setPhone(''); // Clear phone when country changes
        setValidationResult(null);
    };

    return (
        <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
            <h2>Phone Validation Demo</h2>

            {/* Country Selector */}
            <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '8px' }}>
                    Country:
                </label>
                <select
                    value={country}
                    onChange={handleCountryChange}
                    style={{
                        width: '100%',
                        padding: '10px',
                        fontSize: '16px',
                        borderRadius: '8px'
                    }}
                >
                    {COUNTRY_PHONE_CODES.map(c => (
                        <option key={c.code} value={c.code}>
                            {c.flag} {c.name} ({c.dialCode})
                        </option>
                    ))}
                </select>
            </div>

            {/* Phone Input */}
            <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '8px' }}>
                    Phone Number:
                </label>
                <input
                    type="tel"
                    value={phone}
                    onChange={handlePhoneChange}
                    placeholder={`Enter phone number for ${country}`}
                    style={{
                        width: '100%',
                        padding: '10px',
                        fontSize: '16px',
                        borderRadius: '8px',
                        border: validationResult?.valid === false ? '2px solid red' : '1px solid #ccc'
                    }}
                />
            </div>

            {/* Validation Results */}
            {validationResult && (
                <div style={{
                    padding: '15px',
                    borderRadius: '8px',
                    backgroundColor: validationResult.valid ? '#d4edda' : '#f8d7da',
                    border: `1px solid ${validationResult.valid ? '#c3e6cb' : '#f5c6cb'}`,
                    marginBottom: '20px'
                }}>
                    <h3 style={{
                        color: validationResult.valid ? '#155724' : '#721c24',
                        marginTop: 0
                    }}>
                        {validationResult.valid ? '✓ Valid Phone Number' : '✗ Invalid Phone Number'}
                    </h3>

                    {validationResult.valid ? (
                        <div style={{ fontSize: '14px', color: '#155724' }}>
                            <p><strong>International:</strong> {validationResult.international}</p>
                            <p><strong>National:</strong> {validationResult.national}</p>
                            <p><strong>Formatted:</strong> {validationResult.formatted}</p>
                            <p><strong>Country:</strong> {validationResult.countryCode}</p>
                            <p><strong>Type:</strong> {validationResult.type || 'N/A'}</p>
                            <p><strong>Is Mobile:</strong> {isMobileNumber(phone, country) ? 'Yes' : 'No'}</p>
                        </div>
                    ) : (
                        <p style={{ color: '#721c24', marginBottom: 0 }}>
                            {validationResult.error}
                        </p>
                    )}
                </div>
            )}

            {/* Examples */}
            <div style={{
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                marginTop: '20px'
            }}>
                <h4>Example Valid Numbers:</h4>
                <ul style={{ fontSize: '14px' }}>
                    <li><strong>Canada (CA):</strong> +1 514 123 4567 or 514 123 4567</li>
                    <li><strong>USA (US):</strong> +1 202 555 0123 or (202) 555-0123</li>
                    <li><strong>France (FR):</strong> +33 6 12 34 56 78 or 06 12 34 56 78</li>
                    <li><strong>Benin (BJ):</strong> +229 97 12 34 56 or 97 12 34 56</li>
                    <li><strong>UK (GB):</strong> +44 7911 123456 or 07911 123456</li>
                </ul>
            </div>

            {/* API Usage Example */}
            <div style={{
                padding: '15px',
                backgroundColor: '#e7f3ff',
                borderRadius: '8px',
                marginTop: '20px',
                fontSize: '14px'
            }}>
                <h4>Code Example:</h4>
                <pre style={{
                    backgroundColor: '#f5f5f5',
                    padding: '10px',
                    borderRadius: '4px',
                    overflow: 'auto'
                }}>
{`import { validatePhoneNumber } from './utils/phoneValidation';

const result = validatePhoneNumber('514 123 4567', 'CA');

if (result.valid) {  // Output: +15141234567  // Output: +1 514 123 4567  // Output: (514) 123-4567
}`}
                </pre>
            </div>
        </div>
    );
};

export default PhoneValidationExample;
