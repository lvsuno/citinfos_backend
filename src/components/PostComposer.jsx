import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  PhotoIcon,
  PaperClipIcon,
  MusicalNoteIcon,
  VideoCameraIcon,
  ChartBarSquareIcon,
  FaceSmileIcon,
  XMarkIcon,
  TrashIcon,
  PlusCircleIcon
} from '@heroicons/react/24/outline';
import { socialAPI } from '../services/social-api';
import FlexibleTimePicker from './ui/FlexibleTimePicker';
import MentionAutocomplete from './ui/MentionAutocomplete';
import VisibilitySelector from './ui/VisibilitySelector';
import { useMentionInput } from '../hooks/useMentionInput';

/*
  PostComposer
  Frontend-only rich composer supporting:
  - Text with emoji (placeholder emoji picker)
  - Images / Video / Audio / Generic files
  - Poll creation (question + multiple options)
  - Drag & drop for all file types
  - Combined attachments (e.g., image + poll)
*/

const ACCEPT_IMAGE = ['image/png','image/jpeg','image/jpg','image/gif','image/webp'];
const ACCEPT_VIDEO = ['video/mp4','video/webm','video/quicktime'];
const ACCEPT_AUDIO = ['audio/mpeg','audio/wav','audio/ogg','audio/mp3'];
const ACCEPT_PDF = ['application/pdf'];

// Helper function to extract filename from URL
const extractFileName = (url) => {
  if (!url) return 'Unknown file';
  try {
    const pathname = new URL(url).pathname;
    return pathname.split('/').pop() || 'Unknown file';
  } catch {
    return url.split('/').pop() || 'Unknown file';
  }
};

const PostComposer = ({ onSubmit, community = null, placeholder = "Quoi de neuf ?", maxLength = 2000 }) => {
  // Use mention hook for text input with autocomplete
  const {
    text,
    setText,
    cursorPosition,
    textareaRef: mentionInputRef,
    handleChange: handleTextChange,
    handleMentionSelect,
    handleKeyDown,
    handleClick,
    handleSelectionChange
  } = useMentionInput('');

  const [attachments, setAttachments] = useState([]); // { id, file, type, preview }
  const [isDragging, setIsDragging] = useState(false);
  const [showPoll, setShowPoll] = useState(false);
  const [pollQuestion, setPollQuestion] = useState('');
  const [pollOptions, setPollOptions] = useState(['','']);
  const [allowMultiVote, setAllowMultiVote] = useState(false);
  const [pollExpirationDate, setPollExpirationDate] = useState('');
  const [pollExpirationTime, setPollExpirationTime] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showAttachmentMenu, setShowAttachmentMenu] = useState(false);
  const [activeEmojiTab, setActiveEmojiTab] = useState('Recent');
  const [recentEmojis, setRecentEmojis] = useState([]); // most recently used first
  const [focusedEmojiIndex, setFocusedEmojiIndex] = useState(0);
  const [perRow, setPerRow] = useState(10);
  const [emojiTabOffset, setEmojiTabOffset] = useState(0); // window start index for tabs
  const [searchEmoji, setSearchEmoji] = useState('');
  // Visibility state - now handled by VisibilitySelector
  const [visibility, setVisibility] = useState('public'); // public | followers | custom
  const [customFollowers, setCustomFollowers] = useState(''); // comma separated list
  const [showValidation, setShowValidation] = useState(false);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const emojiPickerRef = useRef(null);
  const attachmentMenuRef = useRef(null);
  const toolbarRef = useRef(null);

  // Provide custom readable names for common emojis; others fall back to category + index numbering
  const CUSTOM_EMOJI_NAMES = {
    '😀':'grinning face','😃':'smiling face','😄':'smiling face open eyes','😁':'beaming face','😆':'grinning squinting','😅':'grinning sweat','😂':'face tears of joy','🤣':'rolling on floor laughing','😊':'smiling blushing','🙂':'slightly smiling','😉':'winking face','😍':'smiling face hearts','🥰':'smiling face hearts','😘':'face blowing kiss','😗':'kissing face','😙':'kissing smiling eyes','😚':'kissing closed eyes','😋':'face savoring food','😜':'winking tongue','🤪':'zany face','😝':'squinting tongue','😛':'face with tongue','🤔':'thinking face','🤗':'hugging face','🤭':'face with hand over mouth','🤫':'shushing face','🤐':'zipper mouth','😐':'neutral face','😑':'expressionless','😶':'no mouth','🙄':'face with rolling eyes','😴':'sleeping face','🤤':'drooling face','😪':'sleepy face','🥱':'yawning face','😳':'flushed face','🥵':'hot face','🥶':'cold face','😱':'screaming in fear','😨':'fearful face','😰':'anxious sweat','😥':'sad but relieved','😢':'crying face','😭':'loudly crying','😤':'face with steam','😠':'angry face','😡':'pouting face','🤬':'cursing face','🤯':'exploding head','🥺':'pleading face','👍':'thumbs up','👎':'thumbs down','👊':'oncoming fist','✊':'raised fist','🤞':'crossed fingers','✌️':'victory hand','🤟':'love-you gesture','🤘':'sign of the horns','👌':'OK hand','🤌':'pinched fingers','🤏':'pinching hand','✋':'raised hand','🖐️':'hand with fingers splayed','🤚':'raised back of hand','🖖':'vulcan salute','👋':'waving hand','👏':'clapping hands','🙌':'raising hands','🤝':'handshake','🙏':'folded hands','❤️':'red heart','💔':'broken heart','💕':'two hearts','💞':'revolving hearts','💖':'sparkling heart','💘':'heart with arrow','💝':'heart with ribbon','💟':'heart decoration','✔️':'check mark','❌':'cross mark','✅':'check mark button','❎':'cross mark button','➕':'heavy plus','➖':'heavy minus','➗':'heavy division'
  };

  // Raw category emoji arrays
  const RAW_EMOJI_CATEGORIES = [
    { label: 'Smileys', list: '😀 😃 😄 😁 😆 😅 😂 🤣 😊 🙂 🙃 😉 😌 😍 🥰 😘 😗 😙 😚 😋 😜 🤪 😝 😛 🤑 🤗 🤭 🤫 🤔 🤐 🤨 😐 😑 😶 😏 😒 🙄 😬 🤥 😴 🤤 😪 😮‍💨 😌 😔 😪 😮 😯 😲 🥱 😳 🥵 🥶 😱 😨 😰 😥 😢 😭 😤 😠 😡 🤬 🤯 😳 🥺 😟 😦 😧 😮 😬 😑 😯 😲 ☹️ 🙁 😕' },
    { label: 'Gestures', list: '👍 👎 👊 ✊ 🤛 🤜 🤞 ✌️ 🤟 🤘 👌 🤌 🤏 🫰 ✋ 🖐️ 🤚 🖖 👋 🤙 👏 🙌 👐 🤲 🤝 🙏' },
    { label: 'People', list: '👶 👧 🧒 👦 👩 🧑 👨 👩‍🦱 👨‍🦱 👩‍🦰 👨‍🦰 👱‍♀️ 👱 👨‍🦳 👩‍🦳 👨‍🦲 👩‍🦲 🧔 🤴 👸 👳‍♂️ 👳‍♀️ 🧕 👮‍♂️ 👮‍♀️ 🕵️‍♂️ 🕵️‍♀️ 👩‍⚕️ 👨‍⚕️ 👩‍🎓 👨‍🎓 👩‍🏫 👨‍🏫 👩‍💻 👨‍💻 👩‍💼 👨‍💼 👩‍🔧 👨‍🔧 👩‍🔬 👨‍🔬 👩‍🎤 👨‍🎤 👩‍🚀 👨‍🚀 👩‍✈️ 👨‍✈️ 👩‍🚒 👨‍🚒 👩‍🌾 👨‍🌾' },
    { label: 'Animals', list: '🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐽 🐸 🐵 🙈 🙉 🙊 🐔 🐧 🐦 🐤 🐣 🐥 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🐝 🐛 🦋 🐌 🐞 🐜 🦂 🕷️ 🐢 🐍 🦎 🐙 🐚 🦑 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🐊' },
    { label: 'Food', list: '🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🌽 🥕 🧄 🧅 🥔 🍠 🥐 🥯 🍞 🧀 🍗 🍖 🥩 🥓 🍔 🍟 🍕 🌭 🥪 🌮 🌯 🫔 🥙 🧆 🍜 🍝 🍲 🍛 🍣 🍱 🥗' },
    { label: 'Activities', list: '⚽ 🏀 🏈 ⚾ 🎾 🏐 🏉 🎱 🥏 🏓 🏸 🥅 🥊 🥋 🥇 🥈 🥉 🏆 🎮 🕹️ 🎲 ♟️ 🧩 🎯 🎳 🎰' },
    { label: 'Travel', list: '🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🛵 🏍️ 🚲 🛴 ✈️ 🛫 🛬 🚀 🛸 🚁 🚂 🚆 🚇 🚊 🚉 ⛵ 🚤 🚢 ⚓ 🗺️ 🗽 🗼 🏰 🏯 🏟️ 🎡 🎢 🎠 ⛲ ⛱️ 🏖️ 🏝️ 🌋 🗻 🏔️ ⛰️' },
    { label: 'Objects', list: '⌚ 📱 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📞 ☎️ 📠 📺 📻 🎙️ 🎚️ 🎛️ ⏱️ ⏲️ ⏰ 🕰️ 🔋 🔌 💡 🔦 🕯️ 🧯 🛢️ 💸 💵 💴 💶 💷 💰 💳 🧾 💎 📜 📃 📄 📑 📊 📈 📉 🗂️ 📁 📂 🗃️ 🗄️ 🗑️' },
    { label: 'Symbols', list: '❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 ❤️‍🔥 ❤️‍🩹 💔 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 ☮️ ✝️ ☪️ 🕉️ ☸️ ✡️ 🔯 🕎 ☯️ ☦️ ☢️ ☣️ ♻️ ⚜️ 🔱 📛 🔰 ⭕ ✅ ☑️ ✔️ ❌ ❎ ➕ ➖ ➗ ➰ ➿ ✳️ ✴️ ❇️ ©️ ®️ ™️' }
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

  // Load recent emojis from localStorage once
  useEffect(()=>{
    try {
      const stored = JSON.parse(localStorage.getItem('composer_recent_emojis')||'[]');
      if (Array.isArray(stored)) setRecentEmojis(stored);
    } catch(_){}
  }, []);

  // Persist recent emojis when changed
  useEffect(()=>{
    try { localStorage.setItem('composer_recent_emojis', JSON.stringify(recentEmojis.slice(0,60))); } catch(_){}
  }, [recentEmojis]);

  const pushRecentEmoji = (emoji) => {
    setRecentEmojis(prev => {
      const filtered = prev.filter(e => e !== emoji);
      return [emoji, ...filtered].slice(0,60);
    });
  };

  const reset = () => {
    // Removed preview revocation to keep previews visible in feed after submit
    setText('');
    setAttachments([]);
    setShowPoll(false);
    setPollQuestion('');
    setPollOptions(['','']);
    setAllowMultiVote(false);
    setPollExpirationDate('');
    setPollExpirationTime('');
    setVisibility('public');
    setCustomFollowers('');
    setShowValidation(false);
  };

  const detectType = (file) => {
    if (ACCEPT_IMAGE.includes(file.type)) return 'image';
    if (ACCEPT_VIDEO.includes(file.type)) return 'video';
    if (ACCEPT_AUDIO.includes(file.type)) return 'audio';
    if (ACCEPT_PDF.includes(file.type)) return 'file'; // treat pdf as generic file
    return null; // unsupported generic file types now rejected
  };

  // Helper function to determine post type based on attachments
  const getPostType = () => {
    if (showPoll) return 'poll';
    if (attachments.length === 0) return 'text';
    if (attachments.length === 1) return attachments[0].type;

    // Check if all attachments are the same type
    const uniqueTypes = [...new Set(attachments.map(att => att.type))];
    return uniqueTypes.length > 1 ? 'mixed' : attachments[0].type;
  };

  // Helper function to check video/audio duration
  const checkMediaDuration = (file) => {
    return new Promise((resolve) => {
      const mediaElement = detectType(file) === 'video'
        ? document.createElement('video')
        : document.createElement('audio');

      const onLoadedMetadata = () => {
        const duration = mediaElement.duration;
        mediaElement.removeEventListener('loadedmetadata', onLoadedMetadata);
        URL.revokeObjectURL(mediaElement.src);
        resolve(duration);
      };

      const onError = () => {
        mediaElement.removeEventListener('error', onError);
        URL.revokeObjectURL(mediaElement.src);
        resolve(null); // Return null if duration can't be determined
      };

      mediaElement.addEventListener('loadedmetadata', onLoadedMetadata);
      mediaElement.addEventListener('error', onError);
      mediaElement.src = URL.createObjectURL(file);
    });
  };

  const addFiles = async (fileList) => {
    const fileArray = Array.from(fileList);
    const validItems = [];

    for (const f of fileArray) {
      const kind = detectType(f);
      if (!kind) continue; // skip unsupported

      // Check duration for video and audio files
      if (kind === 'video' || kind === 'audio') {
        try {
          const duration = await checkMediaDuration(f);
          if (duration && duration > 300) { // 5 minutes = 300 seconds
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            alert(`Les fichiers ${kind === 'video' ? 'vidéo' : 'audio'} doivent durer 5 minutes maximum. Durée actuelle : ${minutes}:${seconds.toString().padStart(2, '0')}`);
            continue; // Skip this file
          }
        } catch (error) {
          console.warn(`Could not validate ${kind} duration:`, error);
          // Continue with the file if we can't validate duration
        }
      }

      validItems.push({
        id: crypto.randomUUID(),
        file: f,
        type: kind,
        preview: (ACCEPT_IMAGE.includes(f.type) || ACCEPT_VIDEO.includes(f.type) || ACCEPT_AUDIO.includes(f.type) || ACCEPT_PDF.includes(f.type)) ? URL.createObjectURL(f) : null
      });
    }

    if (validItems.length > 0) {
      setAttachments(prev => [...prev, ...validItems]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files?.length) await addFiles(e.target.files);
    e.target.value = '';
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) await addFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e) => { e.preventDefault(); if (!isDragging) setIsDragging(true); };
  const handleDragLeave = (e) => { if (e.relatedTarget == null) setIsDragging(false); };

  const canSubmit = () => {
    if (isSubmitting) return false;
    if (text.trim()) return true;
    if (attachments.length) return true;
    if (showPoll && pollQuestion.trim() && pollOptions.filter(o => o.trim()).length >= 2) return true;
    return false;
  };

  const handleSubmit = async () => {
    if (!canSubmit()) return;

    // Validate custom visibility
    if (visibility === 'custom' && !customFollowers.trim()) {
      setShowValidation(true);
      alert('Veuillez spécifier des utilisateurs ou des communautés pour la visibilité personnalisée');
      return;
    }

    setIsSubmitting(true);
    setShowValidation(false);

    try {
      // Prepare data for unified API
      const postData = {
        content: text.trim(),
        visibility,
        post_type: getPostType(),
      };

      // Add custom visibility list if applicable
      if (visibility === 'custom') {
        postData.custom_visibility_list = customFollowers.split(',').map(v => v.trim()).filter(Boolean);
      }

      // Add attachments if present
      if (attachments.length > 0) {
        postData.attachments = attachments.map((attachment, index) => ({
          file: attachment.file,
          type: attachment.type,
          order: index + 1
        }));
      }

      // Add polls if present
      if (showPoll && pollQuestion.trim() && pollOptions.filter(o => o.trim()).length >= 2) {
        postData.polls = [{
          question: pollQuestion.trim(),
          allows_multiple_votes: allowMultiVote,
          expires_at: createExpirationDatetime(),
          options: pollOptions.filter(o => o.trim()).map((text, index) => ({
            text: text.trim(),
            order: index + 1
          }))
        }];
      }

      // Submit to server using unified API
      const response = await socialAPI.posts.create(postData);

      // Process mentions in the post content
      // Only pass community context if this post is actually being made within a community
      if (response.id && text.trim()) {
        const communityId = response.community || (community ? community.id : null);
        await socialAPI.utils.processContentMentions(text, response.id, null, communityId);
      }

      // Create local post object for immediate display (if onSubmit expects it)
      const localPost = {
        id: response.id || crypto.randomUUID(),
        content: text.trim(),
        author: response.author || { username: 'You' },
        created_at: response.created_at || new Date().toISOString(),
        attachments: response.attachments ? response.attachments.map(serverAtt => ({
          id: serverAtt.id,
          type: serverAtt.media_type, // Map media_type to type
          preview: serverAtt.file_url || serverAtt.file, // Use file_url or file for preview
          name: serverAtt.name || extractFileName(serverAtt.file_url || serverAtt.file), // Extract name from URL if not provided
          file_url: serverAtt.file_url || serverAtt.file,
          thumbnail_url: serverAtt.thumbnail_url,
          file_size: serverAtt.file_size
        })) : attachments.map(a => ({
          id: crypto.randomUUID(),
          name: a.file.name,
          size: a.file.size,
          type: a.type,
          preview: a.preview,
          file_url: a.preview
        })),
        polls: response.polls || (showPoll ? [{
          id: crypto.randomUUID(),
          question: pollQuestion.trim(),
          options: pollOptions.filter(o => o.trim()).map((t, i) => ({
            id: String(i + 1),
            text: t,
            votes_count: 0,
            vote_percentage: 0
          })),
          allows_multiple_votes: allowMultiVote,
          is_anonymous: false,
          voters_count: 0,
          total_votes: 0,
          user_voted: false,
          user_vote: [],
          is_expired: false,
          expires_at: createExpirationDatetime()
        }] : []),
        visibility,
        custom_visibility_list: visibility === 'custom' ? customFollowers.split(',').map(v => v.trim()).filter(Boolean) : [],
        likes_count: 0,
        dislikes_count: 0,
        comments_count: 0,
        shares_count: 0,
        is_liked: false,
        is_disliked: false,
        comments: []
      };



      // Call parent callback if provided
      if (onSubmit) {
        onSubmit(localPost);
      }

      // Reset form
      reset();

    } catch (err) {
      console.error('Failed to submit post:', err);
      // You might want to show an error message to the user here
      alert('Échec de la publication. Veuillez réessayer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const removeAttachment = (id) => {
    setAttachments(prev => prev.filter(a => {
      if (a.id === id && a.preview) URL.revokeObjectURL(a.preview);
      return a.id !== id;
    }));
  };

  const updatePollOption = (idx, value) => {
    setPollOptions(prev => prev.map((o,i) => i===idx ? value : o));
  };

  const addPollOption = () => setPollOptions(prev => [...prev, '']);
  const removePollOption = (idx) => setPollOptions(prev => prev.filter((_,i)=>i!==idx));

  // Create ISO datetime string from date and time inputs
  const createExpirationDatetime = () => {
    if (pollExpirationDate && pollExpirationTime) {
      try {
        const datetime = new Date(`${pollExpirationDate}T${pollExpirationTime}`);
        return datetime.toISOString();
      } catch (error) {
        console.warn('Invalid date/time format:', error);
        return null;
      }
    }

    // Default to 1 day from now if no expiration is set
    const defaultExpiration = new Date();
    defaultExpiration.setDate(defaultExpiration.getDate() + 1);
    return defaultExpiration.toISOString();
  };

  const insertEmoji = (emoji) => { // override existing
    setText(t => t + emoji);
    pushRecentEmoji(emoji.trim());
    inputRef.current?.focus();
  };

  // Recompute items per row after render when picker/tab changes
  useEffect(() => {
    if (!showEmojiPicker) return;
    const picker = emojiPickerRef.current;
    if (!picker) return;
    // Defer to ensure buttons rendered
    requestAnimationFrame(() => {
      const buttons = picker.querySelectorAll('[data-emoji-index]');
      if (!buttons.length) return;
      const top0 = buttons[0].offsetTop;
      let count = 0;
      for (let i = 0; i < buttons.length; i++) {
        if (buttons[i].offsetTop !== top0) break;
        count++;
      }
      if (count > 0) setPerRow(count);
      setFocusedEmojiIndex(0);
      // focus first button
      setTimeout(()=> {
        const first = picker.querySelector('[data-emoji-index="0"]');
        first && first.focus();
      }, 30);
    });
  }, [showEmojiPicker, activeEmojiTab]);

  // Build tabs list & current set (existing logic preserved)
  const EMOJI_TABS = ['Recent', ...EMOJI_CATEGORIES.map(c=>c.label)];

  const ensureTabVisible = (tab) => {
    const idx = EMOJI_TABS.indexOf(tab);
    if (idx === -1) return;
    if (idx < emojiTabOffset) setEmojiTabOffset(idx);
    else if (idx >= emojiTabOffset + 4) setEmojiTabOffset(Math.min(idx - 3, EMOJI_TABS.length - 4));
  };

  useEffect(()=>{ ensureTabVisible(activeEmojiTab); }, [activeEmojiTab]);

  // Handle outside clicks to close menus
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showEmojiPicker && emojiPickerRef.current && !emojiPickerRef.current.contains(event.target)) {
        setShowEmojiPicker(false);
      }
      if (showAttachmentMenu && attachmentMenuRef.current && !attachmentMenuRef.current.contains(event.target)) {
        setShowAttachmentMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showEmojiPicker, showAttachmentMenu]);

  const visibleTabs = EMOJI_TABS.slice(emojiTabOffset, emojiTabOffset + 4);
  const baseEmojiSet = activeEmojiTab === 'Recent'
    ? recentEmojis.map((ch,i)=> ({ char: ch, name: CUSTOM_EMOJI_NAMES[ch] || `recent ${i+1}` }))
    : (EMOJI_CATEGORIES.find(c=>c.label===activeEmojiTab)?.items || []);
  const lowerSearch = searchEmoji.trim().toLowerCase();
  const currentEmojiSet = baseEmojiSet.filter(e => !lowerSearch || e.char.includes(lowerSearch) || e.name.toLowerCase().includes(lowerSearch));

  const handleTabPrev = () => setEmojiTabOffset(o => Math.max(0, o - 1));
  const handleTabNext = () => setEmojiTabOffset(o => Math.min(EMOJI_TABS.length - 4, o + 1));

  const handleEmojiKeyDown = (e) => {
    if (!showEmojiPicker) return;
    const total = currentEmojiSet.length;
    const ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
      e.preventDefault();
      const tabs = EMOJI_TABS;
      let idx = tabs.indexOf(activeEmojiTab);
      if (e.key === 'ArrowRight') idx = (idx + 1) % tabs.length; else idx = (idx - 1 + tabs.length) % tabs.length;
      const nextTab = tabs[idx];
      setActiveEmojiTab(nextTab);
      // ensure window shows new tab
      setTimeout(()=> ensureTabVisible(nextTab),0);
      return;
    }
    if (!total) return;
    let next = focusedEmojiIndex;
    if (e.key === 'ArrowRight') { e.preventDefault(); next = Math.min(focusedEmojiIndex + 1, total - 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); next = Math.max(focusedEmojiIndex - 1, 0); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); next = Math.min(focusedEmojiIndex + perRow, total - 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); next = Math.max(focusedEmojiIndex - perRow, 0); }
    else if (e.key === 'Home') { e.preventDefault(); next = 0; }
    else if (e.key === 'End') { e.preventDefault(); next = total - 1; }
    else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); const emo = currentEmojiSet[focusedEmojiIndex]; if (emo) insertEmoji(emo.char + ' '); return; }
    else if (e.key === 'Escape') { e.preventDefault(); setShowEmojiPicker(false); return; }
    if (next !== focusedEmojiIndex) {
      setFocusedEmojiIndex(next);
      const btn = emojiPickerRef.current?.querySelector(`[data-emoji-index="${next}"]`);
      btn && btn.focus();
    }
  };

  const dragClasses = isDragging ? 'ring-2 ring-indigo-400 bg-indigo-50/70' : 'hover:bg-gray-50';

  return (
    <div
      className={`relative border border-gray-200 rounded-lg bg-white shadow-sm transition-colors ${dragClasses}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      {isDragging && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center pointer-events-none text-indigo-600 text-sm font-medium bg-white/70 backdrop-blur-sm">
          <PlusCircleIcon className="h-8 w-8 mb-1 animate-pulse" />
          Déposez les fichiers pour les joindre
        </div>
      )}
      <div className={`p-4 ${isDragging ? 'opacity-40' : ''}`}>
        {/* Text input with mention support */}
        <div className="relative">
          <textarea
            ref={mentionInputRef}
            rows={2}
            placeholder="Partagez une mise à jour, posez une question ou déposez des fichiers..."
            className="w-full resize-none border-0 focus:ring-0 focus:outline-none text-sm placeholder-gray-400"
            value={text}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            onClick={handleClick}
            onSelect={handleSelectionChange}
          />
          <MentionAutocomplete
            text={text}
            cursorPosition={cursorPosition}
            onMentionSelect={handleMentionSelect}
            communityId={community?.id}
            className="mt-2"
          />
        </div>

        {/* Attachments preview */}
        {attachments.length > 0 && (
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {attachments.map(a => (
              <div key={a.id} className="group relative rounded-md border border-gray-200 overflow-hidden bg-gray-50">
                {a.type === 'image' && a.preview && (
                  <img src={a.preview} alt={a.file.name} className="h-28 w-full object-cover" />
                )}
                {a.type === 'video' && a.preview && (
                  <video src={a.preview} className="h-28 w-full object-cover" muted playsInline />
                )}
                {a.type === 'audio' && (
                  <div className="h-28 flex items-center justify-center bg-gradient-to-br from-indigo-100 to-blue-50 text-indigo-600 text-xs font-medium px-2 text-center">
                    {a.file.name}
                  </div>
                )}
                {a.type === 'file' && (
                  <div className="h-28 flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-50 text-gray-700 text-xs font-medium px-2 text-center">
                    {a.file.name}
                  </div>
                )}
                <button
                  type="button"
                  onClick={()=>removeAttachment(a.id)}
                  className="absolute top-1 right-1 bg-white/80 hover:bg-white text-gray-600 hover:text-red-500 rounded-full p-0.5 shadow-sm transition-colors"
                  aria-label="Remove attachment"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Poll Editor */}
        {showPoll && (
          <div className="mt-4 border border-indigo-200 rounded-md p-3 bg-indigo-50/40">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-semibold text-indigo-700 tracking-wide">Sondage</p>
              <button type="button" onClick={()=>setShowPoll(false)} className="text-[11px] text-indigo-500 hover:text-indigo-700 font-medium">Retirer</button>
            </div>
            <input
              type="text"
              value={pollQuestion}
              onChange={e=>setPollQuestion(e.target.value)}
              placeholder="Question du sondage"
              className="w-full text-sm border-gray-300 rounded-md mb-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <div className="space-y-2">
              {pollOptions.map((opt,idx)=> (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={opt}
                    onChange={e=>updatePollOption(idx,e.target.value)}
                    placeholder={`Option ${idx+1}`}
                    className="flex-1 text-sm border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  {pollOptions.length > 2 && (
                    <button type="button" onClick={()=>removePollOption(idx)} className="p-1 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors">
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-3">
                <button type="button" onClick={addPollOption} className="text-[11px] font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                  <PlusCircleIcon className="h-4 w-4" /> Ajouter une option
                </button>
                <label className="inline-flex items-center gap-1 cursor-pointer select-none text-[11px] text-indigo-700">
                  <input type="checkbox" className="rounded border-indigo-300 text-indigo-600 focus:ring-indigo-500" checked={allowMultiVote} onChange={e=>setAllowMultiVote(e.target.checked)} />
                  Votes multiples
                </label>
              </div>
              <span className="text-[10px] text-indigo-500">{pollOptions.filter(o=>o.trim()).length} options</span>
            </div>

            {/* Poll Expiration Date & Time */}
            <div className="mt-3 border-t border-indigo-100 pt-3">
              <FlexibleTimePicker
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

        {/* Actions Bar */}
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t pt-3 border-gray-100" ref={toolbarRef}>
          {/* Visibility Selector - using reusable component */}
          <VisibilitySelector
            visibility={visibility}
            onVisibilityChange={(newVisibility) => {
              setVisibility(newVisibility);
              // Clear validation when changing visibility
              if (showValidation) setShowValidation(false);
            }}
            customFollowers={customFollowers}
            onCustomFollowersChange={(value) => {
              setCustomFollowers(value);
              // Clear validation when user starts typing
              if (showValidation && value.trim()) setShowValidation(false);
            }}
            showValidation={showValidation}
          />
          {/* Collapsed media group */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowAttachmentMenu(v => !v)}
              className="composer-btn relative"
              title="Add attachments"
            >
              <PaperClipIcon className="h-5 w-5 text-gray-600" />
              <span className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-indigo-500 text-[8px] flex items-center justify-center text-white font-semibold">+</span>
            </button>
            {showAttachmentMenu && (
              <div
                ref={attachmentMenuRef}
                className="absolute z-20 left-0 top-full mt-1 flex bg-white border border-gray-200 rounded-lg shadow-lg p-2 gap-1 animate-fade-in"
              >
                <button type="button" onClick={()=>{fileInputRef.current?.click(); setShowAttachmentMenu(false);}} className="composer-btn !h-9 !w-9" title="Files"><PaperClipIcon className="h-5 w-5 text-gray-500" /></button>
                <button type="button" onClick={()=>{fileInputRef.current?.click(); setShowAttachmentMenu(false);}} className="composer-btn !h-9 !w-9" title="Images"><PhotoIcon className="h-5 w-5 text-pink-500" /></button>
                <button type="button" onClick={()=>{fileInputRef.current?.click(); setShowAttachmentMenu(false);}} className="composer-btn !h-9 !w-9" title="Video"><VideoCameraIcon className="h-5 w-5 text-indigo-500" /></button>
                <button type="button" onClick={()=>{fileInputRef.current?.click(); setShowAttachmentMenu(false);}} className="composer-btn !h-9 !w-9" title="Audio"><MusicalNoteIcon className="h-5 w-5 text-purple-500" /></button>
                <button type="button" onClick={()=>{setShowPoll(p=>!p); setShowAttachmentMenu(false);}} className={`composer-btn !h-9 !w-9 ${showPoll ? 'bg-indigo-100 ring-1 ring-indigo-300' : ''}`} title="Poll"><ChartBarSquareIcon className="h-5 w-5 text-emerald-600" /></button>
              </div>
            )}
          </div>

          {/* Emoji Picker Trigger */}
          <div className="relative">
            <button type="button" onClick={()=>setShowEmojiPicker(v=>!v)} className={`composer-btn ${showEmojiPicker ? 'ring-2 ring-amber-300' : ''}`} title="Emoji picker">
              <FaceSmileIcon className="h-5 w-5 text-amber-500" />
            </button>
            {showEmojiPicker && (
              <div
                ref={emojiPickerRef}
                className="absolute z-30 left-0 top-full mt-2 w-80 max-h-[340px] bg-white border border-gray-200 rounded-xl shadow-xl p-0 text-sm animate-scale-in origin-top-left flex flex-col"
                role="dialog"
                aria-label="Emoji picker"
                onKeyDown={handleEmojiKeyDown}
              >
                {/* Search */}
                <div className="px-2 pt-2">
                  <input
                    type="text"
                    value={searchEmoji}
                    onChange={e=>{ setSearchEmoji(e.target.value); setFocusedEmojiIndex(0); }}
                    placeholder="Rechercher"
                    className="w-full rounded-md border border-gray-200 px-2 py-1 text-[11px] focus:ring-amber-400 focus:border-amber-400 placeholder-gray-400"
                  />
                </div>
                {/* Tabs with window navigation */}
                <div className="flex items-center gap-1 px-2 pt-2">
                  <button
                    type="button"
                    onClick={handleTabPrev}
                    disabled={emojiTabOffset===0}
                    className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset===0 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                    aria-label="Previous emoji categories"
                  >‹</button>
                  <div className="flex items-center gap-1 flex-1" role="tablist">
                    {visibleTabs.map(tab => (
                      <button
                        key={tab}
                        type="button"
                        role="tab"
                        aria-selected={activeEmojiTab===tab}
                        onClick={()=>{ setActiveEmojiTab(tab); ensureTabVisible(tab); }}
                        className={`flex-1 px-2 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-colors ${activeEmojiTab===tab ? 'bg-amber-200/70 text-amber-800 shadow-inner' : 'hover:bg-amber-50 text-gray-600'} truncate`}
                        title={tab}
                      >{tab}</button>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={handleTabNext}
                    disabled={emojiTabOffset >= EMOJI_TABS.length - 4}
                    className={`h-7 w-7 flex items-center justify-center rounded-md text-xs font-bold ${emojiTabOffset >= EMOJI_TABS.length - 4 ? 'text-gray-300' : 'text-gray-600 hover:bg-amber-50'}`}
                    aria-label="Next emoji categories"
                  >›</button>
                </div>
                <div className="mt-2 px-2 pb-2 overflow-y-auto" role="grid">
                  {activeEmojiTab !== 'Recent' && !searchEmoji && (
                    <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1 px-0.5">{activeEmojiTab}</p>
                  )}
                  {currentEmojiSet.length === 0 && (
                    <div className="text-[11px] text-gray-500 py-6 text-center" role="note">Aucun emoji trouvé.</div>
                  )}
                  <div className="flex flex-wrap gap-1" aria-label="Emoji grid">
                    {currentEmojiSet.map((e,i)=> e && (
                      <button
                        key={i}
                        type="button"
                        role="gridcell"
                        data-emoji-index={i}
                        tabIndex={i===focusedEmojiIndex ? 0 : -1}
                        aria-label={`${e.name}`}
                        title={e.name}
                        onClick={()=>{ setFocusedEmojiIndex(i); insertEmoji(e.char + ' '); }}
                        onFocus={()=> setFocusedEmojiIndex(i)}
                        className={`h-7 w-7 flex items-center justify-center rounded-md text-base hover:bg-amber-50 focus:outline-none focus:ring-2 focus:ring-amber-300 transition ${i===focusedEmojiIndex ? 'ring-1 ring-amber-300' : ''}`}
                      >{e.char}</button>
                    ))}
                  </div>
                  <p className="sr-only">Utilisez les flèches. Recherchez par nom. Survolez pour voir la description.</p>
                </div>
              </div>
            )}
          </div>

          <div className="ml-auto flex items-center gap-2">
            <button type="button" onClick={reset} disabled={!(text || attachments.length || showPoll)} className="text-[11px] font-medium text-gray-500 hover:text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed">Effacer</button>
            <button type="button" onClick={handleSubmit} disabled={!canSubmit()} className="px-4 py-1.5 rounded-md bg-indigo-600 text-white text-sm font-semibold shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">{isSubmitting ? 'Publication...' : 'Publier'}</button>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileChange}
          accept={[
            ...ACCEPT_IMAGE,
            ...ACCEPT_VIDEO,
            ...ACCEPT_AUDIO,
            ...ACCEPT_PDF,
            '.png','.jpg','.jpeg','.gif','.webp','.mp4','.webm','.mov','.wav','.mp3','.ogg','.pdf'
          ].join(',')}
        />
      </div>
      <style>{`
        /* existing styles */
        .composer-btn{display:inline-flex;align-items:center;justify-content:center;height:34px;width:34px;border-radius:8px;background:linear-gradient(135deg,#f8fafc,#f1f5f9);border:1px solid #e2e8f0;box-shadow:0 1px 2px rgba(0,0,0,.04);transition:.2s;}
        .composer-btn:hover{background:linear-gradient(135deg,#eef2ff,#e0e7ff);border-color:#c7d2fe;}
        .composer-btn:active{transform:translateY(1px);}
        @keyframes fadeIn{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}
        .animate-fade-in{animation:fadeIn .18s ease forwards;}
        @keyframes scaleIn{from{opacity:0;transform:scale(.95);}to{opacity:1;transform:scale(1);}}
        .animate-scale-in{animation:scaleIn .15s ease;}
        /* Thin scrollbar (webkit) */
        .scrollbar-thin::-webkit-scrollbar{height:4px;width:4px;}
        .scrollbar-thin::-webkit-scrollbar-track{background:transparent;}
        .scrollbar-thin::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:2px;}
      `}</style>
    </div>
  );
};

export default PostComposer;
