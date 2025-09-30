import React, { useState, useMemo } from 'react';
import PollCard from '../components/PollCard';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

const mockFetchPoll = async (id) => {
  return {
    id: id || '1',
    question: 'Which features would you like next?',
    description: 'Select all that apply so we can prioritize roadmap items.',
    creator: { id: 'u1', username: 'product_team' },
    expires_at: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(),
    vote_count: 120,
    voter_count: 95,
    allows_multiple_votes: true,
    is_anonymous: false,
    options: [
      { id: 'o1', text: 'Real-time notifications', vote_count: 38, percentage: 31.7 },
      { id: 'o2', text: 'Advanced analytics', vote_count: 27, percentage: 22.5 },
      { id: 'o3', text: 'Mobile app', vote_count: 31, percentage: 25.8 },
      { id: 'o4', text: 'Dark mode', vote_count: 24, percentage: 20.0 }
    ],
    user_voted: false,
    user_vote: [],
    is_expired: false,
    time_remaining: 6 * 60 * 60 * 1000,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  };
};

const PollDetail = () => {
  const [poll, setPoll] = useState(null);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(false);

  React.useEffect(() => {
    (async () => {
      const data = await mockFetchPoll('1');
      setPoll(data);
      setLoading(false);
    })();
  }, []);

  const handleVote = async (pollId, optionIds) => {
    setVoting(true);
    // mock update percentages evenly just for UI
    setPoll(prev => {
      if (!prev) return prev;
      const updatedOptions = prev.options.map(o => optionIds.includes(o.id) ? { ...o, vote_count: o.vote_count + 1 } : o);
      const totalVotes = updatedOptions.reduce((s, o) => s + o.vote_count, 0);
      const recalced = updatedOptions.map(o => ({ ...o, percentage: totalVotes ? Number(((o.vote_count / totalVotes) * 100).toFixed(1)) : 0 }));
      return { ...prev, options: recalced, vote_count: totalVotes, voter_count: prev.voter_count + 1, user_voted: true, user_vote: optionIds };
    });
    setTimeout(() => setVoting(false), 400);
  };

  const stats = useMemo(() => {
    if (!poll) return null;
    return [
      { label: 'Total Votes', value: poll.vote_count },
      { label: 'Voters', value: poll.voter_count },
      { label: 'Options', value: poll.options.length },
      { label: 'Multiple Votes', value: poll.allows_multiple_votes ? 'Yes' : 'No' },
      { label: 'Anonymous', value: poll.is_anonymous ? 'Yes' : 'No' },
    ];
  }, [poll]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>
    );
  }

  if (!poll) return null;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Poll Detail</h1>
          <p className="text-gray-600">View poll statistics and participate</p>
        </div>
        <button onClick={() => { setLoading(true); mockFetchPoll(poll.id).then(p => { setPoll(p); setLoading(false); }); }} className="inline-flex items-center px-4 py-2 rounded-md bg-white border text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm">
          <ArrowPathIcon className="h-4 w-4 mr-2" /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <PollCard poll={poll} onVote={handleVote} isVoting={voting} />
        </div>
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Poll Stats</h2>
            <dl className="grid grid-cols-2 gap-4">
              {stats.map(s => (
                <div key={s.label} className="bg-gray-50 rounded-md p-3 border border-gray-100">
                  <dt className="text-xs uppercase tracking-wide text-gray-500">{s.label}</dt>
                  <dd className="mt-1 text-sm font-semibold text-gray-900">{s.value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Guidelines</h2>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              <li>Be respectful and constructive.</li>
              <li>Vote honestly based on your preference.</li>
              <li>Multiple selection is allowed if enabled.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PollDetail;
