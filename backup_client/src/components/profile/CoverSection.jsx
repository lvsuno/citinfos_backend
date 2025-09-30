import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { PhotoIcon, SpeakerWaveIcon, SpeakerXMarkIcon } from '@heroicons/react/24/outline';
import ImageCropperModal from './ImageCropperModal';

/*
  CoverSection with crop modal
*/
const CoverSection = ({ coverUrl, coverMediaType, isOwner, onChange, flushTop = false }) => {
  const [showCrop, setShowCrop] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const [isMuted, setIsMuted] = useState(true); // Start muted by default
  const [isVideoLoaded, setIsVideoLoaded] = useState(false);
  const videoRef = useRef(null);

  // Handle video play/pause based on page visibility
  useEffect(() => {
    const video = videoRef.current;
    if (!video || coverMediaType !== 'video') return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        video.pause();
      } else {
        video.play().catch(console.error);
      }
    };

    const handlePlay = () => {
      video.play().catch(console.error);
    };

    // Auto-play when video loads
    video.addEventListener('loadeddata', handlePlay);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      video.removeEventListener('loadeddata', handlePlay);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [coverMediaType, coverUrl]);

  const toggleMute = () => {
    console.log('Mute button clicked, current muted state:', isMuted);
    const video = videoRef.current;
    if (video) {
      video.muted = !video.muted;
      setIsMuted(video.muted);
      console.log('Video muted state changed to:', video.muted);
    } else {
      console.error('Video ref not found');
    }
  };

  const handleFile = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check if file is image or video
    const isImage = /^image\//.test(file.type);
    const isVideo = /^video\//.test(file.type);

    if (!isImage && !isVideo) return;

    // Size limits: 5MB for images, 15MB for videos (or whatever your backend allows)
    const maxSize = isImage ? 5 * 1024 * 1024 : 15 * 1024 * 1024;
    if (file.size > maxSize) return;

    if (isImage) {
      // For images, use the existing crop modal
      setPendingFile(file);
      setShowCrop(true);
    } else if (isVideo) {
      // For videos, directly upload without cropping
      onChange && onChange(file, null);
    }
  };

  const handleCropped = (blob, previewUrl) => {
    // convert blob to File for upstream if needed
    const file = new File([blob], 'cover.png', { type: 'image/png' });
    onChange && onChange(file, previewUrl);
  };

  return (
    <div className={`relative h-48 md:h-56 w-full overflow-hidden ${flushTop ? 'rounded-b-lg' : 'rounded-lg'} bg-gradient-to-r from-blue-600 to-indigo-600`}>
      {coverUrl && (
        coverMediaType === 'video' ? (
          <video
            ref={videoRef}
            src={coverUrl}
            className="absolute inset-0 h-full w-full object-cover"
            autoPlay
            muted={isMuted}
            loop
            playsInline
            onError={(e) => console.error('Video load error:', e)}
            onLoadStart={() => console.log('Video load started')}
            onLoadedData={() => {
              console.log('Video loaded successfully');
              setIsVideoLoaded(true);
            }}
          />
        ) : (
          <img
            src={coverUrl}
            alt="Cover"
            className="absolute inset-0 h-full w-full object-cover"
            onError={(e) => console.error('Image load error:', e)}
            onLoad={() => console.log('Image loaded successfully')}
          />
        )
      )}

      <div className="absolute inset-0 bg-black/20 pointer-events-none" />

      {/* Sound control button for videos */}
      {coverUrl && coverMediaType === 'video' && isVideoLoaded && (
        <button
          onClick={toggleMute}
          className="absolute bottom-2 right-2 inline-flex items-center justify-center w-10 h-10 bg-black/60 hover:bg-black/80 text-white rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/50 z-10 cursor-pointer"
          title={isMuted ? 'Unmute video' : 'Mute video'}
        >
          {isMuted ? (
            <SpeakerXMarkIcon className="h-5 w-5" />
          ) : (
            <SpeakerWaveIcon className="h-5 w-5" />
          )}
        </button>
      )}

      {/* Change cover button */}
      {/* Change cover button */}
      {isOwner && (
        <label className={`absolute top-2 ${coverMediaType === 'video' ? 'right-2' : 'right-2'} inline-flex items-center gap-1 bg-white/90 hover:bg-white text-gray-700 text-xs font-medium px-2 py-1 rounded-md shadow cursor-pointer transition focus-within:outline-none focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 focus-within:ring-offset-white z-10`}>
          <PhotoIcon className="h-4 w-4" />
          <span>Change</span>
          <input type="file" accept="image/*,video/*" onChange={handleFile} className="hidden" />
        </label>
      )}
      {showCrop && pendingFile && (
        <ImageCropperModal
          file={pendingFile}
          aspect={5/2}
          onClose={()=>{ setShowCrop(false); setPendingFile(null); }}
          onCropped={(blob, url)=>{ handleCropped(blob, url); setShowCrop(false); setPendingFile(null); }}
        />
      )}
    </div>
  );
};

CoverSection.propTypes = {
  coverUrl: PropTypes.string,
  coverMediaType: PropTypes.oneOf(['image', 'video']),
  isOwner: PropTypes.bool,
  onChange: PropTypes.func
};

export default CoverSection;
