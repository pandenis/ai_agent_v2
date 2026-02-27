# 👤 AI Agent System - User Guide

Simple guide to using the AI Agent System v2.3.3

---

## 🚀 Getting Started

### Accessing the System

1. Open your web browser
2. Navigate to: `http://localhost:3000` (or your server address)
3. You'll see the main chat interface

---

## 💬 Basic Usage

### 1. Create a New Session

Click the **"+ New Session"** button in the top-left corner.

A new chat session will be created with the default agent (Groq).

---

### 2. Select an AI Agent

Click the **agent dropdown** at the top of the chat to choose from 7 available agents:

| Agent | Best For | Speed |
|-------|----------|-------|
| **Groq (Llama 3.3)** | General questions, fast responses | ⚡⚡⚡ Ultra-fast |
| **GPT-OSS (20B)** | Complex reasoning, memory tasks | ⚡⚡ Fast |
| **Mixtral (8x7B)** | Premium quality answers | ⚡⚡ Fast |
| **Llama 3.1 (8B)** | Long context (128k tokens) | ⚡⚡ Fast |
| **Mistral (7B)** | Balanced performance | ⚡⚡ Fast |
| **DeepSeek Coder** | Code analysis, debugging | ⚡⚡ Fast |
| **Medical AI** | Health questions (educational) | ⚡⚡ Fast |

**Tip:** Start with **Groq** for general use!

---

### 3. Send a Message

1. Type your message in the input field at the bottom
2. Press **Enter** to send (or **Shift+Enter** for new line)
3. Watch for the **"AI is thinking..."** indicator
4. The AI's response will appear in seconds

**Example questions:**
- "Explain quantum computing in simple terms"
- "Write a Python function to calculate fibonacci numbers"
- "What are the symptoms of hypertension?" (use Medical AI)

---

### 4. Switch Between Sessions

Your previous conversations are saved in the **left sidebar**.

- Click any session to continue that conversation
- Active session is highlighted with a **gradient**
- See message count and time for each session

---

### 5. View Memory Panel

Click the **"Memory"** button (top-right) to see extracted facts.

The Memory Panel shows:
- ⭐⭐⭐⭐⭐ Facts with star ratings (importance)
- 🏷️ Tags for categorization
- 📊 Confidence scores
- 🔍 Facts extracted from your conversations

**Example facts:**
- "User's name is Denis" ⭐⭐⭐⭐⭐
- "User works as QA Engineer" ⭐⭐⭐⭐
- "User loves Python programming" ⭐⭐⭐

---

## 🎯 Advanced Features

### Auto-expanding Input

The input field automatically grows as you type (1-10 lines).

Perfect for:
- Long questions
- Code snippets
- Multi-paragraph messages

---

### Typing Indicator

When the AI is responding, you'll see:
- 💬 **"AI is thinking..."** in the chat area
- 🔵 **"AI is typing..."** in the session list (for active session)

---

### Dark Theme

The entire interface uses a modern **dark theme**:
- Reduces eye strain
- Professional Discord/Slack style
- Better for extended use

---

## 💡 Tips & Best Practices

### Getting the Best Answers

**Be specific:**
❌ "Tell me about AI"
✅ "Explain how neural networks learn from data"

**Provide context:**
❌ "Fix this code"
✅ "This Python code gives an IndexError. Can you help debug it? [paste code]"

**Use the right agent:**
- Code questions → **DeepSeek Coder**
- Medical questions → **Medical AI**
- Complex reasoning → **Mixtral**
- Fast general chat → **Groq**

---

### Managing Sessions

**Organize your work:**
- Create separate sessions for different topics
- Example: "Python Help", "Medical Research", "General Chat"

**Keep sessions focused:**
- One topic per session for better context
- The AI remembers your entire conversation history

---

### Using Memory

The AI automatically:
- ✅ Extracts important facts from conversations
- ✅ Remembers them for future reference
- ✅ Uses them to personalize responses

**You can:**
- View all facts in the Memory Panel
- See importance ratings (⭐⭐⭐⭐⭐)
- Facts persist across sessions

---

## 🔧 Troubleshooting

### "AI is not responding"

1. Check the typing indicator appears
2. Wait 10-30 seconds (some queries take time)
3. Refresh the page (Ctrl+R)
4. Try sending the message again

---

### "Session won't load"

1. Hard refresh: **Ctrl+Shift+R**
2. Check your internet connection
3. Try creating a new session

---

### "Memory Panel is empty"

Memory facts are extracted automatically:
- After you have a few conversations
- When you share personal information
- Give it time - facts appear after responses

---

### "Input field is frozen"

1. Wait for current response to complete
2. Don't send multiple messages rapidly
3. Refresh page if stuck

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Enter** | Send message |
| **Shift+Enter** | New line |
| **Ctrl+R** | Refresh page |
| **Ctrl+Shift+R** | Hard refresh |
| **Esc** | Close Memory Panel |

---

## 📊 Understanding Responses

### Source Attribution

Some responses show sources:
```
"Based on your documents..." → Document search used
"According to web search..." → Web search used
"From our conversation..." → Conversation history
```

### Confidence Indicators

Memory facts show confidence:
- **High confidence** (90%+): ⭐⭐⭐⭐⭐
- **Medium confidence** (70-90%): ⭐⭐⭐⭐
- **Lower confidence** (<70%): ⭐⭐⭐

---

## 🎨 Interface Overview
```
┌─────────────────────────────────────────────────┐
│ Sessions Panel    │  Chat Area  │ Memory Panel  │
│                   │             │  (optional)   │
│ + New Session     │  Session:   │               │
│                   │  f7e9d0bc   │  ⭐⭐⭐⭐⭐      │
│ Session 1 (active)│             │  Facts with   │
│ 5 messages        │  Messages   │  importance   │
│ 2 mins ago        │  appear     │  ratings      │
│                   │  here       │               │
│ Session 2         │             │  🏷️ Tags      │
│ 10 messages       │             │               │
│ 1 hour ago        │  [Input]    │  Close [×]    │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

After you're comfortable with basics:

1. **Try different agents** - Each has unique strengths
2. **Explore Memory Panel** - See what facts are extracted
3. **Create topic-specific sessions** - Better organization
4. **Ask complex questions** - Test premium agents like Mixtral

---

## 💬 Example Conversations

### Example 1: Code Help
```
You: "Write a Python function to validate email addresses"

AI (DeepSeek): "Here's a function using regex:
[code snippet]
This handles common formats and edge cases..."
```

---

### Example 2: Learning
```
You: "Explain machine learning in simple terms"

AI (Groq): "Think of machine learning like teaching
a child to recognize animals. You show examples..."
```

---

### Example 3: Health Question
```
You: "What are early signs of diabetes?"

AI (Medical): "Common early signs include:
1. Increased thirst
2. Frequent urination
3. Unexplained weight loss
[Educational information]"
```

---

## 📞 Need Help?

If you're stuck:

1. Check this guide
2. Try refreshing the page
3. Create a new session
4. Contact support

---

## ✨ Features Coming Soon

- 📱 Mobile optimization
- 📊 Analytics dashboard
- 🔍 Cross-session search
- 📝 Session renaming
- 📤 Export conversations
- 🎨 Custom themes

---

**Last Updated:** December 9, 2025  
**Version:** 2.3.3
**For:** End Users

Happy chatting! 🎉