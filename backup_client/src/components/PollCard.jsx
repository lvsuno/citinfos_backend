import React, { useState } from 'react';
import { ChartBarIcon, UserIcon, ClockIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';
import clsx from 'clsx';
import PropTypes from 'prop-types';

const PollCard = ({ poll, onVote, isVoting = false }) => {
  const [selectedOptions, setSelectedOptions] = useState(poll.user_vote || []);
  const [hasVoted, setHasVoted] = useState(poll.user_voted || false);

  const handleOptionChange = (optionId) => {
    if (hasVoted && !(poll.allows_multiple_votes || false)) return;

    if (poll.allows_multiple_votes || false) {
      setSelectedOptions(prev =>
        prev.includes(optionId)
          ? prev.filter(id => id !== optionId)
          : [...prev, optionId]
      );
    } else {
      setSelectedOptions([optionId]);
    }
  };

  const handleVote = () => {
    if (selectedOptions.length > 0) {
      onVote(poll.id, selectedOptions);
      setHasVoted(true);
    }
  };

  const getMaxPercentage = () => Math.max(...poll.options.map(option => option.percentage));
  const maxPercentage = getMaxPercentage();

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      {/* Poll Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
            {poll.creator?.avatar ? (
              <img
                src={poll.creator.avatar}
                alt={poll.creator.username}
                className="h-10 w-10 rounded-full"
              />
            ) : (
              <UserIcon className="h-6 w-6 text-white" />
            )}
          </div>
          <div>
            <p className="font-medium text-gray-900">{poll.creator?.username}</p>
            <p className="text-sm text-gray-500">
              {poll.created_at ? formatDistanceToNow(new Date(poll.created_at), { addSuffix: true }) : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <ChartBarIcon className="h-4 w-4" />
            <span>{poll.voter_count} voters</span>
        </div>
      </div>

      {/* Poll Question */}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{poll.question}</h3>
      {poll.description && <p className="text-gray-600 mb-4">{poll.description}</p>}

      {/* Poll Options */}
      <div className="space-y-3 mb-4">
        {poll.options.map(option => {
          const isSelected = selectedOptions.includes(option.id);
          const isWinning = option.percentage === maxPercentage && maxPercentage > 0;
          return (
            <div
              key={option.id}
              className={clsx(
                'relative p-3 border rounded-lg cursor-pointer transition-all',
                {
                  'border-blue-500 bg-blue-50': isSelected && !hasVoted,
                  'border-gray-200 hover:border-gray-300': !isSelected && !hasVoted,
                  'border-gray-200': hasVoted,
                  'cursor-not-allowed': hasVoted && !poll.allows_multiple_votes,
                }
              )}
              onClick={() => !(poll.is_expired || false) && handleOptionChange(option.id)}
            >
              {(hasVoted || (poll.is_expired || false)) && (
                <div
                  className={clsx('absolute inset-0 rounded-lg transition-all', {
                    'bg-green-100': isWinning,
                    'bg-gray-100': !isWinning,
                  })}
                  style={{ width: `${option.percentage}%`, opacity: 0.3 }}
                />
              )}

              <div className="relative flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {!hasVoted && !(poll.is_expired || false) && (
                    <input
                      type={(poll.allows_multiple_votes || false) ? 'checkbox' : 'radio'}
                      name={`poll-${poll.id}`}
                      checked={isSelected}
                      onChange={() => handleOptionChange(option.id)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                  )}
                  <span
                    className={clsx('font-medium', {
                      'text-green-700': isWinning && (hasVoted || (poll.is_expired || false)),
                      'text-gray-900': !isWinning || (!hasVoted && !(poll.is_expired || false)),
                    })}
                  >
                    {option.text}
                  </span>
                </div>

                {(hasVoted || (poll.is_expired || false)) && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-700">{option.percentage || 0}%</span>
                    <span className="text-sm text-gray-500">({option.vote_count || 0} votes)</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Poll Actions */}
      {!hasVoted && !(poll.is_expired || false) && (
        <div className="flex items-center justify-between">
          <button
            onClick={handleVote}
            disabled={selectedOptions.length === 0 || isVoting}
            className={clsx('px-4 py-2 rounded-md font-medium transition-colors', {
              'bg-blue-600 text-white hover:bg-blue-700': selectedOptions.length > 0 && !isVoting,
              'bg-gray-300 text-gray-500 cursor-not-allowed': selectedOptions.length === 0 || isVoting,
            })}
          >
            {isVoting ? 'Voting...' : 'Vote'}
          </button>
          {(poll.allows_multiple_votes || false) && <span className="text-sm text-gray-500">Multiple selections allowed</span>}
        </div>
      )}

      {/* Poll Status */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200 mt-4">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <span>{poll.vote_count || 0} total votes</span>
          {(poll.is_anonymous || false) && <span>Anonymous voting</span>}
        </div>
        <div className="flex items-center space-x-2 text-sm">
          <ClockIcon className="h-4 w-4 text-gray-400" />
          {(poll.is_expired || false) ? (
            <span className="text-red-600">Expired</span>
          ) : (
            <span className="text-gray-500">Expires {poll.expires_at ? formatDistanceToNow(new Date(poll.expires_at), { addSuffix: true }) : ''}</span>
          )}
        </div>
      </div>
    </div>
  );
};

PollCard.propTypes = {
  poll: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    question: PropTypes.string.isRequired,
    description: PropTypes.string,
    creator: PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      username: PropTypes.string,
      avatar: PropTypes.string,
    }),
    expires_at: PropTypes.string,
    vote_count: PropTypes.number,
    voter_count: PropTypes.number,
    allows_multiple_votes: PropTypes.bool,
    is_anonymous: PropTypes.bool,
    options: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
        text: PropTypes.string.isRequired,
        vote_count: PropTypes.number,
        percentage: PropTypes.number,
      })
    ).isRequired,
    user_voted: PropTypes.bool,
    user_vote: PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.number])),
    is_expired: PropTypes.bool,
  }).isRequired,
  onVote: PropTypes.func.isRequired,
  isVoting: PropTypes.bool,
};

export default PollCard;
