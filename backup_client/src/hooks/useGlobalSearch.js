import { useQuery } from 'react-query';
import { searchService } from '../services/searchService';
import { useJWTAuth } from '../services/jwtAuthService';

/**
 * Hook for performing global search across all content types
 * @param {string} query - Search query string
 * @param {string} type - Content type filter ('all', 'posts', 'users', 'equipment', 'communities')
 * @param {object} options - Additional search options
 * @returns {object} Query result with search data, loading state, and error
 */
export function useGlobalSearch(query, type = 'all', options = {}) {
  const { isAuthenticated } = useJWTAuth();

  const {
    limit = 20,
    offset = 0,
    filters = {},
    enabled = true
  } = options;

  return useQuery(
    ['global-search', query, type, limit, offset, filters, isAuthenticated],
    async () => {
      // Don't search if query is empty or too short
      if (!query || query.trim().length < 1) {
        return getEmptyResults(query, type);
      }

      try {
        // Map type to content types array
        const contentTypes = getContentTypesFromFilter(type);

        const searchOptions = {
          contentTypes,
          limit,
          offset,
          filters
        };

        const results = await searchService.globalSearch(query, searchOptions);
        return formatResultsForComponent(results, type);
      } catch (error) {
        console.error('Search hook error:', error);

        // Handle authentication errors gracefully
        if (error.message?.includes('Authentication required')) {
          // For unauthenticated users, return limited results or empty
          return getEmptyResults(query, type, 'Authentication required for search');
        }

        // For other errors, return empty results with error message
        return getEmptyResults(query, type, error.message);
      }
    },
    {
      enabled: enabled && typeof query === 'string' && query.trim().length > 0,
      staleTime: 5 * 1000, // 5 seconds
      cacheTime: 10 * 60 * 1000, // 10 minutes
      keepPreviousData: true,
      retry: (failureCount, error) => {
        // Don't retry on authentication errors
        if (error?.message?.includes('Authentication required')) {
          return false;
        }
        // Retry up to 2 times for other errors
        return failureCount < 2;
      }
    }
  );
}

/**
 * Hook for quick search/autocomplete functionality
 * @param {string} query - Search query string
 * @param {number} limit - Maximum results (default: 10)
 * @returns {object} Query result with quick search data
 */
export function useQuickSearch(query, limit = 10) {
  const { isAuthenticated } = useJWTAuth();

  return useQuery(
    ['quick-search', query, limit, isAuthenticated],
    async () => {
      if (!query || query.trim().length < 2) {
        return { suggestions: [], total: 0 };
      }

      try {
        const results = await searchService.quickSearch(query, limit);
        return {
          suggestions: results.suggestions || [],
          total: results.total || 0,
          query: results.query || query
        };
      } catch (error) {
        console.error('Quick search error:', error);
        return { suggestions: [], total: 0, error: error.message };
      }
    },
    {
      enabled: typeof query === 'string' && query.trim().length >= 2,
      staleTime: 2 * 1000, // 2 seconds
      cacheTime: 5 * 60 * 1000, // 5 minutes
      keepPreviousData: true
    }
  );
}

/**
 * Map frontend type filter to backend content types array
 */
function getContentTypesFromFilter(type) {
  switch (type) {
    case 'posts':
      return ['posts'];
    case 'users':
      return ['users'];
    case 'equipment':
      return ['equipment'];
    case 'communities':
      return ['communities'];
    case 'messages':
      return ['messages'];
    case 'polls':
      return ['polls'];
    case 'ai_conversations':
      return ['ai_conversations'];
    case 'all':
    default:
      return ['posts', 'users', 'equipment', 'communities', 'messages', 'polls', 'ai_conversations'];
  }
}

/**
 * Format search results for the SearchResults component
 */
function formatResultsForComponent(searchResults, type) {
  const { results, counts, total_count, query } = searchResults;

  // Format results to match the component's expectations
  const formattedResults = {
    query,
    type,
    total: total_count,
    results: {
      posts: results.posts || [],
      users: results.users || [],
      equipment: results.equipment || [],
      communities: results.communities || [],
      messages: results.messages || [],
      polls: results.polls || [],
      ai_conversations: results.ai_conversations || []
    },
    counts: counts || {}
  };

  return formattedResults;
}

/**
 * Get empty search results structure
 */
function getEmptyResults(query, type, errorMessage = null) {
  return {
    query: query || '',
    type,
    total: 0,
    results: {
      posts: [],
      users: [],
      equipment: [],
      communities: [],
      messages: [],
      polls: [],
      ai_conversations: []
    },
    counts: {
      posts: 0,
      users: 0,
      equipment: 0,
      communities: 0,
      messages: 0,
      polls: 0,
      ai_conversations: 0
    },
    error: errorMessage
  };
}

/**
 * Simple debounced helper for search input
 */
export function debounce(fn, delay = 300) {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}
