import React, { useState, useEffect } from 'react';
import AsyncSelect from 'react-select/async';
import { communitiesAPI } from '../services/communitiesAPI';
import { searchService } from '../services/searchService';
import { useJWTAuth } from '../hooks/useJWTAuth';
import { RichTextEditorLight } from './ui';
// import StyledSelect from './ui/StyledSelect';
import {
  GlobeAltIcon,
  UserGroupIcon,
  UserPlusIcon,
  MapPinIcon,
  XMarkIcon,
  PhotoIcon,
  UserCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  PlusIcon,
  TrashIcon,
  SpeakerWaveIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import CommunityIcon from './ui/CommunityIcon';

const defaultTypes = [
  { id: 'public', label: 'Public', icon: GlobeAltIcon, description: 'Anyone can join and participate' },
  { id: 'private', label: 'Private', icon: UserPlusIcon, description: 'Invitation or approval required' },
  { id: 'restricted', label: 'Restricted', icon: UserGroupIcon, description: 'Limited membership with rules' }
];

const TYPE_COLOR = {
  public: 'green',
  private: 'gray',
  restricted: 'purple'
};

const CommunityForm = ({ visible, onClose, onSubmit, fields = [] }) => {
  const { user } = useJWTAuth(); // Get current user for follower search
  const [form, setForm] = useState({
    name: '',
    description: '',
    slug: '',
    community_type: defaultTypes[0].id,
    allow_posts: true,
    require_post_approval: false,
    allow_external_links: true,
    tags: '',
    cover_media: null,
    avatar: null,
    rules: [],
    moderators: [], // Selected moderators
    // Welcome message fields
    enable_welcome_message: false,
    welcome_message_title: '',
    welcome_message_content: '',
    welcome_message_banner_style: 'none',
  });

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [createdSlug, setCreatedSlug] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [ruleErrors, setRuleErrors] = useState([]);
  const [timezonesCache, setTimezonesCache] = useState(null);

  // Enhanced UI state
  const [coverImagePreview, setCoverImagePreview] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);

  // Real-time validation state
  const [geoValidationError, setGeoValidationError] = useState(null);

  useEffect(() => {
    if (!visible) {
      setForm({
        name: '',
        description: '',
        slug: '',
        community_type: defaultTypes[0].id,
        allow_posts: true,
        require_post_approval: false,
        allow_external_links: true,
        tags: '',
        cover_media: null,
        avatar: null,
        rules: [],
        moderators: [],
        // Welcome message fields
        enable_welcome_message: false,
        welcome_message_title: '',
        welcome_message_content: '',
        welcome_message_banner_style: 'none',
      });
      setError(null);
      setSubmitting(false);
      setRuleErrors([]);
      setCoverImagePreview(null);
      setAvatarPreview(null);
      setGeoValidationError(null);
    } else {
      // When modal opens, scroll to top after a short delay to ensure DOM is ready
      setTimeout(() => {
        const formElement = document.querySelector('[data-community-form-content]');
        if (formElement) {
          formElement.scrollTop = 0;
        }
      }, 100);
    }
  }, [visible]);

  const handleChange = (key) => (e) => {
    const value = e.target ? (e.target.type === 'checkbox' ? e.target.checked : e.target.value) : e;

    // Auto-generate slug from name
    if (key === 'name') {
      const slug = value.toLowerCase()
        .replace(/[^a-z0-9\\s-]/g, '')
        .replace(/\\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
      setForm(prev => ({ ...prev, [key]: value, slug }));
      return;
    }

    setForm(prev => ({ ...prev, [key]: value }));
  };

  const handleFileChange = (key) => (e) => {
    const file = e.target.files[0] || null;

    // For cover_media, also infer and set the media type
    if (key === 'cover_media' && file) {
      const isVideo = file.type.startsWith('video/');
      const isImage = file.type.startsWith('image/');

      if (isVideo || isImage) {
        setForm(prev => ({
          ...prev,
          [key]: file,
          cover_media_type: isVideo ? 'video' : 'image'
        }));
      } else {
        setForm(prev => ({ ...prev, [key]: file }));
      }
    } else {
      setForm(prev => ({ ...prev, [key]: file }));
    }

    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        if (key === 'cover_media') {
          setCoverImagePreview(event.target.result);
        } else if (key === 'avatar') {
          setAvatarPreview(event.target.result);
        }
      };
      reader.readAsDataURL(file);
    } else {
      if (key === 'cover_media') {
        setCoverImagePreview(null);
      } else if (key === 'avatar') {
        setAvatarPreview(null);
      }
    }
  };

  const onlyIncluded = (key) => fields.length === 0 || fields.includes(key);

  // Load moderator options - search through followers of the community creator
  const loadModeratorOptions = (inputValue, callback) => {
    // Return a Promise so react-select can handle it directly.
    return new Promise(async (resolve) => {
      try {
        console.debug('[CommunityForm] loadModeratorOptions called', { inputValue });

        if (!user?.profile?.id) {
          console.debug('[CommunityForm] no user profile id, returning empty options');
          const empty = [];
          if (typeof callback === 'function') callback(empty);
          return resolve(empty);
        }

        // Only search when input has at least 3 characters
        if (!inputValue || inputValue.trim().length === 0) {
          const empty = [];
          if (typeof callback === 'function') callback(empty);
          return resolve(empty);
        }

        const response = await searchService.searchUserFollowers(
          user.profile.id,
          inputValue,
          { limit: 20 }
        );

        const options = (response.users || []).map(follower => ({
          label: `${follower.displayName} (@${follower.username})`,
          value: follower.id,
          id: follower.id,
          meta: {
            username: follower.username,
            displayName: follower.displayName,
            avatar: follower.avatar,
            role: follower.role,
            isVerified: follower.isVerified
          }
        }));

        if (typeof callback === 'function') callback(options);
        resolve(options);
      } catch (err) {
        const empty = [];
        if (typeof callback === 'function') callback(empty);
        resolve(empty);
      }
    });
  };

  // Rules management
  const validateRules = (rules) => {
    const errs = [];
    const names = {};
    (rules || []).forEach((r) => {
      const n = (r && r.name) ? r.name.trim() : '';
      if (!n) return;
      names[n] = (names[n] || 0) + 1;
    });
    (rules || []).forEach((r, i) => {
      const n = (r && r.name) ? r.name.trim() : '';
      if (!n) {
        errs[i] = 'Name required';
      } else if (names[n] > 1) {
        errs[i] = 'Duplicate name';
      } else {
        errs[i] = '';
      }
    });
    return errs;
  };

  const addRule = () => {
    const newRules = [...(form.rules || []), { name: '', description: '' }];
    setForm(prev => ({ ...prev, rules: newRules }));
    setRuleErrors(validateRules(newRules));
  };

  const updateRule = (index, changes) => {
    const prevRules = [...(form.rules || [])];
    prevRules[index] = { ...prevRules[index], ...changes };
    setForm(prev => ({ ...prev, rules: prevRules }));
    setRuleErrors(validateRules(prevRules));
  };

  const removeRule = (index) => {
    const prevRules = [...(form.rules || [])];
    prevRules.splice(index, 1);
    setForm(prev => ({ ...prev, rules: prevRules }));
    setRuleErrors(validateRules(prevRules));
  };

  // Validation helper to check for conflicts between allowed and blocked lists
  const validateGeoRestrictions = () => {
    const validateOptions = (options, type) => {
      if (!Array.isArray(options)) return null;
      for (const option of options) {
        if (!option || typeof option !== 'object') {
          return `Invalid ${type} selection detected. Please refresh and reselect.`;
        }
        if (type === 'countries' || type === 'cities') {
          if (!option.id && !option.value) {
            return `Invalid ${type} selection detected. Please refresh and reselect.`;
          }
        } else if (type === 'timezones') {
          if (!option.value && !option.id) {
            return `Invalid ${type} selection detected. Please refresh and reselect.`;
          }
        }
      }
      return null;
    };

    const countryValidation = validateOptions(form.allowed_countries, 'countries') ||
                            validateOptions(form.blocked_countries, 'countries');
    if (countryValidation) return countryValidation;

    const cityValidation = validateOptions(form.allowed_cities, 'cities') ||
                         validateOptions(form.blocked_cities, 'cities');
    if (cityValidation) return cityValidation;

    const timezoneValidation = validateOptions(form.allowed_timezones, 'timezones') ||
                             validateOptions(form.blocked_timezones, 'timezones');
    if (timezoneValidation) return timezoneValidation;

    // Check for conflicts between allowed and blocked lists
    if (form.allowed_countries && form.blocked_countries &&
        form.allowed_countries.length > 0 && form.blocked_countries.length > 0) {
      const allowedIds = form.allowed_countries.map(c => c.id || c.value);
      const blockedIds = form.blocked_countries.map(c => c.id || c.value);
      const conflicts = allowedIds.filter(id => blockedIds.includes(id));
      if (conflicts.length > 0) {
        const conflictNames = form.allowed_countries
          .filter(c => conflicts.includes(c.id || c.value))
          .map(c => c.label || c.name)
          .join(', ');
        return `Countries cannot be both allowed and blocked: ${conflictNames}`;
      }
    }

    // Check city conflicts
    if (form.allowed_cities && form.blocked_cities &&
        form.allowed_cities.length > 0 && form.blocked_cities.length > 0) {
      const allowedIds = form.allowed_cities.map(c => c.id || c.value);
      const blockedIds = form.blocked_cities.map(c => c.id || c.value);
      const conflicts = allowedIds.filter(id => blockedIds.includes(id));
      if (conflicts.length > 0) {
        const conflictNames = form.allowed_cities
          .filter(c => conflicts.includes(c.id || c.value))
          .map(c => c.label || c.name)
          .join(', ');
        return `Cities cannot be both allowed and blocked: ${conflictNames}`;
      }
    }

    // Check timezone conflicts
    if (form.allowed_timezones && form.blocked_timezones &&
        form.allowed_timezones.length > 0 && form.blocked_timezones.length > 0) {
      const allowedIds = form.allowed_timezones.map(tz => tz.id || tz.value);
      const blockedIds = form.blocked_timezones.map(tz => tz.id || tz.value);
      const conflicts = allowedIds.filter(id => blockedIds.includes(id));
      if (conflicts.length > 0) {
        const conflictNames = form.allowed_timezones
          .filter(tz => conflicts.includes(tz.id || tz.value))
          .map(tz => tz.label || tz.value)
          .join(', ');
        return `Timezones cannot be both allowed and blocked: ${conflictNames}`;
      }
    }

    return null;
  };

  // Real-time validation helper with automatic duplicate removal
  const validateAndUpdateGeo = (newFormData) => {
    let cleanedFormData = { ...newFormData };
    let removedDuplicates = [];

    // Auto-remove duplicates between allowed and blocked lists
    if (cleanedFormData.geo_restriction_type === 'countries') {
      if (cleanedFormData.allowed_countries && cleanedFormData.blocked_countries &&
          cleanedFormData.allowed_countries.length > 0 && cleanedFormData.blocked_countries.length > 0) {
        const allowedIds = cleanedFormData.allowed_countries.map(c => c.id || c.value);
        const blockedIds = cleanedFormData.blocked_countries.map(c => c.id || c.value);
        const conflicts = allowedIds.filter(id => blockedIds.includes(id));

        if (conflicts.length > 0) {
          // Remove conflicts from the opposite list (keep the most recent selection)
          // If we just updated allowed_countries, remove conflicts from blocked_countries
          if (form.allowed_countries && newFormData.allowed_countries !== form.allowed_countries) {
            cleanedFormData.blocked_countries = cleanedFormData.blocked_countries.filter(c =>
              !conflicts.includes(c.id || c.value)
            );
            const conflictNames = form.blocked_countries
              ?.filter(c => conflicts.includes(c.id || c.value))
              ?.map(c => c.label || c.name) || [];
            if (conflictNames.length > 0) {
              removedDuplicates.push(`Removed ${conflictNames.join(', ')} from blocked countries`);
            }
          }
          // If we just updated blocked_countries, remove conflicts from allowed_countries
          else if (form.blocked_countries && newFormData.blocked_countries !== form.blocked_countries) {
            cleanedFormData.allowed_countries = cleanedFormData.allowed_countries.filter(c =>
              !conflicts.includes(c.id || c.value)
            );
            const conflictNames = form.allowed_countries
              ?.filter(c => conflicts.includes(c.id || c.value))
              ?.map(c => c.label || c.name) || [];
            if (conflictNames.length > 0) {
              removedDuplicates.push(`Removed ${conflictNames.join(', ')} from allowed countries`);
            }
          }
        }
      }
    } else if (cleanedFormData.geo_restriction_type === 'cities') {
      if (cleanedFormData.allowed_cities && cleanedFormData.blocked_cities &&
          cleanedFormData.allowed_cities.length > 0 && cleanedFormData.blocked_cities.length > 0) {
        const allowedIds = cleanedFormData.allowed_cities.map(c => c.id || c.value);
        const blockedIds = cleanedFormData.blocked_cities.map(c => c.id || c.value);
        const conflicts = allowedIds.filter(id => blockedIds.includes(id));

        if (conflicts.length > 0) {
          if (form.allowed_cities && newFormData.allowed_cities !== form.allowed_cities) {
            cleanedFormData.blocked_cities = cleanedFormData.blocked_cities.filter(c =>
              !conflicts.includes(c.id || c.value)
            );
            const conflictNames = form.blocked_cities
              ?.filter(c => conflicts.includes(c.id || c.value))
              ?.map(c => c.label || c.name) || [];
            if (conflictNames.length > 0) {
              removedDuplicates.push(`Removed ${conflictNames.join(', ')} from blocked cities`);
            }
          }
          else if (form.blocked_cities && newFormData.blocked_cities !== form.blocked_cities) {
            cleanedFormData.allowed_cities = cleanedFormData.allowed_cities.filter(c =>
              !conflicts.includes(c.id || c.value)
            );
            const conflictNames = form.allowed_cities
              ?.filter(c => conflicts.includes(c.id || c.value))
              ?.map(c => c.label || c.name) || [];
            if (conflictNames.length > 0) {
              removedDuplicates.push(`Removed ${conflictNames.join(', ')} from allowed cities`);
            }
          }
        }
      }
    } else if (cleanedFormData.geo_restriction_type === 'timezone_based') {
      if (cleanedFormData.allowed_timezones && cleanedFormData.blocked_timezones &&
          cleanedFormData.allowed_timezones.length > 0 && cleanedFormData.blocked_timezones.length > 0) {
        const allowedIds = cleanedFormData.allowed_timezones.map(tz => tz.id || tz.value);
        const blockedIds = cleanedFormData.blocked_timezones.map(tz => tz.id || tz.value);
        const conflicts = allowedIds.filter(id => blockedIds.includes(id));

        if (conflicts.length > 0) {
          if (form.allowed_timezones && newFormData.allowed_timezones !== form.allowed_timezones) {
            cleanedFormData.blocked_timezones = cleanedFormData.blocked_timezones.filter(tz =>
              !conflicts.includes(tz.id || tz.value)
            );
            const conflictNames = form.blocked_timezones
              ?.filter(tz => conflicts.includes(tz.id || tz.value))
              ?.map(tz => tz.label || tz.value) || [];
            if (conflictNames.length > 0) {
              removedDuplicates.push(`Removed ${conflictNames.join(', ')} from blocked timezones`);
            }
          }
          else if (form.blocked_timezones && newFormData.blocked_timezones !== form.blocked_timezones) {
            cleanedFormData.allowed_timezones = cleanedFormData.allowed_timezones.filter(tz =>
              !conflicts.includes(tz.id || tz.value)
            );
            const conflictNames = form.allowed_timezones
              ?.filter(tz => conflicts.includes(tz.id || tz.value))
              ?.map(tz => tz.label || tz.value) || [];
            if (conflictNames.length > 0) {
              removedDuplicates.push(`Removed ${conflictNames.join(', ')} from allowed timezones`);
            }
          }
        }
      }
    }

    // Update form with cleaned data
    setForm(cleanedFormData);

    // Show info message about removed duplicates instead of error
    if (removedDuplicates.length > 0) {
      setGeoValidationError(`✓ Auto-resolved duplicates: ${removedDuplicates.join('; ')}`);
      // Clear the message after 3 seconds
      setTimeout(() => setGeoValidationError(null), 3000);
    } else {
      setGeoValidationError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Check for geo-restriction conflicts first
    const geoConflictError = validateGeoRestrictions();
    if (geoConflictError) {
      setError(geoConflictError);
      return;
    }

    // Also check real-time validation error (but not success messages)
    if (geoValidationError && !geoValidationError.startsWith('✓')) {
      setError(geoValidationError);
      return;
    }

    if (!form.name.trim()) {
      setError('Community name is required');
      return;
    }

    // Geo validation: if geo_restricted, ensure proper selections
    if (form.is_geo_restricted) {
      if (form.geo_restriction_type === 'countries') {
        if ((!form.allowed_countries || form.allowed_countries.length === 0) &&
            (!form.blocked_countries || form.blocked_countries.length === 0)) {
          setError('Please select at least one country (either allowed or blocked) for country-based restrictions');
          return;
        }
      } else if (form.geo_restriction_type === 'cities') {
        if (!form.selected_country_for_cities) {
          setError('Please select a country for city-based restrictions');
          return;
        }
        if ((!form.allowed_cities || form.allowed_cities.length === 0) &&
            (!form.blocked_cities || form.blocked_cities.length === 0)) {
          setError('Please select at least one city (either allowed or blocked) for city-based restrictions');
          return;
        }
      } else if (form.geo_restriction_type === 'timezone_based') {
        if ((!form.allowed_timezones || form.allowed_timezones.length === 0) &&
            (!form.blocked_timezones || form.blocked_timezones.length === 0)) {
          setError('Please select at least one timezone (either allowed or blocked) for timezone-based restrictions');
          return;
        }
      }
    }

    const payload = {
      name: form.name,
      // slug intentionally omitted: backend will generate a unique slug
      description: form.description,
      community_type: form.community_type,
      allow_posts: form.allow_posts,
      require_post_approval: form.require_post_approval,
      allow_external_links: form.allow_external_links,
      is_geo_restricted: form.is_geo_restricted,
      geo_restriction_type: form.geo_restriction_type,
      geo_restriction_message: form.geo_restriction_message,
      tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : []
    };

    // Debug form state before processing
    console.log('🔍 Form state before processing:', {
      allowed_countries: form.allowed_countries,
      blocked_countries: form.blocked_countries,
      moderators: form.moderators,
      allowed_countries_type: Array.isArray(form.allowed_countries) ? 'array' : typeof form.allowed_countries,
      blocked_countries_type: Array.isArray(form.blocked_countries) ? 'array' : typeof form.blocked_countries,
      moderators_type: Array.isArray(form.moderators) ? 'array' : typeof form.moderators
    });

    // Helper function to ensure arrays are properly formatted
    const ensureArray = (value) => {
      if (!value) return [];
      if (Array.isArray(value)) return value;
      if (typeof value === 'string') return [value];
      return [value]; // Convert single objects to arrays
    };

    // Helper function to extract values from array items
    const extractValues = (array) => {
      const result = ensureArray(array).map(item => item?.id || item?.value || item);
      console.log('🔍 extractValues:', { input: array, ensured: ensureArray(array), result });
      return result;
    };

    // Add geo restrictions - ensure they're always arrays
    if (form.allowed_countries && (Array.isArray(form.allowed_countries) ? form.allowed_countries.length > 0 : form.allowed_countries)) {
      payload.allowed_countries = extractValues(form.allowed_countries);
    }
    if (form.blocked_countries && (Array.isArray(form.blocked_countries) ? form.blocked_countries.length > 0 : form.blocked_countries)) {
      payload.blocked_countries = extractValues(form.blocked_countries);
    }
    if (form.allowed_cities && (Array.isArray(form.allowed_cities) ? form.allowed_cities.length > 0 : form.allowed_cities)) {
      payload.allowed_cities = extractValues(form.allowed_cities);
    }
    if (form.blocked_cities && (Array.isArray(form.blocked_cities) ? form.blocked_cities.length > 0 : form.blocked_cities)) {
      payload.blocked_cities = extractValues(form.blocked_cities);
    }
    if (form.allowed_timezones && (Array.isArray(form.allowed_timezones) ? form.allowed_timezones.length > 0 : form.allowed_timezones)) {
      payload.allowed_timezones = extractValues(form.allowed_timezones);
    }
    if (form.blocked_timezones && (Array.isArray(form.blocked_timezones) ? form.blocked_timezones.length > 0 : form.blocked_timezones)) {
      payload.blocked_timezones = extractValues(form.blocked_timezones);
    }
    if (form.selected_country_for_cities) {
      payload.selected_country_for_cities = form.selected_country_for_cities?.id || form.selected_country_for_cities?.value || form.selected_country_for_cities;
    }

    // Add rules
    if (form.rules?.length) {
      // Validate rules before submission
      const errs = validateRules(form.rules);
      if (errs.some(Boolean)) {
        setError('Please fix rule errors before submitting');
        setRuleErrors(errs);
        return;
      }
      const rulesMap = {};
      form.rules.forEach(r => {
        if (r.name?.trim()) {
          rulesMap[r.name.trim()] = r.description || '';
        }
      });
      payload.rules = rulesMap;
    }

    // Add moderators - ensure they're always arrays
    if (form.moderators && (Array.isArray(form.moderators) ? form.moderators.length > 0 : form.moderators)) {
      payload.moderators = extractValues(form.moderators);
    }

    // Add welcome message fields
    if (form.enable_welcome_message) {
      payload.enable_welcome_message = form.enable_welcome_message;
      payload.welcome_message_title = form.welcome_message_title?.trim() || 'Welcome!';
      payload.welcome_message_content = form.welcome_message_content?.trim() || '';
      payload.welcome_message_banner_style = form.welcome_message_banner_style || 'none';
    }

    try {
      setSubmitting(true);

      // Handle file uploads
      const hasActualFiles = (form.cover_media instanceof File && form.cover_media.size > 0) ||
                            (form.avatar instanceof File && form.avatar.size > 0);

      // DEBUG: Check file detection
      console.log('🔍 File detection (FormData disabled for debugging):', {
        cover_media: form.cover_media,
        avatar: form.avatar,
        cover_media_instanceof_File: form.cover_media instanceof File,
        avatar_instanceof_File: form.avatar instanceof File,
        cover_media_size: form.cover_media instanceof File ? form.cover_media.size : 'N/A',
        avatar_size: form.avatar instanceof File ? form.avatar.size : 'N/A',
        hasActualFiles: hasActualFiles
      });

      let result = null;

      if (hasActualFiles) {
        // Only use FormData when we actually have files to upload
        const formData = new FormData();

        // Exclude file fields and read-only fields from payload when using FormData
        const payloadWithoutFiles = { ...payload };
        delete payloadWithoutFiles.cover_media;
        delete payloadWithoutFiles.avatar;
        delete payloadWithoutFiles.creator; // Read-only field
        delete payloadWithoutFiles.slug;    // Read-only field
        delete payloadWithoutFiles.id;      // Read-only field
        delete payloadWithoutFiles.created_at; // Read-only field
        delete payloadWithoutFiles.updated_at; // Read-only field

        Object.entries(payloadWithoutFiles).forEach(([key, value]) => {
          if (value !== null && value !== undefined) {
            if (Array.isArray(value)) {
              // Handle arrays properly - always ensure we send arrays correctly
              if (value.length === 0) {
                // For empty arrays, don't send anything (let Django handle the default)
                return;
              } else {
                // For non-empty arrays, append each item with the same key name
                value.forEach(item => formData.append(key, item));
              }
            } else if (typeof value === 'object') {
              formData.append(key, JSON.stringify(value));
            } else {
              formData.append(key, String(value));
            }
          }
        });

        // Add actual file objects only if they're File instances with content
        if (form.cover_media instanceof File && form.cover_media.size > 0) {
          console.log('📎 Adding cover_media file:', form.cover_media.name, form.cover_media.size, 'bytes');
          formData.append('cover_media', form.cover_media, form.cover_media.name);
        }
        if (form.avatar instanceof File && form.avatar.size > 0) {
          console.log('📎 Adding avatar file:', form.avatar.name, form.avatar.size, 'bytes');
          formData.append('avatar', form.avatar, form.avatar.name);
        }

        console.log('🔍 Using FormData mode');

        // Debug: Log FormData contents
        console.log('📋 FormData contents:');
        for (let [key, value] of formData.entries()) {
          if (value instanceof File) {
            console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
          } else {
            console.log(`  ${key}: ${value}`);
          }
        }

        result = await onSubmit(formData);
      } else {
        // No files, send regular JSON payload
        // Ensure read-only fields are excluded from JSON payload too
        const cleanPayload = { ...payload };
        delete cleanPayload.creator;
        delete cleanPayload.slug;
        delete cleanPayload.id;
        delete cleanPayload.created_at;
        delete cleanPayload.updated_at;

        console.log('🔍 Using JSON mode, payload:', cleanPayload);
        result = await onSubmit(cleanPayload);
      }

      // Try to extract slug from response (flexible to different response shapes)
      const extractSlug = (r) => {
        if (!r) return null;
        if (typeof r === 'string') return r; // unlikely, but handle
        if (r.slug) return r.slug;
        if (r.data && r.data.slug) return r.data.slug;
        if (r.url) return r.url.split('/').pop();
        return null;
      };

      const finalSlug = extractSlug(result);
      if (finalSlug) {
        setCreatedSlug(finalSlug);
        setSuccessMessage(`Community created — URL: /c/${finalSlug}`);
        // Give user a short moment to see the final slug before closing
        setTimeout(() => {
          setSuccessMessage(null);
          setCreatedSlug(null);
          onClose();
        }, 2500);
      } else {
        onClose();
      }
    } catch (err) {
      setError(err?.message || 'Failed to create community');
    } finally {
      setSubmitting(false);
    }
  };

  // Media upload handlers for RichTextEditor
  const handleImageUpload = async (file) => {
    try {
      // Create FormData to upload the file
      const formData = new FormData();
      formData.append('image', file);

      // You would implement your actual upload logic here
      // For now, we'll create a local URL
      const imageUrl = URL.createObjectURL(file);

      // In a real implementation, you would upload to your server:
      // const response = await fetch('/api/upload/image', {
      //   method: 'POST',
      //   body: formData,
      //   headers: {
      //     'Authorization': `Bearer ${token}`
      //   }
      // });
      // const result = await response.json();
      // return result.imageUrl;

      return imageUrl;
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  };

  const handleVideoUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('video', file);

      const videoUrl = URL.createObjectURL(file);

      // In a real implementation:
      // const response = await fetch('/api/upload/video', {
      //   method: 'POST',
      //   body: formData
      // });
      // const result = await response.json();
      // return result.videoUrl;

      return videoUrl;
    } catch (error) {
      console.error('Error uploading video:', error);
      throw error;
    }
  };

  const handleAudioUpload = async (file) => {
    try {
      const formData = new FormData();
      formData.append('audio', file);

      const audioUrl = URL.createObjectURL(file);

      // In a real implementation:
      // const response = await fetch('/api/upload/audio', {
      //   method: 'POST',
      //   body: formData
      // });
      // const result = await response.json();
      // return result.audioUrl;

      return audioUrl;
    } catch (error) {
      console.error('Error uploading audio:', error);
      throw error;
    }
  };

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop (clicking outside will no longer close the modal) */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
      />

      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-lg shadow-xl overflow-hidden">
        {/* Header */}
        <div className="bg-blue-600 px-6 py-4 text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Create New Community</h2>
            <button
              type="button"
              onClick={onClose}
              className="p-1 hover:bg-blue-700 rounded transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        {successMessage && (
          <div className="p-4 bg-green-50 border border-green-200 text-green-800">
            {successMessage}
          </div>
        )}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]" data-community-form-content>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-4 flex items-start space-x-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Basic Information</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {onlyIncluded('name') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Community Name *
                  </label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={handleChange('name')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter your community name"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                <input
                  type="text"
                  value={form.tags}
                  onChange={handleChange('tags')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="photography, travel, local (comma separated)"
                />
                <p className="text-xs text-gray-500 mt-1">Add tags to help users find this community (comma separated)</p>
              </div>
            </div>

            {onlyIncluded('description') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={form.description}
                  onChange={handleChange('description')}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  placeholder="Describe what your community is about..."
                />
              </div>
            )}

            {/* <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              <input
                type="text"
                value={form.tags}
                onChange={handleChange('tags')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="photography, travel, local (comma separated)"
              />
            </div> */}

            {onlyIncluded('community_type') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Community Type</label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {defaultTypes.map((type) => (
                    <label
                      key={type.id}
                      className={`flex items-center p-3 border rounded-md cursor-pointer hover:bg-gray-50 ${
                        form.community_type === type.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200'
                      }`}
                    >
                      <input
                        type="radio"
                        name="community_type"
                        value={type.id}
                        checked={form.community_type === type.id}
                        onChange={handleChange('community_type')}
                        className="sr-only"
                      />
                      <CommunityIcon Icon={type.icon} color={TYPE_COLOR[type.id]} size="sm" className="mr-3 flex-shrink-0" />
                      <div className="min-w-0">
                        <div className="font-medium text-gray-900 text-sm">{type.label}</div>
                        <div className="text-xs text-gray-600">{type.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Settings</h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={form.allow_posts}
                  onChange={handleChange('allow_posts')}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-3 text-sm text-gray-700 font-medium">Allow posts</span>
              </label>

              <label className={`flex items-center p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50 ${
                !form.allow_posts ? 'opacity-50 cursor-not-allowed' : ''
              }`}>
                <input
                  type="checkbox"
                  checked={form.require_post_approval}
                  onChange={handleChange('require_post_approval')}
                  disabled={!form.allow_posts}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-3 text-sm text-gray-700 font-medium">Require post approval</span>
              </label>

              <label className="flex items-center p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={form.allow_external_links}
                  onChange={handleChange('allow_external_links')}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="ml-3 text-sm text-gray-700 font-medium">Allow external links</span>
              </label>
            </div>
          </div>

          {/* Media Upload */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Media</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Cover Image */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                {coverImagePreview ? (
                  <div className="relative">
                    {form.cover_media && form.cover_media.type.startsWith('video/') ? (
                      <video src={coverImagePreview} className="w-full h-24 object-cover rounded" controls muted />
                    ) : (
                      <img src={coverImagePreview} alt="Cover preview" className="w-full h-24 object-cover rounded" />
                    )}
                    <button
                      type="button"
                      onClick={() => {
                        setForm(prev => ({ ...prev, cover_media: null }));
                        setCoverImagePreview(null);
                      }}
                      className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <PhotoIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                )}
                <h4 className="text-sm font-medium text-gray-900 mb-2">Cover Media (Image or Video)</h4>
                <label className="inline-flex items-center px-3 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-50">
                  <input type="file" accept="image/*,video/*" onChange={handleFileChange('cover_media')} className="hidden" />
                  {form.cover_media ? 'Change Media' : 'Select Image or Video'}
                </label>
              </div>

              {/* Avatar */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                {avatarPreview ? (
                  <div className="relative">
                    <img src={avatarPreview} alt="Avatar preview" className="w-16 h-16 object-cover rounded-full mx-auto" />
                    <button
                      type="button"
                      onClick={() => {
                        setForm(prev => ({ ...prev, avatar: null }));
                        setAvatarPreview(null);
                      }}
                      className="absolute top-0 right-1/2 translate-x-6 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>
                ) : (
                  <UserCircleIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                )}
                <h4 className="text-sm font-medium text-gray-900 mb-2">Community Avatar</h4>
                <label className="inline-flex items-center px-3 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-50">
                  <input type="file" accept="image/*" onChange={handleFileChange('avatar')} className="hidden" />
                  {form.avatar ? 'Change Avatar' : 'Select Avatar'}
                </label>
              </div>
            </div>
          </div>

          {/* Rules */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Community Rules</h3>
              <button
                type="button"
                onClick={addRule}
                className="inline-flex items-center px-3 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
              >
                <PlusIcon className="w-4 h-4 mr-1" />
                Add Rule
              </button>
            </div>

            <div className="space-y-3">
              {(form.rules || []).map((rule, index) => (
                <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium text-gray-700">Rule #{index + 1}</span>
                    <button
                      type="button"
                      onClick={() => removeRule(index)}
                      className="p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Rule name (e.g., 'Be respectful')"
                      value={rule.name || ''}
                      onChange={(e) => updateRule(index, { name: e.target.value })}
                      className={`w-full px-3 py-2 border rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                        ruleErrors[index] ? 'border-red-300' : 'border-gray-300'
                      }`}
                    />
                    <textarea
                      placeholder="Rule description (optional)"
                      value={rule.description || ''}
                      onChange={(e) => updateRule(index, { description: e.target.value })}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    />
                    {ruleErrors[index] && (
                      <p className="text-sm text-red-600">{ruleErrors[index]}</p>
                    )}
                  </div>
                </div>
              ))}

              {(!form.rules || form.rules.length === 0) && (
                <div className="text-center py-6 text-gray-500">
                  <p className="text-sm">No rules yet. Add some guidelines for your community.</p>
                </div>
              )}
            </div>
          </div>

          {/* Welcome Message */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Welcome Message</h3>
                <p className="text-sm text-gray-600">Create a custom welcome message for new community members</p>
              </div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={form.enable_welcome_message}
                  onChange={handleChange('enable_welcome_message')}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <SpeakerWaveIcon className="w-4 h-4 ml-3 mr-2 text-gray-600" />
                <span className="text-sm text-gray-700">Enable Welcome Message</span>
              </label>
            </div>

            {form.enable_welcome_message && (
              <div className="ml-7 space-y-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                {/* Welcome Message Title */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Welcome Message Title
                  </label>
                  <input
                    type="text"
                    value={form.welcome_message_title}
                    onChange={handleChange('welcome_message_title')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Welcome to the Community!"
                    maxLength={100}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Optional title for the welcome message (max 100 characters)
                  </p>
                </div>

                {/* Welcome Message Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Welcome Message Content *
                  </label>
                  <RichTextEditorLight
                    content={form.welcome_message_content}
                    onChange={(content) => setForm(prev => ({ ...prev, welcome_message_content: content }))}
                    placeholder="Write a warm welcome message for new members..."
                    maxLength={1000}
                    height="h-40"
                    className="bg-white"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Rich text welcome message that new members will see when joining
                  </p>
                </div>

                {/* Banner Style Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Display Style
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                    {[
                      {
                        value: 'none',
                        label: 'Regular',
                        description: 'Normal announcement',
                        icon: ChatBubbleLeftRightIcon,
                        color: 'gray'
                      },
                      {
                        value: 'static',
                        label: 'Static Banner',
                        description: 'Fixed banner display',
                        icon: SpeakerWaveIcon,
                        color: 'blue'
                      },
                      {
                        value: 'scrolling',
                        label: 'Scrolling',
                        description: 'Text scrolls horizontally',
                        icon: SpeakerWaveIcon,
                        color: 'green'
                      },
                      {
                        value: 'fade',
                        label: 'Fade',
                        description: 'Fades in and out',
                        icon: SpeakerWaveIcon,
                        color: 'purple'
                      },
                      {
                        value: 'slide',
                        label: 'Slide',
                        description: 'Slides in from side',
                        icon: SpeakerWaveIcon,
                        color: 'orange'
                      }
                    ].map((style) => (
                      <label
                        key={style.value}
                        className={`flex flex-col items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                          form.welcome_message_banner_style === style.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200'
                        }`}
                      >
                        <input
                          type="radio"
                          name="welcome_message_banner_style"
                          value={style.value}
                          checked={form.welcome_message_banner_style === style.value}
                          onChange={handleChange('welcome_message_banner_style')}
                          className="sr-only"
                        />
                        <CommunityIcon
                          Icon={style.icon}
                          color={style.color}
                          size="sm"
                          className="mb-2"
                        />
                        <div className="text-center">
                          <div className="font-medium text-gray-900 text-sm">{style.label}</div>
                          <div className="text-xs text-gray-600">{style.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>

                  {/* Banner Style Info */}
                  {['scrolling', 'fade', 'slide'].includes(form.welcome_message_banner_style) && (
                    <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="flex items-start">
                        <InformationCircleIcon className="w-4 h-4 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
                        <div className="text-sm text-yellow-800">
                          <p className="font-medium">Animation Banner Notice:</p>
                          <p>Animated banners (scrolling, fade, slide) are limited to 180 characters for optimal display.</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Welcome Message Preview */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Preview</h4>
                  <div className={`border rounded-md p-3 ${
                    form.welcome_message_banner_style === 'none'
                      ? 'bg-white border-gray-200'
                      : 'bg-blue-100 border-blue-300'
                  }`}>
                    {form.welcome_message_title && (
                      <h5 className="font-medium text-gray-900 mb-2">
                        {form.welcome_message_title}
                      </h5>
                    )}
                    <div
                      className="text-sm text-gray-700"
                      dangerouslySetInnerHTML={{
                        __html: form.welcome_message_content || '<p class="text-gray-400 italic">Welcome message content will appear here...</p>'
                      }}
                    />
                    {form.welcome_message_banner_style !== 'none' && (
                      <div className="mt-2 text-xs text-blue-600 font-medium">
                        Banner Style: {form.welcome_message_banner_style}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Moderator Selection */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Community Moderators</h3>
                <p className="text-sm text-gray-600">Select users from your followers to help moderate this community</p>
              </div>
              <div className="flex items-center text-sm text-blue-600">
                <UserGroupIcon className="w-4 h-4 mr-1" />
                <span>{form.moderators?.length || 0} selected</span>
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search Your Followers
              </label>
              <AsyncSelect
                cacheOptions
                defaultOptions={false}
                isMulti
                loadOptions={loadModeratorOptions}
                onChange={(selected) => setForm(prev => ({ ...prev, moderators: selected || [] }))}
                value={form.moderators}
                placeholder="Type to search your followers..."
                className="text-sm"
                formatOptionLabel={(option) => (
                  <div className="flex items-center py-1">
                    <div className="flex-shrink-0 mr-3">
                      {option.meta?.avatar ? (
                        <img
                          src={option.meta.avatar}
                          alt={option.meta.displayName}
                          className="w-8 h-8 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-medium">
                          {(option.meta?.displayName || option.meta?.username || 'U')[0].toUpperCase()}
                        </div>
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900">
                          {option.meta?.displayName || option.meta?.username}
                        </span>
                        {option.meta?.isVerified && (
                          <div className="ml-1 w-4 h-4 text-blue-500">
                            ✓
                          </div>
                        )}
                      </div>
                      <div className="text-xs text-gray-500">
                        @{option.meta?.username}
                        {option.meta?.role !== 'standard' && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {option.meta.role}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                noOptionsMessage={() => "No followers found"}
              />

              {form.moderators && form.moderators.length > 0 && (
                <div className="mt-3">
                  <p className="text-sm font-medium text-gray-700 mb-2">Selected Moderators:</p>
                  <div className="flex flex-wrap gap-2">
                    {form.moderators.map((mod, index) => (
                      <div key={index} className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                        <span>{mod.meta?.displayName || mod.meta?.username || mod.label}</span>
                        <button
                          type="button"
                          onClick={() => {
                            const updated = form.moderators.filter((_, i) => i !== index);
                            setForm(prev => ({ ...prev, moderators: updated }));
                          }}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          <XMarkIcon className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-start">
                <InformationCircleIcon className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">About Community Moderators:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Only your followers can be selected as moderators</li>
                    <li>Moderators can help manage posts, comments, and community guidelines</li>
                    <li>You can add or remove moderators after community creation</li>
                    <li>Moderators will be notified of their role when the community is created</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="border-t bg-gray-50 px-6 py-4 flex items-center justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={submitting || !form.name.trim()}
            className={`px-4 py-2 text-sm font-medium rounded-md ${
              submitting || !form.name.trim()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {submitting ? 'Creating...' : 'Create Community'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CommunityForm;
