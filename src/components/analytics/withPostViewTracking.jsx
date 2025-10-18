/**
 * withPostViewTracking HOC
 * Higher-Order Component that automatically adds PostViewTracker to any post component
 */

import React, { useRef, useEffect } from 'react';
import PostViewTracker from './PostViewTracker';

const withPostViewTracking = (WrappedComponent, options = {}) => {
  const TrackedPostComponent = (props) => {
    const postRef = useRef(null);
    const { postId, source, onViewTracked, onEngagement, ...restProps } = props;

    const handleViewTracked = (result) => {
      if (onViewTracked) {
        onViewTracked(result);
      }
    };

    const handleEngagement = (type, data) => {
      if (onEngagement) {
        onEngagement(type, data);
      }
    };

    return (
      <div ref={postRef}>
        <WrappedComponent {...restProps} />
        {postId && postRef.current && (
          <PostViewTracker
            postId={postId}
            postElement={postRef.current}
            source={source || 'feed'}
            onViewTracked={handleViewTracked}
            onEngagement={handleEngagement}
            {...options}
          />
        )}
      </div>
    );
  };

  TrackedPostComponent.displayName = `withPostViewTracking(${WrappedComponent.displayName || WrappedComponent.name})`;

  return TrackedPostComponent;
};

export default withPostViewTracking;
