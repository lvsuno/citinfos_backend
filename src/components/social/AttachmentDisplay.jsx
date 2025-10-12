import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';

/* AttachmentDisplay
   Unified attachment renderer with CAROUSEL view for multi-attachments.
   Props:
     attachments: [{ id, type: image|video|audio|file, preview, name }]
     expanded (bool)
     onToggle(att) -> toggle expand for gallery items (used e.g. for expand/collapse outside)
     onOpenPdf(att) -> open pdf modal (only for file/pdf)
     readonly (bool) -> disable interactions when true (for read-only displays like embedded posts)
*/

const AttachmentDisplay = ({ attachments = [], expanded=false, onToggle=()=>{}, onOpenPdf=()=>{}, readonly=false }) => {
  const [preview, setPreview] = useState(null); // attachment being previewed (image|video|audio|file non-pdf)
  const [previewIndex, setPreviewIndex] = useState(null); // index in attachments for navigation
  const [touchStartX, setTouchStartX] = useState(null);
  const [touchDeltaX, setTouchDeltaX] = useState(0);
  const [animating, setAnimating] = useState(false); // momentum animation active
  const [animOffset, setAnimOffset] = useState(0);   // current animated translateX when animating

  // Carousel-specific state - simplified
  const [carouselIndex, setCarouselIndex] = useState(0);

  // Video control states
  const [videoStates, setVideoStates] = useState({}); // Track mute state and audio availability per video
  const videoRefs = useRef({}); // Store video element references

  // Helper function to normalize attachment data structure (memoized)
  const normalizeAttachment = useMemo(() => {
    return (att) => {
      if (!att) return null;
      return {
        id: att.id,
        // Handle both 'type' and 'media_type' fields
        type: att.type || att.media_type || 'file',
        // Handle both 'preview' and 'file_url' fields, fallback to thumbnail_url
        preview: att.preview || att.file_url || att.thumbnail_url || null,
        // Handle name field
        name: att.name || (att.file_url ? att.file_url.split('/').pop() : 'Unknown file'),
        // Pass through other properties
        file_url: att.file_url || att.preview,
        thumbnail_url: att.thumbnail_url,
        file_size: att.file_size || att.size
      };
    };
  }, []);

  // Normalize all attachments with useMemo to prevent recreating on every render
  const normalizedAttachments = useMemo(() => {
    return attachments.map(normalizeAttachment).filter(Boolean);
  }, [attachments]);

  // Cleanup effect for video refs and states
  useEffect(() => {
    return () => {
      // Clean up video refs when component unmounts
      videoRefs.current = {};
    };
  }, []);

  // Reset video states when attachments change (with stable dependency)
  useEffect(() => {
    // Clean up old video states that are no longer needed
    const currentIds = new Set();
    normalizedAttachments.forEach(att => {
      if (att.type === 'video') {
        currentIds.add(att.id);
        currentIds.add(`${att.id}_expanded`);
      }
    });

    setVideoStates(prev => {
      const currentKeys = Object.keys(prev);
      const newState = {};
      let hasChanges = false;

      currentKeys.forEach(id => {
        const baseId = id.replace('_expanded', '');
        if (currentIds.has(id) || currentIds.has(baseId)) {
          newState[id] = prev[id];
        } else {
          hasChanges = true;
          // Also clean up the corresponding video ref
          delete videoRefs.current[id];
        }
      });

      // Only update if there are actual changes
      return hasChanges ? newState : prev;
    });
  }, [normalizedAttachments]);  // Helper to check if attachment is a PDF (non-previewable inside this modal)
  const isPdfFile = (att) => att && att.type === 'file' && (att.name||'').toLowerCase().endsWith('.pdf');

  // Determine if an attachment can be previewed in modal
  const isPreviewable = (att) => att && !(att.type === 'file' && isPdfFile(att));

  // Open preview for given attachment (skip PDFs -> delegate)
  const openPreview = (att) => {
    if(!att) return;
    if(att.type === 'file') {
      const isPdf = (att.name||'').toLowerCase().endsWith('.pdf');
      if(isPdf) { onOpenPdf(att); return; }
    }
    const idx = normalizedAttachments.findIndex(a => a.id === att.id);
    setPreviewIndex(idx >=0 ? idx : null);
    setPreview(att);
  };

  const closePreview = () => { setPreview(null); setPreviewIndex(null); setTouchStartX(null); setTouchDeltaX(0); };

  // Navigate to next / previous previewable attachment (NO looping)
  const findNextIndex = (start, dir) => {
    if(start == null) return null;
    let i = start + dir;
    while(i >= 0 && i < normalizedAttachments.length) {
      if(isPreviewable(normalizedAttachments[i])) return i;
      i += dir;
    }
    return start; // no move available
  };

  const animateToIndex = (targetIndex, dir) => {
    if(targetIndex == null || targetIndex === previewIndex || animating) return;
    setAnimating(true);
    // slide current out slightly faster using eased curve
    const exitDistance = 220; // px
    setAnimOffset(dir === 1 ? -exitDistance : exitDistance);
    const exitDuration = 140; // ms
    setTimeout(()=>{
      // switch content
      setPreviewIndex(targetIndex);
      // place off-screen opposite side for entrance
      setAnimOffset(dir === 1 ? exitDistance : -exitDistance);
      requestAnimationFrame(()=>{
        // allow frame then animate to 0
        setAnimOffset(0);
        // total enter duration slightly longer for pleasant ease
        const enterDuration = 260; // ms
        setTimeout(()=> setAnimating(false), enterDuration + 10);
      });
    }, exitDuration);
  };
  const goNext = () => {
    setPreviewIndex(curr => {
      if(curr==null) return curr;
      const ni = findNextIndex(curr, +1);
      if(ni !== curr) animateToIndex(ni, 1);
      return curr; // index change handled in animation
    });
  };
  const goPrev = () => {
    setPreviewIndex(curr => {
      if(curr==null) return curr;
      const pi = findNextIndex(curr, -1);
      if(pi !== curr) animateToIndex(pi, -1);
      return curr;
    });
  };

  // Sync preview object when index changes
  useEffect(()=>{
    if(previewIndex!=null) {
      const att = normalizedAttachments[previewIndex];
      if(att) setPreview(att); else closePreview();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [previewIndex, normalizedAttachments]);

  // Keyboard listeners: Escape (close), ArrowLeft/Right (navigate)
  useEffect(()=>{
    const onKey = (e)=>{
      if(!preview) return;
      if(e.key==='Escape') closePreview();
      else if(e.key==='ArrowRight') goNext();
      else if(e.key==='ArrowLeft') goPrev();
    };
    if(preview){ window.addEventListener('keydown', onKey);}
    return ()=>window.removeEventListener('keydown', onKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  },[preview]);

  // Touch swipe handlers for modal (with momentum)
  const onTouchStart = (e) => { if(!preview || animating) return; setTouchStartX(e.touches[0].clientX); setTouchDeltaX(0); };
  const onTouchMove = (e) => { if(touchStartX==null || animating) return; setTouchDeltaX(e.touches[0].clientX - touchStartX); };
  const onTouchEnd = () => {
    if(touchStartX==null || animating) return;
    const threshold = 60;
    const delta = touchDeltaX;
    const curr = previewIndex;
    const canNext = curr!=null && findNextIndex(curr, +1)!==curr;
    const canPrev = curr!=null && findNextIndex(curr, -1)!==curr;
    if(delta < -threshold && canNext) { // swipe left -> next
      // momentum animate left
      setAnimating(true);
      setAnimOffset(delta - 540); // continue left
      setTimeout(()=>{ setAnimating(false); setTouchDeltaX(0); setTouchStartX(null); goNext(); }, 160);
    } else if(delta > threshold && canPrev) { // swipe right -> prev
      setAnimating(true);
      setAnimOffset(delta + 540);
      setTimeout(()=>{ setAnimating(false); setTouchDeltaX(0); setTouchStartX(null); goPrev(); }, 160);
    } else {
      // snap back
      setAnimating(true);
      setAnimOffset(0);
      setTimeout(()=>{ setAnimating(false); setTouchDeltaX(0); setTouchStartX(null); }, 160);
    }
  };

  // Count previewable attachments for showing nav controls
  const previewableCount = normalizedAttachments.filter(a=>isPreviewable(a)).length;

  // Carousel navigation functions - simplified and memoized
  const goToCarouselIndex = useCallback((index) => {
    if (index >= 0 && index < normalizedAttachments.length) {
      setCarouselIndex(index);
    }
  }, [normalizedAttachments.length]);

  const nextCarouselItem = useCallback(() => {
    setCarouselIndex(prev => Math.min(prev + 1, normalizedAttachments.length - 1));
  }, [normalizedAttachments.length]);

  const prevCarouselItem = useCallback(() => {
    setCarouselIndex(prev => Math.max(prev - 1, 0));
  }, []);

  // Video control functions
  const initializeVideoState = useCallback((videoId, videoElement) => {
    if (!videoElement || videoRefs.current[videoId]) return; // Prevent re-initialization

    // Store video reference
    videoRefs.current[videoId] = videoElement;

    // Set initial volume and muted state
    videoElement.volume = 0.8; // Set reasonable default volume
    videoElement.muted = false; // Start unmuted

    // Initialize with default state immediately
    setVideoStates(prev => {
      // Don't update if already exists
      if (prev[videoId]) {
        return prev;
      }

      return {
        ...prev,
        [videoId]: {
          muted: false, // Start unmuted
          hasAudio: true, // Assume has audio until proven otherwise
          volume: 0.8
        }
      };
    });

    // Check if video has audio track (improved detection)
    const checkAudioTracks = () => {
      let hasAudio = false;

      try {
        // Multiple ways to detect audio
        hasAudio = videoElement.audioTracks?.length > 0 ||
                  videoElement.webkitAudioDecodedByteCount > 0 ||
                  videoElement.mozHasAudio === true ||
                  // Check if duration is reasonable (videos without audio are often very short or 0)
                  (videoElement.duration && videoElement.duration > 0.1);

        // Additional check: try to detect audio context
        if (!hasAudio && videoElement.duration > 0) {
          hasAudio = true; // If we have duration, likely has some form of audio track
        }
      } catch (e) {
        // Fallback: assume has audio for user experience
        hasAudio = true;
      }

      setVideoStates(prev => ({
        ...prev,
        [videoId]: {
          ...prev[videoId],
          hasAudio: hasAudio
        }
      }));
    };

    // Check audio tracks when metadata is loaded (only once)
    const handleLoadedMetadata = () => {
      checkAudioTracks();
      videoElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };

    const handleDurationChange = () => {
      checkAudioTracks();
      videoElement.removeEventListener('durationchange', handleDurationChange);
    };

    const handleLoadedData = () => {
      checkAudioTracks();
      videoElement.removeEventListener('loadeddata', handleLoadedData);
    };

    // Listen to multiple events for better audio detection
    videoElement.addEventListener('loadedmetadata', handleLoadedMetadata);
    videoElement.addEventListener('durationchange', handleDurationChange);
    videoElement.addEventListener('loadeddata', handleLoadedData);

    // Also check immediately if video is already loaded
    if (videoElement.readyState >= 1) {
      checkAudioTracks();
    }
  }, []);

  const toggleVideoMute = useCallback((videoId) => {
    const videoElement = videoRefs.current[videoId];
    if (!videoElement) {
      return;
    }

    const newMutedState = !videoElement.muted;
    videoElement.muted = newMutedState;

    setVideoStates(prev => ({
      ...prev,
      [videoId]: {
        ...prev[videoId],
        muted: newMutedState,
        volume: videoElement.volume
      }
    }));
  }, [videoStates]);

  // Stable callback ref creator (simplified and safe)
  const createVideoRef = useCallback((videoId) => {
    return (el) => {
      if (el && !videoRefs.current[videoId]) {
        initializeVideoState(videoId, el);
      }
      // Don't clean up refs here - let useEffect handle cleanup
    };
  }, [initializeVideoState]);

  // Volume control component
  const VolumeControl = ({ videoId, className = "" }) => {
    const videoState = videoStates[videoId] || { muted: false, hasAudio: true };
    const { muted, hasAudio } = videoState;

    return (
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (hasAudio) {
            toggleVideoMute(videoId);
          }
        }}
        disabled={!hasAudio}
        className={`rounded-full w-8 h-8 flex items-center justify-center text-sm transition pointer-events-auto ${className} ${
          !hasAudio
            ? 'bg-black/20 text-gray-400 cursor-default'
            : muted
              ? 'bg-black/40 hover:bg-black/60 text-white'
              : 'bg-green-600/80 hover:bg-green-600 text-white'
        }`}
        style={{ zIndex: 20 }}
        title={!hasAudio ? 'No audio track' : muted ? 'Unmute' : 'Mute'}
      >
        {!hasAudio ? (
          // Disabled volume icon
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.414 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.414l3.969-3.816a1 1 0 011.617.816zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.983 5.983 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.984 3.984 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
            <path d="M3 3L17 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : muted ? (
          // Muted icon
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.414 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.414l3.969-3.816a1 1 0 011.617.816z" clipRule="evenodd" />
            <path d="M12 8l4 4m0-4l-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        ) : (
          // Unmuted icon
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.617.816L4.414 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.414l3.969-3.816a1 1 0 011.617.816zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.983 5.983 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.984 3.984 0 00-1.172-2.828 1 1 0 010-1.415z" clipRule="evenodd" />
          </svg>
        )}
      </button>
    );
  };

  if (!normalizedAttachments.length) return null;
  if (normalizedAttachments.length === 1) {
    const att = normalizedAttachments[0];
    const isPdf = att.type === 'file' && (att.name||'').toLowerCase().endsWith('.pdf');
    return (
      <div className="mt-3 w-full flex justify-center">
        {att.type === 'image' && att.preview && (
          readonly ? (
            <div className="relative w-full max-w-2xl bg-black/5 rounded-md overflow-hidden">
              <img src={att.preview} alt={att.name} className="w-full max-h-[520px] object-contain bg-black" />
            </div>
          ) : (
            <button type="button" onClick={()=>onToggle(att)} className="relative group focus:outline-none focus:ring-2 focus:ring-indigo-400 rounded-md overflow-hidden w-full max-w-2xl bg-black/5">
              <img src={att.preview} alt={att.name} className="w-full max-h-[520px] object-contain bg-black" />
            </button>
          )
        )}
        {att.type === 'video' && att.preview && (
          readonly ? (
            <div className="relative w-full max-w-2xl bg-black rounded-md overflow-hidden flex items-center justify-center">
              <video src={att.preview} className="w-full max-h-[520px]" controls={false} playsInline muted />
            </div>
          ) : (
            <button type="button" onClick={()=>onToggle(att)} className="relative group focus:outline-none focus:ring-2 focus:ring-indigo-400 rounded-md overflow-hidden w-full max-w-2xl bg-black flex items-center justify-center">
              <video src={att.preview} className="w-full max-h-[520px]" controls playsInline />
            </button>
          )
        )}
        {att.type === 'audio' && (
          <div className="w-full max-w-md mx-auto bg-gradient-to-br from-indigo-50 to-blue-50 rounded-md p-6 flex flex-col items-center justify-center gap-3 border border-indigo-100">
            <span className="text-[11px] font-medium text-indigo-700 truncate w-full text-center">{att.name}</span>
            <audio src={att.preview} controls={!readonly} className="w-full" />
          </div>
        )}
        {att.type === 'file' && (
          readonly ? (
            <div className="relative w-full max-w-2xl bg-gradient-to-br from-gray-50 to-gray-100 rounded-md overflow-hidden flex flex-col items-center justify-center p-10 border border-gray-200">
              <span className="text-sm font-semibold text-gray-700 mb-2">{isPdf ? 'PDF Document' : 'File'}</span>
              <span className="text-[11px] text-gray-500 truncate max-w-full">{att.name}</span>
            </div>
          ) : (
            <button type="button" onClick={()=> isPdf && onOpenPdf(att)} className="relative group focus:outline-none focus:ring-2 focus:ring-indigo-400 rounded-md overflow-hidden w-full max-w-2xl bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col items-center justify-center p-10 border border-gray-200">
              <span className="text-sm font-semibold text-gray-700 mb-2">{isPdf ? 'PDF Document' : 'File'}</span>
              <span className="text-[11px] text-gray-500 truncate max-w-full">{att.name}</span>
              {isPdf && <span className="mt-4 text-[10px] text-indigo-600 underline">Open Preview</span>}
            </button>
          )
        )}
      </div>
    );
  }

  // Modal for individual preview (multi-attachment)
  const renderPreviewModal = () => {
    if(!preview) return null;
    const isPdf = preview.type==='file' && (preview.name||'').toLowerCase().endsWith('.pdf');
    const showNav = previewableCount > 1;
    const canPrev = previewIndex!=null && findNextIndex(previewIndex, -1)!==previewIndex;
    const canNext = previewIndex!=null && findNextIndex(previewIndex, +1)!==previewIndex;
    let translateX = 0;
    if(touchStartX!=null) translateX = touchDeltaX; else if(animating) translateX = animOffset; else translateX = 0;
    return (
      <div className="fixed inset-0 z-[250] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" onClick={closePreview} role="dialog" aria-modal="true">
        <div className="relative max-w-5xl w-full max-h-full flex flex-col bg-gray-900/80 rounded-lg overflow-hidden" onClick={e=>e.stopPropagation()}>
          <button onClick={closePreview} className="absolute top-2 right-2 z-20 text-white/80 hover:text-white text-xs bg-black/40 px-2 py-1 rounded">Close ✕</button>
          {showNav && (
            <>
              <button aria-label="Previous" disabled={!canPrev} onClick={goPrev} className={`absolute left-2 top-1/2 -translate-y-1/2 z-20 rounded-full w-9 h-9 flex items-center justify-center text-xl transition ${canPrev ? 'bg-black/40 hover:bg-black/60 text-white' : 'bg-black/20 text-white/30 cursor-default'}`}>‹</button>
              <button aria-label="Next" disabled={!canNext} onClick={goNext} className={`absolute right-2 top-1/2 -translate-y-1/2 z-20 rounded-full w-9 h-9 flex items-center justify-center text-xl transition ${canNext ? 'bg-black/40 hover:bg-black/60 text-white' : 'bg-black/20 text-white/30 cursor-default'}`}>›</button>
              {previewIndex!=null && <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-20 text-[11px] px-2 py-1 rounded bg-black/40 text-white/80">{normalizedAttachments.filter(a=>isPreviewable(a)).findIndex(a=>a.id===preview.id)+1} / {previewableCount}</div>}
            </>
          )}
          <div className="flex-1 overflow-auto flex items-center justify-center p-4 select-none" onTouchStart={onTouchStart} onTouchMove={onTouchMove} onTouchEnd={onTouchEnd}>
            <div className={`will-change-transform ${ (touchStartX!=null || animating) ? '' : '' }`} style={{ transform: `translateX(${translateX}px)`, transition: (touchStartX!=null) ? 'none' : animating ? 'transform 260ms cubic-bezier(0.22,0.61,0.36,1)' : 'transform 180ms cubic-bezier(0.33,1,0.68,1)' }}>
              {preview.type==='image' && preview.preview && (
                <img src={preview.preview} alt={preview.name} className="max-h-[80vh] max-w-full object-contain rounded" />
              )}
              {preview.type==='video' && preview.preview && (
                <video src={preview.preview} className="max-h-[80vh] max-w-full rounded" controls autoPlay playsInline />
              )}
              {preview.type==='audio' && (
                <div className="w-full max-w-lg mx-auto bg-gradient-to-br from-indigo-50 to-blue-50 rounded-md p-6 flex flex-col items-center justify-center gap-4 border border-indigo-200 shadow">
                  <span className="text-xs font-medium text-indigo-700 truncate w-full text-center">{preview.name}</span>
                  <audio src={preview.preview} controls className="w-full" autoPlay />
                </div>
              )}
              {preview.type==='file' && !isPdf && (
                <div className="w-full max-w-md mx-auto bg-gradient-to-br from-gray-50 to-gray-100 rounded-md p-8 flex flex-col items-center justify-center gap-3 border border-gray-300 shadow">
                  <span className="text-sm font-semibold text-gray-700">File</span>
                  <span className="text-[11px] text-gray-500 break-all text-center">{preview.name}</span>
                  <span className="text-[10px] text-gray-400">No preview available</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Multi-attachment carousel view
  if (!expanded) {
    const renderCarouselItem = (att, onContainerClick) => {
      if (!att) return <div className="h-80 bg-gray-100 flex items-center justify-center"><span className="text-gray-500">No content</span></div>;

      const itemIsPdf = att.type === 'file' && (att.name||'').toLowerCase().endsWith('.pdf');

      return (
        <div className="h-80 w-full">
          {att.type === 'image' && att.preview && (
            <img src={att.preview} alt={att.name} className="object-cover h-full w-full" />
          )}
          {att.type === 'video' && att.preview && (
            <div className="flex items-center justify-center bg-black h-full relative">
              <video
                ref={createVideoRef(att.id)}
                src={att.preview}
                className="h-full max-h-full max-w-full cursor-pointer"
                controls
                playsInline
                onClick={(e) => {
                  // Allow video controls to work - don't prevent default
                  e.stopPropagation();
                }}
                onDoubleClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onContainerClick();
                }}
              />

              {/* Volume Control */}
              <VolumeControl
                videoId={att.id}
                className="absolute top-2 left-2 z-10"
              />

              <div
                className="absolute inset-0 pointer-events-none"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onContainerClick();
                }}
                onDoubleClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onContainerClick();
                }}
              />
              <span className="absolute bottom-2 right-2 text-[10px] bg-black/60 text-white px-2 py-1 rounded pointer-events-none">
                Video • Click to play, double-click for full view
              </span>
            </div>
          )}
          {att.type === 'audio' && (
            <div className="flex items-center justify-center px-6 h-full bg-gradient-to-br from-indigo-50 to-blue-50 relative">
              <div className="w-full">
                <div className="text-center mb-4">
                  <span className="text-sm font-medium text-indigo-700">{att.name}</span>
                </div>
                <audio
                  src={att.preview}
                  controls={!readonly}
                  className="w-full"
                  onClick={(e) => {
                    // Allow audio controls to work
                    e.stopPropagation();
                  }}
                  onDoubleClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onContainerClick();
                  }}
                />
                <div className="text-center mt-2">
                  <span className="text-xs text-indigo-600">
                    Click to play, double-click for full view
                  </span>
                </div>
              </div>
              {/* Invisible overlay for container clicks */}
              <div
                className="absolute inset-0 pointer-events-none"
                style={{
                  // Create holes for the audio element
                  clipPath: 'polygon(0% 0%, 0% 40%, 100% 40%, 100% 0%, 100% 65%, 0% 65%, 0% 100%, 100% 100%)'
                }}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onContainerClick();
                }}
              />
            </div>
          )}
          {att.type === 'file' && (
            <div className="flex flex-col items-center justify-center text-sm font-medium text-gray-700 px-6 h-full bg-gradient-to-br from-gray-50 to-gray-100">
              <div className="text-center">
                <div className="text-lg mb-2">{itemIsPdf ? '📄 PDF' : '📎 FILE'}</div>
                <div className="text-xs text-gray-600 break-all">{att.name}</div>
                {itemIsPdf && <div className="text-xs text-indigo-600 underline mt-2">Click to preview</div>}
              </div>
            </div>
          )}
        </div>
      );
    };

    return (
      <>
        <div className="mt-3 relative">
          {/* Simple Carousel container */}
          <div className="relative overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
            {/* Show only the current item */}
            <div className="w-full">
              {readonly ? (
                renderCarouselItem(normalizedAttachments[carouselIndex], () => {})
              ) : (
                <div className="relative w-full group">
                  {/* For images and files: simple click to open modal */}
                  {(normalizedAttachments[carouselIndex]?.type === 'image' || normalizedAttachments[carouselIndex]?.type === 'file') && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        const att = normalizedAttachments[carouselIndex];
                        if (att?.type === 'file' && att.name?.toLowerCase().endsWith('.pdf')) {
                          onOpenPdf(att);
                        } else {
                          openPreview(att);
                        }
                      }}
                      className="relative w-full focus:outline-none focus:ring-2 focus:ring-indigo-400 transition block"
                    >
                      {renderCarouselItem(normalizedAttachments[carouselIndex], () => {})}
                      <span className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition" />
                    </button>
                  )}

                  {/* For audio and video: inline playback with click-outside for modal */}
                  {(normalizedAttachments[carouselIndex]?.type === 'audio' || normalizedAttachments[carouselIndex]?.type === 'video') && (
                    <div
                      className="relative w-full focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
                      onClick={(e) => {
                        // Only trigger modal on container clicks (outside media elements)
                        if (e.target === e.currentTarget) {
                          e.preventDefault();
                          e.stopPropagation();
                          openPreview(normalizedAttachments[carouselIndex]);
                        }
                      }}
                      onDoubleClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        openPreview(normalizedAttachments[carouselIndex]);
                      }}
                    >
                      {renderCarouselItem(normalizedAttachments[carouselIndex], () => {
                        openPreview(normalizedAttachments[carouselIndex]);
                      })}
                      <span className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition pointer-events-none" />
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Navigation arrows */}
            {normalizedAttachments.length > 1 && !readonly && (
              <>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    prevCarouselItem();
                  }}
                  disabled={carouselIndex === 0}
                  className={`absolute left-2 top-1/2 -translate-y-1/2 z-10 rounded-full w-8 h-8 flex items-center justify-center text-lg transition ${
                    carouselIndex === 0
                      ? 'bg-black/10 text-gray-400 cursor-default'
                      : 'bg-black/30 hover:bg-black/50 text-white'
                  }`}
                >
                  ‹
                </button>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    nextCarouselItem();
                  }}
                  disabled={carouselIndex === normalizedAttachments.length - 1}
                  className={`absolute right-2 top-1/2 -translate-y-1/2 z-10 rounded-full w-8 h-8 flex items-center justify-center text-lg transition ${
                    carouselIndex === normalizedAttachments.length - 1
                      ? 'bg-black/10 text-gray-400 cursor-default'
                      : 'bg-black/30 hover:bg-black/50 text-white'
                  }`}
                >
                  ›
                </button>
              </>
            )}

            {/* Counter overlay */}
            {normalizedAttachments.length > 1 && (
              <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                {carouselIndex + 1} / {normalizedAttachments.length}
              </div>
            )}
          </div>

          {/* Dots indicator */}
          {normalizedAttachments.length > 1 && (
            <div className="flex justify-center mt-3 gap-2">
              {normalizedAttachments.map((_, index) => (
                <button
                  key={index}
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    goToCarouselIndex(index);
                  }}
                  disabled={readonly}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === carouselIndex
                      ? 'bg-indigo-600'
                      : readonly
                        ? 'bg-gray-300 cursor-default'
                        : 'bg-gray-300 hover:bg-gray-400'
                  }`}
                />
              ))}
            </div>
          )}
        </div>
        {renderPreviewModal()}
      </>
    );
  }

  // Expanded view: carousel with larger items
  const renderExpandedCarouselItem = (att, onContainerClick) => {
    if (!att) return <div className="h-96 bg-gray-100 flex items-center justify-center"><span className="text-gray-500">No content</span></div>;

    const itemIsPdf = att.type === 'file' && (att.name||'').toLowerCase().endsWith('.pdf');

    return (
      <div className="h-96 w-full">
        {att.type === 'image' && att.preview && (
          <img src={att.preview} alt={att.name} className="object-cover h-full w-full" />
        )}
        {att.type === 'video' && att.preview && (
          <div className="flex items-center justify-center bg-black h-full relative">
            <video
              ref={createVideoRef(`${att.id}_expanded`)}
              src={att.preview}
              className="h-full max-h-full max-w-full cursor-pointer"
              controls
              playsInline
              onClick={(e) => {
                // Allow video controls to work
                e.stopPropagation();
              }}
              onDoubleClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onContainerClick();
              }}
            />

            {/* Volume Control for expanded view */}
            <VolumeControl
              videoId={`${att.id}_expanded`}
              className="absolute top-3 left-3 z-10"
            />

            <div
              className="absolute inset-0 pointer-events-none"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onContainerClick();
              }}
              onDoubleClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onContainerClick();
              }}
            />
            <span className="absolute bottom-2 right-2 text-xs bg-black/60 text-white px-2 py-1 rounded pointer-events-none">
              Video • Click to play, double-click for full view
            </span>
          </div>
        )}
        {att.type === 'audio' && (
          <div className="flex items-center justify-center px-8 h-full bg-gradient-to-br from-indigo-50 to-blue-50 relative">
            <div className="w-full max-w-lg">
              <div className="text-center mb-6">
                <span className="text-lg font-medium text-indigo-700">{att.name}</span>
              </div>
              <audio
                src={att.preview}
                controls
                className="w-full"
                onClick={(e) => {
                  // Allow audio controls to work
                  e.stopPropagation();
                }}
                onDoubleClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onContainerClick();
                }}
              />
              <div className="text-center mt-4">
                <span className="text-sm text-indigo-600">
                  Click to play, double-click for full view
                </span>
              </div>
            </div>
            {/* Invisible overlay for container clicks */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                // Create holes for the audio element
                clipPath: 'polygon(0% 0%, 0% 35%, 100% 35%, 100% 0%, 100% 70%, 0% 70%, 0% 100%, 100% 100%)'
              }}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onContainerClick();
              }}
            />
          </div>
        )}
        {att.type === 'file' && (
          <div className="flex flex-col items-center justify-center text-lg font-medium text-gray-700 px-8 h-full bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="text-center">
              <div className="text-2xl mb-4">{itemIsPdf ? '📄 PDF Document' : '📎 File'}</div>
              <div className="text-sm text-gray-600 break-all mb-4">{att.name}</div>
              {itemIsPdf && <div className="text-sm text-indigo-600 underline">Click to open preview</div>}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <div className="mt-3 relative">
        {/* Expanded Carousel container */}
        <div className="relative overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
          {/* Show only the current item */}
          <div className="w-full">
            {/* For images and files: simple click to open modal */}
            {(normalizedAttachments[carouselIndex]?.type === 'image' || normalizedAttachments[carouselIndex]?.type === 'file') && (
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const att = normalizedAttachments[carouselIndex];
                  const itemIsPdf = att?.type === 'file' && att?.name?.toLowerCase().endsWith('.pdf');
                  if (itemIsPdf) {
                    onOpenPdf(att);
                  } else {
                    openPreview(att);
                  }
                }}
                className="relative w-full group focus:outline-none focus:ring-2 focus:ring-indigo-400 transition block"
              >
                {renderExpandedCarouselItem(normalizedAttachments[carouselIndex], () => {})}
                <span className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition" />
              </button>
            )}

            {/* For audio and video: inline playback with click-outside for modal */}
            {(normalizedAttachments[carouselIndex]?.type === 'audio' || normalizedAttachments[carouselIndex]?.type === 'video') && (
              <div
                className="relative w-full group focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
                onClick={(e) => {
                  // Only trigger modal on container clicks (outside media elements)
                  if (e.target === e.currentTarget) {
                    e.preventDefault();
                    e.stopPropagation();
                    openPreview(normalizedAttachments[carouselIndex]);
                  }
                }}
                onDoubleClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  openPreview(normalizedAttachments[carouselIndex]);
                }}
              >
                {renderExpandedCarouselItem(normalizedAttachments[carouselIndex], () => {
                  openPreview(normalizedAttachments[carouselIndex]);
                })}
                <span className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition pointer-events-none" />
              </div>
            )}
          </div>

          {/* Navigation arrows for expanded view */}
          {normalizedAttachments.length > 1 && (
            <>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  prevCarouselItem();
                }}
                disabled={carouselIndex === 0}
                className={`absolute left-3 top-1/2 -translate-y-1/2 z-10 rounded-full w-10 h-10 flex items-center justify-center text-xl transition ${
                  carouselIndex === 0
                    ? 'bg-black/10 text-gray-400 cursor-default'
                    : 'bg-black/30 hover:bg-black/50 text-white'
                }`}
              >
                ‹
              </button>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  nextCarouselItem();
                }}
                disabled={carouselIndex === normalizedAttachments.length - 1}
                className={`absolute right-3 top-1/2 -translate-y-1/2 z-10 rounded-full w-10 h-10 flex items-center justify-center text-xl transition ${
                  carouselIndex === normalizedAttachments.length - 1
                    ? 'bg-black/10 text-gray-400 cursor-default'
                    : 'bg-black/30 hover:bg-black/50 text-white'
                }`}
              >
                ›
              </button>
            </>
          )}

          {/* Counter overlay for expanded view */}
          {normalizedAttachments.length > 1 && (
            <div className="absolute top-3 right-3 bg-black/60 text-white text-sm px-3 py-1 rounded">
              {carouselIndex + 1} / {normalizedAttachments.length}
            </div>
          )}
        </div>

        {/* Dots indicator for expanded view */}
        {normalizedAttachments.length > 1 && (
          <div className="flex justify-center mt-4 gap-3">
            {normalizedAttachments.map((_, index) => (
              <button
                key={index}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  goToCarouselIndex(index);
                }}
                className={`w-3 h-3 rounded-full transition-colors ${
                  index === carouselIndex
                    ? 'bg-indigo-600'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
              />
            ))}
          </div>
        )}
      </div>
      {renderPreviewModal()}
    </>
  );
};
export default AttachmentDisplay;
