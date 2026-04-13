# Autonomous Blog Agent - 3D Dashboard

A stunning 3D frontend dashboard for the Autonomous Blog Agent system, featuring:

- 📝 **Blog Posts** - View all generated blog posts with markdown rendering
- 🎮 **3D Agent Visualization** - Watch agents work in real-time with Three.js animations
- 📊 **Pipeline Monitoring** - Track pipeline status and system statistics

## Features

### Blog Posts Page
- Grid view of all generated blog posts
- Filter by tags
- Click to read full post with Mermaid diagrams
- Trigger new post generation

### 3D Agent View
- Interactive 3D scene showing all 7 agents
- Animated workflow progression
- Hover to see agent details
- Orbit controls to explore the scene
- Real-time status updates

### Agents Visualized
1. 🕷️ **Crawler Agent** - Crawls websites autonomously
2. 🔧 **Extractor Agent** - Extracts and structures content
3. 🧠 **Memory System** - FAISS duplicate detection
4. ✍️ **Writer Agent** - Generates blog posts with LLM
5. ✏️ **Editor Agent** - Improves quality
6. 🔍 **Reviewer Agent** - Validates originality
7. 📤 **Publisher Agent** - Saves drafts or publishes to Medium

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Three.js + React Three Fiber** - 3D graphics
- **Drei** - Three.js helpers
- **Vite** - Build tool
- **React Markdown** - Render blog posts

## Architecture

```
frontend/
├── src/
│   ├── components/
│   │   ├── BlogList.tsx          # Blog listing page
│   │   ├── BlogDetail.tsx        # Blog post viewer
│   │   └── AgentVisualization.tsx # 3D agent scene
│   ├── services/
│   │   └── api.ts                # Backend API client
│   ├── App.tsx                   # Main app with routing
│   └── main.tsx                  # Entry point
├── package.json
└── vite.config.ts
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`:

- `GET /pipeline/status` - Pipeline status
- `GET /stats` - System statistics
- `POST /pipeline/trigger` - Start generation
- `GET /history` - Processing history

## Screenshots

The 3D scene includes:
- Glowing agent nodes with pulsing animations
- Connection lines showing data flow
- Particle effects for active agents
- Interactive orbit controls
- Status indicators for each agent

## Development

```bash
# Start backend (in one terminal)
cd .. && python -m src.main run-server

# Start frontend (in another terminal)
npm run dev
```

Open `http://localhost:3000` to view the dashboard.
