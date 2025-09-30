# AI Conversations App Documentation

## Overview
The `ai_conversations` app powers the AI chat and agent system. It manages LLM models, AI agents, user conversations, messages, a single 1–5 helpfulness rating per AI message, issue flags, analytics, and model performance.

---

## Feature Highlights
- Multi-provider LLM registry (read-only via API in current implementation)
- Configurable AI agents with role/system prompts
- Conversation + message storage with token & cost tracking
- Single helpfulness rating (1–5) per user per assistant message
- Issue flags (safety_issue, inappropriate, factual_error, outdated, off_topic) with toggle endpoint
- Aggregated helpful rating + flag summaries per message
- Usage analytics & model performance metrics (read-only)
- Conversation auto summaries

---

## API Endpoints (Current)
All endpoints are prefixed with `/api/`.

### Ratings (`ratings/`)
Each user can store one helpfulness rating (1–5) per message.
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/ratings/ | List your ratings |
| POST | /api/ratings/ | Create / upsert helpful rating { message, score } |
| GET | /api/ratings/{id}/ | Retrieve rating |
| PUT/PATCH | /api/ratings/{id}/ | Update score/comment |
| DELETE | /api/ratings/{id}/ | Delete rating |
| GET | /api/ratings/by_message/?message_id= | All ratings for message |
| GET | /api/ratings/summary/?message_id= | { helpful: { avg, count }, user: { id, score } } |

Example create:
```http
POST /api/ratings/
{"message": "<message_uuid>", "score": 5, "comment": "Great answer"}
```

---

## Main ViewSets
- LLMModelViewSet (read-only)
- ConversationAgentViewSet (full CRUD)
- AIConversationViewSet (full CRUD + soft delete + messages action)
- AIMessageViewSet (list/retrieve/create + by_conversation action)
- AIMessageRatingViewSet (CRUD + by_message + summary)
- AIMessageFlagViewSet (CRUD + toggle + by_message + summary)
- AIUsageAnalyticsViewSet (read-only + summary + daily)
- AIModelPerformanceViewSet (read-only)
- AIConversationSummaryViewSet (read-only + by_conversation)

---

## Models (Summary)
- LLMModel
- ConversationAgent
- AIConversation
- AIMessage
- AIMessageRating (quality dimensions)
- AIMessageFlag (issue flags)
- AIUsageAnalytics
- AIModelPerformance
- AIConversationSummary

(See `models.py` for full field definitions.)

---

## Example Usage

Create conversation:
```http
POST /api/conversations/
{"agent": "<agent_uuid>", "title": "Chat with AI"}
```

Send message:
```http
POST /api/messages/
{"conversation": "<conversation_uuid>", "role": "user", "content": "Explain transformers"}
```

Rate message (accuracy = 5):
```http
POST /api/ratings/
{"message": "<message_uuid>", "rating_type": "accuracy", "score": 5}
```

Get rating summary:
```http
GET /api/ratings/summary/?message_id=<message_uuid>
```

Toggle a factual error flag:
```http
POST /api/flags/toggle/
{"message": "<message_uuid>", "flag_type": "factual_error"}
```

Get flag summary:
```http
GET /api/flags/summary/?message_id=<message_uuid>
```

---

## Background Tasks (Celery)
Same as previously documented: conversation summaries, usage & performance updates, feedback processing, cleanup, archiving, trend analysis. (See project Celery config.)

---

## Tests
Run:
```sh
python manage.py test ai_conversations
```

---

## Permissions & Security
- Authentication required for all endpoints
- Users only see their own conversations/messages/feedback & analytics
- Agents visible if created_by user or public
- Soft deletion for conversations cascades to messages (flag/rating data retained)

---

## Roadmap / Potential Enhancements
- Moderator/admin endpoints for reviewing flags
- Caching aggregated ratings per agent/message
- Real-time websocket updates for new messages & feedback
- Data migration scripts for legacy rating types (if applicable)

---

## See Also
- ../AI_CONVERSATION_SYSTEM_IMPLEMENTATION.md
- ../README.md
