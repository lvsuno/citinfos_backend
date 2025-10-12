import React, { useState, useRef } from 'react';
import {
  XMarkIcon,
  PhotoIcon,
  PaperClipIcon,
  ChartBarIcon,
  GlobeAltIcon,
  LockClosedIcon,
  UserGroupIcon,
  ArrowPathRoundedSquareIcon
} from '@heroicons/react/24/outline';
import PostCard from './PostCard';
import { socialAPI } from '../../services/social-api';
import toast from 'react-hot-toast';

/**
 * RepostModal - A reusable modal for creating reposts with rich content
 *
 * Features:
 * - Shows original post preview
 * - Allows adding text, attachments, and polls to repost
 * - Supports different visibility levels
 * - Handles file uploads
 * - Reusable across the app
 *
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible
 * @param {Function} props.onClose - Close modal callback
 * @param {Function} props.onRepost - Success callback with created repost data
 * @param {Object} props.originalPost - The post being reposted
 */
const RepostModal = ({
  isOpen,
  onClose,
  onRepost,
  originalPost
}) => {
  const [repostForm, setRepostForm] = useState({
    content: '',
    visibility: 'public',
    attachments: [],
    poll: null
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showVisibilityMenu, setShowVisibilityMenu] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef();

  // Visibility options
  const visibilityOptions = [
    {
      value: 'public',
      label: 'Public',
      icon: GlobeAltIcon,
      description: 'Anyone can see this repost'
    },
    {
      value: 'followers',
      label: 'Followers',
      icon: UserGroupIcon,
      description: 'Only your followers can see this repost'
    },
    {
      value: 'private',
      label: 'Private',
      icon: LockClosedIcon,
      description: 'Only you can see this repost'
    }
  ];

  const currentVisibility = visibilityOptions.find(v => v.value === repostForm.visibility) || visibilityOptions[0];

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (isSubmitting) return;

    setIsSubmitting(true);

    try {
      let response;

      // If there are attachments, we need to create a full post first
      if (repostForm.attachments.length > 0) {
        // Create a repost with attachments using the posts API
        response = await socialAPI.posts.create({
          content: repostForm.content.trim(),
          visibility: repostForm.visibility,
          post_type: 'repost',
          original_post: originalPost.id,
          attachments: repostForm.attachments
        });
      } else {
        // Simple repost using the repost endpoint
        response = await socialAPI.reposts.create(originalPost.id, repostForm.content.trim());
      }

      toast.success('Repost created successfully!');

      if (onRepost) {
        onRepost(response);
      }

      handleClose();

    } catch (error) {
      console.error('Error creating repost:', error);
      toast.error(error.message || 'Failed to create repost');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (files) => {
    const newAttachments = Array.from(files).map(file => ({
      id: `temp-${Date.now()}-${Math.random()}`,
      file,
      name: file.name,
      type: file.type,
      size: file.size,
      url: URL.createObjectURL(file)
    }));

    setRepostForm(prev => ({
      ...prev,
      attachments: [...prev.attachments, ...newAttachments]
    }));
  };

  // Handle drag and drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  // Remove attachment
  const removeAttachment = (attachmentId) => {
    setRepostForm(prev => ({
      ...prev,
      attachments: prev.attachments.filter(att => att.id !== attachmentId)
    }));
  };

  // Close modal and reset form
  const handleClose = () => {
    setRepostForm({
      content: '',
      visibility: 'public',
      attachments: [],
      poll: null
    });
    setShowVisibilityMenu(false);
    setDragActive(false);
    onClose();
  };

  if (!isOpen || !originalPost) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        {/* Modal */}
        <div className="relative w-full max-w-2xl transform overflow-hidden rounded-lg bg-white shadow-xl transition-all">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
            <div className="flex items-center gap-3">
              <ArrowPathRoundedSquareIcon className="h-6 w-6 text-purple-600" />
              <h2 className="text-lg font-semibold text-gray-900">Create Repost</h2>
            </div>
            <button
              onClick={handleClose}
              className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="flex flex-col">
            {/* Content Area */}
            <div className="px-6 py-4">
              {/* Text Input */}
              <div className="mb-4">
                <textarea
                  value={repostForm.content}
                  onChange={(e) => setRepostForm(prev => ({ ...prev, content: e.target.value }))}
                  placeholder="Add your thoughts to this repost..."
                  className="w-full resize-none border-none p-0 text-lg placeholder-gray-500 focus:outline-none focus:ring-0"
                  rows={3}
                />
              </div>

              {/* File Upload Area */}
              <div
                className={`rounded-lg border-2 border-dashed p-4 transition-colors ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <div className="text-center">
                  <PhotoIcon className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600">
                    Drag and drop files here, or{' '}
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="text-blue-600 hover:text-blue-500"
                    >
                      browse
                    </button>
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*,video/*,audio/*,.pdf,.doc,.docx"
                    onChange={(e) => handleFileSelect(e.target.files)}
                    className="hidden"
                  />
                </div>
              </div>

              {/* Attachments Preview */}
              {repostForm.attachments.length > 0 && (
                <div className="mt-4 space-y-2">
                  {repostForm.attachments.map((attachment) => (
                    <div
                      key={attachment.id}
                      className="flex items-center justify-between rounded-md border border-gray-200 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <PaperClipIcon className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{attachment.name}</p>
                          <p className="text-xs text-gray-500">
                            {(attachment.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeAttachment(attachment.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Original Post Preview */}
              <div className="mt-6">
                <p className="mb-2 text-sm font-medium text-gray-700">Reposting:</p>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <PostCard
                    post={originalPost}
                    isRepost={true}
                    showBorder={false}
                    compact={true}
                  />
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4">
              {/* Visibility Selector */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowVisibilityMenu(!showVisibilityMenu)}
                  className="flex items-center gap-2 rounded-md border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
                >
                  <CommunityIcon Icon={currentVisibility.icon} size="sm" />
                  {currentVisibility.label}
                </button>

                {showVisibilityMenu && (
                  <div className="absolute bottom-full left-0 z-10 mb-2 w-64 rounded-md border border-gray-200 bg-white shadow-lg">
                    {visibilityOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => {
                          setRepostForm(prev => ({ ...prev, visibility: option.value }));
                          setShowVisibilityMenu(false);
                        }}
                        className="flex w-full items-start gap-3 p-3 text-left hover:bg-gray-50"
                      >
                        <CommunityIcon Icon={option.icon} size="sm" className="mt-0.5 text-gray-400" />
                        <div>
                          <p className="font-medium text-gray-900">{option.label}</p>
                          <p className="text-xs text-gray-500">{option.description}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-md border border-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`px-4 py-2 text-sm font-medium text-white rounded-md ${
                    isSubmitting
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2'
                  }`}
                >
                  {isSubmitting ? 'Posting...' : 'Repost'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default RepostModal;
