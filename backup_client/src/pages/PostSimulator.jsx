import React, { useState } from 'react';
import { PlusIcon, PaperAirplaneIcon, PhotoIcon } from '@heroicons/react/24/outline';
import PostCard from '../components/social/PostCard';

const uid = () => Math.random().toString(36).slice(2,10);

const initialPosts = [
  { id: 'post-1', content: 'Just set up a new equipment monitoring dashboard! #productivity', author: { id: 'u1', username: 'john_dev', avatar: '' }, visibility: 'public', created_at: Date.now() - 1000*60*25, likes_count: 3, dislikes_count: 0, comments_count: 1, shares_count: 0, is_liked: false, is_disliked: false, community: null, comments: [ { id: 'c1', author: { id: 'u2', username: 'sarah_frontend' }, content: 'Nice work!', created_at: Date.now() - 1000*60*10 } ] },
  { id: 'post-2', content: 'Which feature should we build next? @you #roadmap', author: { id: 'u2', username: 'sarah_frontend', avatar: '' }, visibility: 'public', created_at: Date.now() - 1000*60*60*3, likes_count: 5, dislikes_count: 1, comments_count: 2, shares_count: 1, is_liked: true, is_disliked: false, community: { id: 'c1', name: 'Tech Enthusiasts' }, comments: [ { id: 'c2', author: { id: 'u1', username: 'john_dev' }, content: 'Add bulk editing!', created_at: Date.now() - 1000*60*20 }, { id: 'c3', author: { id: 'u3', username: 'charlie' }, content: 'Dark mode please', created_at: Date.now() - 1000*60*15 } ] },
];

const timeAgo = (ts) => { const diff = Date.now() - ts; const m = Math.floor(diff/60000); if (m<1) return 'Just now'; if (m<60) return m+'m'; const h=Math.floor(m/60); if(h<24) return h+'h'; const d=Math.floor(h/24); return d+'d'; };

const PostSimulator = () => {
  const [posts, setPosts] = useState(initialPosts);
  const [postForm, setPostForm] = useState({ content: '', visibility: 'public' });
  const [showComposer, setShowComposer] = useState(false);

  const handleCreatePost = (e) => {
    e.preventDefault();
    if(!postForm.content.trim()) return;
    const newPost={ id: uid(), content: postForm.content.trim(), author:{ id:'current', username:'you' }, visibility: postForm.visibility, created_at: Date.now(), likes_count:0, dislikes_count:0, comments_count:0, shares_count:0, is_liked:false, is_disliked:false, community:null, comments:[] };
    setPosts(p=>[newPost,...p]);
    setPostForm({ content:'', visibility:'public'});
    setShowComposer(false);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Post Simulator</h1>
          <p className="text-gray-600">Prototype social posting interactions</p>
        </div>
        <button onClick={()=>setShowComposer(s=>!s)} className="inline-flex items-center px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm"><PlusIcon className="h-4 w-4 mr-2" /> {showComposer ? 'Close Composer':'New Post'}</button>
      </div>
      {showComposer && (
        <form onSubmit={handleCreatePost} className="bg-white rounded-lg shadow p-6 space-y-4">
          <div>
            <textarea value={postForm.content} onChange={e=>setPostForm(f=>({...f, content:e.target.value}))} rows={3} placeholder="What's on your mind? Use @username or #hashtag" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm" />
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
            <div className="flex items-center gap-3">
              <select value={postForm.visibility} onChange={e=>setPostForm(f=>({...f, visibility:e.target.value}))} className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500">
                <option value="public">Public</option>
                <option value="community">Community</option>
                <option value="private">Private</option>
              </select>
              <button type="button" className="p-2 rounded-md text-gray-500 hover:text-blue-600 hover:bg-blue-50" title="Add image"><PhotoIcon className="h-5 w-5" /></button>
            </div>
            <div className="flex items-center gap-3">
              <button type="submit" disabled={!postForm.content.trim()} className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white ${postForm.content.trim() ? 'bg-blue-600 hover:bg-blue-700':'bg-gray-400 cursor-not-allowed'}`}><PaperAirplaneIcon className="h-4 w-4 mr-2" /> Post</button>
            </div>
          </div>
        </form>
      )}
      <div className="space-y-6">
        {posts.map(p => (
          <PostCard key={p.id} post={p} onDelete={(id)=>setPosts(prev=>prev.filter(po=>po.id!==id))} onUpdate={(id,patch)=>setPosts(prev=>prev.map(po=>po.id===id?{...po,...patch}:po))} onVote={(pollId, optionIds)=>{}} />
        ))}
        {posts.length===0 && <div className="text-center py-12 bg-white rounded-lg shadow text-gray-500">No posts yet.</div>}
      </div>
    </div>
  );
};

export default PostSimulator;
