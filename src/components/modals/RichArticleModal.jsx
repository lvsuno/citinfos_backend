import React, { useState, useEffect, useRef } from 'react';
import { XMarkIcon, EyeIcon, CodeBracketIcon } from '@heroicons/react/24/outline';
import RichTextEditor from '../ui/RichTextEditor';
import { useAuth } from '../../contexts/AuthContext';
import contentAPI from '../../services/contentAPI';

const RichArticleModal = ({
  isOpen,
  onClose,
  division,
  section,
  community,
  onSubmit
}) => {
  const { user } = useAuth();

  // Content state
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [excerpt, setExcerpt] = useState('');
  const [featuredImage, setFeaturedImage] = useState(null);
  const [visibility, setVisibility] = useState('public');

  // UI state
  const [mode, setMode] = useState('edit'); // edit | preview
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [autoSaveStatus, setAutoSaveStatus] = useState(''); // 'saving' | 'saved' | 'error'

  // Draft management
  const [draftId, setDraftId] = useState(null); // Track the backend draft ID
  const lastSaveRef = useRef(null); // Track last save timestamp
  const lastContentRef = useRef({ title: '', content: '', excerpt: '' }); // Track last saved content

  // Track previous section to detect changes
  const prevSectionRef = useRef(section);

  // Auto-save to localStorage (deprecated - keeping for backward compatibility)
  useEffect(() => {
    if (!isOpen) return;

    const savedDraft = localStorage.getItem('article_draft');
    if (savedDraft) {
      try {
        const draft = JSON.parse(savedDraft);
        if (draft.title) setTitle(draft.title);
        if (draft.content) setContent(draft.content);
        if (draft.excerpt) setExcerpt(draft.excerpt);
      } catch (err) {
        console.error('Failed to load draft:', err);
      }
    }
  }, [isOpen]);

  // Backend auto-save with hybrid strategy
  // - Debounce: Save 5 seconds after user stops typing
  // - Max interval: Force save every 60 seconds if typing continuously
  // - Change detection: Only save if content actually changed
  useEffect(() => {
    if (!isOpen) return;

    const hasContent = title.trim() || content.trim() || excerpt.trim() || featuredImage;
    if (!hasContent) return;

    // Check if content changed since last save
    const contentChanged =
      title !== lastContentRef.current.title ||
      content !== lastContentRef.current.content ||
      excerpt !== lastContentRef.current.excerpt;

    if (!contentChanged && draftId) {
      // No changes, skip save
      return;
    }

    // Debounce timer: Save 5 seconds after user stops typing
    const debounceTimer = setTimeout(async () => {
      const now = Date.now();
      const timeSinceLastSave = lastSaveRef.current ? now - lastSaveRef.current : Infinity;

      // Only save if content changed
      if (contentChanged) {
        await saveDraftToBackend();
      }
    }, 5000); // 5 seconds debounce

    // Force save timer: Max 60 seconds between saves
    const forceSaveInterval = setInterval(async () => {
      const now = Date.now();
      const timeSinceLastSave = lastSaveRef.current ? now - lastSaveRef.current : Infinity;

      // Force save if 60 seconds passed and content changed
      if (timeSinceLastSave >= 60000 && contentChanged && hasContent) {
        await saveDraftToBackend();
      }
    }, 10000); // Check every 10 seconds

    return () => {
      clearTimeout(debounceTimer);
      clearInterval(forceSaveInterval);
    };
  }, [title, content, excerpt, featuredImage, isOpen, draftId]);

  // Function to save draft to backend
  const saveDraftToBackend = async () => {
    try {
      setAutoSaveStatus('saving');

      const formData = new FormData();
      formData.append('content', title.trim() || 'Brouillon sans titre');
      formData.append('article_content', content);
      if (excerpt.trim()) {
        formData.append('excerpt', excerpt.trim());
      }
      formData.append('post_type', 'article');
      formData.append('visibility', visibility);
      formData.append('is_draft', true); // Always a draft for auto-save

      // Add featured image if exists
      if (featuredImage instanceof File) {
        formData.append('featured_image', featuredImage);
      }

      // Add community context
      if (community?.id) {
        formData.append('community', community.id);
      }

      // Auto-context
      if (division?.id) {
        formData.append('division_id', division.id);
      }
      if (section) {
        formData.append('section', section);
      }

      let response;
      if (draftId) {
        // Update existing draft
        response = await contentAPI.updatePost(draftId, formData);
      } else {
        // Create new draft
        response = await contentAPI.createPost(formData);
        setDraftId(response.id); // Store draft ID for future updates
      }

      // Update tracking refs
      lastSaveRef.current = Date.now();
      lastContentRef.current = {
        title,
        content,
        excerpt
      };

      setAutoSaveStatus('saved');

      // Clear status message after 3 seconds
      setTimeout(() => setAutoSaveStatus(''), 3000);

    } catch (err) {
      console.error('Auto-save failed:', err);
      setAutoSaveStatus('error');

      // Clear error status after 3 seconds
      setTimeout(() => setAutoSaveStatus(''), 3000);
    }
  };

  // Handle section change when modal is open
  useEffect(() => {
    // Only handle if modal is open and section actually changed
    if (!isOpen || prevSectionRef.current === section) {
      prevSectionRef.current = section;
      return;
    }

    // Section changed while modal is open
    prevSectionRef.current = section;

    // Check if there's content that would be lost (including excerpt/résumé)
    const hasContent = title.trim() || content.trim() || excerpt.trim() || featuredImage;

    if (hasContent) {
      // Show confirmation dialog
      if (window.confirm('Vous avez du contenu non publié dans cet article. Voulez-vous sauvegarder ce brouillon avant de changer de rubrique ?')) {
        // Keep draft in localStorage for later
        console.log('Draft saved for later use');
      } else {
        localStorage.removeItem('article_draft');
      }
    } else {
      // No content, just clear draft and close silently
      localStorage.removeItem('article_draft');
    }

    // Close the modal and reset form
    resetForm();
    onClose();
  }, [section, isOpen, title, content, excerpt, featuredImage, onClose]);

  // Clear draft on close
  const handleClose = () => {
    // Only show confirmation if there's unsaved content (including excerpt/résumé)
    const hasContent = title.trim() || content.trim() || excerpt.trim() || featuredImage;

    if (hasContent) {
      if (window.confirm('Voulez-vous sauvegarder ce brouillon pour plus tard ?')) {
        // Keep draft in localStorage for later
      } else {
        localStorage.removeItem('article_draft');
      }
    } else {
      // No content, just clear draft
      localStorage.removeItem('article_draft');
    }

    resetForm();
    onClose();
  };

  const resetForm = () => {
    setTitle('');
    setContent('');
    setExcerpt('');
    setFeaturedImage(null);
    setVisibility('public');
    setMode('edit');
    setError(null);
    setDraftId(null);
    setAutoSaveStatus('');
    lastSaveRef.current = null;
    lastContentRef.current = { title: '', content: '', excerpt: '' };
  };

  // Check if article is completely empty
  const isEmpty = () => {
    return !title.trim() && !content.trim() && !excerpt.trim() && !featuredImage;
  };

  const handleSubmit = async (e, saveAsDraft = false) => {
    e.preventDefault();
    setError(null);

    // Validation for published articles
    if (!saveAsDraft) {
      if (!title.trim()) {
        setError('Le titre est requis');
        return;
      }

      if (!content.trim()) {
        setError('Le contenu est requis');
        return;
      }
    }

    setIsSubmitting(true);

    try {
      // Create FormData for file upload
      const formData = new FormData();

      // Basic fields
      formData.append('content', title.trim() || 'Brouillon sans titre'); // Short description
      formData.append('article_content', content); // Rich HTML content
      if (excerpt.trim()) {
        formData.append('excerpt', excerpt.trim());
      }
      formData.append('post_type', 'article');
      formData.append('visibility', visibility);
      formData.append('is_draft', saveAsDraft);

      // Add featured image if exists
      if (featuredImage instanceof File) {
        formData.append('featured_image', featuredImage);
      }

      // Add community context
      if (community?.id) {
        formData.append('community', community.id);
      }

      // Auto-context
      if (division?.id) {
        formData.append('division_id', division.id);
      }
      if (section) {
        formData.append('section', section);
      }

      // If we have a draft ID and we're publishing, update the existing draft
      if (draftId && !saveAsDraft) {
        // Update existing draft and set is_draft to false (publish it)
        await contentAPI.updatePost(draftId, formData);

        // Clear draft tracking since it's now published
        setDraftId(null);
        lastSaveRef.current = null;
        lastContentRef.current = { title: '', content: '', excerpt: '' };
      } else {
        // Create new post or save as new draft
        await onSubmit(formData);
      }

      // Clear localStorage draft (legacy)
      localStorage.removeItem('article_draft');

      // Reset form and close
      resetForm();
      onClose();
    } catch (err) {
      setError(err.message || `Erreur lors de ${saveAsDraft ? 'la sauvegarde du brouillon' : 'la publication'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (5MB max)
      if (file.size > 5 * 1024 * 1024) {
        setError('L\'image ne doit pas dépasser 5 MB');
        return;
      }

      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Veuillez sélectionner une image valide');
        return;
      }

      // Store the actual file object for upload
      setFeaturedImage(file);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop - Non-dismissible to prevent accidental data loss */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          // Don't allow closing by clicking backdrop - users must use X button
          // This prevents accidental loss of article content
        }}
      />

      {/* Modal - positioned relative to content area, accounting for sidebar */}
      <div className="flex min-h-full items-start justify-center p-4 pt-8 lg:ml-[300px]">
        <div
          className="relative w-full max-w-3xl bg-white rounded-2xl shadow-2xl my-8"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Créer un article enrichi
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-sm text-gray-500">
                  {division?.name} • {section}
                </p>
                {/* Auto-save status indicator */}
                {autoSaveStatus && (
                  <span className={`text-xs font-medium ${
                    autoSaveStatus === 'saving' ? 'text-blue-600' :
                    autoSaveStatus === 'saved' ? 'text-green-600' :
                    'text-red-600'
                  }`}>
                    {autoSaveStatus === 'saving' && '💾 Sauvegarde...'}
                    {autoSaveStatus === 'saved' && '✓ Brouillon sauvegardé'}
                    {autoSaveStatus === 'error' && '⚠ Erreur de sauvegarde'}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Mode Toggle */}
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <button
                  type="button"
                  onClick={() => setMode('edit')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    mode === 'edit'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <CodeBracketIcon className="w-4 h-4 inline-block mr-1" />
                  Éditer
                </button>
                <button
                  type="button"
                  onClick={() => setMode('preview')}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    mode === 'preview'
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <EyeIcon className="w-4 h-4 inline-block mr-1" />
                  Aperçu
                </button>
              </div>

              {/* Close Button */}
              <button
                type="button"
                onClick={handleClose}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="flex flex-col" style={{ maxHeight: 'calc(100vh - 200px)' }}>
            <div className="flex-1 overflow-y-auto px-6 py-6">
              {error && (
                <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {mode === 'edit' ? (
                <div className="space-y-6">
                  {/* Title */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Titre de l'article *
                    </label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="Donnez un titre accrocheur à votre article..."
                      className="w-full px-4 py-3 text-2xl font-bold border-0 border-b-2 border-gray-200 focus:border-blue-500 focus:outline-none placeholder-gray-400"
                      maxLength={200}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {title.length}/200 caractères
                    </p>
                  </div>

                  {/* Featured Image */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Image à la une (optionnel)
                    </label>
                    {featuredImage ? (
                      <div className="relative">
                        <img
                          src={featuredImage instanceof File ? URL.createObjectURL(featuredImage) : featuredImage}
                          alt="Featured"
                          className="w-full h-64 object-cover rounded-lg"
                        />
                        <button
                          type="button"
                          onClick={() => setFeaturedImage(null)}
                          className="absolute top-2 right-2 p-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        >
                          <XMarkIcon className="w-5 h-5" />
                        </button>
                      </div>
                    ) : (
                      <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-blue-500 transition-colors">
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          <svg className="w-10 h-10 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          <p className="mb-2 text-sm text-gray-500">
                            <span className="font-semibold">Cliquez pour télécharger</span> ou glissez-déposez
                          </p>
                          <p className="text-xs text-gray-500">PNG, JPG ou GIF (MAX. 5MB)</p>
                        </div>
                        <input
                          type="file"
                          className="hidden"
                          accept="image/*"
                          onChange={handleImageUpload}
                        />
                      </label>
                    )}
                  </div>

                  {/* Content Editor */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Contenu de l'article *
                    </label>
                    <div className="border border-gray-300 rounded-lg overflow-hidden">
                      <RichTextEditor
                        mode="full"
                        content={content}
                        onChange={setContent}
                        placeholder="Rédigez votre article avec tous les outils de mise en forme..."
                        minHeight="400px"
                        enableAdvancedFeatures={true}
                      />
                    </div>
                  </div>

                  {/* Excerpt */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Résumé (optionnel)
                    </label>
                    <textarea
                      value={excerpt}
                      onChange={(e) => setExcerpt(e.target.value)}
                      placeholder="Un court résumé qui apparaîtra dans le fil d'actualité..."
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      rows={3}
                      maxLength={300}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {excerpt.length}/300 caractères
                    </p>
                  </div>
                </div>
              ) : (
                /* Preview Mode */
                <div className="prose prose-lg max-w-none">
                  {featuredImage && (
                    <img
                      src={featuredImage instanceof File ? URL.createObjectURL(featuredImage) : featuredImage}
                      alt="Featured"
                      className="w-full h-96 object-cover rounded-lg mb-8"
                    />
                  )}

                  <h1 className="text-4xl font-bold text-gray-900 mb-4">
                    {title || 'Sans titre'}
                  </h1>

                  {excerpt && (
                    <p className="text-xl text-gray-600 italic mb-6 pb-6 border-b border-gray-200">
                      {excerpt}
                    </p>
                  )}

                  <div
                    className="article-content"
                    dangerouslySetInnerHTML={{ __html: content || '<p class="text-gray-400">Aucun contenu...</p>' }}
                  />
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center gap-4">
                {/* Visibility */}
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="public">🌍 Public</option>
                  <option value="followers">👥 Abonnés</option>
                  <option value="private">🔒 Privé</option>
                </select>

                <p className="text-xs text-gray-500">
                  Brouillon sauvegardé automatiquement
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  disabled={isSubmitting}
                >
                  Annuler
                </button>
                <button
                  type="button"
                  onClick={(e) => handleSubmit(e, true)}
                  disabled={isSubmitting || isEmpty()}
                  className="px-4 py-2 bg-gray-600 text-white font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title={isEmpty() ? "Ajoutez du contenu avant de sauvegarder" : "Sauvegarder comme brouillon"}
                >
                  {isSubmitting ? 'Sauvegarde...' : 'Sauvegarder comme brouillon'}
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !title.trim() || !content.trim()}
                  className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSubmitting ? 'Publication...' : 'Publier l\'article'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RichArticleModal;
