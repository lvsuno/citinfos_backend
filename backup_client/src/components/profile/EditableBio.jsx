import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

/*
  EditableBio
  Props:
    value: string
    max: number (default 250)
    isOwner: boolean
    onSave: (string)=>Promise|void
*/
const EditableBio = ({ value, max = 250, isOwner, onSave, pending=false }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value || '');
  const [saving, setSaving] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const MAX_COLLAPSED = 100;

  const start = () => { if (!isOwner || pending) return; setDraft(value || ''); setEditing(true); };
  const cancel = () => { if (saving) return; setEditing(false); setDraft(value || ''); };
  const save = async () => {
    if (!draft.trim() || saving) return;
    try {
      setSaving(true);
      await onSave?.(draft.trim());
      setEditing(false);
    } finally { setSaving(false); }
  };

  if (!editing) {
    const full = value?.trim() || '';
    const isLong = full.length > MAX_COLLAPSED;
    const display = !expanded && isLong ? full.slice(0, MAX_COLLAPSED) + '…' : full || (isOwner ? 'Add a short bio about yourself.' : 'No bio provided.');
    return (
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-gray-700 flex-1 whitespace-pre-line">
          {display}
          {isLong && (
            <button
              type="button"
              onClick={()=>setExpanded(e=>!e)}
              className="ml-1 text-blue-600 hover:text-blue-700 text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
            >{expanded ? 'Show less' : 'Show more'}</button>
          )}
        </p>
        {isOwner && (
          <button onClick={start} disabled={pending} className="p-2 rounded-md bg-gray-100 hover:bg-blue-50 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white" title="Edit Bio" aria-label="Edit bio">
            <PencilIcon className="h-4 w-4 text-gray-500" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <textarea
        value={draft}
        onChange={e=>setDraft(e.target.value)}
        rows={3}
        maxLength={max}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
      />
      <div className="flex justify-end gap-2">
        <button onClick={cancel} type="button" disabled={saving} className="px-3 py-1.5 rounded-md bg-gray-100 text-gray-700 text-xs font-medium hover:bg-gray-200 inline-flex items-center gap-1 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"><XMarkIcon className="h-4 w-4" /> Cancel</button>
        <button onClick={save} type="button" disabled={!draft.trim() || saving} className={`px-3 py-1.5 rounded-md text-xs font-medium inline-flex items-center gap-1 ${draft.trim() ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'} disabled:opacity-70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white`}>
          <CheckIcon className="h-4 w-4" /> {saving ? 'Saving...' : 'Save'}
        </button>
      </div>
      <p className="text-[10px] text-gray-500 text-right">{draft.length}/{max}</p>
    </div>
  );
};

EditableBio.propTypes = {
  value: PropTypes.string,
  max: PropTypes.number,
  isOwner: PropTypes.bool,
  onSave: PropTypes.func,
  pending: PropTypes.bool
};

export default EditableBio;
