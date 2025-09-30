import React, { useState, useEffect, useCallback, useRef } from 'react';
import AttachmentDisplay from './AttachmentDisplay';
import PostContentRenderer from './PostContentRenderer';
import PostActionBar from './PostActionBar';
import PostCommentThread from './PostCommentThread';
import PollDisplay from './PollDisplay';
import InlineRepostComposer from './InlineRepostComposer';
import usePostInteractions from './usePostInteractions';
import { useJWTAuth } from '../../hooks/useJWTAuth';
import { useNavigate } from 'react-router-dom';
import FlexibleTimePicker from '../ui/FlexibleTimePicker';
import ConfirmationModal from '../ui/ConfirmationModal';
import ClickableAuthorName from '../ui/ClickableAuthorName';
import socialAPI from '../../services/social-api';
import PostViewTracker from '../analytics/PostViewTracker';
import { XMarkIcon, MagnifyingGlassPlusIcon, MagnifyingGlassMinusIcon, ArrowsPointingOutIcon, XMarkIcon as XMini } from '@heroicons/react/24/outline';
import { FaXTwitter, FaFacebookF, FaLinkedinIn, FaRedditAlien, FaWhatsapp, FaTelegram, FaEnvelope, FaLink } from 'react-icons/fa6';
import { formatTimeAgo, formatFullDateTime } from '../../utils/timeUtils';
import UserBadgeList from '../UserBadgeList';
import TinyBadgeList from '../TinyBadgeList';

/* PostCard
   Unified post presentation & interaction component.
   Props:
     post (object) – supports fields: id, text|content, attachments[], poll, visibility, comments[], etc.
     onDelete(postId)
     onUpdate(postId, patch) – used when saving edits
     onVote(pollId, optionIds[])
     context (string) – e.g. 'feed' | 'community' (currently cosmetic hook)
*/

const PostCard = ({
  post,
  onDelete,
  onUpdate,
  onVote,
  context='feed',
  isRepost = false,
  showBorder = true,
  compact = false,
  readOnly = false,
  hideActions = false
}) => {

  // Get user data from JWT authentication
  const { user, isAuthenticated } = useJWTAuth();
  const navigate = useNavigate();

  // PostSee tracking - ref for the post container
  const postElementRef = useRef(null);

  const { postState, toggleReaction, addComment, editComment, deleteComment, toggleCommentReaction, share, repost, directShare, isLoading, error } = usePostInteractions(post);
  const [expanded, setExpanded] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draftText, setDraftText] = useState(post.text || post.content || '');
  const [editAttachments, setEditAttachments] = useState(post.attachments || []);
  const [editPolls, setEditPolls] = useState(post.polls || []);
  const [editVisibility, setEditVisibility] = useState(post.visibility || 'public');
  const [attachmentToReplace, setAttachmentToReplace] = useState(null);
  const [pdfViewer, setPdfViewer] = useState(null); // { url, name, scale }
  const [dragActive, setDragActive] = useState(false); // drag & drop state
  const [dragPreview, setDragPreview] = useState([]); // [{name,type,preview?,fullType}]
  const [dragPreviewUrls, setDragPreviewUrls] = useState([]); // for cleanup
  const [dragTotal, setDragTotal] = useState(0);
  const [shareMenuOpen, setShareMenuOpen] = useState(false);

  // Confirmation modal states
  const [deleteConfirmModal, setDeleteConfirmModal] = useState({ isOpen: false, type: null, id: null });
  const [shareToUser, setShareToUser] = useState('');
  const [reposting, setReposting] = useState(false);
  const [showInlineRepost, setShowInlineRepost] = useState(false);
  const [shareAnchor, setShareAnchor] = useState(null);
  const [sharePos, setSharePos] = useState({ top: 0, left: 0 });
  const [shareTab, setShareTab] = useState('social'); // 'social' | 'direct'

  // Ref for auto-scrolling to repost composer
  const repostComposerRef = useRef(null);
  const hasMedia = (post.attachments || []).length > 0;
  const hasPoll = !!(post.polls && post.polls.length > 0) || !!post.poll; // Support both new polls array and legacy poll
  const fileReplaceInputId = `replace-${post.id}`;
  const fileAddInputId = `add-${post.id}`; // new add input id

  // Check if current user is the author of this post
  const currentUserProfileId = user?.profile?.id;
  const postAuthorProfileId = post.author?.id || post.author; // Handle both object and UUID formats
  const isAuthor = currentUserProfileId && postAuthorProfileId && currentUserProfileId === postAuthorProfileId;

  // Debug logging for authorship detection
  useEffect(() => {
    console.log('PostCard authorship check:', {
      postId: post.id,
      currentUserProfileId,
      postAuthorProfileId,
      postAuthor: post.author,
      isAuthor,
      userObject: user
    });
  }, [currentUserProfileId, postAuthorProfileId, post.id, isAuthor, user]);

  // Sync local state with post prop changes
  useEffect(() => {
    setDraftText(post.text || post.content || '');
    setEditAttachments(post.attachments || []);
    setEditPolls(post.polls || []);
    setEditVisibility(post.visibility || 'public');
  }, [post.text, post.content, post.attachments, post.polls, post.visibility]);

  const openPdf = (att) => { if(att.type==='file' && att.preview && att.name?.toLowerCase().endsWith('.pdf')) setPdfViewer({ url: att.preview, name: att.name, scale:1 }); };
  const closePdf = () => setPdfViewer(null);
  const zoomPdf = (delta) => setPdfViewer(p => p ? { ...p, scale: Math.min(3, Math.max(0.5, +(p.scale + delta).toFixed(2))) } : p);

  const detectType = (file) => { if (!file||!file.type) return 'file'; if (file.type.startsWith('image/')) return 'image'; if (file.type.startsWith('video/')) return 'video'; if (file.type.startsWith('audio/')) return 'audio'; if (file.type === 'application/pdf') return 'file'; return 'file'; };

  const triggerReplace = (id) => { setAttachmentToReplace(id); setTimeout(()=>{ const el=document.getElementById(fileReplaceInputId); el && el.click(); },0); };
  const handleReplaceInputChange = (e) => { const file = e.target.files && e.target.files[0]; if(file && attachmentToReplace){ setEditAttachments(prev => prev.map(a => a.id===attachmentToReplace ? { ...a, name:file.name, size:file.size, type:detectType(file), preview:(file.type.startsWith('image/')||file.type.startsWith('video/')||file.type.startsWith('audio/')||file.type==='application/pdf')?URL.createObjectURL(file):null } : a)); setAttachmentToReplace(null);} e.target.value=''; };
  const handleAddFiles = (e) => { const files = Array.from(e.target.files||[]); if(!files.length) return; addNewAttachments(files); e.target.value=''; };
  const addNewAttachments = (files) => {
    const accepted = files.filter(f => f && (f.type.startsWith('image/') || f.type.startsWith('video/') || f.type.startsWith('audio/') || f.type === 'application/pdf'));
    if(!accepted.length) return;
    setEditAttachments(prev => [...prev, ...accepted.map(f=>({ id:`new-${Date.now()}-${Math.random().toString(36).slice(2,8)}`, name:f.name, size:f.size, type:detectType(f), preview:(f.type.startsWith('image/')||f.type.startsWith('video/')||f.type.startsWith('audio/')||f.type==='application/pdf')?URL.createObjectURL(f):null }))]);
  };
  const triggerAdd = () => { const el = document.getElementById(fileAddInputId); el && el.click(); };
  // Drag & Drop handlers
  const onDragOver = (e) => { e.preventDefault(); e.stopPropagation(); if(!dragActive) setDragActive(true); collectDragPreview(e); };
  const onDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); if(e.currentTarget === e.target){ clearDragPreview(); setDragActive(false);} };
  const onDrop = (e) => { e.preventDefault(); e.stopPropagation(); clearDragPreview(); setDragActive(false); const files = Array.from(e.dataTransfer.files||[]); addNewAttachments(files); };
  const clearDragPreview = () => { dragPreviewUrls.forEach(u=>{ try{URL.revokeObjectURL(u);}catch(_){} }); setDragPreviewUrls([]); setDragPreview([]); setDragTotal(0); };
  const hashString = (str) => { let h=0; for(let i=0;i<str.length;i++){ h = Math.imul(31,h) + str.charCodeAt(i) |0;} return Math.abs(h); };
  const genWaveHeights = (name) => { const h = hashString(name); const arr=[]; for(let i=0;i<12;i++){ arr.push(30 + ( ( (h >> (i%24)) & 0xF) /15)*50 ); } return arr; };
  const collectDragPreview = (e) => {
    try {
      const items = Array.from(e.dataTransfer.items||[]).filter(it => it.kind === 'file');
      setDragTotal(items.length);
      if(!items.length) return;
      const next = [];
      const urls = [];
      for (let it of items.slice(0,4)) {
        const f = it.getAsFile();
        if(!f) continue;
        const baseType = (f.type||'').split('/')[0];
        let preview = null;
        if (f.type.startsWith('image/') || f.type.startsWith('video/')) { preview = URL.createObjectURL(f); urls.push(preview); }
        next.push({ name: f.name, type: baseType, fullType: f.type, preview, wave: baseType==='audio'? genWaveHeights(f.name): null });
      }
      clearDragPreview(); // revoke previous before setting new
      setDragPreview(next);
      setDragPreviewUrls(urls);
    } catch(_) { /* ignore */ }
  };
  const typeBadge = (t, full) => { if(full==='application/pdf') return 'PDF'; if(t==='image') return 'IMG'; if(t==='video') return 'VID'; if(t==='audio') return 'AUD'; return 'FILE'; };
  const removeAttachmentEdit = (id) => setEditAttachments(prev => prev.filter(a=>a.id!==id));
  const removeAllAttachments = () => setEditAttachments([]);

  // Poll editing functions
  const canEditPoll = (poll) => {
    if (!poll || !isAuthenticated || !user) return false; // No poll, not authenticated, or no user data

    // Can edit if poll has no votes yet
    if (poll.vote_count === 0 || poll.total_votes === 0) {
      return true;
    }

    // Can edit if user is the post author AND is the only voter
    // Compare UserProfile UUIDs: user.profile.id vs post.author
    const currentUserProfileId = user.profile?.id;
    const postAuthorProfileId = post.author; // This is the UserProfile UUID from the serializer
    const isAuthor = currentUserProfileId && postAuthorProfileId && currentUserProfileId === postAuthorProfileId;

    if (isAuthor && poll.voters_count === 1 && poll.user_has_voted) {
      return true;
    }

    return false;
  };

  const canDeletePoll = (poll) => {
    // Can always delete own polls
    return poll;
  };

  const updatePollQuestion = (pollId, newQuestion) => {
    setEditPolls(prev => prev.map(p =>
      p.id === pollId ? { ...p, question: newQuestion } : p
    ));
  };

  const updatePollOption = (pollId, optionId, newText) => {
    setEditPolls(prev => prev.map(p =>
      p.id === pollId ? {
        ...p,
        options: p.options.map(opt =>
          opt.id === optionId ? { ...opt, text: newText } : opt
        )
      } : p
    ));
  };

  const addPollOption = (pollId) => {
    setEditPolls(prev => prev.map(p =>
      p.id === pollId ? {
        ...p,
        options: [...p.options, {
          id: `new-option-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
          text: '',
          order: Math.max(...p.options.map(opt => opt.order || 0), -1) + 1,
          vote_count: 0,
          percentage: 0,
          user_has_voted: false
        }]
      } : p
    ));
  };

  const removePollOption = (pollId, optionId) => {
    setEditPolls(prev => prev.map(p =>
      p.id === pollId ? {
        ...p,
        options: p.options.filter(opt => opt.id !== optionId)
      } : p
    ));
  };

  const deletePoll = (pollId) => {
    setDeleteConfirmModal({
      isOpen: true,
      type: 'poll',
      id: pollId
    });
  };

  const handleDeletePost = () => {
    setDeleteConfirmModal({
      isOpen: true,
      type: 'post',
      id: post.id
    });
  };

  const executeDelete = async () => {
    const { type, id } = deleteConfirmModal;

    try {
      if (type === 'post') {
        // Use the parent's delete function which handles server sync properly
        if (onDelete) {
          await onDelete(id);
        }
      } else if (type === 'poll') {
        // For polls, try to delete from server first
        try {
          await socialAPI.posts.deletePoll(id);
        } catch (error) {
          // If it's a 404, the poll doesn't exist on server
          if (error.response?.status === 404) {
            // Poll doesn't exist on server, removing from local state only
          } else {
            throw error;
          }
        }

        // Remove poll from local state
        setEditPolls(prev => prev.filter(p => p.id !== id));
        // Save the updated post
        if (onUpdate) {
          const updatedPolls = editPolls.filter(p => p.id !== id);
          await onUpdate(post.id, { polls: updatedPolls });
        }
      }
    } catch (error) {
      console.error(`Error deleting ${type}:`, error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error occurred';
      alert(`Failed to delete ${type}: ${errorMessage}`);
    }

    // Close modal
    setDeleteConfirmModal({ isOpen: false, type: null, id: null });
  };  const closeDeleteModal = () => {
    setDeleteConfirmModal({ isOpen: false, type: null, id: null });
  };

  const togglePollMultipleChoice = (pollId) => {
    setEditPolls(prev => prev.map(p =>
      p.id === pollId ? {
        ...p,
        multiple_choice: !p.multiple_choice,
        allows_multiple_votes: !p.multiple_choice // Keep both for compatibility
      } : p
    ));
  };

  const updatePollExpiration = useCallback((pollId, date, time) => {
    let expires_at = null;

    if (date && time) {
      try {
        expires_at = new Date(`${date}T${time}`).toISOString();
      } catch (error) {
        console.warn('Invalid date/time format:', error);
        expires_at = null;
      }
    } else {
      // If no date/time specified, extend by 1 day from current expiration or now
      const currentPoll = editPolls.find(p => p.id === pollId);
      const baseDate = currentPoll?.expires_at ? new Date(currentPoll.expires_at) : new Date();
      baseDate.setDate(baseDate.getDate() + 1);
      expires_at = baseDate.toISOString();
    }

    setEditPolls(prev => prev.map(p =>
      p.id === pollId ? { ...p, expires_at } : p
    ));
  }, [editPolls]);

  const saveEdit = () => {
    // Filter polls to only send fields that backend accepts for updates
    const filteredPolls = editPolls.map(poll => ({
      id: poll.id,
      question: poll.question,
      multiple_choice: poll.multiple_choice || poll.allows_multiple_votes || false,
      anonymous_voting: poll.anonymous_voting || false,
      expires_at: poll.expires_at,
      options: (poll.options || []).map(option => {
        const optionData = {
          text: option.text
        };

        // Only include ID and order if it's a valid UUID (existing option)
        // Skip temporary IDs like "new-option-xyz" and let server assign order
        if (option.id && !option.id.toString().startsWith('new-')) {
          optionData.id = option.id;
          optionData.order = option.order;
        }

        return optionData;
      })
    }));

    const patch = {
      attachments: editAttachments,
      polls: filteredPolls,
      visibility: editVisibility
    };
    if (post.text !== undefined) patch.text = draftText.trim();
    else patch.content = draftText.trim();

    onUpdate && onUpdate(post.id, patch);
    setEditing(false);
  };
  const cancelEdit = () => {
    setEditing(false);
    setDraftText(post.text || post.content || '');
    setEditAttachments(post.attachments || []);
    setEditPolls(post.polls || []);
    setEditVisibility(post.visibility || 'public');
  };

  const bodyText = post.text || post.content || '';
  const visibilityLabel = post.visibility === 'public' ? '🌍 Public' : post.visibility === 'followers' ? '👥 Followers' : post.visibility === 'custom' ? '🎯 Custom' : '';
  const attachmentCount = (post.attachments || []).length;
  const showExpandButton = (
    ((bodyText && bodyText.length > 180) || attachmentCount > 0)
    && !(attachmentCount === 1 || attachmentCount === 4)
  );

  const openShareMenu = (_post, anchorEl) => {
    if (anchorEl && anchorEl.getBoundingClientRect) {
      const rect = anchorEl.getBoundingClientRect();
      const top = rect.bottom + 4 + window.scrollY; // place 4px below
      // Try to align left edge; clamp within viewport (allow 8px margin)
      const desiredLeft = rect.left + window.scrollX;
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
      const menuWidth = 288; // w-72 = 18rem = 288px
      const left = Math.min(Math.max(8, desiredLeft), viewportWidth - menuWidth - 8);
      setSharePos({ top, left });
    }
    setShareAnchor(anchorEl);
    setShareMenuOpen(true);
  };
  const closeShareMenu = () => { setShareMenuOpen(false); setShareToUser(''); setShareAnchor(null); setShareTab('social'); };
  const handleShareToUser = async (e) => {
    e.preventDefault();
    if (!shareToUser.trim()) return;

    try {
      // For now, we'll treat this as a direct share to a single user
      // In a real app, you'd have a user search/select component
      // This is a placeholder - you need to convert username to profile ID
      const recipientIds = [shareToUser.trim()]; // This should be profile IDs, not usernames
      await directShare(recipientIds, `Shared from ${user?.username || 'someone'}`);
      closeShareMenu();
    } catch (error) {
      console.error('Share to user failed:', error);
      // Error is handled by usePostInteractions hook
    }
  };

  const handleRepost = async (comment = '') => {
    // Show the inline repost composer
    setShowInlineRepost(true);

    // Scroll to the repost composer after it renders
    setTimeout(() => {
      if (repostComposerRef.current) {
        repostComposerRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    }, 100);
  };

  // Handle successful repost creation from inline composer
  const handleRepostSuccess = (repostData) => {
    setShowInlineRepost(false);
    // Update the post state to reflect that it's been reposted
    if (repostData) {
      // Navigate to the user's profile where they can see and manage their repost
      // Add a slight delay to ensure the repost appears in the feed
      setTimeout(() => {
        if (user?.username) {
          navigate(`/profile/${user.username}`, {
            state: { scrollToPost: repostData.id }
          });
        }
      }, 1000);
    }
  };

  // Handle repost cancel
  const handleRepostCancel = () => {
    setShowInlineRepost(false);
  };

  return (
    <>
      {/* Inline Repost Composer - appears as a new post at the top */}
      {showInlineRepost && (
        <div ref={repostComposerRef} className="mb-4 animate-in fade-in duration-200">
          <InlineRepostComposer
            originalPost={post}
            onCancel={handleRepostCancel}
            onRepost={handleRepostSuccess}
          />
        </div>
      )}

      <div
        ref={postElementRef}
        className={`${showBorder ? 'bg-white rounded-lg shadow border border-gray-100' : ''} ${isRepost ? 'p-3' : 'p-4'} relative`}
      >
      {/* PostSee Analytics Tracking */}
      {!isRepost && post.id && postElementRef.current && (
        <PostViewTracker
          postId={post.id}
          postElement={postElementRef.current}
          source={context}
          trackScrollDepth={true}
          trackTimeSpent={true}
          trackClicks={true}
          minViewTime={1000}
          minScrollPercentage={25}
        />
      )}

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white/70 backdrop-blur-sm rounded-lg flex items-center justify-center z-10">
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-full shadow-lg">
            <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            <span className="text-sm text-gray-600">Processing...</span>
          </div>
        </div>
      )}

      {/* Error notification */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500 flex-shrink-0"></div>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* PDF Modal */}
      {pdfViewer && (
        <div className="fixed inset-0 z-[300] bg-black/60 backdrop-blur-sm flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-900/70 text-white text-xs">
            <span className="truncate max-w-[60%]" title={pdfViewer.name}>{pdfViewer.name}</span>
            <div className="flex items-center gap-2">
              <button onClick={()=>zoomPdf(0.1)} className="px-2 py-1 rounded bg-white/10 hover:bg-white/20" title="Zoom in"><MagnifyingGlassPlusIcon className="h-4 w-4" /></button>
              <button onClick={()=>zoomPdf(-0.1)} className="px-2 py-1 rounded bg-white/10 hover:bg-white/20" title="Zoom out"><MagnifyingGlassMinusIcon className="h-4 w-4" /></button>
              <button onClick={()=>setPdfViewer(p=> p ? { ...p, scale:1 } : p)} className="px-2 py-1 rounded bg-white/10 hover:bg-white/20" title="Reset zoom"><ArrowsPointingOutIcon className="h-4 w-4" /></button>
              <button onClick={closePdf} className="px-2 py-1 rounded bg-white/10 hover:bg-white/20" title="Close"><XMarkIcon className="h-4 w-4" /></button>
            </div>
          </div>
          <div className="flex-1 overflow-auto p-4 flex items-start justify-center" onClick={closePdf}>
            <div className="bg-white shadow-2xl rounded max-w-5xl w-full flex justify-center" style={{ transform:`scale(${pdfViewer.scale})`, transformOrigin:'top center' }} onClick={e=>e.stopPropagation()}>
              <iframe title="PDF Preview" src={pdfViewer.url} className="w-full h-[calc(100vh-120px)] rounded-b" />
            </div>
          </div>
        </div>
      )}

      {shareMenuOpen && (
        <div className="fixed z-[260]" style={{ top: sharePos.top, left: sharePos.left }} onClick={closeShareMenu}>
          <div className="bg-white border border-gray-200 rounded-lg shadow-lg w-72 text-[11px] p-2" onClick={e=>e.stopPropagation()}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <button onClick={()=>setShareTab('social')} className={`px-2 py-1 rounded text-[10px] font-medium ${shareTab==='social'?'bg-indigo-600 text-white':'text-gray-600 hover:bg-gray-100'}`}>Social</button>
                <button onClick={()=>setShareTab('direct')} className={`px-2 py-1 rounded text-[10px] font-medium ${shareTab==='direct'?'bg-indigo-600 text-white':'text-gray-600 hover:bg-gray-100'}`}>Users</button>
              </div>
              <button onClick={closeShareMenu} className="p-1 rounded hover:bg-gray-100"><XMini className="h-3 w-3" /></button>
            </div>
            {shareTab==='social' && (
              <div className="py-1">
                <div className="grid grid-cols-4 gap-2">
                  {[
                    {k:'twitter', label:'Twitter', icon:<FaXTwitter className='h-4 w-4' />},
                    {k:'facebook', label:'Facebook', icon:<FaFacebookF className='h-4 w-4' />},
                    {k:'linkedin', label:'LinkedIn', icon:<FaLinkedinIn className='h-4 w-4' />},
                    {k:'reddit', label:'Reddit', icon:<FaRedditAlien className='h-4 w-4' />},
                    {k:'whatsapp', label:'WhatsApp', icon:<FaWhatsapp className='h-4 w-4' />},
                    {k:'telegram', label:'Telegram', icon:<FaTelegram className='h-4 w-4' />},
                    {k:'email', label:'Email', icon:<FaEnvelope className='h-4 w-4' />},
                    {k:'copy', label:'Copy', icon:<FaLink className='h-4 w-4' />},
                  ].map(net => (
                    <button key={net.k} onClick={()=>{ /* share placeholder */ closeShareMenu(); }} className="flex flex-col items-center gap-1 p-2 rounded hover:bg-gray-50 text-gray-600 hover:text-indigo-600">
                      <span className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center">{net.icon}</span>
                      <span className="text-[9px] truncate max-w-[60px]">{net.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {shareTab==='direct' && (
              <form onSubmit={handleShareToUser} className="py-1">
                <div className="flex items-center gap-2 mb-2">
                  <input value={shareToUser} onChange={e=>setShareToUser(e.target.value)} placeholder="username(s)" className="flex-1 px-2 py-1 rounded border border-gray-300 text-[11px] focus:ring-indigo-500 focus:border-indigo-500" />
                  <button type="submit" className="px-2 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700">Send</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      <input id={fileReplaceInputId} type="file" className="hidden" onChange={handleReplaceInputChange} accept="application/pdf,image/*,video/*,audio/*" />
      <input id={fileAddInputId} type="file" className="hidden" multiple onChange={handleAddFiles} accept="application/pdf,image/*,video/*,audio/*" />
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center text-white text-xs font-semibold">{(post.author?.username||'U').charAt(0).toUpperCase()}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <ClickableAuthorName
                  author={post.author}
                  authorUsername={post.author_username}
                />
                {visibilityLabel && <span className="ml-2 text-[10px] font-normal text-gray-500">{visibilityLabel}</span>}
                <span className="text-gray-400">•</span>
                <span
                  className="text-gray-500 text-sm cursor-help"
                  title={formatFullDateTime(post.created_at)}
                >
                  {formatTimeAgo(post.created_at)}
                </span>
              </div>
              {post.author && (
                <div className="flex items-center gap-2">
                  <TinyBadgeList userId={post.author.id || post.author} maxVisible={3} />
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {!editing && !readOnly && isAuthor && <button onClick={()=>setEditing(true)} className="text-[10px] px-2 py-0.5 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-600">Edit</button>}
              {!editing && !isRepost && isAuthor && <button onClick={handleDeletePost} className="text-[10px] px-2 py-0.5 rounded-md bg-red-50 hover:bg-red-100 text-red-600">Delete</button>}
            </div>
          </div>
          {!editing && bodyText && (
            <p className={`mt-1 text-sm text-gray-700 whitespace-pre-wrap ${!expanded && bodyText.length>180 ? 'line-clamp-4' : ''}`}>
              <PostContentRenderer text={bodyText} mentions={post?.mentions || {}} />
            </p>
          )}
          {editing && (
            <div className="mt-3">
              <textarea value={draftText} onChange={e=>setDraftText(e.target.value)} className="w-full text-sm border border-gray-300 rounded-md p-2 focus:ring-indigo-500 focus:border-indigo-500" rows={3} />
              <div className="mt-3 space-y-2">
                <label className="block text-[11px] font-semibold text-gray-500">Edit Attachments</label>
                {editAttachments.length === 0 && <p className="text-[11px] text-gray-400">No attachments.</p>}
                {editAttachments.length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {editAttachments.map(att => (
                      <div key={att.id} className="relative rounded-md border border-gray-200 bg-gray-50 overflow-hidden group">
                        {att.type==='image' && att.preview && <img src={att.preview} alt={att.name} className="h-24 w-full object-cover" />}
                        {att.type==='video' && att.preview && <video src={att.preview} className="h-24 w-full object-cover" muted playsInline />}
                        {att.type==='audio' && <div className="h-24 flex items-center justify-center text-[10px] font-medium text-indigo-600 px-2 bg-gradient-to-br from-indigo-50 to-blue-50">{att.name}</div>}
                        {att.type==='file' && <div className="h-24 flex items-center justify-center text-[10px] font-medium text-gray-600 px-2 bg-gradient-to-br from-gray-50 to-gray-100">{att.name}</div>}
                        <div className="absolute inset-0 flex flex-col justify-end gap-1 p-1 opacity-0 group-hover:opacity-100 transition bg-black/10">
                          <button type="button" onClick={()=>triggerReplace(att.id)} className="w-full text-[10px] py-0.5 rounded bg-white/90 hover:bg-white text-gray-700 font-medium">Replace</button>
                          <button type="button" onClick={()=>removeAttachmentEdit(att.id)} className="w-full text-[10px] py-0.5 rounded bg-red-500/80 hover:bg-red-500 text-white font-medium">Remove</button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div className="flex items-center gap-3 flex-wrap">
                  <button type="button" onClick={triggerAdd} className="text-[10px] font-medium px-2 py-1 rounded-md bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-200">Add Attachments</button>
                  {editAttachments.length > 1 && <button type="button" onClick={removeAllAttachments} className="text-[10px] font-medium text-red-600 hover:text-red-700">Remove All</button>}
                </div>
                {/* Drag & Drop Zone */}
                <div onDragEnter={onDragOver} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop} className={`mt-2 relative border-2 border-dashed rounded-md p-4 text-center transition text-[11px] ${dragActive ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400'}`}>
                  <p className="text-gray-600">Drag & drop images, video, audio or PDF here<br/>or <button type="button" onClick={triggerAdd} className="underline text-indigo-600 hover:text-indigo-700">browse</button></p>
                  <p className="mt-1 text-[10px] text-gray-400">Accepted: images, video, audio, PDF</p>
                  {dragActive && dragPreview.length > 0 && (
                    <div className="absolute inset-0 bg-white/90 backdrop-blur-sm flex flex-col items-center justify-center p-4 animate-fade-in" aria-live="polite">
                      <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-indigo-600 text-white text-[10px] font-medium shadow">{dragTotal}</div>
                      <p className="text-[10px] font-semibold text-indigo-700 mb-2">Release to add {dragPreview.length}{dragTotal>4?'+':''}</p>
                      <div className="grid grid-cols-2 gap-2 mb-2 max-w-xs w-full">
                        {dragPreview.map((f, index) => (
                          <div key={`drag-preview-${f.name}-${index}`} className="relative rounded-md overflow-hidden border border-indigo-200 bg-indigo-50/60 h-20 flex items-center justify-center">
                            {f.preview && f.fullType.startsWith('image/') && <img src={f.preview} alt={f.name} className="object-cover w-full h-full" />}
                            {f.preview && f.fullType.startsWith('video/') && <video src={f.preview} className="object-cover w-full h-full" muted autoPlay loop playsInline />}
                            {f.type==='audio' && (
                              <div className="flex items-end gap-[2px] h-12 w-24">
                                {f.wave.map((h,i)=>(<span key={i} style={{height:`${h}%`}} className="w-[4px] bg-gradient-to-t from-indigo-400 to-indigo-600 rounded-sm animate-pulse [animation-duration:1.2s]" />))}
                              </div>
                            )}
                            {!f.preview && f.type!=='audio' && (
                              <span className="text-[9px] text-indigo-600 font-medium px-2 text-center leading-tight">
                                {typeBadge(f.type, f.fullType)}<br/><span className="text-[8px] text-gray-500 line-clamp-2">{f.name}</span>
                              </span>
                            )}
                            <span className="absolute top-1 left-1 text-[9px] bg-indigo-600/90 text-white px-1.5 py-0.5 rounded-md shadow-sm tracking-wide font-semibold">{typeBadge(f.type, f.fullType)}</span>
                          </div>
                        ))}
                      </div>
                      <p className="text-[9px] text-gray-500">Drop files to attach</p>
                    </div>
                  )}
                  <style>{`.animate-fade-in{animation:fadeIn .18s ease-out;}@keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}`}</style>
                </div>
              </div>

              {/* Poll Editing Section */}
              {editPolls.length > 0 && (
                <div className="mt-3 space-y-2">
                  <label className="block text-[11px] font-semibold text-gray-500">Edit Polls</label>
                  {editPolls.map(poll => (
                    <div key={poll.id} className="border border-gray-200 rounded-md p-3 bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[10px] font-medium text-gray-600">
                          Poll • {poll.vote_count || poll.total_votes || 0} votes
                        </span>
                        <div className="flex items-center gap-1">
                          {canEditPoll(poll) ? (
                            <span className="text-[9px] text-green-600 font-medium">✓ Editable</span>
                          ) : (
                            <span className="text-[9px] text-orange-600 font-medium">⚠ Has votes - Delete only</span>
                          )}
                          <button
                            type="button"
                            onClick={() => deletePoll(poll.id)}
                            className="text-[10px] px-2 py-0.5 rounded bg-red-100 text-red-600 hover:bg-red-200 ml-2"
                          >
                            Delete Poll
                          </button>
                        </div>
                      </div>

                      {canEditPoll(poll) ? (
                        <div className="space-y-2">
                          {/* Poll Question */}
                          <input
                            type="text"
                            value={poll.question}
                            onChange={(e) => updatePollQuestion(poll.id, e.target.value)}
                            className="w-full text-[11px] border border-gray-300 rounded px-2 py-1 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder="Poll question..."
                          />

                          {/* Poll Options */}
                          <div className="space-y-1">
                            {poll.options.map((option, index) => (
                              <div key={option.id} className="flex items-center gap-2">
                                <span className="text-[10px] text-gray-400 w-4">{index + 1}.</span>
                                <input
                                  type="text"
                                  value={option.text}
                                  onChange={(e) => updatePollOption(poll.id, option.id, e.target.value)}
                                  className="flex-1 text-[10px] border border-gray-300 rounded px-2 py-1 focus:ring-indigo-500 focus:border-indigo-500"
                                  placeholder="Option text..."
                                />
                                {poll.options.length > 2 && (
                                  <button
                                    type="button"
                                    onClick={() => removePollOption(poll.id, option.id)}
                                    className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-600 hover:bg-red-200"
                                  >
                                    ✕
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>

                          {/* Add Option Button */}
                          <button
                            type="button"
                            onClick={() => addPollOption(poll.id)}
                            className="text-[10px] px-2 py-1 rounded bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-200"
                          >
                            + Add Option
                          </button>

                          {/* Poll Settings */}
                          <div className="flex items-center gap-3 text-[10px] pt-2 border-t border-gray-200">
                            <label className="flex items-center gap-1">
                              <input
                                type="checkbox"
                                checked={poll.allows_multiple_votes || poll.multiple_choice || false}
                                onChange={() => togglePollMultipleChoice(poll.id)}
                                className="w-3 h-3 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                              />
                              <span className="text-gray-600">Allow multiple choices</span>
                            </label>
                          </div>

                          {/* Poll Expiration Date & Time */}
                          <div className="pt-2 border-t border-gray-200">
                            <FlexibleTimePicker
                              onDateTimeChange={(date, time) => updatePollExpiration(poll.id, date, time)}
                              initialDate={poll.expires_at ? new Date(poll.expires_at).toISOString().split('T')[0] : ''}
                              initialTime={poll.expires_at ? new Date(poll.expires_at).toTimeString().substr(0, 5) : ''}
                              size="small"
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <p className="text-[11px] font-medium text-gray-700">{poll.question}</p>
                          <div className="space-y-0.5">
                            {poll.options.map((option, index) => (
                              <div key={option.id} className="flex items-center justify-between text-[10px] text-gray-600">
                                <span>{index + 1}. {option.text}</span>
                                <span>{option.vote_count || 0} votes</span>
                              </div>
                            ))}
                          </div>
                          {poll.voters_count > 1 ? (
                            <p className="text-[9px] text-orange-600 mt-2">
                              ⚠ Cannot edit poll with votes from multiple users. You can only delete and create a new one.
                            </p>
                          ) : poll.voters_count === 1 ? (
                            <p className="text-[9px] text-green-600 mt-2">
                              ✓ You're the only voter - editing is enabled above.
                            </p>
                          ) : (
                            <p className="text-[9px] text-blue-600 mt-2">
                              ℹ No votes yet - editing is enabled above.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Post Settings */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex items-center gap-3 text-[11px]">
                  <label className="flex items-center gap-2">
                    <span className="text-gray-600 font-medium">Visibility:</span>
                    <select
                      value={editVisibility}
                      onChange={(e) => setEditVisibility(e.target.value)}
                      className="text-[10px] border border-gray-300 rounded px-2 py-1 focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="public">🌍 Public</option>
                      <option value="followers">👥 Followers</option>
                      <option value="private">🔒 Private</option>
                    </select>
                  </label>
                </div>
              </div>

              <div className="flex items-center gap-2 mt-2">
                <button onClick={saveEdit} className="px-2 py-1 text-[11px] rounded-md bg-indigo-600 text-white hover:bg-indigo-700">Save</button>
                <button onClick={cancelEdit} className="px-2 py-1 text-[11px] rounded-md bg-gray-100 text-gray-600 hover:bg-gray-200">Cancel</button>
              </div>
            </div>
          )}
          {!editing && hasMedia && (
            <AttachmentDisplay
              attachments={post.attachments}
              expanded={expanded}
              onToggle={()=>setExpanded(e=>!e)}
              onOpenPdf={openPdf}
            />
          )}
          {!editing && hasPoll && (
            <div className="mt-3 space-y-3">
              {/* Handle multiple polls (new format) */}
              {post.polls && post.polls.length > 0 && post.polls.map((poll, index) => (
                <PollDisplay
                  key={`${poll.id}-${poll.options?.length || 0}-${post.updated_at}-${post._lastUpdated}`}
                  poll={poll}
                  onVote={onVote}
                  readonly={readOnly}
                />
              ))}
              {/* Handle legacy single poll format */}
              {post.poll && !post.polls && (
                <PollDisplay
                  key={`${post.poll.id}-${post.poll.options?.length || 0}-${post.updated_at}-${post._lastUpdated}`}
                  poll={post.poll}
                  onVote={onVote}
                  readonly={readOnly}
                />
              )}
            </div>
          )}
          {showExpandButton ? (
            <button type="button" onClick={()=>setExpanded(e=>!e)} className="mt-3 text-[11px] font-medium text-indigo-600 hover:text-indigo-800">{expanded ? 'Collapse' : 'Expand'}</button>
          ) : null}
          {!editing && (
            <div className="mt-3">
              <PostActionBar
                post={postState}
                onToggleReaction={hideActions || readOnly ? () => {} : (_,kind)=>toggleReaction(kind)}
                onToggleComments={hideActions || readOnly ? () => {} : ()=>setShowComments(s=>!s)}
                onShare={hideActions || readOnly ? () => {} : ()=>share()}
                onOpenShareMenu={hideActions || readOnly ? () => {} : openShareMenu}
                onRepost={hideActions || readOnly ? () => {} : handleRepost}
                readOnly={hideActions || readOnly}
              />
            </div>
          )}
          {showComments && !editing && (
            <PostCommentThread
              postId={post.id}
              comments={postState.comments}
              onAddComment={(_,parentId,text)=>addComment(text,parentId)}
              onToggleCommentReaction={(_,commentId,kind)=>toggleCommentReaction(commentId,kind)}
              onDeleteComment={(_,commentId)=>deleteComment(commentId)}
              onEditComment={(_,commentId,newText)=>editComment(commentId,newText)}
            />
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteConfirmModal.isOpen}
        onClose={closeDeleteModal}
        onConfirm={executeDelete}
        title={`Delete ${deleteConfirmModal.type === 'post' ? 'Post' : 'Poll'}`}
        message={
          deleteConfirmModal.type === 'post'
            ? 'Are you sure you want to delete this post? This action cannot be undone.'
            : 'Are you sure you want to delete this poll? This will remove all votes and cannot be undone.'
        }
        confirmText="Delete"
        cancelText="Cancel"
        type="danger"
      />
    </div>
    </>
  );
};
export default PostCard;
