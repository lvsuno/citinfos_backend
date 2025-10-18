import React, { useState, useMemo, useEffect } from 'react';

/* PollDisplay
   Lightweight inline poll renderer for PostCard.
   Props:
     poll: {
       id, question, options:[{id,text,vote_count, percentage?}], allows_multiple_votes,
       user_voted, user_vote (array of option ids), is_expired, vote_count, voter_count
     }
     onVote(pollId, optionIds[]) => void
     readonly (bool) => disable voting when true (for read-only displays like embedded posts)
*/

const PollDisplay = ({ poll, onVote = () => {}, readonly = false }) => {
  const [localPoll, setLocalPoll] = useState(poll);
  const [selected, setSelected] = useState(poll?.user_vote || []);
  const [submitting, setSubmitting] = useState(false);

  // Sync local state when poll prop changes
  useEffect(() => {
    if (poll) {
      setLocalPoll(poll);
      setSelected(poll.user_vote || []);
    }
  }, [poll, poll?.options?.length, poll?.question]);

  const computedOptions = useMemo(() => {
    if (!localPoll?.options) return [];
    const total = localPoll.options.reduce((acc,o)=>acc + (o.vote_count||0),0) || 0;
    return localPoll.options.map(o => ({
      ...o,
      percentage: total ? Math.round((o.vote_count||0)*100/total) : 0
    }));
  }, [localPoll?.options]);

  if (!poll) return null;

  const alreadyVoted = localPoll.user_voted || localPoll.is_expired || readonly;
  const multiple = localPoll.allows_multiple_votes;
  const maxPct = Math.max(0, ...computedOptions.map(o=>o.percentage));

  const toggle = (id) => {
    if (alreadyVoted) return;
    setSelected(prev => multiple ? (prev.includes(id)? prev.filter(i=>i!==id): [...prev,id]) : [id]);
  };

  const submit = async () => {
    if (!selected.length) return;
    try {
      setSubmitting(true);
      await onVote(localPoll.id, selected);
      // Optimistic local update
      setLocalPoll(prev => {
        const updatedOptions = prev.options.map(o => selected.includes(o.id) ? { ...o, vote_count: (o.vote_count||0) + 1 } : o);
        const newTotal = updatedOptions.reduce((a,o)=>a + (o.vote_count||0),0) || 0;
        const recomputed = updatedOptions.map(o => ({ ...o, percentage: newTotal ? Math.round((o.vote_count||0)*100/newTotal) : 0 }));
        return {
          ...prev,
            options: recomputed,
            vote_count: newTotal,
            voter_count: prev.voter_count + 1,
            user_voted: true,
            user_vote: selected,
        };
      });
    } finally { setSubmitting(false); }
  };

  return (
    <div className="mt-4 border border-gray-200 rounded-lg p-4 bg-gray-50/50">
      <h4 className="text-sm font-semibold text-gray-900 mb-3">{localPoll.question}</h4>
      <div className="space-y-2">
        {computedOptions.map(opt => {
          const chosen = selected.includes(opt.id);
          const showResults = alreadyVoted || localPoll.user_voted;
          const winning = showResults && opt.percentage === maxPct && maxPct > 0;
          return (
            <button key={opt.id} type="button" disabled={showResults && !multiple} onClick={()=>toggle(opt.id)} className={`relative w-full text-left px-3 py-2 rounded-md border text-[12px] transition ${showResults ? 'pr-10' : ''} ${showResults ? 'border-gray-200 bg-white' : chosen ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300 bg-white'} ${(showResults && !multiple)?'cursor-default':'cursor-pointer'}`}>
              {showResults && (
                <span className={`absolute inset-0 rounded-md opacity-25 ${winning ? 'bg-green-400' : 'bg-gray-400'}`} style={{ width: `${opt.percentage}%` }} />
              )}
              <span className="relative flex items-center justify-between">
                <span className={`truncate ${winning && showResults ? 'font-semibold text-green-700' : 'text-gray-800'}`}>{opt.text}</span>
                {showResults ? (
                  <span className="ml-3 flex items-center gap-2 text-[11px] text-gray-600">
                    <span>{opt.percentage}%</span>
                    <span className="text-gray-400">({opt.vote_count})</span>
                  </span>
                ) : multiple ? (
                  <input type="checkbox" readOnly checked={chosen} className="h-3.5 w-3.5 text-indigo-600 border-gray-300 rounded" />
                ) : (
                  <span className={`h-3.5 w-3.5 inline-flex items-center justify-center rounded-full border ${chosen ? 'bg-indigo-600 border-indigo-600' : 'border-gray-300'}`}>{chosen && <span className="h-1.5 w-1.5 bg-white rounded-full" />}</span>
                )}
              </span>
            </button>
          );
        })}
      </div>
      {!alreadyVoted && !localPoll.user_voted && !readonly && (
        <div className="mt-3 flex items-center justify-between">
          <button type="button" disabled={!selected.length || submitting} onClick={submit} className={`text-[11px] px-3 py-1.5 rounded-md font-medium transition ${selected.length && !submitting ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-gray-200 text-gray-500 cursor-not-allowed'}`}>{submitting ? 'Submitting...' : 'Vote'}</button>
          {multiple && <span className="text-[10px] text-gray-500">Multiple selection</span>}
        </div>
      )}
      <div className="mt-3 flex items-center justify-between text-[10px] text-gray-500 border-t pt-2">
        <span>{localPoll.vote_count} votes</span>
        <div className="flex items-center gap-2">
          {localPoll.expires_at && (
            <span>
              {localPoll.is_expired
                ? `Expired ${new Date(localPoll.expires_at).toLocaleDateString()}`
                : `Expires ${new Date(localPoll.expires_at).toLocaleString()}`
              }
            </span>
          )}
          <span>{localPoll.is_expired ? 'Expired' : 'Active'}</span>
        </div>
      </div>
    </div>
  );
};

export default PollDisplay;