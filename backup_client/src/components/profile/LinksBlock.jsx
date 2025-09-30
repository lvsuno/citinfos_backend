import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

/* LinksBlock
   Props: links: {label:string, url:string}[]
          isOwner: boolean
          onChange: (links)=>void
*/
const LinksBlock = ({ links = [], isOwner, onChange }) => {
  const [draft, setDraft] = useState(links);
  const [adding, setAdding] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newUrl, setNewUrl] = useState('');

  const submit = () => {
    if (!newLabel.trim() || !newUrl.trim()) return;
    const next = [...draft, { label: newLabel.trim(), url: newUrl.trim() }];
    setDraft(next);
    onChange?.(next);
    setNewLabel(''); setNewUrl(''); setAdding(false);
  };
  const remove = (idx) => {
    const next = draft.filter((_,i)=>i!==idx);
    setDraft(next);
    onChange?.(next);
  };

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">Links</h3>
      <ul className="space-y-2 mb-3">
        {draft.map((l,i)=>(
          <li key={i} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded">
            <a href={l.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline truncate max-w-[75%]">{l.label}</a>
            {isOwner && (
              <button onClick={()=>remove(i)} className="p-1 rounded hover:bg-red-50" aria-label="Remove link">
                <XMarkIcon className="h-4 w-4 text-gray-400" />
              </button>
            )}
          </li>
        ))}
        {draft.length===0 && <li className="text-xs text-gray-500">No links added.</li>}
      </ul>
      {isOwner && !adding && (
        <button onClick={()=>setAdding(true)} className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-700">
          <PlusIcon className="h-4 w-4" /> Add link
        </button>
      )}
      {isOwner && adding && (
        <div className="space-y-2">
          <input value={newLabel} onChange={e=>setNewLabel(e.target.value)} placeholder="Label" className="w-full border px-2 py-1 rounded text-xs" />
          <input value={newUrl} onChange={e=>setNewUrl(e.target.value)} placeholder="https://" className="w-full border px-2 py-1 rounded text-xs" />
          <div className="flex gap-2 justify-end">
            <button onClick={()=>{setAdding(false); setNewLabel(''); setNewUrl('');}} className="px-2 py-1 text-[11px] rounded bg-gray-100 hover:bg-gray-200">Cancel</button>
            <button onClick={submit} disabled={!newLabel.trim()||!newUrl.trim()} className="px-2 py-1 text-[11px] rounded bg-blue-600 text-white disabled:opacity-50">Save</button>
          </div>
        </div>
      )}
    </div>
  );
};

LinksBlock.propTypes = { links: PropTypes.array, isOwner: PropTypes.bool, onChange: PropTypes.func };
export default LinksBlock;
