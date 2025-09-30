import React, { useEffect, useRef, useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { XMarkIcon, ArrowsPointingOutIcon } from '@heroicons/react/24/outline';

/* ImageCropperModal
   Generic lightweight cropper (rectangle select) without external deps.
   Props:
     file: File (required) - original image file user selected
     aspect: number (width/height)
     onClose: ()=>void
     onCropped: (Blob, previewUrl)=>void  (Blob is PNG)
     targetWidth, targetHeight: desired output size in px (optional, default based on container)
*/
const ImageCropperModal = ({ file, aspect = 1, onClose, onCropped, targetWidth, targetHeight }) => {
  const [imgEl, setImgEl] = useState(null);
  const imgRef = useRef(null);
  const containerRef = useRef(null);
  const [error, setError] = useState(null);
  const [ready, setReady] = useState(false);
  const [crop, setCrop] = useState(null); // {x,y,w,h} in displayed coords
  const dragState = useRef({ mode: null, sx:0, sy:0, startCrop:null });
  const [zoom, setZoom] = useState(1); // 1 = fit
  const baseScaleRef = useRef(1);
  const [imgOffset, setImgOffset] = useState({ x: 0, y: 0 }); // displayed top-left
  const [mode, setMode] = useState('crop'); // 'crop' | 'pan'

  // Load file into object URL
  const [url, setUrl] = useState('');
  useEffect(()=>{
    if (!file) return;
    const u = URL.createObjectURL(file);
    setUrl(u);
    return ()=> URL.revokeObjectURL(u);
  }, [file]);

  const initCrop = useCallback(()=>{
    if (!imgRef.current || !containerRef.current) return;
    const cw = containerRef.current.clientWidth;
    const ch = containerRef.current.clientHeight;
    // Fit image inside container (contain)
    const naturalW = imgRef.current.naturalWidth;
    const naturalH = imgRef.current.naturalHeight;
    if (!naturalW || !naturalH) return;
    let scaleFit = Math.min(cw / naturalW, ch / naturalH);
    baseScaleRef.current = scaleFit;
    const dispW = naturalW * scaleFit * zoom;
    const dispH = naturalH * scaleFit * zoom;
    const offsetX = (cw - dispW)/2;
    const offsetY = (ch - dispH)/2;
    imgRef.current.dataset.scale = scaleFit * zoom;
    setImgOffset({ x: offsetX, y: offsetY });
    // default crop = largest rect honoring aspect
    let w = dispW; let h = w / aspect;
    if (h > dispH) { h = dispH; w = h * aspect; }
    const x = offsetX + (dispW - w)/2;
    const y = offsetY + (dispH - h)/2;
    setCrop({ x, y, w, h });
    setReady(true);
  }, [aspect, zoom]);

  const onImageLoad = () => {
    try { initCrop(); } catch(e){ setError('Failed to load image'); }
  };

  // Recompute offsets when zoom changes, keeping crop centered relative to previous image area
  useEffect(()=>{
    if (!ready || !imgRef.current || !crop) return;
    const container = containerRef.current; if (!container) return;
    const cw = container.clientWidth; const ch = container.clientHeight;
    const naturalW = imgRef.current.naturalWidth; const naturalH = imgRef.current.naturalHeight;
    const dispW = naturalW * baseScaleRef.current * zoom;
    const dispH = naturalH * baseScaleRef.current * zoom;
    // keep crop center relative to container
    const cx = crop.x + crop.w/2; const cy = crop.y + crop.h/2;
    let newOffsetX = cx - dispW/2; let newOffsetY = cy - dispH/2;
    setImgOffset({ x: newOffsetX, y: newOffsetY });
    imgRef.current.dataset.scale = baseScaleRef.current * zoom;
  }, [zoom, ready]);

  const clampOffset = (offset, dispW, dispH, cropRect) => {
    // ensure image fully covers crop rectangle
    const minX = cropRect.x + cropRect.w - dispW;
    const maxX = cropRect.x;
    const minY = cropRect.y + cropRect.h - dispH;
    const maxY = cropRect.y;
    return {
      x: Math.min(Math.max(offset.x, minX), maxX),
      y: Math.min(Math.max(offset.y, minY), maxY)
    };
  };

  // Mouse / pointer interactions
  const pointerDown = (e, modeOverride) => {
    if (!crop) return;
    const activeMode = modeOverride || (mode === 'pan' ? 'panImage' : 'move');
    dragState.current = { mode: activeMode, sx: e.clientX, sy: e.clientY, startCrop: { ...crop }, startOffset: { ...imgOffset } };
    window.addEventListener('pointermove', pointerMove);
    window.addEventListener('pointerup', pointerUp);
  };
  const clamp = (val,min,max)=>Math.min(Math.max(val,min),max);
  const pointerMove = (e) => {
    const st = dragState.current; if (!st.mode) return;
    const dx = e.clientX - st.sx; const dy = e.clientY - st.sy;
    if (st.mode === 'panImage') {
      const naturalW = imgRef.current.naturalWidth; const naturalH = imgRef.current.naturalHeight;
      const dispW = naturalW * baseScaleRef.current * zoom;
      const dispH = naturalH * baseScaleRef.current * zoom;
      const next = { x: st.startOffset.x + dx, y: st.startOffset.y + dy };
      setImgOffset(prev => clampOffset(next, dispW, dispH, st.startCrop));
      return;
    }
    // crop manipulation
    setCrop(prev => {
      if (!prev) return prev;
      let { x,y,w,h } = st.startCrop;
      if (st.mode === 'move') { x += dx; y += dy; }
      else {
        // resize preserving aspect
        const dir = st.mode; // 'nw','ne','sw','se'
        let delta = 0;
        if (dir === 'nw') delta = -dx; else if (dir === 'ne') delta = dx; else if (dir === 'sw') delta = -dx; else if (dir === 'se') delta = dx;
        w += delta; h = w / aspect; if (w < 40) { w = 40; h = w / aspect; }
        if (dir.includes('n')) { y = y + (st.startCrop.h - h); }
        if (dir.includes('w')) { x = x + (st.startCrop.w - w); }
      }
      // bounds (stay within container)
      const cw = containerRef.current.clientWidth; const ch = containerRef.current.clientHeight;
      if (x < 0) x = 0; if (y < 0) y = 0; if (x + w > cw) x = cw - w; if (y + h > ch) y = ch - h;
      return { x,y,w,h };
    });
  };
  const pointerUp = () => {
    dragState.current.mode = null;
    window.removeEventListener('pointermove', pointerMove);
    window.removeEventListener('pointerup', pointerUp);
  };

  const doCrop = async () => {
    if (!crop || !imgRef.current) return;
    const displayedScale = baseScaleRef.current * zoom;
    const naturalW = imgRef.current.naturalWidth;
    const naturalH = imgRef.current.naturalHeight;
    const natX = (crop.x - imgOffset.x) / displayedScale;
    const natY = (crop.y - imgOffset.y) / displayedScale;
    const natW = crop.w / displayedScale;
    const natH = crop.h / displayedScale;

    const outW = targetWidth || Math.round(natW);
    const outH = targetHeight || Math.round(natH);

    const canvas = document.createElement('canvas');
    canvas.width = outW; canvas.height = outH;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(imgRef.current, natX, natY, natW, natH, 0,0,outW,outH);
    canvas.toBlob(blob => {
      if (!blob) return;
      const preview = URL.createObjectURL(blob);
      onCropped && onCropped(blob, preview);
      onClose && onClose();
    }, 'image/png');
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl h-[560px] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-gray-700">Adjust Image</h2>
            <div className="flex items-center gap-2 text-[11px]">
              <label className="flex items-center gap-1">
                <span className="text-gray-500">Zoom</span>
                <input type="range" min="1" max="3" step="0.01" value={zoom} onChange={e=>setZoom(parseFloat(e.target.value))} />
              </label>
              <button onClick={()=>setMode(m => m==='crop' ? 'pan' : 'crop')} className={`px-2 py-0.5 rounded text-[11px] font-medium border ${mode==='pan' ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'}`}>{mode==='pan' ? 'Pan (on)' : 'Pan'}</button>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-gray-100" aria-label="Close cropper"><XMarkIcon className="h-5 w-5 text-gray-500" /></button>
        </div>
        <div ref={containerRef} className="relative flex-1 bg-gray-900 select-none overflow-hidden">
          {url && (
            <img
              ref={imgRef}
              src={url}
              alt="to crop"
              onLoad={onImageLoad}
              className="absolute top-0 left-0 max-w-none"
              style={{ transform: `translate(${imgOffset.x}px, ${imgOffset.y}px) scale(${baseScaleRef.current * zoom})`, transformOrigin: 'top left', visibility: ready ? 'visible':'hidden' }}
              onPointerDown={(e)=> mode==='pan' && pointerDown(e,'panImage')}
            />
          )}
          {!ready && !error && <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-300">Loading...</div>}
          {error && <div className="absolute inset-0 flex items-center justify-center text-xs text-red-400">{error}</div>}
          {ready && crop && (
            <div
              className={`absolute border-2 ${mode==='pan' ? 'border-white/40' : 'border-white/90'} shadow-[0_0_0_150vmax_rgba(0,0,0,0.45)] box-content ${mode==='pan' ? 'cursor-grab' : 'cursor-move'}`}
              style={{ left: crop.x, top: crop.y, width: crop.w, height: crop.h }}
              onPointerDown={(e)=> mode==='crop' && pointerDown(e,'move')}
            >
              {mode==='crop' && ['nw','ne','sw','se'].map(c=> (
                <span key={c} onPointerDown={(e)=>{e.stopPropagation(); pointerDown(e,c);}} className={`absolute h-3 w-3 bg-white rounded-full border border-gray-400 cursor-pointer ${c==='nw'?'top-0 left-0 -translate-x-1/2 -translate-y-1/2':c==='ne'?'top-0 right-0 translate-x-1/2 -translate-y-1/2':c==='sw'?'bottom-0 left-0 -translate-x-1/2 translate-y-1/2':'bottom-0 right-0 translate-x-1/2 translate-y-1/2'}`}></span>
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
          <div className="text-[11px] text-gray-500 flex flex-col">
            <span>{mode==='crop' ? 'Resize / move crop rectangle' : 'Drag image to position under crop'}</span>
            <span>Aspect {aspect.toFixed(2)}</span>
          </div>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-3 py-1.5 rounded text-xs font-medium bg-gray-100 hover:bg-gray-200 text-gray-700">Cancel</button>
            <button onClick={doCrop} disabled={!ready} className="px-3 py-1.5 rounded text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">Save</button>
          </div>
        </div>
      </div>
    </div>
  );
};

ImageCropperModal.propTypes = {
  file: PropTypes.instanceOf(File),
  aspect: PropTypes.number,
  onClose: PropTypes.func,
  onCropped: PropTypes.func,
  targetWidth: PropTypes.number,
  targetHeight: PropTypes.number
};

export default ImageCropperModal;
