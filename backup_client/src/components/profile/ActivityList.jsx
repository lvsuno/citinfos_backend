import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { UserCircleIcon, ChartBarSquareIcon, UserGroupIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';
import CommunityIcon from '../../components/ui/CommunityIcon';

const iconFor = (type) => {
  switch (type) {
    case 'poll': return <CommunityIcon Icon={ChartBarSquareIcon} size="sm" color="blue" />;
    case 'community': return <CommunityIcon Icon={UserGroupIcon} size="sm" color="purple" />;
    case 'post': return <CommunityIcon Icon={ChatBubbleLeftRightIcon} size="sm" color="green" />;
    case 'vote': return <CommunityIcon Icon={ChartBarSquareIcon} size="sm" color="indigo" />;
    default: return <CommunityIcon Icon={UserCircleIcon} size="sm" color="gray" />;
  }
};

const timeAgo = (ts) => {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
};

/* ActivityList
   Props: items: {id,type,description,created_at}[]
          loading: boolean
          skeletonCount?: number
          onLoadMore?: ()=>void (triggered when sentinel visible)
          hasMore?: boolean
*/
const ActivityList = ({ items, loading=false, skeletonCount=5, onLoadMore, hasMore=false }) => {
  const sentinelRef = useRef(null);
  useEffect(()=>{
    if (!onLoadMore || !hasMore) return;
    const el = sentinelRef.current; if (!el) return;
    const io = new IntersectionObserver(entries => {
      entries.forEach(en => { if (en.isIntersecting) onLoadMore(); });
    }, { threshold: 0.1 });
    io.observe(el);
    return ()=> io.disconnect();
  }, [onLoadMore, hasMore]);

  const Skeleton = () => (
    <div className="flex items-start gap-3 animate-pulse">
      <div className="h-5 w-5 rounded bg-gray-200" />
      <div className="flex-1 space-y-2">
        <div className="h-3 w-2/3 rounded bg-gray-200" />
        <div className="h-2 w-1/4 rounded bg-gray-200" />
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {items?.map(item => (
        <div key={item.id} className="flex items-start gap-3">
          <div className="flex-shrink-0">{iconFor(item.type)}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-800">{item.description}</p>
            <p className="text-xs text-gray-500 mt-1">{timeAgo(item.created_at)}</p>
          </div>
        </div>
      ))}
      {loading && Array.from({ length: skeletonCount }).map((_,i)=>(<Skeleton key={`sk-${i}`} />))}
      {!loading && (!items || items.length===0) && <p className="text-sm text-gray-500">No activity yet.</p>}
      {hasMore && !loading && (
        <div ref={sentinelRef} className="h-6" />
      )}
    </div>
  );
};

ActivityList.propTypes = { items: PropTypes.array };

export default ActivityList;
