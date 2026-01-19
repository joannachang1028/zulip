# Implementation

## Feature 1: Message Recap

**Demo video:** https://drive.google.com/file/d/1mESRUY3JMrLKB2GfguFMi8RQbZdir0G8/view?usp=sharing

### What it does
Users click "Message Recap" in the help menu (top right corner), and they get a quick AI-generated summary of their unread messages, with clickable links to jump to each message.

### How the backend works

The main logic is in [zerver/actions/message_recap.py](zerver/actions/message_recap.py).

When a user hits the `/json/messages/recap` endpoint (defined in [zerver/views/message_recap.py](zerver/views/message_recap.py)), here's what happens:

1. We grab the user's unread message IDs using Zulip's built-in `get_raw_unread_data()` — this includes unreads from streams, DMs, and group chats
2. We cap it at 80 messages so we don't overwhelm the LLM or rack up costs
3. For each message, we format it as JSON with the sender name, topic, content, and a URL that links directly to that message (using Zulip's `near_message_url()` helper)
4. We send all this to Groq's Llama 3.3 70B model via LiteLLM, asking it to summarize into bullet points with inline markdown links
5. The LLM returns markdown, which we convert to HTML so the links actually work in the browser

The key part for making links work: we pass each message's URL to the model and ask it to include `[text](url)` links in its response. Example URL format: `#narrow/stream/123-general/topic/meeting/near/456789`

### Frontend

Added a "Message Recap" menu item to the navbar help popover ([web/templates/popovers/navbar/navbar_help_menu_popover.hbs](web/templates/popovers/navbar/navbar_help_menu_popover.hbs)). When clicked, it calls `show_message_recap()` in [web/src/message_recap.ts](web/src/message_recap.ts) which pops up a modal, calls the API, and displays the HTML result.

---

## Feature 2: Topic Title Improver

**Demo video:** https://drive.google.com/file/d/1wZ0uxMmdiAJMDTNDQ4U90KMDf0ufSJbe/view?usp=sharing

### What it does
Right-click any topic in the left sidebar and select "Improve topic title". The AI analyzes if the conversation has drifted from the topic name, and if so, suggests a better title that you can apply with one click.

### Backend — Latency, Cost, and Scalability

Main code: [zerver/actions/topic_title_improver.py](zerver/actions/topic_title_improver.py)

**Cost considerations:**
- Only fetches the last 30 messages in a topic — enough context to detect drift without sending huge amounts of data
- Using Groq which has a free tier (also very fast, ~1-2 seconds)
- This feature is user-initiated (not automatic) so it only runs when someone actually asks for a suggestion

**Latency:**
- Groq is one of the fastest LLM inference providers out there
- We only send a small context window (30 messages) to keep response times low
- In testing, responses come back in 1-3 seconds

**Scalability:**
- If this was deployed for real, I'd probably add caching — if a topic was analyzed recently and no new messages were added, just return the cached result
- Could also add rate limiting per user to prevent abuse
- The feature is "pull" not "push", so server load only happens when users request it

### How it works

1. User triggers the feature via the topic popover menu
2. Backend fetches recent messages for that stream+topic combo
3. Sends to LLM with a prompt asking it to output JSON: `{has_drifted, suggested_title, reason}`
4. If drift detected, we show the suggestion in a modal with an "Apply" button
5. Apply button uses Zulip's existing message edit API to rename the topic

### Frontend

Added "Improve topic title" to the left sidebar topic popover ([web/templates/popovers/left_sidebar/left_sidebar_topic_actions_popover.hbs](web/templates/popovers/left_sidebar/left_sidebar_topic_actions_popover.hbs)), with the handler in [web/src/topic_title_improver.ts](web/src/topic_title_improver.ts).

---

## Setup

To run these features, you need a Groq API key:

1. Get a key from https://console.groq.com
2. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_key_here
   ```
3. Install dependencies in Vagrant:
   ```bash
   source /srv/zulip/.venv/bin/activate
   pip install python-dotenv litellm markdown
   ```
4. Start the dev server: `./tools/run-dev`

---

## Future Improvements

1. **Caching:** Cache recap results for a short period to reduce API calls
2. **Streaming:** Stream LLM responses for better UX on longer summaries
3. **User Preferences:** Allow users to customize summary length/style
4. **Keyboard Shortcuts:** Add hotkey for Message Recap
5. **Batch Processing:** Support for summarizing specific channels/time ranges
