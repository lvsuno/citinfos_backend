import React, { useState, useMemo } from 'react';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import PollCard from '../components/PollCard';

// Utility to create option ids
const uid = () => Math.random().toString(36).slice(2, 10);

const CreatePoll = () => {
  const [question, setQuestion] = useState('');
  const [description, setDescription] = useState('');
  const [options, setOptions] = useState([
    { id: uid(), text: '' },
    { id: uid(), text: '' }
  ]);
  const [allowsMultipleVotes, setAllowsMultipleVotes] = useState(false);
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [expiresInHours, setExpiresInHours] = useState(24);
  const [submitting, setSubmitting] = useState(false);
  const [createdPolls, setCreatedPolls] = useState([]);

  const handleOptionChange = (id, value) => {
    setOptions(prev => prev.map(o => o.id === id ? { ...o, text: value } : o));
  };
  const addOption = () => setOptions(prev => [...prev, { id: uid(), text: '' }]);
  const removeOption = (id) => {
    if (options.length <= 2) return; // keep minimum 2
    setOptions(prev => prev.filter(o => o.id !== id));
  };

  const canSubmit = question.trim() && options.filter(o => o.text.trim()).length >= 2 && !submitting;

  const previewPoll = useMemo(() => {
    const now = Date.now();
    const exp = now + expiresInHours * 60 * 60 * 1000;
    return {
      id: 'preview',
      question: question || 'Your poll question…',
      description: description || '',
      creator: { id: 'current', username: 'you' },
      expires_at: new Date(exp).toISOString(),
      vote_count: 0,
      voter_count: 0,
      allows_multiple_votes: allowsMultipleVotes,
      is_anonymous: isAnonymous,
      options: options.filter(o => o.text.trim()).map(o => ({ id: o.id, text: o.text.trim() || 'Option', vote_count: 0, percentage: 0 })),
      user_voted: false,
      user_vote: [],
      is_expired: false,
      time_remaining: exp - now,
      created_at: new Date(now).toISOString(),
    };
  }, [question, description, options, allowsMultipleVotes, isAnonymous, expiresInHours]);

  const resetForm = () => {
    setQuestion('');
    setDescription('');
    setOptions([{ id: uid(), text: '' }, { id: uid(), text: '' }]);
    setAllowsMultipleVotes(false);
    setIsAnonymous(false);
    setExpiresInHours(24);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      // Mock create
      const newPoll = { ...previewPoll, id: `poll-${Date.now()}` };
      setCreatedPolls(prev => [newPoll, ...prev]);
      resetForm();
    } finally {
      setSubmitting(false);
    }
  };

  const handleVotePreview = () => {};

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Create Poll</h1>
          <p className="text-gray-600">Compose a new poll for the community</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form */}
        <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-6 bg-white rounded-lg shadow p-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Question *</label>
            <input value={question} onChange={(e) => setQuestion(e.target.value)} required maxLength={200} placeholder="What do you want to ask?" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500" />
            <p className="mt-1 text-xs text-gray-500">{question.length}/200</p>
          </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
              <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} maxLength={500} placeholder="Provide more context..." className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500" />
              <p className="mt-1 text-xs text-gray-500">{description.length}/500</p>
            </div>

          {/* Options */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">Options *</label>
              <button type="button" onClick={addOption} className="inline-flex items-center text-xs px-2 py-1 rounded-md bg-blue-50 text-blue-600 hover:bg-blue-100"><PlusIcon className="h-4 w-4 mr-1" /> Add</button>
            </div>
            <div className="space-y-3">
              {options.map((opt, idx) => (
                <div key={opt.id} className="flex items-center gap-2">
                  <input value={opt.text} onChange={(e) => handleOptionChange(opt.id, e.target.value)} required={idx < 2} placeholder={`Option ${idx + 1}`} maxLength={150} className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500" />
                  {options.length > 2 && (
                    <button type="button" onClick={() => removeOption(opt.id)} className="p-2 text-gray-400 hover:text-red-600" title="Remove option"><TrashIcon className="h-5 w-5" /></button>
                  )}
                </div>
              ))}
            </div>
            <p className="mt-1 text-xs text-gray-500">Minimum 2 options. Empty options are ignored.</p>
          </div>

          {/* Settings */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200 flex items-start">
              <input id="multiple" type="checkbox" checked={allowsMultipleVotes} onChange={(e) => setAllowsMultipleVotes(e.target.checked)} className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
              <label htmlFor="multiple" className="ml-3 text-sm">
                <span className="font-medium text-gray-900 block">Multiple Votes</span>
                <span className="text-gray-500">Allow users to select more than one option.</span>
              </label>
            </div>
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200 flex items-start">
              <input id="anonymous" type="checkbox" checked={isAnonymous} onChange={(e) => setIsAnonymous(e.target.checked)} className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500" />
              <label htmlFor="anonymous" className="ml-3 text-sm">
                <span className="font-medium text-gray-900 block">Anonymous</span>
                <span className="text-gray-500">Hide voter identities.</span>
              </label>
            </div>
            <div className="bg-gray-50 rounded-md p-4 border border-gray-200">
              <label className="block text-sm font-medium text-gray-700 mb-1">Expires In (hours)</label>
              <input type="number" min={1} max={24 * 30} value={expiresInHours} onChange={(e) => setExpiresInHours(Number(e.target.value) || 1)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500" />
              <p className="mt-1 text-xs text-gray-500">When poll voting closes.</p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button type="button" onClick={resetForm} className="px-4 py-2 rounded-md border text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">Reset</button>
            <button disabled={!canSubmit} type="submit" className={`px-4 py-2 rounded-md text-sm font-medium text-white ${canSubmit ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}`}>{submitting ? 'Creating...' : 'Create Poll'}</button>
          </div>
        </form>

        {/* Live Preview */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold text-gray-700 tracking-wide uppercase">Preview</h2>
          <div className="sticky top-4">
            <PollCard poll={previewPoll} onVote={handleVotePreview} />
          </div>
        </div>
      </div>

      {createdPolls.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Recently Created (Session)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {createdPolls.map(p => <PollCard key={p.id} poll={p} onVote={() => {}} />)}
          </div>
        </div>
      )}
    </div>
  );
};

export default CreatePoll;
