import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PhotoIcon,
  PaperClipIcon,
  ArrowPathRoundedSquareIcon,
  XMarkIcon,
  FaceSmileIcon
} from '@heroicons/react/24/outline';
import PostCard from './PostCard';
import VisibilitySelector from '../ui/VisibilitySelector';
import MentionAutocomplete from '../ui/MentionAutocomplete';
import { socialAPI } from '../../services/social-api';
import { useMentionInput } from '../../hooks/useMentionInput';
import toast from 'react-hot-toast';

// File type constants from PostComposer
const ACCEPT_IMAGE = ['image/jpeg','image/png','image/gif','image/webp'];
const ACCEPT_VIDEO = ['video/mp4','video/webm','video/quicktime'];
const ACCEPT_AUDIO = ['audio/mpeg','audio/wav','audio/ogg','audio/mp3'];
const ACCEPT_PDF = ['application/pdf'];

// Emoji constants (simplified version from PostComposer)
const CUSTOM_EMOJI_NAMES = {
  '😀':'grinning face','😃':'smiling face','😄':'smiling face open eyes','😁':'beaming face','😆':'grinning squinting','😅':'grinning sweat','😂':'face tears of joy','🤣':'rolling on floor laughing','😊':'smiling blushing','🙂':'slightly smiling','😉':'winking face','😍':'smiling face hearts','🥰':'smiling face hearts','😘':'face blowing kiss','😗':'kissing face','😙':'kissing smiling eyes','😚':'kissing closed eyes','😋':'face savoring food','😜':'winking tongue','🤪':'zany face','😝':'squinting tongue','😛':'face with tongue','🤔':'thinking face','🤗':'hugging face','🤭':'face with hand over mouth','🤫':'shushing face','🤐':'zipper mouth','😐':'neutral face','😑':'expressionless','😶':'no mouth','🙄':'face with rolling eyes','😴':'sleeping face','🤤':'drooling face','😪':'sleepy face','🥱':'yawning face','😳':'flushed face','🥵':'hot face','🥶':'cold face','😱':'screaming in fear','😨':'fearful face','😰':'anxious sweat','😥':'sad but relieved','😢':'crying face','😭':'loudly crying','😤':'face with steam','😠':'angry face','😡':'pouting face','🤬':'cursing face','🤯':'exploding head','🥺':'pleading face','👍':'thumbs up','👎':'thumbs down','👊':'oncoming fist','✊':'raised fist','🤞':'crossed fingers','✌️':'victory hand','🤟':'love-you gesture','🤘':'sign of the horns','👌':'OK hand','🤌':'pinched fingers','🤏':'pinching hand','✋':'raised hand','🖐️':'hand with fingers splayed','🤚':'raised back of hand','🖖':'vulcan salute','👋':'waving hand','👏':'clapping hands','🙌':'raising hands','🤝':'handshake','🙏':'folded hands','❤️':'red heart','💔':'broken heart','💕':'two hearts','💞':'revolving hearts','💖':'sparkling heart','💘':'heart with arrow','💝':'heart with ribbon','💟':'heart decoration','✔️':'check mark','❌':'cross mark','✅':'check mark button','❎':'cross mark button','➕':'heavy plus','➖':'heavy minus','➗':'heavy division'
};

const RAW_EMOJI_CATEGORIES = [
  { label: 'Smileys', list: '😀 😃 😄 😁 😆 😅 😂 🤣 😊 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😜 🤪 😝 😛 🤑 🤗 🤭 🤫 🤔 🤐 🤨 😐 😑 😶 😏 😒 🙄 😬 🤥 😴 🤤 😪 😮‍💨 😌 😔 😪 😮 😯 😲 🥱 😳 🥵 🥶 😱 😨 😰 😥 😢 😭 😤 😠 😡 🤬 🤯 😳 🥺 😟 😦 😧 😮 😬 😑 😯 😲 ☹️ 🙁 😕' },
  { label: 'Gestures', list: '👍 👎 👊 ✊ 🤛 🤜 🤞 ✌️ 🤟 🤘 👌 🤌 🤏 🫰 ✋ 🖐️ 🤚 🖖 👋 🤙 👏 🙌 👐 🤲 🤝 🙏' },
  { label: 'People', list: '👶 👧 🧒 👦 👩 🧑 👨 👩‍🦱 👨‍🦱 👩‍🦰 👨‍🦰 👱‍♀️ 👱 👨‍🦳 👩‍🦳 👨‍🦲 👩‍🦲 🧔 🤴 👸' },
  { label: 'Animals', list: '🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐽 🐸 🐵 🙈 🙉 🙊 🐔 🐧 🐦 🐤 🐣 🐥 🦆 🦅 🦉 🦇' },
  { label: 'Food', list: '🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🌽 🥕 🧄 🧅 🥔' },
  { label: 'Activities', list: '⚽ 🏀 🏈 ⚾ 🎾 🏐 🏉 🎱 🥏 🏓 🏸 🥅 🥊 🥋 🥇 🥈 🥉 🏆 🎮 🕹️ 🎲 ♟️ 🧩 🎯 🎳 🎰' },
  { label: 'Objects', list: '⌚ 📱 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📞 ☎️ 📠 📺 📻' },
  { label: 'Symbols', list: '❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 ❤️‍🔥 ❤️‍🩹 💔 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 ☮️ ✔️ ❌ ✅ ❎ ➕ ➖ ➗' }
];

const EMOJI_CATEGORIES = RAW_EMOJI_CATEGORIES.map(cat => {
  const chars = cat.list.split(/\s+/).filter(Boolean);
  return {
    label: cat.label,
    items: chars.map((ch, idx) => ({
      char: ch,
      name: CUSTOM_EMOJI_NAMES[ch] || `${cat.label.toLowerCase()} ${idx+1}`
    }))
  };
});

/**
 * InlineRepostComposer - An inline repost creation interface
 *
 * Features:
 * - Inline repost creation (replaces modal)
 * - File attachment support with drag & drop
 * - Visibility settings (public, followers, custom)
 * - Custom visibility with user/community specification
 * - Form validation and error handling
 * - Read-only original post display
 *
 * @param {Object} props.originalPost - The post being reposted
 * @param {Function} props.onCancel - Cancel callback
 * @param {Function} props.onRepost - Success callback with created repost data
 */
const InlineRepostComposer = ({
  originalPost,
  onCancel,
  onRepost
}) => {
  // Use mention hook for text input with autocomplete
  const {
    text: content,
    setText: setContent,
    cursorPosition,
    textareaRef,
    handleChange: handleContentChange,
    handleMentionSelect,
    handleKeyDown,
    handleClick,
    handleSelectionChange
  } = useMentionInput('');

  const [repostForm, setRepostForm] = useState({
    visibility: 'public',
    attachments: []
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [customFollowers, setCustomFollowers] = useState(''); // comma separated list
  const [showValidation, setShowValidation] = useState(false);

  // Emoji picker state
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [activeEmojiTab, setActiveEmojiTab] = useState('Recent');
  const [recentEmojis, setRecentEmojis] = useState([]);
  const [focusedEmojiIndex, setFocusedEmojiIndex] = useState(0);
  const [emojiTabOffset, setEmojiTabOffset] = useState(0);
  const [searchEmoji, setSearchEmoji] = useState('');

  const fileInputRef = useRef();
  // textareaRef now comes from mention hook
  const emojiPickerRef = useRef();

  // Emoji functionality
  const EMOJI_TABS = ['Recent', ...EMOJI_CATEGORIES.map(c=>c.label)];

  // Load recent emojis from localStorage
  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('repost_recent_emojis')||'[]');
      if (Array.isArray(stored)) setRecentEmojis(stored);
    } catch(_) {}
  }, []);

  // Persist recent emojis when changed
  useEffect(() => {
    try {
      localStorage.setItem('repost_recent_emojis', JSON.stringify(recentEmojis.slice(0,30)));
    } catch(_) {}
  }, [recentEmojis]);

  const pushRecentEmoji = (emoji) => {
    setRecentEmojis(prev => {
      const filtered = prev.filter(e => e !== emoji);
      return [emoji, ...filtered].slice(0,30);
    });
  };

  const insertEmoji = (emoji) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const currentContent = content;

    const newContent = currentContent.substring(0, start) + emoji + currentContent.substring(end);

    setContent(newContent);
    pushRecentEmoji(emoji.trim());

    // Keep focus on textarea without setTimeout to prevent picker from closing
    textarea.focus();
    textarea.setSelectionRange(start + emoji.length, start + emoji.length);
  };

  const ensureTabVisible = (tab) => {
    const idx = EMOJI_TABS.indexOf(tab);
    if (idx < emojiTabOffset) setEmojiTabOffset(idx);
    else if (idx >= emojiTabOffset + 4) setEmojiTabOffset(Math.min(idx - 3, EMOJI_TABS.length - 4));
  };

  useEffect(() => { ensureTabVisible(activeEmojiTab); }, [activeEmojiTab]);

  // Close emoji picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (emojiPickerRef.current && !emojiPickerRef.current.contains(event.target)) {
        setShowEmojiPicker(false);
      }
    };

    if (showEmojiPicker) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showEmojiPicker]);

  // Helper function to detect file type based on MIME type
  const detectType = (file) => {
    if (ACCEPT_IMAGE.includes(file.type)) return 'image';
    if (ACCEPT_VIDEO.includes(file.type)) return 'video';
    if (ACCEPT_AUDIO.includes(file.type)) return 'audio';
    if (ACCEPT_PDF.includes(file.type)) return 'file'; // treat pdf as generic file
    return null; // unsupported generic file types now rejected
  };

  // Helper function to determine post type based on attachments
  const getPostType = () => {
    if (repostForm.attachments.length === 0) return 'repost';
    // For reposts with attachments, use the first attachment type
    // Backend doesn't support "mixed" type, so we use the primary attachment type
    return repostForm.attachments[0].type;
  };

  // Auto-resize textarea
  const handleTextareaResize = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (isSubmitting) return;

    // Validate custom visibility
    if (repostForm.visibility === 'custom' && !customFollowers.trim()) {
      setShowValidation(true);
      toast.error('Please specify users or communities for custom visibility');
      return;
    }

    setIsSubmitting(true);
    setShowValidation(false);

    try {
      // Prepare post data
      const postData = {
        content: content.trim(),
        visibility: repostForm.visibility,
        post_type: getPostType(),
        original_post: originalPost.id
      };

      // Add custom visibility list if applicable
      if (repostForm.visibility === 'custom') {
        postData.custom_visibility_list = customFollowers.split(',').map(v => v.trim()).filter(Boolean);
      }

      let response;

      // Always use the reposts endpoint - it now handles both simple and complex reposts
      if (repostForm.attachments.length > 0) {
        // Add attachments to post data
        postData.attachments = repostForm.attachments;
      }

      // Use the reposts API which will route to the correct endpoint
      response = await socialAPI.reposts.create(originalPost.id, postData);

      toast.success('Repost created successfully!');

      if (onRepost) {
        onRepost(response);
      }

      // Reset form
      setRepostForm({
        content: '',
        visibility: 'public',
        attachments: []
      });
      setCustomFollowers('');

    } catch (error) {      toast.error(error.message || 'Failed to create repost');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileSelect = (files) => {
    const newAttachments = Array.from(files).map(file => {
      const detectedType = detectType(file);
      if (!detectedType) {
        toast.error(`Unsupported file type: ${file.type}`);
        return null;
      }
      return {
        id: `temp-${Date.now()}-${Math.random()}`,
        file,
        name: file.name,
        type: detectedType, // Use detected type instead of MIME type
        size: file.size,
        url: URL.createObjectURL(file)
      };
    }).filter(Boolean); // Remove null entries for unsupported files

    if (newAttachments.length > 0) {
      setRepostForm(prev => ({
        ...prev,
        attachments: [...prev.attachments, ...newAttachments]
      }));
    }
  };

  const removeAttachment = (id) => {
    setRepostForm(prev => ({
      ...prev,
      attachments: prev.attachments.filter(att => att.id !== id)
    }));
  };

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  return (
    <div className="bg-white rounded-lg border-2 border-blue-200 shadow-lg p-4 space-y-4 animate-in slide-in-from-top duration-300">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
          Create Repost
        </h3>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Cancel repost"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Original Post Preview */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-gray-700">Reposting:</p>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <PostCard
            post={originalPost}
            isRepost={true}
            showBorder={false}
            compact={false}
            readOnly={true}
            hideActions={false}
          />
        </div>
      </div>

      {/* Repost Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Content Input with Mention Support */}
        <div className="relative">
          <label htmlFor="repost-content" className="sr-only">
            Add your comment
          </label>
          <textarea
            id="repost-content"
            ref={textareaRef}
            value={content}
            onChange={(e) => {
              handleContentChange(e);
              handleTextareaResize();
            }}
            onKeyDown={handleKeyDown}
            onClick={handleClick}
            onSelect={handleSelectionChange}
            placeholder="Add your comment (optional). Use @username to mention users..."
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows="3"
            style={{ minHeight: '80px' }}
          />
          <MentionAutocomplete
            text={content}
            cursorPosition={cursorPosition}
            onMentionSelect={handleMentionSelect}
            className="mt-2 z-20"
          />
        </div>

        {/* File Upload Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
            dragActive
              ? 'border-blue-400 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center space-y-2">
            <PhotoIcon className="h-8 w-8 text-gray-400" />
            <div className="text-sm text-gray-600">
              Drop files here or{' '}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                browse
              </button>
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            accept="image/*,video/*,audio/*,.pdf"
            onChange={(e) => handleFileSelect(e.target.files)}
          />
        </div>

        {/* Attachments Preview */}
        {repostForm.attachments.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Attachments:</p>
            <div className="grid gap-2">
              {repostForm.attachments.map(attachment => (
                <div
                  key={attachment.id}
                  className="flex items-center justify-between bg-gray-50 p-2 rounded-lg"
                >
                  <div className="flex items-center space-x-2">
                    <PaperClipIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-700 truncate">
                      {attachment.name}
                    </span>
                    <span className="text-xs text-gray-500">
                      ({attachment.type})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeAttachment(attachment.id)}
                    className="text-red-500 hover:text-red-700 transition-colors"
                    aria-label={`Remove ${attachment.name}`}
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Visibility Selector and Emoji Picker */}
        <div className="flex items-center space-x-3">
          <VisibilitySelector
            visibility={repostForm.visibility}
            onVisibilityChange={(visibility) => setRepostForm(prev => ({ ...prev, visibility }))}
            customFollowers={customFollowers}
            onCustomFollowersChange={setCustomFollowers}
            showValidation={showValidation}
          />

          {/* Emoji Picker Button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowEmojiPicker(v => !v)}
              className={`flex items-center justify-center h-8 w-8 rounded-md border transition-colors ${
                showEmojiPicker
                  ? 'border-amber-300 bg-amber-50 text-amber-600 ring-2 ring-amber-300'
                  : 'border-gray-300 bg-white text-amber-500 hover:border-amber-300 hover:bg-amber-50'
              }`}
              title="Add emoji"
            >
              <FaceSmileIcon className="h-5 w-5" />
            </button>

            {showEmojiPicker && (
              <div
                ref={emojiPickerRef}
                className="absolute z-30 left-0 top-full mt-2 w-80 max-h-[340px] bg-white border border-gray-200 rounded-xl shadow-xl p-0 text-sm animate-in zoom-in-95 duration-150 origin-top-left flex flex-col"
                role="dialog"
                aria-label="Emoji picker"
              >
                {/* Search */}
                <div className="px-2 pt-2">
                  <input
                    type="text"
                    value={searchEmoji}
                    onChange={e => { setSearchEmoji(e.target.value); setFocusedEmojiIndex(0); }}
                    placeholder="Search emojis"
                    className="w-full rounded-md border border-gray-200 px-2 py-1 text-[11px] focus:ring-amber-400 focus:border-amber-400 placeholder-gray-400"
                  />
                </div>

                {/* Tabs */}
                <div className="flex items-center gap-1 px-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setEmojiTabOffset(o => Math.max(0, o - 1))}
                    disabled={emojiTabOffset === 0}
                    className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset === 0 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                  >‹</button>

                  <div className="flex items-center gap-1 flex-1" role="tablist">
                    {EMOJI_TABS.slice(emojiTabOffset, emojiTabOffset + 4).map(tab => (
                      <button
                        key={tab}
                        type="button"
                        role="tab"
                        onClick={() => { setActiveEmojiTab(tab); ensureTabVisible(tab); }}
                        className={`flex-1 px-2 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-colors ${
                          activeEmojiTab === tab
                            ? 'bg-amber-200/70 text-amber-800 shadow-inner'
                            : 'hover:bg-amber-50 text-gray-600'
                        } truncate`}
                        title={tab}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={() => setEmojiTabOffset(o => Math.min(EMOJI_TABS.length - 4, o + 1))}
                    disabled={emojiTabOffset >= EMOJI_TABS.length - 4}
                    className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset >= EMOJI_TABS.length - 4 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                  >›</button>
                </div>

                {/* Emoji Grid */}
                <div className="mt-2 px-2 pb-2 overflow-y-auto" role="grid">
                  {(() => {
                    const visibleTabs = EMOJI_TABS.slice(emojiTabOffset, emojiTabOffset + 4);
                    const baseEmojiSet = activeEmojiTab === 'Recent'
                      ? recentEmojis.map((ch,i) => ({ char: ch, name: CUSTOM_EMOJI_NAMES[ch] || `recent ${i+1}` }))
                      : (EMOJI_CATEGORIES.find(c => c.label === activeEmojiTab)?.items || []);
                    const lowerSearch = searchEmoji.trim().toLowerCase();
                    const currentEmojiSet = baseEmojiSet.filter(e => !lowerSearch || e.char.includes(lowerSearch) || e.name.toLowerCase().includes(lowerSearch));

                    return (
                      <>
                        {activeEmojiTab !== 'Recent' && !searchEmoji && (
                          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1 px-0.5">{activeEmojiTab}</p>
                        )}
                        {currentEmojiSet.length === 0 && (
                          <div className="text-[11px] text-gray-500 py-6 text-center" role="note">No emojis found.</div>
                        )}
                        <div className="flex flex-wrap gap-1" aria-label="Emoji grid">
                          {currentEmojiSet.map((e, i) => e && (
                            <button
                              key={i}
                              type="button"
                              role="gridcell"
                              data-emoji-index={i}
                              tabIndex={i === focusedEmojiIndex ? 0 : -1}
                              aria-label={`${e.name}`}
                              title={e.name}
                              onClick={() => { setFocusedEmojiIndex(i); insertEmoji(e.char + ' '); }}
                              onFocus={() => setFocusedEmojiIndex(i)}
                              className={`h-7 w-7 flex items-center justify-center rounded-md text-base hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-300 transition ${i === focusedEmojiIndex ? 'ring-1 ring-amber-300' : ''}`}
                            >
                              {e.char}
                            </button>
                          ))}
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-2 pt-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <ArrowPathRoundedSquareIcon className="h-4 w-4" />
            <span>{isSubmitting ? 'Creating...' : 'Repost'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default InlineRepostComposer;
