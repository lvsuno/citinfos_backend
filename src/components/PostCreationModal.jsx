import React, { useState, useRef, useEffect } from 'react';
import {
  XMarkIcon,
  DocumentTextIcon,
  ChartBarSquareIcon,
  PhotoIcon,
  PlusIcon,
  TrashIcon,
  GlobeAltIcon,
  UserGroupIcon,
  UsersIcon,
  EyeIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import RichTextEditor from './ui/RichTextEditor';
import StyledSelect from './ui/StyledSelect';
import contentAPI from '../services/contentAPI';
import socialAPI from '../services/social-api';
import { transformPostDataForAPI, transformArticleUpdateForAPI } from '../utils/postTransformers';
import { useAuth } from '../contexts/AuthContext';

const PostCreationModal = ({
  isOpen,
  onClose,
  onSubmit,
  onImageUpload,
  onVideoUpload,
  onAudioUpload
}) => {
  const { user } = useAuth();

  // Mode state: 'post' or 'thread'
  const [mode, setMode] = useState('post');

  // Main state
  const [activeType, setActiveType] = useState('article'); // Single selection now

  // Thread-specific state
  const [threadTitle, setThreadTitle] = useState('');
  const [threadBody, setThreadBody] = useState('');
  const [includeFirstPost, setIncludeFirstPost] = useState(false);

  // Community/Thread selection state
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [selectedThread, setSelectedThread] = useState(null);
  const [communities, setCommunities] = useState([]);
  const [threads, setThreads] = useState([]);
  const [loadingCommunities, setLoadingCommunities] = useState(false);
  const [loadingThreads, setLoadingThreads] = useState(false);

  // Content state
  const [articleContent, setArticleContent] = useState('');
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['', '']);
  const [allowMultipleVotes, setAllowMultipleVotes] = useState(false);
  const [pollExpirationHours, setPollExpirationHours] = useState(24);

  // Media state
  const [attachedMedia, setAttachedMedia] = useState([]);

  // Visibility state
  const [visibility, setVisibility] = useState('public'); // public, followers, custom
  const [customAudience, setCustomAudience] = useState('');

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const fileInputRef = useRef(null);
  const richTextEditorRef = useRef(null);

  // Load communities when modal opens
  useEffect(() => {
    if (isOpen && mode === 'post') {
      loadCommunities();
    }
  }, [isOpen, mode]);

  // Load threads when community is selected
  useEffect(() => {
    if (selectedCommunity) {
      loadThreads(selectedCommunity.id);
    } else {
      setThreads([]);
      setSelectedThread(null);
    }
  }, [selectedCommunity]);

  const loadCommunities = async () => {
    setLoadingCommunities(true);
    try {
      // If user has a division, filter by division; otherwise get all
      const divisionId = user?.profile?.division?.id;
      const response = await socialAPI.communities.list(divisionId);
      setCommunities(response.results || response);

      // Auto-select first community if available
      if ((response.results || response).length > 0 && !selectedCommunity) {
        setSelectedCommunity((response.results || response)[0]);
      }
    } catch (error) {
      console.error('Failed to load communities:', error);
    } finally {
      setLoadingCommunities(false);
    }
  };

  const loadThreads = async (communityId) => {
    setLoadingThreads(true);
    try {
      const response = await socialAPI.threads.list(communityId);
      setThreads(response.results || response);
    } catch (error) {
      console.error('Failed to load threads:', error);
      setThreads([]);
    } finally {
      setLoadingThreads(false);
    }
  };

  // Reset form state
  const resetForm = () => {
    setMode('post');
    setActiveType('article'); // Reset to first option
    setThreadTitle('');
    setThreadBody('');
    setIncludeFirstPost(false);
    setSelectedCommunity(null);
    setSelectedThread(null);
    setArticleContent('');
    setPollQuestion('');
    setPollOptions(['', '']);
    setAllowMultipleVotes(false);
    setPollExpirationHours(24);
    setAttachedMedia([]);
    setVisibility('public');
    setCustomAudience('');
    setErrors({});
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleTypeChange = (type) => {
    setActiveType(type);
    setErrors({}); // Clear errors when changing type
  };

  // Poll options management
  const addPollOption = () => {
    if (pollOptions.length < 6) { // Max 6 options
      setPollOptions([...pollOptions, '']);
    }
  };

  const removePollOption = (index) => {
    if (pollOptions.length > 2) { // Min 2 options
      setPollOptions(pollOptions.filter((_, i) => i !== index));
    }
  };

  const updatePollOption = (index, value) => {
    const newOptions = [...pollOptions];
    newOptions[index] = value;
    setPollOptions(newOptions);
  };

  // Media management
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const mediaItem = {
        id: Date.now() + Math.random(),
        file,
        type: file.type.startsWith('image/') ? 'image' :
              file.type.startsWith('video/') ? 'video' :
              file.type.startsWith('audio/') ? 'audio' : 'file',
        url: URL.createObjectURL(file),
        name: file.name,
        description: '' // Add description field
      };
      setAttachedMedia(prev => [...prev, mediaItem]);
    });
    e.target.value = ''; // Reset input
  };

  const removeMedia = (id) => {
    setAttachedMedia(prev => {
      const item = prev.find(m => m.id === id);
      if (item && item.url) {
        URL.revokeObjectURL(item.url);
      }
      return prev.filter(m => m.id !== id);
    });
  };

  const updateMediaDescription = (id, description) => {
    setAttachedMedia(prev => prev.map(m =>
      m.id === id ? { ...m, description } : m
    ));
  };

  // Form validation
  const validateForm = () => {
    const newErrors = {};

    // Thread mode validation
    if (mode === 'thread') {
      if (!threadTitle.trim()) {
        newErrors.threadTitle = 'Le titre du sujet est requis';
      }
      if (!threadBody.trim()) {
        newErrors.threadBody = 'Le corps du sujet est requis';
      }
      if (!selectedCommunity) {
        newErrors.community = 'Vous devez sélectionner une communauté';
      }

      // If including first post, validate it
      if (includeFirstPost) {
        if (activeType === 'article' && !articleContent.trim()) {
          newErrors.article = 'Le contenu de l\'article est requis';
        }
        if (activeType === 'poll') {
          if (!pollQuestion.trim()) {
            newErrors.pollQuestion = 'La question du sondage est requise';
          }
          const validOptions = pollOptions.filter(opt => opt.trim());
          if (validOptions.length < 2) {
            newErrors.pollOptions = 'Au moins 2 options sont requises';
          }
        }
        if (activeType === 'media' && attachedMedia.length === 0) {
          newErrors.media = 'Au moins un fichier média est requis';
        }
      }
    } else {
      // Post mode validation
      if (!selectedCommunity) {
        newErrors.community = 'Vous devez sélectionner une communauté';
      }

      if (activeType === 'article' && !articleContent.trim()) {
        newErrors.article = 'Le contenu de l\'article est requis';
      }

      if (activeType === 'poll') {
        if (!pollQuestion.trim()) {
          newErrors.pollQuestion = 'La question du sondage est requise';
        }
        const validOptions = pollOptions.filter(opt => opt.trim());
        if (validOptions.length < 2) {
          newErrors.pollOptions = 'Au moins 2 options sont requises';
        }
      }

      if (activeType === 'media' && attachedMedia.length === 0) {
        newErrors.media = 'Au moins un fichier média est requis';
      }
    }

    if (visibility === 'custom' && !customAudience.trim()) {
      newErrors.customAudience = 'L\'audience personnalisée est requise';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // THREAD MODE: Create thread with optional first post
      if (mode === 'thread') {
        const threadData = {
          community_id: selectedCommunity.id,
          title: threadTitle,
          body: threadBody
        };

        // If including first post, add it to thread creation
        if (includeFirstPost) {
          if (activeType === 'article') {
            threadData.first_post_content = articleContent;
            threadData.first_post_type = 'text';
          } else if (activeType === 'poll') {
            threadData.first_post_content = JSON.stringify({
              question: pollQuestion,
              options: pollOptions.filter(opt => opt.trim()),
              allowMultiple: allowMultipleVotes,
              expirationHours: pollExpirationHours
            });
            threadData.first_post_type = 'poll';
          }
          // Note: Media posts in threads would need special handling (not implemented yet)
        }

        const createdThread = await socialAPI.threads.create(threadData);

        // Process mentions/hashtags for thread first post if it's an article
        if (includeFirstPost && activeType === 'article' && articleContent && createdThread?.first_post?.id) {
          try {
            await socialAPI.utils.processContentMentions(
              articleContent,
              createdThread.first_post.id,
              null, // commentId
              selectedCommunity.id
            );
          } catch (mentionError) {
            console.error('Failed to process mentions/hashtags in thread first post:', mentionError);
          }
        }

        handleClose();
        return;
      }

      // POST MODE: Create post in community or thread
      const modalData = {
        type: activeType,
        content: {
          article: activeType === 'article' ? articleContent : null,
          poll: activeType === 'poll' ? {
            question: pollQuestion,
            options: pollOptions.filter(opt => opt.trim()),
            allowMultiple: allowMultipleVotes,
            expirationHours: pollExpirationHours
          } : null,
          media: activeType === 'media' ? attachedMedia.map(item => ({
            ...item,
            description: item.description || ''
          })) : null
        },
        visibility,
        customAudience: visibility === 'custom' ? customAudience : null,
        community_id: selectedCommunity?.id,
        thread_id: selectedThread?.id || null
      };

      // Special handling for ARTICLE posts with embedded media (two-phase upload)
      if (activeType === 'article' && richTextEditorRef.current) {
        const { processContentForSubmission, getMediaAttachments } = richTextEditorRef.current;
        const embeddedMedia = getMediaAttachments();

        // If there are embedded media files, use two-phase upload
        if (embeddedMedia && embeddedMedia.length > 0) {
          // Phase 1: Create post with placeholder content
          const apiPost = transformPostDataForAPI(modalData);
          const createdPost = await onSubmit(apiPost);

          // Phase 2: Upload media files and replace blob URLs
          const { processedContent } = await processContentForSubmission(async (file, mediaType) => {
            // Use appropriate upload handler based on media type
            if (mediaType === 'image' && onImageUpload) {
              return await onImageUpload(file);
            } else if (mediaType === 'video' && onVideoUpload) {
              return await onVideoUpload(file);
            } else if (mediaType === 'audio' && onAudioUpload) {
              return await onAudioUpload(file);
            }
            throw new Error(`No upload handler for media type: ${mediaType}`);
          });

          // Phase 3: Update post with final content (real media URLs)
          if (createdPost && createdPost.id && processedContent !== articleContent) {
            const updateData = transformArticleUpdateForAPI(processedContent);
            await contentAPI.updatePost(createdPost.id, updateData);
            console.log('✅ Article updated with final media URLs. Post ID:', createdPost.id);
          }

          // Process mentions and hashtags for article posts with embedded media
          if (createdPost?.id && processedContent) {
            try {
              await socialAPI.utils.processContentMentions(
                processedContent,
                createdPost.id,
                null, // commentId (not applicable for posts)
                selectedCommunity?.id
              );
            } catch (mentionError) {
              console.error('Failed to process mentions/hashtags:', mentionError);
              // Don't fail the entire submission if mention processing fails
            }
          }

          handleClose();
          return;
        }
      }

      // Standard submission for all other cases (poll, media, article without embedded media)
      const apiPost = transformPostDataForAPI(modalData);
      const createdPost = await onSubmit(apiPost);

      // Process mentions and hashtags for article posts
      if (activeType === 'article' && articleContent && createdPost?.id) {
        try {
          await socialAPI.utils.processContentMentions(
            articleContent,
            createdPost.id,
            null, // commentId (not applicable for posts)
            selectedCommunity?.id
          );
        } catch (mentionError) {
          console.error('Failed to process mentions/hashtags:', mentionError);
          // Don't fail the entire submission if mention processing fails
        }
      }

      handleClose();

    } catch (error) {
      console.error('Post creation error:', error);
      setErrors({ submit: error.message || 'Échec de la création de la publication' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const visibilityOptions = [
    {
      value: 'public',
      label: 'Public',
      description: 'Tout le monde peut voir cette publication',
      icon: GlobeAltIcon
    },
    {
      value: 'followers',
      label: 'Abonnés',
      description: 'Seulement vos abonnés peuvent voir',
      icon: UserGroupIcon
    },
    {
      value: 'custom',
      label: 'Personnalisé',
      description: 'Audience spécifique que vous définissez',
      icon: UsersIcon
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" onClick={handleClose}>
      {/* Centered in the space left by sidebar (256px) and accounting for top bar */}
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col"
        style={{
          marginLeft: '128px', // Half of 256px sidebar width to center in remaining space
          marginTop: '32px' // Account for top bar
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {mode === 'thread' ? 'Créer un nouveau sujet' : 'Créer une nouvelle publication'}
          </h2>
          <button
            onClick={handleClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Mode Selection */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Mode</h3>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setMode('post')}
                  className={`flex-1 px-4 py-3 border rounded-lg transition-colors ${
                    mode === 'post'
                      ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <DocumentTextIcon className="w-5 h-5 mx-auto mb-1 text-blue-600" />
                  <div className="font-medium text-sm">Publication</div>
                  <div className="text-xs text-gray-600">Créer une publication</div>
                </button>
                <button
                  type="button"
                  onClick={() => setMode('thread')}
                  className={`flex-1 px-4 py-3 border rounded-lg transition-colors ${
                    mode === 'thread'
                      ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <ChatBubbleLeftRightIcon className="w-5 h-5 mx-auto mb-1 text-purple-600" />
                  <div className="font-medium text-sm">Sujet</div>
                  <div className="text-xs text-gray-600">Créer un sujet de discussion</div>
                </button>
              </div>
            </div>

            {/* Community Display (read-only) */}
            {selectedCommunity && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <UserGroupIcon className="w-5 h-5 text-blue-600" />
                  <div>
                    <div className="text-sm font-medium text-gray-900">Publication dans:</div>
                    <div className="text-lg font-semibold text-blue-700">{selectedCommunity.name}</div>
                    {selectedCommunity.description && (
                      <div className="text-sm text-gray-600 mt-1">{selectedCommunity.description}</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Thread Selection (only for post mode) */}
            {mode === 'post' && selectedCommunity && (
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Sujet (optionnel)
                </label>
                <select
                  value={selectedThread?.id || ''}
                  onChange={(e) => {
                    const thread = threads.find(t => t.id === parseInt(e.target.value));
                    setSelectedThread(thread);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={loadingThreads}
                >
                  <option value="">Publication dans la communauté (pas de sujet)</option>
                  {threads.map(thread => (
                    <option key={thread.id} value={thread.id}>
                      {thread.title}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Thread Details (only for thread mode) */}
            {mode === 'thread' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Titre du sujet
                  </label>
                  <input
                    type="text"
                    value={threadTitle}
                    onChange={(e) => setThreadTitle(e.target.value)}
                    placeholder="Entrez le titre du sujet..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.threadTitle && (
                    <p className="mt-1 text-sm text-red-600">{errors.threadTitle}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Description du sujet
                  </label>
                  <textarea
                    value={threadBody}
                    onChange={(e) => setThreadBody(e.target.value)}
                    placeholder="Décrivez le sujet de discussion..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.threadBody && (
                    <p className="mt-1 text-sm text-red-600">{errors.threadBody}</p>
                  )}
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="includeFirstPost"
                    checked={includeFirstPost}
                    onChange={(e) => setIncludeFirstPost(e.target.checked)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="includeFirstPost" className="ml-2 text-sm text-gray-900">
                    Inclure une première publication
                  </label>
                </div>
              </div>
            )}

            {/* Content Type Selection (only if posting or including first post in thread) */}
            {(mode === 'post' || (mode === 'thread' && includeFirstPost)) && (
              <div className="flex flex-col lg:flex-row gap-6 items-start">
              {/* Content Type Selection - Left Side */}
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Type de contenu</h3>
                <div className="flex flex-wrap gap-3">
                  {/* Article Radio */}
                  <label className={`flex items-center px-4 py-3 border rounded-lg cursor-pointer transition-colors ${
                    activeType === 'article' ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' : 'border-gray-200 hover:bg-gray-50'
                  }`}>
                    <input
                      type="radio"
                      name="contentType"
                      value="article"
                      checked={activeType === 'article'}
                      onChange={(e) => handleTypeChange(e.target.value)}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                    <DocumentTextIcon className="w-5 h-5 text-blue-600 ml-3 mr-2" />
                    <div>
                      <div className="font-medium text-gray-900 text-sm">Article</div>
                      <div className="text-xs text-gray-600">Texte enrichi</div>
                    </div>
                  </label>

                  {/* Poll Radio */}
                  <label className={`flex items-center px-4 py-3 border rounded-lg cursor-pointer transition-colors ${
                    activeType === 'poll' ? 'border-green-500 bg-green-50 ring-2 ring-green-200' : 'border-gray-200 hover:bg-gray-50'
                  }`}>
                    <input
                      type="radio"
                      name="contentType"
                      value="poll"
                      checked={activeType === 'poll'}
                      onChange={(e) => handleTypeChange(e.target.value)}
                      className="h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500"
                    />
                    <ChartBarSquareIcon className="w-5 h-5 text-green-600 ml-3 mr-2" />
                    <div>
                      <div className="font-medium text-gray-900 text-sm">Sondage</div>
                      <div className="text-xs text-gray-600">Choix multiples</div>
                    </div>
                  </label>

                  {/* Media Radio */}
                  <label className={`flex items-center px-4 py-3 border rounded-lg cursor-pointer transition-colors ${
                    activeType === 'media' ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200' : 'border-gray-200 hover:bg-gray-50'
                  }`}>
                    <input
                      type="radio"
                      name="contentType"
                      value="media"
                      checked={activeType === 'media'}
                      onChange={(e) => handleTypeChange(e.target.value)}
                      className="h-4 w-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                    />
                    <PhotoIcon className="w-5 h-5 text-purple-600 ml-3 mr-2" />
                    <div>
                      <div className="font-medium text-gray-900 text-sm">Média</div>
                      <div className="text-xs text-gray-600">Images et fichiers</div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Visibility Dropdown - Right Side */}
              <div className="lg:w-48">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Visibilité</h3>
                <div className="space-y-3">
                  <StyledSelect
                    value={visibility}
                    onChange={setVisibility}
                    options={[
                      { value: 'public', label: '🌍 Public - Tout le monde peut voir' },
                      { value: 'followers', label: '👥 Abonnés - Seulement vos abonnés' },
                      { value: 'custom', label: '⚙️ Personnalisé - Audience spécifique' }
                    ]}
                    placeholder="Sélectionner la visibilité"
                    size="normal"
                  />

                  {/* Custom Audience Input */}
                  {visibility === 'custom' && (
                    <div>
                      {errors.customAudience && (
                        <p className="text-sm text-red-600 mb-1">{errors.customAudience}</p>
                      )}
                      <input
                        type="text"
                        value={customAudience}
                        onChange={(e) => setCustomAudience(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm"
                        placeholder="@utilisateur1, @utilisateur2..."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Entrez des noms d'utilisateurs, groupes ou communautés
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            )}

            {/* Article Content */}
            {(mode === 'post' || (mode === 'thread' && includeFirstPost)) && activeType === 'article' && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Contenu de l'article</h4>
                {errors.article && (
                  <p className="text-sm text-red-600">{errors.article}</p>
                )}
                <RichTextEditor
                  ref={richTextEditorRef}
                  content={articleContent}
                  onChange={setArticleContent}
                  placeholder="Rédigez votre article..."
                  maxLength={5000}
                  height="h-64"
                  onImageUpload={onImageUpload}
                  onVideoUpload={onVideoUpload}
                  onAudioUpload={onAudioUpload}
                />

                {/* Article Preview */}
                {articleContent && (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Aperçu</h4>
                    <div className="bg-white border border-gray-200 rounded-md p-3">
                      <div
                        className="text-sm text-gray-700"
                        dangerouslySetInnerHTML={{
                          __html: articleContent || '<p class="text-gray-400 italic">Le contenu de l\'article apparaîtra ici...</p>'
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Poll Content */}
            {(mode === 'post' || (mode === 'thread' && includeFirstPost)) && activeType === 'poll' && (
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Détails du sondage</h4>

                {/* Poll Question */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Question du sondage
                  </label>
                  {errors.pollQuestion && (
                    <p className="text-sm text-red-600 mb-1">{errors.pollQuestion}</p>
                  )}
                  <input
                    type="text"
                    value={pollQuestion}
                    onChange={(e) => setPollQuestion(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Que voulez-vous demander ?"
                  />
                </div>

                {/* Poll Options */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Options du sondage
                  </label>
                  {errors.pollOptions && (
                    <p className="text-sm text-red-600 mb-2">{errors.pollOptions}</p>
                  )}
                  <div className="space-y-2">
                    {pollOptions.map((option, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={option}
                          onChange={(e) => updatePollOption(index, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                          placeholder={`Option ${index + 1}`}
                        />
                        {pollOptions.length > 2 && (
                          <button
                            type="button"
                            onClick={() => removePollOption(index)}
                            className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>

                  {pollOptions.length < 6 && (
                    <button
                      type="button"
                      onClick={addPollOption}
                      className="mt-2 flex items-center text-sm text-blue-600 hover:text-blue-700"
                    >
                      <PlusIcon className="w-4 h-4 mr-1" />
                      Ajouter une option
                    </button>
                  )}
                </div>

                {/* Poll Settings */}
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={allowMultipleVotes}
                      onChange={(e) => setAllowMultipleVotes(e.target.checked)}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Autoriser les sélections multiples</span>
                  </label>

                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-700">Expire dans :</label>
                    <select
                      value={pollExpirationHours}
                      onChange={(e) => setPollExpirationHours(Number(e.target.value))}
                      className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value={1}>1 heure</option>
                      <option value={6}>6 heures</option>
                      <option value={12}>12 heures</option>
                      <option value={24}>1 jour</option>
                      <option value={48}>2 jours</option>
                      <option value={168}>1 semaine</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* Media Content */}
            {(mode === 'post' || (mode === 'thread' && includeFirstPost)) && activeType === 'media' && (
              <div className="space-y-4">
                {/* Media Caption/Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description du média (optionnel)
                  </label>
                  <textarea
                    value={articleContent}
                    onChange={(e) => setArticleContent(e.target.value)}
                    placeholder="Ajoutez une légende ou une description pour vos médias..."
                    rows={3}
                    className="w-full border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm"
                    maxLength={500}
                  />
                  <div className="text-xs text-gray-400 mt-1">
                    {articleContent?.length || 0}/500 caractères
                  </div>
                </div>

                <h4 className="font-medium text-gray-900">Pièces jointes média</h4>
                {errors.media && (
                  <p className="text-sm text-red-600">{errors.media}</p>
                )}

                {/* File Upload */}
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <PhotoIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <div className="space-y-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                    >
                      <PhotoIcon className="w-4 h-4 mr-2" />
                      Sélectionner des fichiers
                    </button>
                    <p className="text-sm text-gray-500">
                      Images, vidéos, fichiers audio ou documents
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*,video/*,audio/*,.pdf,.doc,.docx"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>

                {/* Attached Media Preview */}
                {attachedMedia.length > 0 && (
                  <div className="space-y-3">
                    {attachedMedia.map((item) => (
                      <div key={item.id} className="group relative rounded-md border border-gray-200 overflow-hidden bg-gray-50">
                        <div className="flex gap-3 p-3">
                          {/* Preview Thumbnail */}
                          <div className="flex-shrink-0 w-24 h-24 rounded-md overflow-hidden bg-gray-100">
                            {item.type === 'image' ? (
                              <img
                                src={item.url}
                                alt={item.name}
                                className="w-full h-full object-cover"
                              />
                            ) : item.type === 'video' ? (
                              <video
                                src={item.url}
                                className="w-full h-full object-cover"
                                muted
                                playsInline
                              />
                            ) : item.type === 'audio' ? (
                              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-indigo-100 to-blue-50">
                                <svg className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                                </svg>
                              </div>
                            ) : (
                              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-50">
                                <DocumentTextIcon className="w-8 h-8 text-gray-700" />
                              </div>
                            )}
                          </div>

                          {/* Description Input */}
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium text-gray-700 mb-1 truncate" title={item.name}>
                              {item.name}
                            </div>
                            <input
                              type="text"
                              value={item.description || ''}
                              onChange={(e) => updateMediaDescription(item.id, e.target.value)}
                              placeholder="Ajouter une description (optionnel)..."
                              className="w-full text-xs border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 placeholder-gray-400"
                              maxLength={200}
                            />
                            <div className="text-[10px] text-gray-400 mt-1">
                              {item.description?.length || 0}/200 caractères
                            </div>
                          </div>

                          {/* Remove Button */}
                          <button
                            type="button"
                            onClick={() => removeMedia(item.id)}
                            className="flex-shrink-0 self-start bg-white/80 hover:bg-white text-gray-600 hover:text-red-500 rounded-full p-1.5 shadow-sm transition-colors"
                            aria-label="Supprimer la pièce jointe"
                          >
                            <XMarkIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Submit Error */}
            {errors.submit && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-600">{errors.submit}</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-6 py-2 text-sm font-medium text-white rounded-md ${
                isSubmitting
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isSubmitting ? 'Création...' : 'Créer la publication'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PostCreationModal;