import React, { useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { CameraIcon } from '@heroicons/react/24/outline';
import ImageCropperModal from './ImageCropperModal';

/* AvatarUploader with crop modal */
const AvatarUploader = ({ avatarUrl, username, isOwner, onChange }) => {
  const inputRef = useRef(null);
  const [pendingFile, setPendingFile] = useState(null);
  const [showCrop, setShowCrop] = useState(false);

  const pick = () => inputRef.current?.click();
  const handle = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/^image\//.test(file.type) || file.size > 5 * 1024 * 1024) return;
    setPendingFile(file);
    setShowCrop(true);
  };
  const handleCropped = (blob, previewUrl) => {
    const file = new File([blob], 'avatar.png', { type: 'image/png' });
    onChange && onChange(file, previewUrl);
  };

  return (
    <div className="relative inline-block">
      {avatarUrl ? (
        <img src={avatarUrl} alt={username} className="h-28 w-28 rounded-full object-cover ring-4 ring-white shadow-md shadow-black/10" />
      ) : (
        <div className="h-28 w-28 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-3xl font-semibold ring-4 ring-white shadow-md shadow-black/10 select-none">
          {username?.[0]?.toUpperCase() || '?'}
        </div>
      )}
      {isOwner && (
        <button type="button" onClick={pick} className="absolute bottom-1 right-1 p-1.5 rounded-full bg-white shadow hover:bg-blue-50 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white" aria-label="Change avatar">
          <CameraIcon className="h-4 w-4 text-gray-600" />
        </button>
      )}
      <input ref={inputRef} type="file" accept="image/*" onChange={handle} className="hidden" />
      {showCrop && pendingFile && (
        <ImageCropperModal
          file={pendingFile}
            aspect={1}
            targetWidth={320}
            targetHeight={320}
            onClose={()=>{ setShowCrop(false); setPendingFile(null); }}
            onCropped={(blob, url)=>{ handleCropped(blob, url); setShowCrop(false); setPendingFile(null); }}
        />
      )}
    </div>
  );
};

AvatarUploader.propTypes = {
  avatarUrl: PropTypes.string,
  username: PropTypes.string,
  isOwner: PropTypes.bool,
  onChange: PropTypes.func
};

export default AvatarUploader;
