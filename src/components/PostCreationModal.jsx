import React, { useState, useRef } from 'react';
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
  EyeIcon
} from '@heroicons/react/24/outline';
import RichTextEditor from './ui/RichTextEditor';
import StyledSelect from './ui/StyledSelect';

const PostCreationModal = ({
  isOpen,
  onClose,
  onSubmit,
  onImageUpload,
  onVideoUpload,
  onAudioUpload
}) => {
  // Main state
  const [activeType, setActiveType] = useState('article'); // Single selection now

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

  // Reset form state
  const resetForm = () => {
    setActiveType('article'); // Reset to first option
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
        name: file.name
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

  // Form validation
  const validateForm = () => {
    const newErrors = {};

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
      const postData = {
        type: activeType, // Single type now
        content: {
          article: activeType === 'article' ? articleContent : null,
          poll: activeType === 'poll' ? {
            question: pollQuestion,
            options: pollOptions.filter(opt => opt.trim()),
            allowMultiple: allowMultipleVotes,
            expirationHours: pollExpirationHours
          } : null,
          media: activeType === 'media' ? attachedMedia : null
        },
        visibility,
        customAudience: visibility === 'custom' ? customAudience : null
      };

      await onSubmit(postData);
      handleClose();
    } catch (error) {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" onClick={handleClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Créer une nouvelle publication</h2>
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
            {/* Content Type Selection & Visibility */}
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

            {/* Article Content */}
            {activeType === 'article' && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Contenu de l'article</h4>
                {errors.article && (
                  <p className="text-sm text-red-600">{errors.article}</p>
                )}
                <RichTextEditor
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
            {activeType === 'poll' && (
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
            {activeType === 'media' && (
              <div className="space-y-4">
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
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {attachedMedia.map((item) => (
                      <div key={item.id} className="relative group">
                        <div className="aspect-square rounded-lg overflow-hidden bg-gray-100 border border-gray-200">
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
                              controls
                            />
                          ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
                              <DocumentTextIcon className="w-8 h-8 mb-2" />
                              <span className="text-xs text-center px-1">{item.name}</span>
                            </div>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => removeMedia(item.id)}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <XMarkIcon className="w-3 h-3" />
                        </button>
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