# 🏋️‍♂️ FitNation - Gym Management Web Application

FitNation is a premium Gym Management Web Application built using **Django** and styled with **Tailwind CSS**. It provides a comprehensive solution for managing gym memberships, class scheduling, interactive user accounts, security, and next-generation AI-powered recommendation systems.

---

## 📌 Features

- **🧑‍💻 Interactive Dashboard**: Seamless navigation and custom profile-based navbar toggling based on user login states.
- **🔐 Robust User Authentication**: Includes standard login, signup (with verification mails), profile management, and a complete secure password reset flow.
- **✉️ Automated Notifications**: Seamless email confirmations and messages using Gmail SMTP server.
- **🤖 Groq AI Fitness Plans**: Personalized workout and fitness recommendations generated dynamically via the **Groq API** (Llama models).
- **📺 YouTube Workout Guides**: Automated searching of video tutorials and workout guides powered by the **YouTube Data API v3**.
- **📊 Admin Controls**: Complete admin suite to manage gym members, workouts, generated plans, and inquiries.
- **🎨 Highly Responsive UI**: Beautiful dark-neon theme designed specifically with Tailwind CSS, custom grids, and interactive components.

---

## 🛠️ Tech Stack

- **Backend:** Django (Python 3.x)
- **Frontend:** HTML5, modern vanilla JavaScript, Tailwind CSS (supported by PostCSS)
- **Database:** SQLite (Default Django representation)
- **APIs and Services:**
  - Groq API v1.5.0 (AI Fitness generation via Llama models)
  - YouTube Data API v3 (Workout guidelines video query)
  - Gmail SMTP (Automated signup & system alerts)

---

## 📁 Project Structure

```
gymproject/
├── gymapp/                       # Core Django Application
│   ├── migrations/               # Database Migrations
│   ├── services/                 # External API integrations
│   │   ├── gemini_service.py     # Groq Llama API client
│   │   └── youtube_service.py    # YouTube Data API client
│   ├── static/                   # Static CSS, JavaScript, images, and videos
│   ├── templates/gymapp/         # Elegant Tailwind HTML templates
│   ├── admin.py                  # Admin interface configuration
│   ├── models.py                 # Django Database Models (Workout, UserProfile, etc.)
│   ├── views.py                  # Controllers and page logic
│   └── urls.py                   # App routing endpoints
├── gymproject/                   # Django Project configurations
│   ├── settings.py               # Django Settings & Environment Variable Loader
│   └── urls.py                   # Global Project routing endpoints
├── interview_prep_guide.md       # Full interview guide for developers
├── tailwind.config.js            # Tailwind CSS styling parameters
├── postcss.config.js             # PostCSS plugin parameters
└── .gitignore                    # Excluded files (node_modules, pycache, .env, DBs)
```

---

## 🚀 Setup & Local Installation

### 1. Pre-requisites
Make sure you have **Python 3.x** and **Node.js** installed on your system.

### 2. Clone and Setup Environment
Navigate into the root directory:
```bash
cd gymproject
```

### 3. Install Dependencies
Install Python libraries (or use virtual environment):
```bash
pip install django groq==1.5.0 requests
```
Install frontend development packages:
```bash
npm install
```

### 4. Configure Environmental Variables (`.env`)
Create a `.env` file in the root directory (this file is ignored by Git in `.gitignore`) and provide your API keys:
```env
EMAIL_HOST_PASSWORD=your-gmail-smtp-app-password
GROQ_API_KEY=your-groq-api-key
YOUTUBE_API_KEY=your-youtube-data-api-key
```

### 5. Compile Styles & Start Tailwind CSS Watcher
Build the custom styling sheets using Tailwind:
```bash
npm run dev
# or build
npx tailwindcss -i ./gymapp/static/gymapp/input.css -o ./gymapp/static/gymapp/output.css --watch
```

### 6. Run Migrations & Start Server
Run the local database migration scripts:
```bash
python manage.py migrate
```
Start the local development server:
```bash
python manage.py runserver
```
Visit the local server in your web browser:
`http://127.0.0.1:8000/`

---

## 🔒 Security Best Practices
- Hardcoded secrets and API keys are strictly excluded from the codebase.
- Dynamic credential loading is configured via `os.getenv` parsing local `.env` values dynamically.
- Cache structures (`__pycache__`) and local node configuration dependencies (`node_modules`) are permanently excluded from commits through git rules.
