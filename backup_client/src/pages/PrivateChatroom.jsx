import React, { useState } from 'react';
import { UserCircleIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { UsersIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/solid';

const mockUsers = [
  { id: 'u1', username: 'alice', status: 'online', last_active: Date.now() - 1000 * 60 },
  { id: 'u2', username: 'bob', status: 'away', last_active: Date.now() - 1000 * 60 * 8 },
  { id: 'u3', username: 'charlie', status: 'offline', last_active: Date.now() - 1000 * 60 * 60 },
];

const mockInitialMessages = {
  u1: [ { id: 'm1', sender: 'alice', content: 'Hey there! Need help with your equipment setup?', created_at: Date.now() - 1000 * 60 * 5 } ],
  u2: [],
  u3: []
};

const statusColor = (s) => ({ online: 'bg-green-500', away: 'bg-yellow-500', offline: 'bg-gray-400' }[s] || 'bg-gray-400');

const PrivateChatroom = () => {
  const [users] = useState(mockUsers);
  // Group chat additions
  const initialGroups = [
    { id: 'g1', name: 'Core Team', memberIds: ['u1','u2','u3'] },
  ];
  const [groups, setGroups] = useState(initialGroups);
  const [activeTarget, setActiveTarget] = useState({ type: 'user', id: users[0].id }); // {type:'user'|'group', id}
  const [messages, setMessages] = useState(mockInitialMessages);
  const [groupMessages, setGroupMessages] = useState({ g1: [ { id: 'gm1', sender: 'alice', content: 'Welcome to the Core Team group!', created_at: Date.now() - 1000*60*20 } ] });
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [typing, setTyping] = useState(false);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupMembers, setNewGroupMembers] = useState([]); // array of user ids
  const [searchUser, setSearchUser] = useState('');
  const [showManageGroup, setShowManageGroup] = useState(false);
  const [groupTyping, setGroupTyping] = useState({}); // { groupId: true }
  const [addMembersSelection, setAddMembersSelection] = useState([]);

  const currentUserId = 'u1'; // simulate logged-in user

  const activeUser = activeTarget.type === 'user' ? users.find(u => u.id === activeTarget.id) : null;
  const activeGroup = activeTarget.type === 'group' ? groups.find(g => g.id === activeTarget.id) : null;

  const currentMessages = activeTarget.type === 'user'
    ? (messages[activeUser?.id] || [])
    : (groupMessages[activeGroup?.id] || []);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setSending(true);
    const text = input.trim();
    setInput('');
    const newMsg = { id: `m-${Date.now()}`, sender: 'you', content: text, created_at: Date.now() };
    if (activeTarget.type === 'user' && activeUser) {
      setMessages(prev => ({ ...prev, [activeUser.id]: [...(prev[activeUser.id] || []), newMsg] }));
      setTimeout(() => {
        const reply = { id: `m-${Date.now()}-r`, sender: activeUser.username, content: 'Got it! (mock reply)', created_at: Date.now() };
        setMessages(prev => ({ ...prev, [activeUser.id]: [...(prev[activeUser.id] || []), reply] }));
        setSending(false);
      }, 900);
    } else if (activeTarget.type === 'group' && activeGroup) {
      setGroupMessages(prev => ({ ...prev, [activeGroup.id]: [...(prev[activeGroup.id] || []), newMsg] }));
      setGroupTyping(prev => ({ ...prev, [activeGroup.id]: true }));
      setTimeout(() => {
        const reply = { id: `gm-${Date.now()}-r`, sender: 'system', content: 'Mock group echo', created_at: Date.now() };
        setGroupMessages(prev => ({ ...prev, [activeGroup.id]: [...(prev[activeGroup.id] || []), reply] }));
        setSending(false);
        setGroupTyping(prev => ({ ...prev, [activeGroup.id]: false }));
      }, 700);
    }
  };

  const handleInput = (e) => {
    setInput(e.target.value);
    if (!typing) setTyping(true);
    setTimeout(() => setTyping(false), 1200);
  };

  const toggleMember = (uid) => {
    setNewGroupMembers(prev => prev.includes(uid) ? prev.filter(x => x !== uid) : [...prev, uid]);
  };

  const createGroup = (e) => {
    e.preventDefault();
    const name = newGroupName.trim();
    if (!name || newGroupMembers.length === 0) return;
    const id = `g-${Date.now()}`;
    setGroups(prev => [{ id, name, memberIds: newGroupMembers.slice() }, ...prev]);
    setGroupMessages(prev => ({ ...prev, [id]: [{ id: `gm-${Date.now()}`, sender: 'system', content: `Group '${name}' created`, created_at: Date.now() }] }));
    setShowCreateGroup(false);
    setNewGroupName('');
    setNewGroupMembers([]);
    setActiveTarget({ type: 'group', id });
  };

  const isActiveTarget = (target) => activeTarget.type === target.type && activeTarget.id === target.id;

  const leaveGroup = (groupId) => {
    setGroups(prev => prev.map(g => g.id === groupId ? { ...g, memberIds: g.memberIds.filter(id => id !== currentUserId) } : g).filter(g => g.memberIds.length > 0));
    if (activeTarget.type === 'group' && activeTarget.id === groupId) {
      setActiveTarget({ type: 'user', id: users[0].id });
    }
    setShowManageGroup(false);
  };

  const addMembersToGroup = (groupId) => {
    if (addMembersSelection.length === 0) return;
    setGroups(prev => prev.map(g => g.id === groupId ? { ...g, memberIds: Array.from(new Set([...g.memberIds, ...addMembersSelection])) } : g));
    setAddMembersSelection([]);
  };

  const toggleAddMember = (uid) => {
    setAddMembersSelection(prev => prev.includes(uid) ? prev.filter(x => x !== uid) : [...prev, uid]);
  };

  const filteredUsers = users.filter(u => u.username.toLowerCase().includes(searchUser.toLowerCase()));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Private Chat</h1>
          <p className="text-gray-600">Direct & group conversations</p>
        </div>
        <button onClick={() => setShowCreateGroup(true)} className="inline-flex items-center px-4 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium shadow-sm"><PlusIcon className="h-4 w-4 mr-2" /> New Group</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 bg-white rounded-lg shadow p-4 flex flex-col max-h-[70vh]">
          <h2 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Direct Messages</h2>
          <div className="mb-2">
            <input value={searchUser} onChange={(e)=>setSearchUser(e.target.value)} placeholder="Search user..." className="w-full px-2 py-1.5 rounded-md border border-gray-300 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div className="space-y-2 overflow-y-auto pr-1 mb-4">
            {filteredUsers.map(u => (
              <button key={u.id} onClick={() => setActiveTarget({ type: 'user', id: u.id })} className={`w-full text-left p-3 rounded-md border text-sm transition flex items-center gap-3 ${isActiveTarget({ type:'user', id: u.id }) ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-white border-gray-200 hover:bg-gray-50'}`}>
                <div className="relative">
                  <UserCircleIcon className="h-8 w-8 text-gray-400" />
                  <span className={`absolute bottom-0 right-0 h-3 w-3 rounded-full ring-2 ring-white ${statusColor(u.status)}`}></span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{u.username}</p>
                  <p className="text-[10px] text-gray-500">{u.status}</p>
                </div>
              </button>
            ))}
            {filteredUsers.length === 0 && <p className="text-xs text-gray-500">No users found.</p>}
          </div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wide">Groups</h2>
          <div className="space-y-2 overflow-y-auto pr-1">
            {groups.map(g => (
              <button key={g.id} onClick={() => setActiveTarget({ type: 'group', id: g.id })} className={`w-full text-left p-3 rounded-md border text-sm transition flex items-center gap-3 ${isActiveTarget({ type:'group', id: g.id }) ? 'bg-indigo-50 border-indigo-200 text-indigo-700' : 'bg-white border-gray-200 hover:bg-gray-50'}`}>
                <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600"><UsersIcon className="h-5 w-5" /></div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{g.name}</p>
                  <p className="text-[10px] text-gray-500">{g.memberIds.length} members</p>
                </div>
              </button>
            ))}
            {groups.length === 0 && <p className="text-xs text-gray-500">No groups.</p>}
          </div>
        </div>

        {/* Active Chat */}
        <div className="lg:col-span-3 bg-white rounded-lg shadow flex flex-col h-[70vh]">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            {activeTarget.type === 'group' && activeGroup ? (
              <div className="flex items-center gap-3">
                <div>
                  <h2 className="font-semibold text-gray-900 text-lg">{activeGroup.name}</h2>
                  <p className="text-xs text-gray-500">Members: {activeGroup.memberIds.length}</p>
                </div>
                <button onClick={()=>setShowManageGroup(true)} className="text-xs px-2 py-1 rounded-md border bg-white hover:bg-gray-50">Manage</button>
              </div>
            ) : activeTarget.type === 'user' && activeUser && (
              <div>
                <h2 className="font-semibold text-gray-900 text-lg">{activeUser.username}</h2>
                <p className="text-xs text-gray-500">Status: {activeUser.status}</p>
              </div>
            )}
          </div>
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {currentMessages.map(m => (
              <div key={m.id} className={`flex ${m.sender === 'you' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[70%] rounded-lg px-4 py-3 text-sm leading-relaxed shadow ${m.sender === 'you' ? 'bg-blue-600 text-white' : (m.sender === 'system' ? 'bg-gray-200 text-gray-700 italic' : 'bg-gray-100 text-gray-800')}`}>{m.content}</div>
              </div>
            ))}
            {typing && activeTarget.type==='user' && activeUser && <div className="flex justify-start"><div className="px-3 py-2 rounded-lg bg-gray-100 text-xs text-gray-500 animate-pulse">{activeUser.username} is typing...</div></div>}
            {currentMessages.length === 0 && !typing && <div className="h-full flex items-center justify-center text-sm text-gray-500">No messages yet. Say hi!</div>}
            {groupTyping[activeGroup?.id] && <div className="flex justify-start"><div className="px-3 py-2 rounded-lg bg-gray-100 text-xs text-gray-500 animate-pulse">Several members are typing...</div></div>}
          </div>
          <form onSubmit={handleSend} className="border-t border-gray-100 p-4">
            <div className="flex items-end gap-3">
              <textarea disabled={!activeTarget} value={input} onChange={handleInput} rows={1} placeholder={activeTarget.type==='user' && activeUser ? `Message ${activeUser.username}...` : activeTarget.type==='group' && activeGroup ? `Message #${activeGroup.name}` : 'Select a chat'} className="flex-1 resize-none px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm" />
              <button disabled={!input.trim() || sending} type="submit" className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white ${(input.trim() && !sending) ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-400 cursor-not-allowed'}`}><PaperAirplaneIcon className="h-4 w-4 mr-2" /> {sending ? 'Sending...' : 'Send'}</button>
            </div>
          </form>
        </div>
      </div>
      {showManageGroup && activeGroup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={()=>setShowManageGroup(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Manage Group</h3>
              <button type="button" onClick={()=>setShowManageGroup(false)} className="text-gray-400 hover:text-gray-600"><XMarkIcon className="h-5 w-5" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Current Members</p>
                <div className="flex flex-wrap gap-2">
                  {activeGroup.memberIds.map(uid => {
                    const u = users.find(x => x.id === uid);
                    return <span key={uid} className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">{u?u.username:uid}</span>;
                  })}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-1">Add Members</p>
                <div className="max-h-40 overflow-y-auto border rounded-md divide-y">
                  {users.filter(u=>!activeGroup.memberIds.includes(u.id)).map(u => (
                    <label key={u.id} className="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" checked={addMembersSelection.includes(u.id)} onChange={()=>toggleAddMember(u.id)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                      <span className="flex-1">{u.username}</span>
                      <span className={`h-2.5 w-2.5 rounded-full ${statusColor(u.status)}`}></span>
                    </label>
                  ))}
                  {users.filter(u=>!activeGroup.memberIds.includes(u.id)).length === 0 && <p className="text-xs text-gray-500 px-3 py-2">No users to add.</p>}
                </div>
                <button type="button" onClick={()=>addMembersToGroup(activeGroup.id)} disabled={addMembersSelection.length===0} className="mt-2 px-3 py-1.5 rounded-md text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">Add Selected</button>
              </div>
              <div className="pt-2 border-t">
                <button type="button" onClick={()=>leaveGroup(activeGroup.id)} className="px-3 py-2 rounded-md text-xs font-medium bg-red-50 text-red-700 hover:bg-red-100 border border-red-200">Leave Group</button>
              </div>
            </div>
          </div>
        </div>
      )}
      {showCreateGroup && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30" onClick={() => setShowCreateGroup(false)} />
          <form onSubmit={createGroup} className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">New Group</h3>
              <button type="button" onClick={() => setShowCreateGroup(false)} className="text-gray-400 hover:text-gray-600"><XMarkIcon className="h-5 w-5" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Group Name</label>
                <input value={newGroupName} onChange={(e) => setNewGroupName(e.target.value)} className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-sm" placeholder="e.g. Project Alpha" />
              </div>
              <div>
                <p className="block text-sm font-medium text-gray-700 mb-1">Members</p>
                <div className="max-h-40 overflow-y-auto border rounded-md divide-y">
                  {users.map(u => (
                    <label key={u.id} className="flex items-center gap-2 px-3 py-2 text-sm cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" checked={newGroupMembers.includes(u.id)} onChange={() => toggleMember(u.id)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                      <span className="flex-1">{u.username}</span>
                      <span className={`h-2.5 w-2.5 rounded-full ${statusColor(u.status)}`}></span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setShowCreateGroup(false)} className="px-4 py-2 rounded-md border text-sm font-medium bg-white hover:bg-gray-50 text-gray-700">Cancel</button>
              <button type="submit" disabled={!newGroupName.trim() || newGroupMembers.length===0} className="px-4 py-2 rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">Create</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default PrivateChatroom;
