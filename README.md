# ⚽ Football Survivor Pool

A full-stack survivor pool application for football leagues (Premier League, La Liga, Bundesliga, Serie A, Ligue 1) where players compete by making weekly predictions. Built with FastAPI, React Native, and PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/React_Native-0.81-61dafb.svg)](https://reactnative.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)](https://www.postgresql.org/)

## 📱 Demo

**Live Demo:** [Coming Soon - Deployed on Railway]

**Test Credentials:**
- Email: `firstUserTest@gmail.com`
- Password: `password`

## ✨ Features

### User Management
- 🔐 Secure authentication with bcrypt password hashing
- 👤 User profiles with first name, last name, username
- 📧 Email-based login system

### Pool Management
- 🏆 Create custom survivor pools for any major European league (Premier League, La Liga, Bundesliga, Serie A, Ligue 1)
- 🎯 Configurable rules: max lives (default: 3), max picks per team (default: 2)
- 📊 Real-time leaderboard with points and lives tracking
- 🔗 Share pools via unique session codes (e.g., PL123456)
- 🌍 Multi-league support: Premier League, La Liga, Bundesliga, Serie A, Ligue 1

### Gameplay
- ⚽ Make weekly predictions by selecting a team to win or draw
- 📅 View upcoming fixtures with kickoff times
- 🚫 Usage limits prevent picking the same team multiple times
- 💔 Lose a life when your selected team loses
- 🏅 Earn points for correct predictions (Win: 3pts, Draw: 1pt)
- 📈 Track your selection history and performance

### Live Data Integration
- 🔄 Real-time fixture data from API-Football (RapidAPI)
- 📡 Automatic fixture updates and result processing
- 🗓️ Current gameweek detection
- 🏟️ Team information with logos and venue details

### Admin Features
- ⚙️ Bulk fixture synchronization
- 🔧 Result processing for completed gameweeks
- 📊 Database management via Alembic migrations

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── crud/               # Database operations
│   │   ├── competition_crud.py
│   │   ├── pick_crud.py
│   │   ├── pool_crud.py
│   │   └── user_crud.py
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── competiton_data.py  # Competition, Team, Fixture
│   │   ├── pick.py             # User picks/predictions
│   │   ├── pool.py             # Pools and user stats
│   │   └── user.py             # User authentication
│   ├── routers/            # API endpoints
│   │   ├── auth_router.py      # Login/Signup
│   │   ├── competition_router.py
│   │   ├── pick_router.py
│   │   ├── pool_router.py
│   │   └── external_football_router.py
│   ├── schemas/            # Pydantic validation
│   ├── services/           # Business logic
│   │   ├── football_api.py     # External API integration
│   │   ├── leaderboard.py      # Ranking calculations
│   │   └── results.py          # Result processing
│   └── utils/              # Helper functions
│       └── auth.py             # Password hashing
├── alembic/                # Database migrations
└── requirements.txt
```

### Frontend (React Native)
```
frontend/survivorpool-mobile/
├── src/
│   ├── screens/            # Main app screens
│   │   ├── LoginScreen.js
│   │   ├── SignupScreen.js
│   │   └── HomeScreen.js
│   ├── components/         # Reusable UI components
│   │   ├── Header.js
│   │   ├── Leaderboard.js
│   │   ├── TeamSelector.js
│   │   ├── PlayerSelections.js
│   │   ├── LeagueManager.js
│   │   └── UserLeagues.js
│   ├── nav/               # Navigation components
│   │   └── HomeNav.js
│   ├── api/               # API integration
│   │   └── api.js
│   │       ├── endpoints/ # API service functions for endpoints
│   │       │   └── pools.js
│   └── styles/            # Separated stylesheets
└── App.js
```

### Database Schema
- **Users**: Authentication and profile data
- **Competitions**: League information (PL, LL, BL, SA, L1)
- **Teams**: Team details with logos and external IDs
- **Fixtures**: Match schedules with live status updates
- **Pools**: Custom survivor pool configurations
- **PoolUserStats**: Lives, points, elimination tracking
- **Picks**: User predictions with results

## 🚀 Getting Started

### Prerequisites
```bash
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Expo CLI
- RapidAPI key for API-Football
```

### Backend Setup

1. **Clone the repository**
```bash
git clone https://github.com/NjokuM/SurvivorPoolApp.git
cd SurvivorPoolApp/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env # This creates a .env file and copies the .env layout from the .env.example file

# Edit .env with your credentials:
# - DATABASE_URL
# - RAPIDAPI_KEY
# - RAPIDAPI_HOST
# - SECRET_KEY
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Start the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to mobile app**
```bash
cd ../frontend/survivorpool-mobile
```

2. **Install dependencies**
```bash
npm install
```

3. **Update API endpoint**
```javascript
// src/api/api.js
const API = axios.create({
    baseURL: "http://YOUR_LOCAL_IP:8000"  // Update with your IP
});
```

4. **Start Expo**
```bash
npx expo start
```

5. **Run on device/simulator**
- Press `a` for Android emulator
- Press `i` for iOS simulator
- Scan QR code with Expo Go app for physical device

## 📊 API Documentation

### Authentication
```
POST   /signup          # Create new user
POST   /login           # User login
POST   /logout          # User logout
GET    /me              # Get current user
```

### Pools
```
GET    /pools                    # List all pools
POST   /pools/create             # Create new pool
GET    /pools/{pool_id}          # Get pool details
POST   /pools/{pool_id}/join     # Join a pool
GET    /pools/{pool_id}/leaderboard  # Get rankings
```

### Picks
```
POST   /picks                    # Make a prediction
GET    /picks/user/{user_id}    # User's picks
GET    /picks/pool/{pool_id}    # Pool's all picks
PUT    /picks/{pick_id}         # Update pick (before kickoff)
```

### Competitions & Fixtures
```
GET    /competitions/leagues              # Get leagues
GET    /competitions/teams                # Get teams
GET    /competitions/fixtures             # Get fixtures
POST   /external/football/fixtures/sync  # Sync from API
PUT    /external/football/fixtures/update/all  # Update results
```

### Admin
```
POST   /admin/process-results/{competition_id}/{gameweek}
```

## 🎮 How to Play

1. **Sign Up / Login**: Create an account or log in
2. **Join or Create Pool**: Enter a session code or create your own pool
3. **Select League**: Choose from 5 major European leagues
4. **Make Weekly Picks**: 
   - Pick one team per gameweek
   - Your team must win or draw
   - Can't pick same team more than 2x per season
5. **Earn Points**: Win = 3pts, Draw = 1pt, Loss = -1 life
6. **Survive**: Last player with lives remaining wins!

## 🛠️ Tech Stack

**Backend:**
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with async support
- **PostgreSQL** - Relational database
- **Alembic** - Database migrations
- **Bcrypt** - Password hashing
- **Pydantic** - Data validation
- **HTTPX** - Async HTTP client

**Frontend:**
- **React Native** - Cross-platform mobile framework
- **Expo** - Development toolchain
- **React Navigation** - Routing
- **Axios** - HTTP client
- **Ionicons** - Icon library

**External Services:**
- **API-Football (RapidAPI)** - Live football data
- **Railway** - Backend deployment

## 🔧 Key Technical Decisions

### Why FastAPI?
- Native async/await support for high concurrency
- Automatic API documentation with Swagger
- Fast performance comparable to Node.js
- Type hints and validation with Pydantic

### Why React Native?
- Cross-platform: one codebase for iOS and Android
- Large ecosystem and community support
- Hot reloading for faster development
- Easy integration with native features

### Database Design
- Normalized schema with proper foreign keys
- Unique constraints prevent duplicate picks
- Timezone-aware timestamps for global users
- Indexes on frequently queried columns

### Result Processing Algorithm
- Idempotent design: can run multiple times safely
- Batch processing for efficiency
- Atomic transactions prevent data corruption
- Flexible rules engine (eliminated players can continue, etc.)

## 🚢 Deployment

### Backend (Railway)
```bash
# Railway automatically detects Dockerfile
railway up
```

### Environment Variables
Set in Railway dashboard:
- `DATABASE_URL`
- `RAPIDAPI_KEY`
- `RAPIDAPI_HOST`
- `SECRET_KEY`
- `PORT` (automatically set by Railway)

## 📈 Future Enhancements

- [ ] Push notifications for fixture reminders
- [ ] In-app chat for pool members
- [ ] Historical statistics and analytics
- [ ] Custom scoring rules per pool
- [ ] Bracket-style tournaments
- [ ] Social features (follow friends, share results)
- [ ] Payment integration for paid pools
- [ ] Machine learning prediction suggestions

## 🐛 Known Issues

- [ ] Fixture updates require manual trigger
- [ ] No automatic result processing (admin endpoint required)
- [ ] Session management needs Redis for production scale

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👨‍💻 Author

**Michael Njoku**
- LinkedIn: [https://www.linkedin.com/in/michael-njoku-aa6159290/]
- GitHub: [https://github.com/NjokuM]

## 🙏 Acknowledgments

- API-Football for providing comprehensive football data
- Premier League, La Liga, Bundesliga, Serie A, Ligue 1 for inspiration
- FastAPI and React Native communities

---

⭐ Star this repo if you found it helpful!
