import React, { useState, useEffect } from 'react';

/* AttachmentDisplayGrid
   Unified attachment renderer with GRID view for multi-attachments.
   This is the original grid-based implementation preserved as backup.
   Props:
     attachments: [{ id, type: image|video|audio|file, preview, name }]
     expanded (bool)
     onToggle(att) -> toggle expand for gallery items (used e.g. for expand/collapse outside)
     onOpenPdf(att) -> open pdf modal (only for file/pdf)
     readonly (bool) -> disable interactions when true (for read-only displays like embedded posts)
*/

const AttachmentDisplayGrid = ({ attachments = [], expanded=false, onToggle=()=>{}, onOpenPdf=()=>{}, readonly=false }) => {
  const [preview, setPreview] = useState(null); // attachment being previewed (image|video|audio|file non-pdf)
  const [previewIndex, setPreviewIndex] = useState(null); // index in attachments for navigation
  const [touchStartX, setTouchStartX] = useState(null);
  const [touchDeltaX, setTouchDeltaX] = useState(0);
  const [animating, setAnimating] = useState(false); // momentum animation active
  const [animOffset, setAnimOffset] = useState(0);   // current animated translateX when animating

  // Helper function to normalize attachment data structure
  const normalizeAttachment = (att) => {
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

  // Normalize all attachments
  const normalizedAttachments = attachments.map(normalizeAttachment).filter(Boolean);

  // Helper to check if attachment is a PDF (non-previewable inside this modal)
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

  // Condensed multi-attachment (not expanded) - GRID VIEW
  if (!expanded) {
    const total = normalizedAttachments.length;
    const showPlus = total > 4;
    const visible = showPlus ? normalizedAttachments.slice(0,3) : normalizedAttachments.slice(0,4);
    const remaining = showPlus ? total - 3 : 0;

    return (
      <>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {visible.map(att => {
            const isPdf = att.type === 'file' && (att.name||'').toLowerCase().endsWith('.pdf');
            const content = (
              <>
                {att.type === 'image' && att.preview && (
                  <img src={att.preview} alt={att.name} className="object-cover h-40 w-full" />
                )}
                {att.type === 'video' && att.preview && (
                  <div className="flex items-center justify-center bg-black h-40">
                    <video src={att.preview} className="h-full max-h-full max-w-full" muted playsInline />
                    <span className="absolute bottom-1 right-1 text-[10px] bg-black/60 text-white px-1 rounded">Video</span>
                  </div>
                )}
                {att.type === 'audio' && (
                  <div className="flex items-center justify-center px-2 h-40 bg-gradient-to-br from-indigo-50 to-blue-50 w-full">
                    <audio src={att.preview} controls={!readonly} className="w-full" />
                  </div>
                )}
                {att.type === 'file' && (
                  <div className="flex flex-col items-center justify-center text-[11px] font-medium text-gray-700 px-2 h-40 bg-gradient-to-br from-gray-50 to-gray-100 w-full">
                    {isPdf ? 'PDF' : 'FILE'}<br/>
                    <span className="text-[9px] truncate w-full">{att.name}</span>
                  </div>
                )}
              </>
            );

            if (readonly) {
              return (
                <div key={att.id} className="relative rounded-md overflow-hidden border border-gray-200 bg-gray-50">
                  {content}
                </div>
              );
            }

            return (
              <button key={att.id} type="button" onClick={()=>{ if(att.type==='file' && isPdf) onOpenPdf(att); else openPreview(att); }} className="group relative rounded-md overflow-hidden border border-gray-200 bg-gray-50 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 transition">
                {content}
                <span className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition" />
              </button>
            );
          })}
          {showPlus && (
            <button type="button" onClick={()=>onToggle(normalizedAttachments[0])} className="relative rounded-md overflow-hidden border border-gray-300 bg-gray-100 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-indigo-400">
              <span className="text-xl font-semibold text-gray-700">+{remaining}</span>
              <span className="absolute bottom-1 right-1 text-[10px] font-medium text-gray-500">more</span>
            </button>
          )}
        </div>
        {renderPreviewModal()}
      </>
    );
  }

  // Expanded view: show all attachments grid
  return (
    <>
      <div className={`mt-3 grid gap-2 ${expanded ? 'grid-cols-2 md:grid-cols-3' : 'grid-cols-3 md:grid-cols-4'} `}>
        {normalizedAttachments.map(att => {
          const isPdf = att.type === 'file' && (att.name||'').toLowerCase().endsWith('.pdf');
          return (
            <button key={att.id} type="button" onClick={()=>{ if(att.type==='file' && isPdf) onOpenPdf(att); else openPreview(att); }} className="group relative rounded-md overflow-hidden border border-gray-200 bg-gray-50 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 transition">
              {att.type === 'image' && att.preview && (
                <img src={att.preview} alt={att.name} className={`object-cover ${expanded ? 'h-72 w-full' : 'h-24 w-full'} transition-all`} />
              )}
              {att.type === 'video' && att.preview && (
                <div className={`flex items-center justify-center bg-black ${expanded ? 'h-72' : 'h-24'}`}>
                  <video src={att.preview} className="h-full max-h-full max-w-full" muted playsInline />
                </div>
              )}
              {att.type === 'audio' && (
                <div className={`flex items-center justify-center px-2 ${expanded ? 'h-40' : 'h-24'} bg-gradient-to-br from-indigo-50 to-blue-50 w-full`}>
                  <audio src={att.preview} controls className="w-full" />
                </div>
              )}
              {att.type === 'file' && (
                <div className={`flex flex-col items-center justify-center text-[11px] font-medium text-gray-700 px-2 ${expanded ? 'h-40' : 'h-24'} bg-gradient-to-br from-gray-50 to-gray-100 w-full`}>{isPdf ? 'PDF' : 'FILE'}<br/><span className="text-[9px] truncate w-full">{att.name}</span></div>
              )}
              {!expanded && att.type!=='file' && <span className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition" />}
            </button>
          );
        })}
      </div>
      {renderPreviewModal()}
    </>
  );
};
export default AttachmentDisplayGrid;
