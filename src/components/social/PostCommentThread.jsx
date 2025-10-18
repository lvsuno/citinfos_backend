import React, { useState, useRef } from 'react';
import PostContentRenderer from './PostContentRenderer';
import { HandThumbUpIcon as HandThumbUpSolid } from '@heroicons/react/24/solid';
import { HandThumbUpIcon as HandThumbUpOutline } from '@heroicons/react/24/outline';
import ReactionPicker, { getReactionEmoji } from './ReactionPicker';
import MentionAutocomplete from '../ui/MentionAutocomplete';
import ClickableAuthorName from '../ui/ClickableAuthorName';
import TinyBadgeList from '../TinyBadgeList';
import { useMentionInput } from '../../hooks/useMentionInput';
import { formatTimeAgo } from '../../utils/timeUtils';

/*
  PostCommentThread
  Simplified reusable comment thread with reply + emoji reactions for comments.

  Like button behavior:
  - Click: Shows quick reaction bar (5 reactions + "more" button)
  - Selected reaction shows as emoji instead of thumbs up

  Props:
    postId
    comments: [{ id, author:{username}, content, created_at, parent, user_reaction, likes_count, dislikes_count, is_edited }]
    onAddComment(postId, parentId, text)
    onToggleCommentReaction(postId, commentId, reactionType)
    onDeleteComment(postId, commentId)
    onEditComment(postId, commentId, newText)
*/

const buildThread = (comments=[]) => {
  // Check if comments are already nested (have replies property)
  if (comments.length > 0 && comments[0].hasOwnProperty('replies')) {
    // Comments are already nested, return as-is
    return comments.sort((a,b)=>new Date(a.created_at) - new Date(b.created_at));
  }

  // Legacy flat structure - build nested structure
  const byParent = {};
  comments.forEach(c => { const p = c.parent || 'root'; (byParent[p] = byParent[p] || []).push(c); });
  return (byParent['root']||[]).map(top => ({
    ...top,
    replies: (byParent[top.id]||[]).sort((a,b)=>new Date(a.created_at) - new Date(b.created_at))
  })).sort((a,b)=>new Date(a.created_at) - new Date(b.created_at));
};

export const PostCommentThread = ({ postId, comments, onAddComment, onToggleCommentReaction, onDeleteComment, onEditComment }) => {
  const [replyTarget, setReplyTarget] = useState(null); // commentId
  const [editing, setEditing] = useState(null); // commentId
  const [editValue, setEditValue] = useState('');
  const [showReactionPicker, setShowReactionPicker] = useState(null); // commentId
  const [pickerMode, setPickerMode] = useState('quick'); // 'quick' or 'full'
  const [reactionPickerPosition, setReactionPickerPosition] = useState({ top: 0, left: 0 });
  const reactionButtonRefs = useRef({});

  // Main comment input mention functionality
  const mainCommentMention = useMentionInput('');

  // Reply inputs - we'll use a simple Map approach
  const [replyTexts, setReplyTexts] = useState({});
  const [replyCursors, setReplyCursors] = useState({});
  const replyRefs = useRef({});

  const thread = buildThread(comments);
  const getKey = (parentId) => parentId ? `${postId}:${parentId}` : postId;

  // Helper functions for reply inputs
  const updateReplyText = (commentId, value) => {
    setReplyTexts(prev => ({ ...prev, [commentId]: value }));
    // Update cursor position
    setTimeout(() => {
      const ref = replyRefs.current[commentId];
      if (ref) {
        setReplyCursors(prev => ({ ...prev, [commentId]: ref.selectionStart }));
      }
    }, 0);
  };

  const handleReplyMentionSelect = (commentId, mentionData) => {
    const currentText = replyTexts[commentId] || '';
    const { startPos, endPos, replacement } = mentionData;
    const newText = currentText.slice(0, startPos) + replacement + currentText.slice(endPos);
    setReplyTexts(prev => ({ ...prev, [commentId]: newText }));

    // Set cursor position after the mention
    const newCursorPos = startPos + replacement.length;
    setTimeout(() => {
      const ref = replyRefs.current[commentId];
      if (ref) {
        ref.focus();
        ref.setSelectionRange(newCursorPos, newCursorPos);
        setReplyCursors(prev => ({ ...prev, [commentId]: newCursorPos }));
      }
    }, 0);
  };

  // Handle opening reaction picker for a comment (quick mode first)
  const handleReactionClick = (commentId, event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setReactionPickerPosition({
      top: rect.top - 60 + window.scrollY, // Show above the button
      left: rect.left + window.scrollX
    });
    setPickerMode('quick');
    setShowReactionPicker(commentId);
  };

  // Handle "more" button click (switch to full grid)
  const handleShowMore = () => {
    setPickerMode('full');
  };

  // Handle reaction selection for a comment
  const handleReactionSelect = (commentId, reactionType) => {
    onToggleCommentReaction(postId, commentId, reactionType);
  };

  const submit = (parentId=null) => {
    if (parentId) {
      // For replies
      const replyText = replyTexts[parentId] || '';
      if (!replyText.trim()) return;
      onAddComment(postId, parentId, replyText);
      setReplyTexts(prev => ({ ...prev, [parentId]: '' }));
      setReplyCursors(prev => ({ ...prev, [parentId]: null }));
      setReplyTarget(null);
    } else {
      // For main comment
      if (!mainCommentMention.text.trim()) return;
      onAddComment(postId, null, mainCommentMention.text);
      mainCommentMention.setText('');
    }
  };

  const beginEdit = (c) => { setEditing(c.id); setEditValue(c.content); };
  const saveEdit = (c) => { const v = editValue.trim(); if(!v) return; onEditComment(postId, c.id, v); setEditing(null); setEditValue(''); };
  const cancelEdit = () => { setEditing(null); setEditValue(''); };

  return (
    <>
      <div className="space-y-3 pt-2 border-t border-gray-100">
      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
        {thread.map(c => (
          <div key={c.id} className="space-y-1">
            <div className="flex items-start gap-2 text-xs bg-gray-50 rounded-md p-2">
              <div className="flex flex-col">
                <ClickableAuthorName
                  author={c.author}
                  authorUsername={c.author_username}
                  className="font-semibold text-gray-700 hover:text-blue-600 transition-colors"
                />
                {c.author && (
                  <TinyBadgeList userId={c.author.id || c.author} maxVisible={2} />
                )}
              </div>
              <span className="text-gray-600 break-words flex-1">
                {editing === c.id ? (
                  <input
                    className="w-full border px-2 py-1 rounded"
                    value={editValue}
                    onChange={e=>setEditValue(e.target.value)}
                    onKeyDown={e=>{ if(e.key==='Enter'){ saveEdit(c);} if(e.key==='Escape'){ cancelEdit(); } }}
                    autoFocus
                  />
                ) : (
                  <><PostContentRenderer text={c.content} mentions={c?.mentions || {}} /> {c.is_edited && <span className="text-[10px] text-gray-400 ml-1">(edited)</span>}</>
                )}
              </span>
              <span className="text-[10px] text-gray-400 whitespace-nowrap">{formatTimeAgo(c.created_at)}</span>
            </div>
            <div className="flex items-center gap-3 pl-12 -mt-1 mb-1">
              {editing !== c.id && (
                <button onClick={()=>beginEdit(c)} className="text-[10px] text-gray-500 hover:text-blue-600">Edit</button>
              )}
              {editing !== c.id && (
                <button onClick={()=>onDeleteComment(postId,c.id)} className="text-[10px] text-gray-500 hover:text-red-600">Delete</button>
              )}
              {editing === c.id && (
                <>
                  <button onClick={()=>saveEdit(c)} className="text-[10px] text-blue-600">Save</button>
                  <button onClick={cancelEdit} className="text-[10px] text-gray-500">Cancel</button>
                </>
              )}
              {editing !== c.id && (
                <button onClick={()=>setReplyTarget(c.id)} className="text-[10px] text-gray-500 hover:text-blue-600">Reply</button>
              )}
              <div className="flex items-center gap-3 text-[10px] ml-2">
                <button
                  ref={(el) => { reactionButtonRefs.current[c.id] = el; }}
                  onClick={(e)=>handleReactionClick(c.id, e)}
                  className="flex items-center gap-1 hover:text-blue-600"
                >
                  {c.user_reaction ? (
                    c.user_reaction === 'like' ? (
                      <HandThumbUpSolid className="h-4 w-4 text-blue-600" />
                    ) : (
                      <span className="text-base leading-none">{getReactionEmoji(c.user_reaction)}</span>
                    )
                  ) : (
                    <HandThumbUpOutline className="h-4 w-4" />
                  )}
                  <span className={c.user_reaction ? 'text-blue-600':'text-gray-500'}>{c.likes_count||0}</span>
                </button>
              </div>
            </div>
            {/* Replies */}
            {c.replies.map(r => (
              <div key={r.id} className="ml-6 flex items-start gap-2 text-[11px] bg-gray-50 rounded-md p-2 border-l border-gray-200">
                <div className="flex flex-col">
                  <ClickableAuthorName
                    author={r.author}
                    authorUsername={r.author_username}
                    className="font-semibold text-gray-700 hover:text-blue-600 transition-colors text-[11px]"
                  />
                  {r.author && (
                    <TinyBadgeList userId={r.author.id || r.author} maxVisible={2} />
                  )}
                </div>
                <span className="text-gray-600 break-words flex-1">
                  {editing === r.id ? (
                    <input
                      className="w-full border px-2 py-1 rounded"
                      value={editValue}
                      onChange={e=>setEditValue(e.target.value)}
                      onKeyDown={e=>{ if(e.key==='Enter'){ saveEdit(r);} if(e.key==='Escape'){ cancelEdit(); } }}
                      autoFocus
                    />
                  ) : (
                    <><PostContentRenderer text={r.content} mentions={r?.mentions || {}} /> {r.is_edited && <span className="text-[9px] text-gray-400 ml-1">(edited)</span>}</>
                  )}
                </span>
                <span className="text-[9px] text-gray-400 whitespace-nowrap">{formatTimeAgo(r.created_at)}</span>
                <div className="flex items-center gap-3 ml-2">
                  {editing !== r.id && (
                    <button onClick={()=>beginEdit(r)} className="text-[9px] text-gray-500 hover:text-blue-600">Edit</button>) }
                  {editing !== r.id && (
                    <button onClick={()=>onDeleteComment(postId,r.id)} className="text-[9px] text-gray-500 hover:text-red-600">Delete</button>) }
                  {editing === r.id && (<>
                    <button onClick={()=>saveEdit(r)} className="text-[9px] text-blue-600">Save</button>
                    <button onClick={cancelEdit} className="text-[9px] text-gray-500">Cancel</button>
                  </>)}
                  {editing !== r.id && (
                    <button onClick={()=>setReplyTarget(r.id)} className="text-[9px] text-gray-500 hover:text-blue-600">Reply</button>
                  )}
                  <div className="flex items-center gap-2 text-[9px] ml-1">
                    <button
                      ref={(el) => { reactionButtonRefs.current[r.id] = el; }}
                      onClick={(e)=>handleReactionClick(r.id, e)}
                      className="flex items-center gap-1 hover:text-blue-600"
                    >
                      {r.user_reaction ? (
                        r.user_reaction === 'like' ? (
                          <HandThumbUpSolid className="h-3 w-3 text-blue-600" />
                        ) : (
                          <span className="text-sm leading-none">{getReactionEmoji(r.user_reaction)}</span>
                        )
                      ) : (
                        <HandThumbUpOutline className="h-3 w-3" />
                      )}
                      <span className={r.user_reaction ? 'text-blue-600':'text-gray-500'}>{r.likes_count||0}</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
            {/* Reply input */}
            {replyTarget === c.id && (
              <div className="ml-6 mt-1 relative">
                <div className="flex items-center gap-2">
                  <input
                    ref={(el) => { replyRefs.current[c.id] = el; }}
                    className="flex-1 px-2 py-1 border border-gray-300 rounded-md text-[11px] focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder={`Reply to @${c.author_username||'user'}`}
                    value={replyTexts[c.id] || ''}
                    onChange={(e) => updateReplyText(c.id, e.target.value)}
                    onKeyDown={(e) => {
                      if(e.key==='Enter' && !e.shiftKey){
                        e.preventDefault();
                        submit(c.id);
                      }
                      if(e.key==='Escape'){
                        setReplyTarget(null);
                      }
                    }}
                    onClick={() => {
                      setTimeout(() => {
                        const ref = replyRefs.current[c.id];
                        if (ref) {
                          setReplyCursors(prev => ({ ...prev, [c.id]: ref.selectionStart }));
                        }
                      }, 0);
                    }}
                    autoFocus
                  />
                  <button
                    onClick={()=>submit(c.id)}
                    disabled={!(replyTexts[c.id] || '').trim()}
                    className={`px-2 py-1 rounded-md text-[10px] text-white ${(replyTexts[c.id] || '').trim()? 'bg-blue-600 hover:bg-blue-700':'bg-gray-400 cursor-not-allowed'}`}
                  >Reply</button>
                  <button onClick={()=>setReplyTarget(null)} className="text-[10px] text-gray-500">Cancel</button>
                </div>
                <MentionAutocomplete
                  text={replyTexts[c.id] || ''}
                  cursorPosition={replyCursors[c.id]}
                  postId={postId}
                  onMentionSelect={(mentionData) => handleReplyMentionSelect(c.id, mentionData)}
                  className="absolute z-10 mt-1 w-64"
                />
              </div>
            )}
          </div>
        ))}
        {thread.length === 0 && (
          <p className="text-[11px] text-gray-400">No comments yet.</p>
        )}
      </div>
      <div className="relative">
        <div className="flex items-center gap-2">
          <input
            ref={mainCommentMention.textareaRef}
            value={mainCommentMention.text}
            onChange={mainCommentMention.handleChange}
            onKeyDown={(e) => {
              mainCommentMention.handleKeyDown(e);
              if(e.key==='Enter' && !e.shiftKey){
                e.preventDefault();
                submit();
              }
            }}
            onClick={mainCommentMention.handleClick}
            placeholder="Write a comment... Use @username or #hashtag"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
          <button
            onClick={()=>submit()}
            disabled={!mainCommentMention.text.trim()}
            className={`px-3 py-2 rounded-md text-xs font-medium text-white ${mainCommentMention.text.trim() ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}`}
          >Comment</button>
        </div>
        <MentionAutocomplete
          text={mainCommentMention.text}
          cursorPosition={mainCommentMention.cursorPosition}
          postId={postId}
          onMentionSelect={mainCommentMention.handleMentionSelect}
          className="absolute z-10 mt-1 w-64"
        />
      </div>
      <p className="text-[11px] text-gray-500">Use @username to mention someone or #hashtag for topics.</p>
    </div>

    {/* Reaction Picker for Comments */}
    {showReactionPicker && (
      <ReactionPicker
        mode={pickerMode}
        onShowMore={handleShowMore}
        onReact={(reactionType) => handleReactionSelect(showReactionPicker, reactionType)}
        onClose={() => setShowReactionPicker(null)}
        currentReaction={
          thread.flatMap(c => [c, ...(c.replies || [])])
            .find(c => c.id === showReactionPicker)?.user_reaction || null
        }
        position={reactionPickerPosition}
      />
    )}
  </>
  );
};
export default PostCommentThread;
