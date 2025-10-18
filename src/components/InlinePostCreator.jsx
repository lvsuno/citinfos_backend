import React, { useState, useRef, useEffect } from 'react';
import {
  PhotoIcon,
  VideoCameraIcon,
  MusicalNoteIcon,
  ChartBarSquareIcon,
  SparklesIcon,
  GlobeAltIcon,
  UserGroupIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { socialAPI } from '../services/social-api';
import RichTextEditor from './ui/RichTextEditor';
import RichArticleModal from './modals/RichArticleModal';
import ThreadCreatorModal from './modals/ThreadCreatorModal';
import PollExpirationPicker from './ui/PollExpirationPicker';

const InlinePostCreator = ({
  division,
  section,
  rubriqueTemplateId,  // UUID of the rubrique template
  community = null,
  threadId = null,
  municipalitySlug = null,
  onPostCreated,
  placeholder = "Quoi de neuf ?"
}) => {
  const { user } = useAuth();

  // UI State
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Modal State
  const [showArticleModal, setShowArticleModal] = useState(false);
  const [showThreadModal, setShowThreadModal] = useState(false);

  // Content State
  const [content, setContent] = useState('');
  const [attachedMedia, setAttachedMedia] = useState([]);
  const [visibility, setVisibility] = useState('public');
  const [showAdvancedMenu, setShowAdvancedMenu] = useState(false);

  // Mode State
  const [activeMode, setActiveMode] = useState('text'); // text, media, poll
  const [showPollCreator, setShowPollCreator] = useState(false);

  // Poll State
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['', '']);
  const [pollExpirationDate, setPollExpirationDate] = useState('');
  const [pollExpirationTime, setPollExpirationTime] = useState('');
  const [pollMultipleChoice, setPollMultipleChoice] = useState(false);
  const [pollAnonymousVoting, setPollAnonymousVoting] = useState(false);

  // Refs
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const advancedMenuRef = useRef(null);

  // Reset state when section changes (user navigates to different rubrique)
  useEffect(() => {
    // Reset inline editor content and UI state when section changes
    // Note: Article modal handles its own closing logic with confirmation
    setContent('');
    setAttachedMedia([]);
    setIsExpanded(false);
    // Don't automatically close article modal - let it handle section changes internally
    setShowThreadModal(false);
    setShowPollCreator(false);
    setPollQuestion('');
    setPollOptions(['', '']);
    setPollExpirationDate('');
    setPollExpirationTime('');
    setPollMultipleChoice(false);
    setPollAnonymousVoting(false);
    setActiveMode('text');
    setVisibility('public');
    setShowAdvancedMenu(false);
  }, [section]); // Reset when section prop changes

  // Get user display info
  const getUserAvatar = () => {
    if (user?.avatar) return user.avatar;
    if (user?.profile?.avatar) return user.profile.avatar;
    return null;
  };

  const getUserInitials = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.firstName && user?.lastName) {
      return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
    }
    if (user?.username) {
      return user.username[0].toUpperCase();
    }
    return 'U';
  };

  const getUserName = () => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    if (user?.firstName && user?.lastName) {
      return `${user.firstName} ${user.lastName}`;
    }
    return user?.username || 'User';
  };

  // Handlers
  const handleExpand = () => {
    if (!user) {
      // TODO: Show login prompt
      return;
    }
    setIsExpanded(true);
  };

  const handleCollapse = () => {
    if (content || attachedMedia.length > 0) {
      if (!window.confirm('Vous avez du contenu non publié. Voulez-vous vraiment annuler ?')) {
        return;
      }
    }
    setIsExpanded(false);
    resetForm();
  };

  const resetForm = () => {
    setContent('');
    setAttachedMedia([]);
    setPollQuestion('');
    setPollOptions(['', '']);
    setActiveMode('text');
    setVisibility('public');
  };

  const handleMediaUpload = (type) => {
    if (!isExpanded) {
      setIsExpanded(true);
    }

    // Trigger the appropriate file input
    switch(type) {
      case 'image':
        imageInputRef.current?.click();
        break;
      case 'video':
        videoInputRef.current?.click();
        break;
      case 'audio':
        audioInputRef.current?.click();
        break;
      default:
        break;
    }
  };

  const handleFileSelect = (e, type) => {
    const files = Array.from(e.target.files || []);

    if (files.length === 0) return;

    files.forEach(file => {
      // Validate file size (max 50MB)
      const maxSize = 50 * 1024 * 1024; // 50MB
      if (file.size > maxSize) {
        alert(`Le fichier ${file.name} est trop volumineux. Taille maximale: 50MB`);
        return;
      }

      // Create preview
      const reader = new FileReader();
      reader.onload = (event) => {
        const mediaItem = {
          file,
          type,
          preview: event.target.result,
          name: file.name,
          size: file.size,
          url: null, // Will be set after upload
          uploading: false,
          progress: 0
        };

        setAttachedMedia(prev => [...prev, mediaItem]);
      };

      if (type === 'image') {
        reader.readAsDataURL(file);
      } else {
        // For video/audio, just add file info
        const mediaItem = {
          file,
          type,
          preview: null,
          name: file.name,
          size: file.size,
          url: null,
          uploading: false,
          progress: 0
        };
        setAttachedMedia(prev => [...prev, mediaItem]);
      }
    });

    // Reset input
    e.target.value = '';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const removeMedia = (index) => {
    setAttachedMedia(attachedMedia.filter((_, i) => i !== index));
  };

  const handlePollClick = () => {
    if (!isExpanded) {
      setIsExpanded(true);
    }
    setShowPollCreator(!showPollCreator);
  };

  const handleAdvancedClick = () => {
    setShowAdvancedMenu(!showAdvancedMenu);
  };

  const handleRichArticle = () => {
    setShowArticleModal(true);
    setShowAdvancedMenu(false);
  };

  const handleNewThread = () => {
    setShowThreadModal(true);
    setShowAdvancedMenu(false);
  };

  const handleSubmit = async () => {
    if (!content.trim() && attachedMedia.length === 0 && activeMode !== 'poll') {
      return;
    }

    setIsSubmitting(true);
    try {
      const postData = {
        content,
        visibility,
        division_id: division?.id,
        section,
        thread_id: threadId,
        community: community?.id,
        // TODO: Add media and poll data
      };

      // TODO: Make API call
      console.log('Submitting post:', postData);

      if (onPostCreated) {
        await onPostCreated(postData);
      }

      // Reset and collapse
      resetForm();
      setIsExpanded(false);
    } catch (error) {
      console.error('Error creating post:', error);
      // TODO: Show error message
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleArticleSubmit = async (articleData) => {
    // This will be called from RichArticleModal
    // TODO: Make API call to create article
    console.log('Submitting article:', articleData);

    if (onPostCreated) {
      await onPostCreated(articleData);
    }
  };

  const handleThreadSubmit = async (threadData) => {
    try {
      // Call the API to create the thread
      const createdThread = await socialAPI.threads.create(threadData);

      // Refresh the parent if needed
      if (onPostCreated) {
        onPostCreated();
      }

      return createdThread;
    } catch (error) {
      console.error('Error creating thread:', error);
      throw error;
    }
  };

  const visibilityOptions = [
    { value: 'public', label: 'Public', icon: GlobeAltIcon },
    { value: 'followers', label: 'Abonnés', icon: UserGroupIcon },
  ];

  // Collapsed state
  if (!isExpanded) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div
          onClick={handleExpand}
          className="flex items-center gap-3 cursor-pointer hover:bg-gray-50 rounded-lg p-2 transition-colors"
        >
          {/* User Avatar */}
          <div className="flex-shrink-0">
            {getUserAvatar() ? (
              <img
                src={getUserAvatar()}
                alt={getUserName()}
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                {getUserInitials()}
              </div>
            )}
          </div>

          {/* Placeholder */}
          <div className="flex-1 text-gray-500 text-base">
            {placeholder}
          </div>
        </div>
      </div>
    );
  }

  // Expanded state
  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-5 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {getUserAvatar() ? (
            <img
              src={getUserAvatar()}
              alt={getUserName()}
              className="w-10 h-10 rounded-full object-cover"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold">
              {getUserInitials()}
            </div>
          )}
          <div>
            <div className="font-semibold text-gray-900">{getUserName()}</div>
            {threadId && (
              <div className="text-xs text-gray-500">Répondre au sujet</div>
            )}
          </div>
        </div>

        <button
          onClick={handleCollapse}
          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Content Editor - Always visible when expanded */}
      {isExpanded && (
        <div className="mb-4">
          <RichTextEditor
            content={content}
            onChange={setContent}
            placeholder={threadId ? "Répondre au sujet..." : "Partagez quelque chose..."}
            mode="inline"
            minHeight="80px"
            maxHeight="300px"
            maxLength={threadId ? 2000 : 1000}
          />
          {threadId && (
            <p className="text-xs text-gray-500 mt-1 text-right">
              {content.length}/2000 caractères
            </p>
          )}
        </div>
      )}

      {/* Poll Creator - Expands below text editor */}
      {isExpanded && showPollCreator && (
        <div className="mb-4 p-4 border-2 border-indigo-200 bg-indigo-50 rounded-lg space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ChartBarSquareIcon className="w-5 h-5 text-indigo-600" />
              <h3 className="font-semibold text-gray-900">Créer un sondage</h3>
            </div>
            <button
              onClick={() => {
                setShowPollCreator(false);
                setPollQuestion('');
                setPollOptions(['', '']);
                setPollExpirationDate('');
                setPollExpirationTime('');
                setPollMultipleChoice(false);
                setPollAnonymousVoting(false);
              }}
              className="p-1 text-gray-400 hover:text-gray-600 hover:bg-white rounded-lg transition-colors"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Poll Question */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Question du sondage *
            </label>
            <input
              type="text"
              value={pollQuestion}
              onChange={(e) => setPollQuestion(e.target.value)}
              placeholder="Quelle est votre question ?"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              maxLength={500}
            />
          </div>

          {/* Poll Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Options de réponse *
            </label>
            <div className="space-y-2">
              {pollOptions.map((option, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="text-sm text-gray-500 font-medium w-8">{index + 1}.</span>
                  <input
                    type="text"
                    value={option}
                    onChange={(e) => {
                      const newOptions = [...pollOptions];
                      newOptions[index] = e.target.value;
                      setPollOptions(newOptions);
                    }}
                    placeholder={`Option ${index + 1}`}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    maxLength={200}
                  />
                  {pollOptions.length > 2 && (
                    <button
                      type="button"
                      onClick={() => {
                        const newOptions = pollOptions.filter((_, i) => i !== index);
                        setPollOptions(newOptions);
                      }}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <XMarkIcon className="w-5 h-5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            {pollOptions.length < 10 && (
              <button
                type="button"
                onClick={() => setPollOptions([...pollOptions, ''])}
                className="mt-2 text-indigo-600 hover:text-indigo-700 text-sm font-medium"
              >
                + Ajouter une option
              </button>
            )}
          </div>

          {/* Poll Settings */}
          <div className="space-y-3 pt-3 border-t border-indigo-200">
            <h4 className="text-sm font-semibold text-gray-700">Paramètres du sondage</h4>

            {/* Multiple Choice */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={pollMultipleChoice}
                onChange={(e) => setPollMultipleChoice(e.target.checked)}
                className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <span className="text-sm text-gray-700">
                Choix multiples (permettre plusieurs sélections)
              </span>
            </label>

            {/* Anonymous Voting */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={pollAnonymousVoting}
                onChange={(e) => setPollAnonymousVoting(e.target.checked)}
                className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <span className="text-sm text-gray-700">
                Vote anonyme (masquer les identités des votants)
              </span>
            </label>
          </div>

          {/* Poll Expiration */}
          <div className="pt-3 border-t border-indigo-200">
            <PollExpirationPicker
              onDateTimeChange={(date, time) => {
                setPollExpirationDate(date);
                setPollExpirationTime(time);
              }}
              initialDate={pollExpirationDate}
              initialTime={pollExpirationTime}
              size="normal"
            />
          </div>
        </div>
      )}

      {/* Media Preview */}
      {isExpanded && attachedMedia.length > 0 && (
        <div className="mb-4 space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Fichiers joints ({attachedMedia.length})
          </label>
          <div className="space-y-2">
            {attachedMedia.map((media, index) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                {/* Preview/Icon */}
                <div className="flex-shrink-0">
                  {media.type === 'image' && media.preview ? (
                    <img
                      src={media.preview}
                      alt="Preview"
                      className="w-16 h-16 object-cover rounded-lg"
                    />
                  ) : media.type === 'video' ? (
                    <div className="w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
                      <VideoCameraIcon className="w-8 h-8 text-blue-600" />
                    </div>
                  ) : media.type === 'audio' ? (
                    <div className="w-16 h-16 bg-purple-100 rounded-lg flex items-center justify-center">
                      <MusicalNoteIcon className="w-8 h-8 text-purple-600" />
                    </div>
                  ) : (
                    <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                      <PhotoIcon className="w-8 h-8 text-gray-400" />
                    </div>
                  )}
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {media.name}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-500">
                      {formatFileSize(media.size)}
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-500 capitalize">
                      {media.type}
                    </span>
                  </div>
                  {media.uploading && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${media.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Téléversement... {media.progress}%
                      </p>
                    </div>
                  )}
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeMedia(index)}
                  className="flex-shrink-0 p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="Supprimer"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-200">
        <div className="flex items-center gap-2">
          {/* Media Buttons */}
          <button
            onClick={() => handleMediaUpload('image')}
            className="p-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors"
            title="Ajouter une photo"
          >
            <PhotoIcon className="w-5 h-5" />
          </button>

          <button
            onClick={() => handleMediaUpload('video')}
            className="p-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors"
            title="Ajouter une vidéo"
          >
            <VideoCameraIcon className="w-5 h-5" />
          </button>

          <button
            onClick={() => handleMediaUpload('audio')}
            className="p-2 text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors"
            title="Ajouter un audio"
          >
            <MusicalNoteIcon className="w-5 h-5" />
          </button>

          <button
            onClick={handlePollClick}
            className={`p-2 rounded-lg transition-colors ${
              showPollCreator
                ? 'bg-indigo-100 text-indigo-600'
                : 'text-gray-600 hover:bg-blue-50 hover:text-blue-600'
            }`}
            title="Créer un sondage"
          >
            <ChartBarSquareIcon className="w-5 h-5" />
          </button>

          {/* Advanced Dropdown */}
          {!threadId && (
            <div className="relative" ref={advancedMenuRef}>
              <button
                onClick={handleAdvancedClick}
                className="flex items-center gap-1 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                title="Options avancées"
              >
                <SparklesIcon className="w-5 h-5" />
                <span className="text-sm font-medium">Avancé</span>
              </button>

              {showAdvancedMenu && !threadId && (
                <div className="absolute left-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                  <button
                    onClick={handleRichArticle}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                  >
                    <span>📝</span>
                    <span>Article enrichi</span>
                  </button>
                  <button
                    onClick={handleNewThread}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                  >
                    <span>💬</span>
                    <span>Nouveau sujet</span>
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-3">
          {/* Visibility Selector */}
          <select
            value={visibility}
            onChange={(e) => setVisibility(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {visibilityOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || (!content.trim() && attachedMedia.length === 0 && activeMode !== 'poll')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              isSubmitting || (!content.trim() && attachedMedia.length === 0 && activeMode !== 'poll')
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isSubmitting ? 'Publication...' : 'Publier'}
          </button>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,video/*,audio/*"
        className="hidden"
        onChange={(e) => {
          // TODO: Handle file selection
          console.log('Files selected:', e.target.files);
        }}
      />

      {/* Modals */}
      <RichArticleModal
        isOpen={showArticleModal}
        onClose={() => setShowArticleModal(false)}
        division={division}
        section={section}
        community={community}
        onSubmit={handleArticleSubmit}
      />

      <ThreadCreatorModal
        isOpen={showThreadModal}
        onClose={() => setShowThreadModal(false)}
        division={division}
        section={section}
        rubriqueTemplateId={rubriqueTemplateId}
        community={community}
        municipalitySlug={municipalitySlug}
        onSubmit={handleThreadSubmit}
      />

      {/* Hidden File Inputs */}
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        multiple
        onChange={(e) => handleFileSelect(e, 'image')}
        className="hidden"
      />
      <input
        ref={videoInputRef}
        type="file"
        accept="video/*"
        onChange={(e) => handleFileSelect(e, 'video')}
        className="hidden"
      />
      <input
        ref={audioInputRef}
        type="file"
        accept="audio/*"
        onChange={(e) => handleFileSelect(e, 'audio')}
        className="hidden"
      />
    </div>
  );
};

export default InlinePostCreator;
