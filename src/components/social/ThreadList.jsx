import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  ClockIcon,
  UserIcon,
  ChevronRightIcon,
  EllipsisVerticalIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { socialAPI } from '../../services/social-api';
import { useAuth } from '../../contexts/AuthContext';
import ConfirmationModal from '../modals/ConfirmationModal';

/**
 * ThreadList - Component for displaying threads in a community
 *
 * Features:
 * - Lists all threads in a community
 * - Shows thread title, post count, creator, last activity
 * - Click to navigate to thread view
 * - Loading and error states
 */
const ThreadList = ({ communityId, onThreadSelect }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showOptionsMenu, setShowOptionsMenu] = useState(null);
  const [deleteThreadModal, setDeleteThreadModal] = useState({ show: false, threadId: null, threadTitle: '' });
  const optionsMenuRef = useRef(null);

  useEffect(() => {
    if (communityId) {
      fetchThreads();
    }
  }, [communityId]);

  // Click outside handler to close menu
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (optionsMenuRef.current && !optionsMenuRef.current.contains(event.target)) {
        setShowOptionsMenu(null);
      }
    };

    if (showOptionsMenu !== null) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showOptionsMenu]);

  const fetchThreads = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await socialAPI.threads.list(communityId);
      setThreads(response.results || response);
    } catch (err) {      setError('Impossible de charger les sujets');
    } finally {
      setLoading(false);
    }
  };

  const handleThreadClick = (thread) => {
    if (onThreadSelect) {
      onThreadSelect(thread);
    } else {
      // Default navigation (can be customized based on routing structure)
      navigate(`/community/${communityId}/thread/${thread.id}`);
    }
  };

  const handleEditThread = (thread, e) => {
    e.stopPropagation();
    setShowOptionsMenu(null);
    // TODO: Open edit thread modal
    console.log('Edit thread:', thread);
    // You can implement thread editing here or pass to parent component
  };

  const handleDeleteThread = (thread, e) => {
    e.stopPropagation();
    setShowOptionsMenu(null);
    setDeleteThreadModal({
      show: true,
      threadId: thread.id,
      threadTitle: thread.title
    });
  };

  const confirmDeleteThread = async () => {
    try {
      await socialAPI.threads.delete(deleteThreadModal.threadId);
      setThreads(prev => prev.filter(t => t.id !== deleteThreadModal.threadId));
      setDeleteThreadModal({ show: false, threadId: null, threadTitle: '' });
    } catch (err) {
      console.error('Error deleting thread:', err);
      alert('Erreur lors de la suppression du sujet');
    }
  };

  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 animate-pulse">
            <div className="h-5 bg-gray-300 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700 text-sm">{error}</p>
        <button
          onClick={fetchThreads}
          className="mt-2 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (threads.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto text-gray-400 mb-2" />
        <h3 className="text-gray-700 font-medium mb-1">Aucun sujet</h3>
        <p className="text-gray-500 text-sm">
          Aucun sujet de discussion n'a été créé dans cette communauté.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-2">
        {threads.map((thread) => {
          const isThreadCreator = user?.profile?.id === thread.creator?.id;

          return (
            <div
              key={thread.id}
              onClick={() => handleThreadClick(thread)}
              className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Thread Title */}
                  <div className="flex items-start gap-2 mb-2">
                    <ChatBubbleLeftRightIcon className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                    <h3 className="text-gray-900 font-semibold group-hover:text-blue-600 transition-colors">
                      {thread.title}
                    </h3>
                  </div>

                  {/* Thread Body Preview */}
                  {thread.body && (
                    <p className="text-gray-600 text-sm line-clamp-2 mb-3 ml-7">
                      {thread.body}
                    </p>
                  )}

                  {/* Thread Metadata */}
                  <div className="flex items-center gap-4 text-xs text-gray-500 ml-7">
                    {/* Post Count */}
                    <div className="flex items-center gap-1">
                      <ChatBubbleLeftRightIcon className="w-4 h-4" />
                      <span>{thread.posts_count || 0} {(thread.posts_count || 0) === 1 ? 'post' : 'posts'}</span>
                    </div>

                    {/* Creator */}
                    {thread.creator && (
                      <div className="flex items-center gap-1">
                        <UserIcon className="w-4 h-4" />
                        <span>
                          par {thread.creator.display_name || thread.creator.username}
                        </span>
                      </div>
                    )}

                    {/* Last Activity */}
                    {thread.updated_at && (
                      <div className="flex items-center gap-1">
                        <ClockIcon className="w-4 h-4" />
                        <span>
                          {formatDistanceToNow(new Date(thread.updated_at), {
                            addSuffix: true,
                            locale: fr
                          })}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Three-Dot Menu for Thread Creator */}
                <div className="flex items-center gap-2">
                  {isThreadCreator && (
                    <div
                      className="relative"
                      ref={optionsMenuRef}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowOptionsMenu(showOptionsMenu === thread.id ? null : thread.id);
                        }}
                        className="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
                        title="Options"
                      >
                        <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
                      </button>

                      {showOptionsMenu === thread.id && (
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50 animate-fade-in">
                          <button
                            onClick={(e) => handleEditThread(thread, e)}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2 transition-colors"
                          >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                            Modifier
                          </button>
                          <button
                            onClick={(e) => handleDeleteThread(thread, e)}
                            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors"
                          >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Supprimer
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Arrow Icon */}
                  <ChevronRightIcon className="w-5 h-5 text-gray-400 group-hover:text-blue-600 transition-colors flex-shrink-0" />
                </div>
              </div>

              {/* Thread Stats Bar (Optional - can show engagement metrics) */}
              {thread.view_count > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span>{thread.view_count} vues</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteThreadModal.show}
        onClose={() => setDeleteThreadModal({ show: false, threadId: null, threadTitle: '' })}
        onConfirm={confirmDeleteThread}
        title="Supprimer le sujet"
        message={`Êtes-vous sûr de vouloir supprimer le sujet "${deleteThreadModal.threadTitle}" ? Cela supprimera également tous les posts dans ce sujet. Cette action est irréversible.`}
        confirmText="Supprimer"
        cancelText="Annuler"
        confirmButtonClass="bg-red-600 hover:bg-red-700 text-white"
      />
    </>
  );
};

export default ThreadList;
