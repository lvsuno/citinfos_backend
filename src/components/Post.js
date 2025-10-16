import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getTotalReactions, getTopReactionIcons, formatTimeAgo } from '../data/sherbrookePosts';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import ShareIcon from '@mui/icons-material/Share';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import SendIcon from '@mui/icons-material/Send';
import PostHeader from './PostHeader';
import PostContent from './PostContent';
import PostAttachments from './PostAttachments';
import ReactionsPanel from './ReactionsPanel';
import styles from './Post.module.css';

const Post = ({ post }) => {
  const { user } = useAuth();
  const [showComments, setShowComments] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);
  const [showReactionsPanel, setShowReactionsPanel] = useState(false);
  const [userReaction, setUserReaction] = useState(post.userReaction);
  const [reactions, setReactions] = useState(post.reactions || {
    like: 0,
    love: 0,
    haha: 0,
    wow: 0,
    sad: 0,
    angry: 0
  });
  const [comments, setComments] = useState(post.comments || []);

  const reactionEmojis = {
    like: '👍',
    love: '❤️',
    haha: '😂',
    wow: '😮',
    sad: '😢',
    angry: '😠'
  };

  const handleReactionSelect = (reactionType) => {
    // Vérifier si l'utilisateur est connecté
    if (!user) {
      return; // Les utilisateurs non connectés ne peuvent pas réagir
    }

    const newReactions = { ...reactions };

    // Si l'utilisateur avait déjà une réaction, la retirer
    if (userReaction) {
      newReactions[userReaction] = Math.max(0, newReactions[userReaction] - 1);
    }

    // Si c'est une nouvelle réaction différente, l'ajouter
    if (reactionType !== userReaction) {
      newReactions[reactionType] = (newReactions[reactionType] || 0) + 1;
      setUserReaction(reactionType);
    } else {
      setUserReaction(null);
    }

    setReactions(newReactions);
    setShowReactionsPanel(false);
  };

  const handleLikeClick = () => {
    // Vérifier si l'utilisateur est connecté
    if (!user) {
      return; // Les utilisateurs non connectés ne peuvent pas réagir
    }

    if (userReaction === 'like') {
      handleReactionSelect('like'); // Retire la réaction
    } else {
      handleReactionSelect('like'); // Ajoute like
    }
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || isSubmittingComment || !user) return;

    setIsSubmittingComment(true);

    const comment = {
      id: `comment-${Date.now()}`,
      author: {
        id: user.id,
        name: user.name,
        avatar: user.avatar,
        initials: user.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'
      },
      content: newComment.trim(),
      timestamp: new Date(),
      reactions: { like: 0 }
    };

    setComments(prev => [...prev, comment]);
    setNewComment('');
    setIsSubmittingComment(false);
  };

  const totalReactions = getTotalReactions(reactions);
  const topReactionIcons = getTopReactionIcons(reactions);

  return (
    <article className={styles.post}>
      <PostHeader
        author={post.author}
        timestamp={post.timestamp}
        section={post.section}
      />

      <PostContent content={post.content} />

      <PostAttachments attachments={post.attachments} />

      {totalReactions > 0 && (
        <div className={styles.postStats}>
          <div className={styles.reactionsCount}>
            <div className={styles.reactionIcons}>
              {topReactionIcons.map((emoji, index) => (
                <span key={index} className={styles.reactionEmoji}>{emoji}</span>
              ))}
            </div>
            <span className={styles.reactionsNumber}>{totalReactions}</span>
          </div>
          <button
            className={styles.statsButton}
            onClick={() => setShowComments(!showComments)}
          >
            {comments.length} commentaire{comments.length !== 1 ? 's' : ''}
          </button>
        </div>
      )}

      <div className={styles.postActions}>
        <div
          className={styles.reactionWrapper}
          onMouseEnter={() => user && setShowReactionsPanel(true)}
          onMouseLeave={() => user && setShowReactionsPanel(false)}
        >
          <button
            className={`${styles.actionButton} ${userReaction ? styles.reacted : ''} ${!user ? styles.disabled : ''}`}
            onClick={handleLikeClick}
            disabled={!user}
            title={!user ? "Connectez-vous pour réagir" : "J'aime"}
          >
            {userReaction ? (
              <span className={styles.userReactionEmoji}>
                {reactionEmojis[userReaction]}
              </span>
            ) : (
              <ThumbUpIcon />
            )}
            <span>J'aime</span>
          </button>

          {user && (
            <ReactionsPanel
              isVisible={showReactionsPanel}
              onReactionSelect={handleReactionSelect}
              onClose={() => setShowReactionsPanel(false)}
              currentReaction={userReaction}
            />
          )}
        </div>

        <button
          className={`${styles.actionButton} ${showComments ? styles.active : ''}`}
          onClick={() => setShowComments(!showComments)}
        >
          <ChatBubbleOutlineIcon />
          <span>Commenter</span>
        </button>

        <button
          className={`${styles.actionButton} ${!user ? styles.disabled : ''}`}
          disabled={!user}
          title={!user ? "Connectez-vous pour partager" : "Partager"}
        >
          <ShareIcon />
          <span>Partager</span>
        </button>
      </div>

      {showComments && (
        <div className={styles.commentsSection}>
          {comments.length > 0 && (
            <div className={styles.commentsList}>
              {comments.map((comment) => (
                <div key={comment.id} className={styles.comment}>
                  <div className={styles.commentAvatar}>
                    {comment.author.avatar ? (
                      <img src={comment.author.avatar} alt={comment.author.name} />
                    ) : (
                      comment.author.initials
                    )}
                  </div>
                  <div className={styles.commentContent}>
                    <div className={styles.commentBubble}>
                      <h4 className={styles.commentAuthor}>{comment.author.name}</h4>
                      <p className={styles.commentText}>{comment.content}</p>
                    </div>
                    <div className={styles.commentActions}>
                      <span className={styles.commentTime}>
                        {formatTimeAgo(comment.timestamp)}
                      </span>
                      <button className={styles.commentAction}>J'aime</button>
                      <button className={styles.commentAction}>Répondre</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {user && (
            <form className={styles.commentForm} onSubmit={handleCommentSubmit}>
              <div className={styles.commentInputWrapper}>
                <div className={styles.commentAvatar}>
                  {user.avatar ? (
                    <img src={user.avatar} alt={user.name} />
                  ) : (
                    user.name?.split(' ').map(n => n[0]).join('').toUpperCase() || 'U'
                  )}
                </div>
                <div className={styles.commentInputContainer}>
                  <textarea
                    className={styles.commentInput}
                    placeholder="Écrivez un commentaire..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    disabled={isSubmittingComment}
                    rows="1"
                  />
                  <div className={styles.commentFormActions}>
                    <button
                      type="button"
                      className={styles.attachmentButton}
                      aria-label="Ajouter une pièce jointe"
                    >
                      <AttachFileIcon />
                    </button>
                    <button
                      type="submit"
                      className={styles.submitComment}
                      disabled={!newComment.trim() || isSubmittingComment}
                      aria-label="Publier le commentaire"
                    >
                      {isSubmittingComment ? (
                        <div className={styles.spinner} />
                      ) : (
                        <SendIcon />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          )}

          {/* Message pour les utilisateurs non connectés */}
          {!user && (
            <div className={styles.publicUserMessage}>
              <p className={styles.publicUserText}>
                <strong>Mode public :</strong> Connectez-vous pour réagir et commenter sur les publications.
              </p>
            </div>
          )}
        </div>
      )}
    </article>
  );
};

export default Post;