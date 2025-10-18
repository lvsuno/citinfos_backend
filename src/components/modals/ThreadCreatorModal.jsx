import React, { useState } from 'react';
import {
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  UserIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { useNavigate, useLocation } from 'react-router-dom';
import RichTextEditor from '../ui/RichTextEditor';

const ThreadCreatorModal = ({
  isOpen,
  onClose,
  division,
  section,
  rubriqueTemplateId,  // UUID of the rubrique template
  community,
  municipalitySlug,
  onSubmit
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Log props when modal opens
  React.useEffect(() => {
    if (isOpen) {
      console.log('ThreadCreatorModal opened with props:', {
        division,
        section,
        rubriqueTemplateId,
        community,
        municipalitySlug
      });
    }
  }, [isOpen, division, section, rubriqueTemplateId, community, municipalitySlug]);

  // Get current URL path (municipality, commune, etc.)
  const currentUrlPath = location.pathname.split('/')[1];

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [includeFirstPost, setIncludeFirstPost] = useState(false);
  const [firstPostContent, setFirstPostContent] = useState('');

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setIncludeFirstPost(false);
    setFirstPostContent('');
    setError(null);
  };

  const handleClose = () => {
    if (title || description || firstPostContent) {
      if (!window.confirm('Voulez-vous vraiment annuler ? Les modifications seront perdues.')) {
        return;
      }
    }

    resetForm();
    onClose();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    console.log('Thread creation started');
    console.log('Props:', { division, section, rubriqueTemplateId, community, municipalitySlug });

    // Validation
    if (!title.trim()) {
      setError('Le titre est requis');
      return;
    }

    if (title.length < 5) {
      setError('Le titre doit contenir au moins 5 caractères');
      return;
    }

    if (includeFirstPost && !firstPostContent.trim()) {
      setError('Veuillez écrire le premier message ou décochez l\'option');
      return;
    }

    setIsSubmitting(true);

    try {
      const threadData = {
        title: title.trim(),
        body: description.trim() || undefined,
        community_id: community?.id || division?.id,  // Use community if available, otherwise division ID (they're the same)
        rubrique_template_id: rubriqueTemplateId,  // Pass the rubrique template UUID
        include_first_post: includeFirstPost,
        first_post_content: includeFirstPost ? firstPostContent.trim() : undefined,
        first_post_type: 'text',  // Default type for first post
        // Auto-context (optional, may not be used by backend)
        division_id: division?.id,
        section: section,
      };

      console.log('Thread data prepared:', threadData);

      // Validate required fields
      if (!threadData.community_id) {
        console.error('Missing community_id');
        setError('Communauté non trouvée. Veuillez réessayer.');
        setIsSubmitting(false);
        return;
      }
      if (!threadData.rubrique_template_id) {
        console.error('Missing rubrique_template_id', { section, rubriqueTemplateId });
        setError(`Section "${section}" non trouvée. Les sections sont en cours de chargement, veuillez réessayer dans un instant.`);
        setIsSubmitting(false);
        return;
      }

      console.log('Creating thread with data:', threadData);
      const createdThread = await onSubmit(threadData);
      console.log('Thread created:', createdThread);

      // Redirect to thread view using slug (not ID) since ThreadViewSet uses lookup_field='slug'
      if (createdThread?.slug && municipalitySlug && currentUrlPath) {
        const threadUrl = `/${currentUrlPath}/${municipalitySlug}/thread/${createdThread.slug}`;
        navigate(threadUrl);
      } else if (createdThread?.id && municipalitySlug && currentUrlPath) {
        // Fallback to ID if slug is not available (shouldn't happen with new threads)
        console.warn('Thread slug not found, using ID. This may cause 404 errors.');
        const threadUrl = `/${currentUrlPath}/${municipalitySlug}/thread/${createdThread.id}`;
        navigate(threadUrl);
      }

      resetForm();
      onClose();
    } catch (err) {
      setError(err.message || 'Erreur lors de la création du sujet');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal - positioned relative to content area, accounting for sidebar */}
      <div className="flex min-h-full items-start justify-center p-4 pt-8 lg:ml-[300px]">
        <div
          className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl max-h-[85vh] overflow-hidden flex flex-col my-8"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <ChatBubbleLeftRightIcon className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Créer un nouveau sujet
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                  {division?.name} • {section}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
            <div className="px-6 py-6 space-y-6 overflow-y-auto flex-1">
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {/* Informational Banner */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 <strong>Conseil :</strong> Créez un sujet pour démarrer une discussion autour d'un thème spécifique.
                  Les autres utilisateurs pourront répondre et contribuer à la conversation.
                </p>
              </div>

              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Titre du sujet *
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ex: Quels sont vos événements préférés de l'été ?"
                  className="w-full px-4 py-3 text-lg font-semibold border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 placeholder-gray-400"
                  maxLength={200}
                  autoFocus
                />
                <div className="flex items-center justify-between mt-1">
                  <p className="text-xs text-gray-500">
                    Un titre clair et descriptif aide les autres à comprendre le sujet
                  </p>
                  <p className="text-xs text-gray-500">
                    {title.length}/200
                  </p>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (optionnel)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Ajoutez plus de détails sur ce dont vous voulez discuter..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  rows={4}
                  maxLength={1000}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {description.length}/1000 caractères
                </p>
              </div>

              {/* Include First Post Checkbox */}
              <div className="border-t border-gray-200 pt-6">
                <label className="flex items-start gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={includeFirstPost}
                    onChange={(e) => setIncludeFirstPost(e.target.checked)}
                    className="mt-1 w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900 group-hover:text-blue-600">
                      Créer le premier message maintenant
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Lancez la conversation immédiatement avec votre premier message
                    </p>
                  </div>
                </label>

                {includeFirstPost && (
                  <div className="mt-4 ml-8">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Votre premier message
                    </label>
                    <div className="border border-gray-300 rounded-lg overflow-hidden">
                      <RichTextEditor
                        mode="inline"
                        content={firstPostContent}
                        onChange={setFirstPostContent}
                        placeholder="Partagez votre première pensée sur ce sujet..."
                        minHeight="120px"
                        maxHeight="200px"
                        maxLength={2000}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {firstPostContent.length}/2000 caractères - Utilisez la mise en forme pour mieux exprimer vos idées
                    </p>
                  </div>
                )}
              </div>

              {/* Preview Section */}
              {title && (
                <div className="border-t border-gray-200 pt-6">
                  <p className="text-sm font-medium text-gray-700 mb-3">
                    Aperçu du sujet :
                  </p>
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <h3 className="text-lg font-bold text-gray-900 mb-2">
                      {title}
                    </h3>
                    {description && (
                      <p className="text-sm text-gray-600 mb-2">
                        {description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <UserIcon className="w-4 h-4" />
                        Vous
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <CalendarIcon className="w-4 h-4" />
                        À l'instant
                      </span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <ChatBubbleLeftRightIcon className="w-4 h-4" />
                        0 réponses
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 flex-shrink-0">
              <p className="text-xs text-gray-500">
                Les sujets sont publics et visibles par tous les membres
              </p>

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
                  type="submit"
                  disabled={isSubmitting || !title.trim() || (includeFirstPost && !firstPostContent.trim())}
                  className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Création...
                    </>
                  ) : (
                    <>
                      <ChatBubbleLeftRightIcon className="w-5 h-5" />
                      Créer le sujet
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ThreadCreatorModal;
