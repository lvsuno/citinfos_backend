import { useState, useEffect, useRef } from 'react';
import { useJWTAuth } from '../hooks/useJWTAuth';
import axios from 'axios';
import Select from 'react-select';
import { FaUser, FaEnvelope, FaLock, FaPhone, FaBirthdayCake, FaGlobe, FaCity, FaInfoCircle, FaMapMarkerAlt } from 'react-icons/fa';
import { EyeIcon, EyeSlashIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline';
import PasswordGenerator from '../components/PasswordGenerator';
import SocialLoginButtons from '../components/SocialLoginButtons';
import { SecureForm } from '../components/SecureForm';
import {
  clearPasswordField,
  clearPasswordState,
  preventDevToolsPasswordExposure
} from '../utils/passwordSecurity';

const Register = ({ onSuccess }) => {
  const { register } = useJWTAuth();

  // Password field refs for security
  const passwordInputRef = useRef(null);
  const passwordConfirmInputRef = useRef(null);

  const [form, setForm] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    phone_number: '',
    date_of_birth: '',
    bio: '',
    country: '',
    city: '',
    address: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showVerifyButton, setShowVerifyButton] = useState(false);

  // Security setup
  useEffect(() => {
    preventDevToolsPasswordExposure();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (name === 'password') setPasswordStrength(getPasswordStrength(value));
  };

  // Address autocomplete
  const [addressOptions, setAddressOptions] = useState([]);
  const [addressLoading, setAddressLoading] = useState(false);
  const [addressInput, setAddressInput] = useState('');

  useEffect(() => {
    const handler = setTimeout(async () => {
      if (!addressInput || addressInput.length < 3) {
        setAddressOptions([]);
        setAddressLoading(false);
        return;
      }
      setAddressLoading(true);
      try {
        const res = await axios.get('http://localhost:4000/autocomplete', {
          params: { q: addressInput },
          timeout: 3000,
        });
        setAddressOptions((res.data || []).map((item) => {
          const parts = [];
          if (item.full_addr) parts.push(item.full_addr);
          if (item.postal_code) parts.push(item.postal_code);
          if (item.provice) parts.push(item.provice);
          parts.push('Canada');
          const label = parts.join(', ');
          return { label, value: label };
        }));
      } catch (e) {
        setAddressOptions([]);
      } finally {
        setAddressLoading(false);
      }
    }, 400);
    return () => clearTimeout(handler);
  }, [addressInput]);

  const handleAddressInputChange = (inputValue) => {
    setAddressInput(inputValue);
    return inputValue;
  };
  const handleAddressSelect = (option) => {
    if (option) {
      setForm((prev) => ({ ...prev, address: option.value }));
      setAddressInput('');
    } else {
      setForm((prev) => ({ ...prev, address: '' }));
      setAddressInput('');
    }
  };
  const handleAddressBlur = () => {
    if (addressInput && addressInput !== form.address) {
      setForm((prev) => ({ ...prev, address: addressInput }));
    }
  };

  function getPasswordStrength(password) {
    if (!password) return '';
    if (password.length < 6) return 'Weak';
    if (/^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).{8,}$/.test(password)) return 'Strong';
    if (password.length >= 8) return 'Medium';
    return 'Weak';
  }

  const handlePasswordSelect = (password) => {
    setForm(prev => ({ ...prev, password }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    setShowVerifyButton(false);

    try {
      const result = await register(form);
      localStorage.setItem('pendingEmail', form.email);
      setSuccess('Registration successful! Please verify your account.');

      // Clear password fields immediately after successful registration
      clearPasswordField(passwordInputRef.current);
      clearPasswordField(passwordConfirmInputRef.current);
      clearPasswordState(password => setForm(prev => ({ ...prev, password: '' })));
      clearPasswordState(password_confirm => setForm(prev => ({ ...prev, password_confirm: '' })));

      if (onSuccess) {
        onSuccess();
      } else {
        setShowVerifyButton(true);
      }
    } catch (err) {
      console.error('Registration error:', err);
      setError(err?.response?.data?.message || err?.message || 'Registration failed. Please try again.');

      // Clear passwords even on error to prevent exposure
      clearPasswordField(passwordInputRef.current);
      clearPasswordField(passwordConfirmInputRef.current);
      clearPasswordState(password => setForm(prev => ({ ...prev, password: '' })));
      clearPasswordState(password_confirm => setForm(prev => ({ ...prev, password_confirm: '' })));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh] bg-gradient-to-br from-blue-100 to-purple-200">
      <div className="w-full max-w-xl max-h-[80vh] overflow-auto bg-white rounded-2xl shadow-2xl p-6 animate-fade-in">
        <h2 className="text-2xl font-bold text-center text-blue-700 mb-6 flex items-center justify-center gap-2">
          <FaUser className="text-blue-500" /> Create Your Account
        </h2>

        {/* Social Registration Section */}
        <div className="mb-6">
          <SocialLoginButtons
            onSuccess={(result) => {
              // Handle successful social registration
              if (onSuccess) {
                onSuccess();
              }
            }}
            onError={(errorMessage) => {
              setError(errorMessage);
            }}
            isRegistering={true}
          />
        </div>

        <SecureForm onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <FaUser className="absolute left-3 top-3 text-gray-400" />
              <input name="username" placeholder="Username" value={form.username} onChange={handleChange} required className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
            <div className="relative">
              <FaEnvelope className="absolute left-3 top-3 text-gray-400" />
              <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} required className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
            <div className="relative">
              <FaUser className="absolute left-3 top-3 text-gray-400" />
              <input name="first_name" placeholder="First Name" value={form.first_name} onChange={handleChange} required className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
            <div className="relative">
              <FaUser className="absolute left-3 top-3 text-gray-400" />
              <input name="last_name" placeholder="Last Name" value={form.last_name} onChange={handleChange} required className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-2 relative">
              <div className="relative w-full">
                <FaLock className="absolute left-3 top-3 text-gray-400" />
                <input
                  ref={passwordInputRef}
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={form.password}
                  onChange={handleChange}
                  required
                  data-lpignore="true"
                  autoComplete="new-password"
                  className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300"
                />
                <button type="button" onClick={() => setShowPassword((v) => !v)} className="absolute right-3 top-2 text-blue-500 hover:bg-blue-100 rounded-full p-1">
                  {showPassword ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
                </button>
                {form.password && (
                  <div className={`mt-1 text-xs font-semibold ${passwordStrength === 'Strong' ? 'text-green-600' : passwordStrength === 'Medium' ? 'text-yellow-600' : 'text-red-600'}`}>Strength: {passwordStrength}</div>
                )}
              </div>
              <div className="flex items-center gap-1">
                <PasswordGenerator onPasswordSelect={handlePasswordSelect} />
                <div className="relative group">
                  <button type="button" tabIndex={-1} className="text-blue-400 hover:text-blue-600">
                    <QuestionMarkCircleIcon className="h-5 w-5" />
                  </button>
                  <div className="hidden group-hover:block absolute right-0 mt-2 w-64 bg-white border border-blue-200 rounded-lg shadow-lg p-3 text-xs text-gray-700 z-20">
                    <strong>Password tips:</strong>
                    <ul className="list-disc ml-4 mt-1">
                      <li>At least 8 characters</li>
                      <li>Include uppercase and lowercase letters</li>
                      <li>Include numbers</li>
                      <li>Include special characters (!@#$%^&*)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            <div className="relative">
              <FaLock className="absolute left-3 top-3 text-gray-400" />
              <input
                ref={passwordConfirmInputRef}
                name="password_confirm"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm Password"
                value={form.password_confirm}
                onChange={handleChange}
                required
                data-lpignore="true"
                autoComplete="new-password"
                className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300"
              />
              <button type="button" onClick={() => setShowConfirmPassword((v) => !v)} className="absolute right-3 top-2 text-blue-500 hover:bg-blue-100 rounded-full p-1">
                {showConfirmPassword ? <EyeSlashIcon className="h-5 w-5" /> : <EyeIcon className="h-5 w-5" />}
              </button>
              {form.password_confirm && form.password !== form.password_confirm && (
                <div className="mt-1 text-xs text-red-600 font-semibold">Passwords do not match</div>
              )}
            </div>
          </div>

          {/* Address with autocomplete */}
          <div className="relative">
            <FaMapMarkerAlt className="absolute left-3 top-3 text-gray-400 z-10" />
            <Select
              classNamePrefix="react-select"
              placeholder="Address (start typing for suggestions)"
              isClearable
              isLoading={addressLoading}
              options={addressOptions}
              value={form.address ? { label: form.address, value: form.address } : null}
              inputValue={addressInput}
              onInputChange={handleAddressInputChange}
              onChange={handleAddressSelect}
              onBlur={handleAddressBlur}
              filterOption={() => true}
              isSearchable
              styles={{ control: (base) => ({ ...base, paddingLeft: '2.5rem', minHeight: '2.5rem' }), menu: (base) => ({ ...base, zIndex: 20 }) }}
              components={{ DropdownIndicator: () => null }}
              noOptionsMessage={() => 'Type to search addresses or enter manually'}
              inputId="address-autocomplete"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <FaPhone className="absolute left-3 top-3 text-gray-400" />
              <input name="phone_number" placeholder="Phone Number" value={form.phone_number} onChange={handleChange} required className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
            <div className="relative">
              <FaBirthdayCake className="absolute left-3 top-3 text-gray-400" />
              <input name="date_of_birth" type="date" placeholder="Date of Birth" value={form.date_of_birth} onChange={handleChange} required className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>

          <div className="relative">
            <FaInfoCircle className="absolute left-3 top-3 text-gray-400" />
            <textarea name="bio" placeholder="Bio (Tell us about yourself)" value={form.bio} onChange={handleChange} className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300 min-h-[60px]" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <FaGlobe className="absolute left-3 top-3 text-gray-400" />
              <input name="country" placeholder="Country" value={form.country} onChange={handleChange} className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
            <div className="relative">
              <FaCity className="absolute left-3 top-3 text-gray-400" />
              <input name="city" placeholder="City" value={form.city} onChange={handleChange} className="pl-10 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-300" />
            </div>
          </div>

          <button type="submit" disabled={loading} className="w-full py-3 mt-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold rounded-lg shadow-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {loading ? (<span className="animate-spin mr-2">🔄</span>) : (<FaUser />)}
            {loading ? 'Registering...' : 'Register'}
          </button>
        </SecureForm>

        {error && <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-center animate-shake">{error}</div>}
        {success && (
          <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-lg text-center animate-fade-in">
            {success}
            {showVerifyButton && (
              <div className="mt-2 text-sm text-gray-600">Return to the login page to complete verification.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Register;
