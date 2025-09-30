import React, { useState, useEffect } from 'react';
import { ChatBubbleLeftRightIcon, CpuChipIcon, PaperAirplaneIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

const mockConversations = [
	{
		id: 'c1',
		title: 'Optimize equipment maintenance schedule',
		created_at: Date.now() - 1000 * 60 * 60,
		messages: [
			{
				role: 'user',
				content: 'How can I optimize maintenance tasks across all homes?',
			},
			{
				role: 'assistant',
				content:
					'You can group similar equipment by maintenance frequency and create a rotating schedule...',
			},
		],
	},
	{
		id: 'c2',
		title: 'Draft a community welcome message',
		created_at: Date.now() - 1000 * 60 * 60 * 5,
		messages: [
			{
				role: 'user',
				content: 'Write a friendly welcome message for new community members.',
			},
			{
				role: 'assistant',
				content: 'Welcome to our community! We are excited to have you...',
			},
		],
	},
];

// Mock agents (can be replaced with API data later)
const mockAgents = [
	{
		id: 'a1',
		name: 'General Assistant',
		model: 'gpt-4',
		description: 'Versatile AI assistant for general questions and tasks',
		system_prompt: 'You are a helpful AI assistant.',
		temperature: 0.7,
	},
	{
		id: 'a2',
		name: 'Equipment Expert',
		model: 'gpt-4',
		description: 'Specialized in equipment maintenance & troubleshooting',
		system_prompt: 'You are an expert in equipment management and maintenance.',
		temperature: 0.3,
	},
	{
		id: 'a3',
		name: 'Code Assistant',
		model: 'claude-3-sonnet',
		description: 'Focused on programming, code review & technical docs',
		system_prompt: 'You are a precise senior software engineer.',
		temperature: 0.2,
	},
];

const AIConversations = () => {
	const [conversations, setConversations] = useState(mockConversations);
	const [activeId, setActiveId] = useState(conversations[0]?.id || null);
	const [input, setInput] = useState('');
	const [creating, setCreating] = useState(false);
	const [isNewModalOpen, setIsNewModalOpen] = useState(false);
	const [selectedAgent, setSelectedAgent] = useState('');
	const [conversationTitle, setConversationTitle] = useState('');
	const [showAgentMenu, setShowAgentMenu] = useState(false);
	const [ratings, setRatings] = useState({}); // { messageKey: score (1-5) }
	const [flags, setFlags] = useState({});
	const [openFlagMenu, setOpenFlagMenu] = useState(null); // key of message showing flag menu

	const flagOptions = {
		safety_issue: 'Safety Issue',
		inappropriate: 'Inappropriate',
		factual_error: 'Factual Error',
		outdated: 'Outdated Info',
		off_topic: 'Off Topic'
	};

	// Load last used agent from localStorage once
	useEffect(() => {
		const saved = localStorage.getItem('lastAgentId');
		if (saved && !selectedAgent) {
			setSelectedAgent(saved);
		}
	}, []);

	// Extend conversation objects to include agent meta
	const active = conversations.find((c) => c.id === activeId) || null;

	const currentAgent = (() => {
		if (active && active.agent_id)
			return mockAgents.find((a) => a.id === active.agent_id);
		if (selectedAgent) return mockAgents.find((a) => a.id === selectedAgent);
		return null;
	})();

	const handleAgentSelectInline = (agentId) => {
		setShowAgentMenu(false);
		setSelectedAgent(agentId);
		localStorage.setItem('lastAgentId', agentId);
		const agent = mockAgents.find((a) => a.id === agentId);
		if (!agent) return;
		// Start new conversation if none active OR switching agent on a conversation that already has messages/ different agent
		if (!active || (active && active.messages && active.messages.length > 0 && active.agent_id !== agentId)) {
			const newConv = {
				id: `c-${Date.now()}`,
				title: agent.name,
				created_at: Date.now(),
				agent_id: agent.id,
				agent_name: agent.name,
				agent_model: agent.model,
				messages: []
			};
			setConversations(prev => [newConv, ...prev]);
			setActiveId(newConv.id);
			setCreating(true);
			return;
		}
		// Attach agent to empty conversation without one
		if (active && (!active.agent_id || active.messages.length === 0)) {
			setConversations(prev => prev.map(c => c.id === active.id ? { ...c, agent_id: agent.id, agent_name: agent.name, agent_model: agent.model, title: c.messages.length === 0 ? agent.name : c.title } : c));
		}
	};

	const startNew = () => {
		setConversationTitle('');
		// Pre-fill agent with last used if available
		const saved = localStorage.getItem('lastAgentId');
		if (saved) setSelectedAgent(saved);
		setIsNewModalOpen(true);
	};

	const createConversation = () => {
		if (!selectedAgent) return;
		localStorage.setItem('lastAgentId', selectedAgent);
		const agent = mockAgents.find((a) => a.id === selectedAgent);
		const newConv = {
			id: `c-${Date.now()}`,
			title: conversationTitle.trim() || agent.name,
			created_at: Date.now(),
			agent_id: agent.id,
			agent_name: agent.name,
			agent_model: agent.model,
			messages: [],
		};
		setConversations((prev) => [newConv, ...prev]);
		setActiveId(newConv.id);
		setCreating(true);
		setIsNewModalOpen(false);
	};

	const sendMessage = (e) => {
		e.preventDefault();
		if (!input.trim() || !active) return;
		const userMsg = { role: 'user', content: input.trim() };
		setInput('');
		// Mock assistant reply
		const assistantMsg = {
			role: 'assistant',
			content:
				'This is a mock AI response elaborating on: ' +
				userMsg.content.slice(0, 60) +
				'...',
		};
		setConversations((prev) =>
			prev.map((c) =>
				c.id === active.id
					? {
							...c,
							title:
								c.messages.length === 0
									? userMsg.content.slice(0, 40)
									: c.title,
							messages: [...c.messages, userMsg, assistantMsg],
					  }
					: c
			)
		);
		setCreating(false);
	};

	// Helper to build message key
	const messageKey = (conversationId, index) => `${conversationId}-m${index}`;

	// Single helpful rating handler
	const handleHelpfulRate = (msgKey, score) => {
		setRatings(prev => {
			const current = prev[msgKey];
			// toggle off if same score clicked
			if (current === score) {
				const clone = { ...prev };
				delete clone[msgKey];
				return clone;
			}
			return { ...prev, [msgKey]: score };
		});
		// TODO: backend upsert: POST /api/ratings/ { message: <id>, score }
	};

	const toggleFlag = (msgKey, flagType) => {
		setFlags(prev => {
			const current = new Set(prev[msgKey] || []);
			if (current.has(flagType)) current.delete(flagType); else current.add(flagType);
			return { ...prev, [msgKey]: Array.from(current) };
		});
		// TODO: POST /api/flags/toggle/ { message, flag_type }
	};

	// Per-dimension rating buttons component
	const DimensionRater = ({ msgKey, dimension, value }) => {
		return (
			<div className="flex items-center gap-1" key={dimension}>
				<span className="text-[10px] uppercase tracking-wide text-gray-500 w-16">{dimension}</span>
				{[1,2,3,4,5].map(n => (
					<button
						key={n}
						type="button"
						onClick={() => handleRate(msgKey, dimension, n)}
						className={`h-6 w-6 flex items-center justify-center rounded text-[11px] font-medium border transition
						${value >= n ? 'bg-indigo-600 border-indigo-600 text-white' : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'}`}
						aria-label={`${dimension} ${n}`}
					>
						{n}
					</button>
				))}
			</div>
		);
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
				<div>
					<h1 className="text-2xl font-bold text-gray-900">AI Conversations</h1>
					<p className="text-gray-600">
						Interact with AI agents to get help and insights
					</p>
				</div>
				<button
					onClick={startNew}
					className="inline-flex items-center px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-sm"
				>
					<PlusIcon className="h-4 w-4 mr-2" /> New Chat
				</button>
			</div>

			<div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
				{/* Sidebar WITHOUT Agents Panel */}
				<div className="lg:col-span-1 space-y-4">
					{/* Conversations Panel only */}
					<div className="bg-white rounded-lg shadow p-4">
						<h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
							Conversations
						</h2>
						<div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
							{conversations.map((conv) => (
								<button
									key={conv.id}
									onClick={() => {
										setActiveId(conv.id);
										setCreating(false);
									}}
									className={`w-full text-left p-3 rounded-md border text-sm transition ${
										conv.id === activeId
											? 'bg-blue-50 border-blue-200 text-blue-700'
											: 'bg-white border-gray-200 hover:bg-gray-50'
									}`}
								>
									{' '}
									<div className="flex items-start">
										<ChatBubbleLeftRightIcon className="h-4 w-4 mt-0.5 mr-2 text-gray-400" />
										<div className="flex-1 min-w-0">
											<p className="font-medium truncate">
												{conv.title}
											</p>
											<p className="text-xs text-gray-500">
												{new Date(
													conv.created_at
												).toLocaleDateString()}
											</p>
										</div>
									</div>
								</button>
							))}
							{conversations.length === 0 && (
								<p className="text-xs text-gray-500">
									No conversations yet.
								</p>
							)}
						</div>
					</div>
				</div>
				{/* Active Conversation */}
				<div className="lg:col-span-3 space-y-4">
					<div className="bg-white rounded-lg shadow flex flex-col h-[70vh]">
						<div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
							<div>
								<h2 className="font-semibold text-gray-900 text-lg">
									{active ? active.title : 'No Conversation Selected'}
								</h2>
								{active && (
									<p className="text-xs text-gray-500">
										Started{' '}
										{new Date(active.created_at).toLocaleString()}
									</p>
								)}
							</div>
						</div>
						<div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
							{active ? (
								active.messages.length > 0 ? (
									active.messages.map((m, i) => {
										const isAssistant = m.role === 'assistant';
										const mKey = messageKey(active.id, i);
										const currentFlags = new Set(flags[mKey] || []);
										const currentScore = ratings[mKey] || 0;
										return (
											<div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
												<div className="max-w-[75%] space-y-2">
													<div className={`rounded-lg px-4 py-3 text-sm leading-relaxed shadow ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'}`}>{m.content}</div>
													{isAssistant && (
														<div className="relative flex items-center gap-1 pl-1">
															{[1,2,3,4,5].map(n => {
																const activeStar = currentScore >= n;
																return (
																	<button
																		key={n}
																		type="button"
																		onClick={() => handleHelpfulRate(mKey, n)}
																		aria-label={`Set helpful rating ${n}`}
																		className="h-5 w-5 flex items-center justify-center p-0 m-0"
																	>
																		<span className={`text-base leading-none select-none transition-colors ${activeStar ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'}`}>{activeStar ? '★' : '☆'}</span>
																	</button>
																);
															})}
															<button
																onClick={() => setOpenFlagMenu(v => v === mKey ? null : mKey)}
																className={`h-6 px-2 text-[11px] rounded-full border flex items-center gap-1 transition ${currentFlags.size ? 'bg-red-600 border-red-600 text-white' : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'}`}
																aria-label="Toggle flag menu"
															>
																🚩 {currentFlags.size ? <span className="text-[10px] font-semibold">{currentFlags.size}</span> : null}
															</button>
															{openFlagMenu === mKey && (
																<div className="absolute -top-1 left-0 -translate-y-full w-40 p-1.5 border border-gray-200 rounded-md bg-white shadow-md z-10">
																	<div className="flex items-center justify-between mb-1 pb-0.5 border-b border-gray-100">
																		<p className="text-[9px] uppercase tracking-wide text-gray-500">Flags</p>
																		<button
																			onClick={() => setOpenFlagMenu(null)}
																			className="text-[9px] text-gray-400 hover:text-gray-600 px-1"
																			aria-label="Close flag menu"
																		>✕</button>
																	</div>
																	<div className="max-h-16 overflow-y-auto space-y-0.5 pr-0.5">
																		{Object.entries(flagOptions).map(([fKey,label]) => {
																			const activeFlag = currentFlags.has(fKey);
																			return (
																				<button
																					key={fKey}
																					type="button"
																					onClick={() => toggleFlag(mKey, fKey)}
																					className={`w-full text-left px-2 py-1 rounded text-[10px] flex items-center justify-between ${activeFlag ? 'bg-red-50 text-red-700 border border-red-200' : 'hover:bg-gray-50 text-gray-600'}`}
																				>
																					<span className="truncate">{label}</span>
																					{activeFlag && <span className="ml-1">✓</span>}
																				</button>
																			);
																		})}
																	</div>
																</div>
															)}
														</div>
													)}
												</div> {/* end inner wrapper */}
											</div> /* end outer flex */
										);
												})
								) : (
									<div className="h-full flex items-center justify-center text-sm text-gray-500">
										{creating ? 'Start typing to begin the conversation...' : 'No messages yet.'}
									</div>
								)
							) : (
								<div className="h-full flex items-center justify-center text-sm text-gray-500">
									Select or start a conversation
								</div>
							)}
						</div>
						{/* Replace / augment message form */}
						<form
							onSubmit={sendMessage}
							className="border-t border-gray-100 p-4"
						>
							<div className="flex items-end gap-3">
								<div className="flex-1 relative">
									<textarea
										disabled={!active}
										value={input}
										onChange={(e) => setInput(e.target.value)}
										rows={1}
										placeholder={
											active
												? currentAgent
													? `Message ${currentAgent.name}...`
													: 'Select an AI agent (chip icon)...'
												: 'Select a conversation first'
										}
										className="w-full resize-none pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
									/>
									<button
										type="button"
										onClick={() => setShowAgentMenu(v => !v)}
										className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-indigo-600 p-1 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
										title={
											currentAgent
												? `${currentAgent.name} (${currentAgent.model})`
												: 'Select AI Agent'
										}
									>
										<CpuChipIcon className={`h-5 w-5 ${currentAgent ? 'text-indigo-600' : ''}`} />
									</button>
									{showAgentMenu && (
										<div className="absolute bottom-full left-0 mb-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg p-2 space-y-1 z-10">
											<p className="text-xs text-gray-500 px-1 mb-1">
												Choose Agent
											</p>
											{mockAgents.map((a) => (
												<button
													key={a.id}
													type="button"
													onClick={() => handleAgentSelectInline(a.id)}
													className={`w-full text-left px-2 py-2 rounded-md text-sm hover:bg-gray-50 flex items-start ${
														currentAgent?.id === a.id
															? 'bg-indigo-50 border border-indigo-200'
															: ''
													}`}
												>
													<CpuChipIcon className="h-4 w-4 mr-2 mt-0.5 text-indigo-500" />
													<div className="flex-1 min-w-0">
														<p className="font-medium leading-5 truncate">
															{a.name}
														</p>
														<p className="text-[10px] text-gray-500 uppercase tracking-wide">
															{a.model}
														</p>
													</div>
												</button>
											))}
											<button
												type="button"
												onClick={() => setShowAgentMenu(false)}
												className="w-full mt-1 text-xs text-gray-500 hover:text-gray-700 py-1"
											>
												Close
											</button>
										</div>
									)}
								</div>
								<button
									disabled={!active || !input.trim()}
									type="submit"
									className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white ${
										input.trim() && active
											? 'bg-blue-600 hover:bg-blue-700'
											: 'bg-gray-400 cursor-not-allowed'
									}`}
								>
									<PaperAirplaneIcon className="h-4 w-4 mr-2" /> Send
								</button>
							</div>
						</form>
					</div>
				</div>
			</div>

			{/* New Conversation Modal */}
			{isNewModalOpen && (
				<div className="fixed inset-0 z-50 flex items-center justify-center">
					<div
						className="absolute inset-0 bg-black/40"
						onClick={() => setIsNewModalOpen(false)}
					/>
					<div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6 space-y-5">
						<div className="flex items-center justify-between">
							<h3 className="text-lg font-semibold text-gray-900">
								Start New Conversation
							</h3>
							<button
								onClick={() => setIsNewModalOpen(false)}
								className="text-gray-400 hover:text-gray-600"
							>
								<XMarkIcon className="h-5 w-5" />
							</button>
						</div>
						<div className="space-y-4">
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-1">
									AI Agent
								</label>
								<select
									value={selectedAgent}
									onChange={(e) => {
										setSelectedAgent(e.target.value);
										if (!conversationTitle.trim()) {
											const a = mockAgents.find(
												(x) => x.id === e.target.value
											);
											if (a) setConversationTitle(a.name);
										}
									}}
									className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-sm"
								>
									<option value="">Select an agent...</option>
									{mockAgents.map((a) => (
										<option key={a.id} value={a.id}>
											{a.name} ({a.model})
										</option>
									))}
								</select>
							</div>
							{selectedAgent && (
								<div className="bg-gray-50 rounded-md p-3 text-xs text-gray-600 leading-relaxed">
									{mockAgents.find((a) => a.id === selectedAgent)
										?.description}
								</div>
							)}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-1">
									Title (optional)
								</label>
								<input
									value={conversationTitle}
									onChange={(e) => setConversationTitle(e.target.value)}
									placeholder="e.g., HVAC optimization plan"
									className="w-full rounded-md border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-sm"
								/>
							</div>
						</div>
						<div className="flex justify-end space-x-3 pt-2">
							<button
								onClick={() => setIsNewModalOpen(false)}
								className="px-4 py-2 rounded-md border text-sm font-medium bg-white hover:bg-gray-50 text-gray-700"
							>
								Cancel
							</button>
							<button
								onClick={createConversation}
								disabled={!selectedAgent}
								className="px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Start
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default AIConversations;
