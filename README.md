# 🎬 ClipForge

> **Automated Video Clipping & Social Media Posting - 100% Free, No Maintenance Required**

ClipForge automatically finds the best moments in your videos, extracts them as clips, generates engaging captions and hashtags, and posts them to your connected social media accounts.

![ClipForge](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)

## ✨ Features

- 📹 **Smart Clip Detection** - Uses audio analysis, scene detection, and motion tracking to find the most engaging moments
- ✂️ **Automatic Extraction** - Creates optimized clips for social media (15-60 seconds)
- 📝 **Caption Generation** - Auto-generates engaging captions without any AI subscriptions
- #️⃣ **Hashtag Generation** - Creates relevant, trending hashtags for each platform
- 🐦 **Multi-Platform Posting** - Post to Twitter/X, YouTube Shorts, and TikTok
- 📅 **Scheduling** - Schedule posts for optimal engagement times
- 🔒 **Privacy-First** - All processing happens locally on your server
- 💰 **100% Free** - No monthly subscriptions, no hidden costs

## 🚀 Why ClipForge?

| Feature | ClipForge | Other Tools |
|---------|-----------|-------------|
| Monthly Cost | **$0** | $20-100/month |
| AI Processing | Local (Free) | Cloud (Paid) |
| Data Privacy | Your Server | Third Party |
| Maintenance | Zero | Updates Required |
| Social APIs | Free Tier | Often Paid |

## 🛠️ Tech Stack

All tools are **free and open-source**:

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: React, TypeScript, Tailwind CSS
- **Video Processing**: FFmpeg, PySceneDetect, Librosa
- **Database**: SQLite (file-based, no external service)
- **Social APIs**: Official free APIs (Twitter, YouTube, TikTok)

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- FFmpeg (installed system-wide)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/clipforge.git
cd clipforge
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access ClipForge!

## 🔐 Social Media Setup

### Twitter / X

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create a project and app
3. Enable **OAuth 2.0** with PKCE
4. Set callback URL: `http://localhost:8000/api/auth/twitter/callback`
5. Copy **Client ID** and **Client Secret** to `.env`:
   ```
   TWITTER_CLIENT_ID=your_client_id
   TWITTER_CLIENT_SECRET=your_client_secret
   ```

### YouTube

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 credentials**
5. Add redirect URI: `http://localhost:8000/api/auth/google/callback`
6. Copy credentials to `.env`:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

> **Note**: YouTube API has a free quota of 10,000 units/day. Video uploads cost 1,600 units, allowing ~6 uploads/day for free.

### TikTok

1. Go to [TikTok Developer Portal](https://developers.tiktok.com)
2. Create a developer account
3. Create an app
4. Apply for **Content Posting API** access
5. Set callback URL: `http://localhost:8000/api/auth/tiktok/callback`
6. Copy credentials to `.env`:
   ```
   TIKTOK_CLIENT_KEY=your_client_key
   TIKTOK_CLIENT_SECRET=your_client_secret
   ```

## 📖 Usage

### 1. Upload a Video

- Click **Upload** in the sidebar
- Drag & drop your video or click to browse
- Supported formats: MP4, MOV, AVI, WebM (up to 500MB)

### 2. Process the Video

- Click **Process** on your uploaded video
- ClipForge will analyze the video and find the best moments
- Clips are automatically generated with:
  - Optimal start/end points
  - Generated captions
  - Relevant hashtags

### 3. Review & Edit

- Browse generated clips in the **Clips** section
- Preview each clip before posting
- Edit captions and hashtags as needed
- Regenerate content if you want different suggestions

### 4. Post to Social Media

- Connect your accounts in **Settings**
- Click **Post** on any clip
- Select platforms to post to
- Optionally schedule for later

## 🧠 How Clip Detection Works

ClipForge uses **multiple signals** to find interesting moments:

1. **Audio Analysis** (Librosa)
   - Detects loud moments and audio peaks
   - Identifies speech patterns
   - Finds musical segments

2. **Scene Detection** (PySceneDetect)
   - Identifies scene boundaries
   - Finds natural transition points
   - Scores scene significance

3. **Motion Analysis** (OpenCV)
   - Detects high-action segments
   - Identifies movement patterns
   - Scores visual interest

Each clip gets a **combined score** from these signals, and the top clips are extracted.

## 🏗️ Project Structure

```
clipforge/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # SQLite setup
│   │   ├── models.py            # Database models
│   │   ├── routes/              # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── videos.py
│   │   │   ├── clips.py
│   │   │   └── social.py
│   │   ├── video_processor/     # Video analysis
│   │   │   ├── analyzer.py
│   │   │   ├── clipper.py
│   │   │   ├── scene_detector.py
│   │   │   └── audio_analyzer.py
│   │   ├── content_generator/   # Caption/hashtag generation
│   │   │   ├── caption_generator.py
│   │   │   └── hashtag_generator.py
│   │   └── social/              # Social media clients
│   │       ├── twitter.py
│   │       ├── youtube.py
│   │       └── tiktok.py
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── api/client.ts        # API client
    │   ├── store/authStore.ts   # Auth state
    │   ├── components/
    │   │   └── Layout.tsx
    │   └── pages/
    │       ├── Dashboard.tsx
    │       ├── Upload.tsx
    │       ├── VideoDetail.tsx
    │       ├── Clips.tsx
    │       └── Settings.tsx
    ├── package.json
    └── tailwind.config.js
```

## 🔧 Configuration

All settings are in `backend/.env`:

```env
# App Settings
SECRET_KEY=your-super-secret-key
DEBUG=false

# Database (SQLite - no external service needed)
DATABASE_URL=sqlite+aiosqlite:///./clipforge.db

# Video Processing
MAX_VIDEO_SIZE_MB=500
CLIP_MIN_DURATION=15
CLIP_MAX_DURATION=60
MAX_CLIPS_PER_VIDEO=10

# Social Media (see setup instructions above)
TWITTER_CLIENT_ID=
TWITTER_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
```

## 🐳 Docker Deployment (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY backend/ .
RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t clipforge .
docker run -p 8000:8000 -v ./data:/app/data clipforge
```

## 📊 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Get access token |
| POST | `/api/videos/upload` | Upload video |
| POST | `/api/videos/{id}/process` | Start processing |
| GET | `/api/clips/` | List all clips |
| POST | `/api/social/post` | Post to social media |

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - feel free to use this for personal or commercial projects.

## 🙏 Credits

Built with these amazing open-source projects:

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [FFmpeg](https://ffmpeg.org/)
- [PySceneDetect](https://www.scenedetect.com/)
- [Librosa](https://librosa.org/)
- [Tailwind CSS](https://tailwindcss.com/)

---

<p align="center">
  <strong>🎬 ClipForge - Automated Video Clips, Zero Monthly Fees</strong>
</p>
