# Input Device Blocker - Web UI

Modern React + Material-UI web interface for the Input Device Blocker.

## Features

- 🎨 **Modern UI**: Glassmorphism design with dark theme
- 📱 **Device Cards**: Visual cards for each input device
- 🔒 **One-Click Blocking**: Toggle device blocking with switches
- ⏱️ **Block Timer**: Set timed blocks with visual countdown
- 📊 **Statistics**: Charts showing block history and usage
- 🔔 **Real-time Updates**: WebSocket-powered live updates
- ⚡ **Quick Actions**: Block all / Unblock all buttons

## Tech Stack

### Frontend
- React 18 + TypeScript
- Material-UI (MUI) v5
- Framer Motion (animations)
- Recharts (statistics charts)
- Axios (API calls)
- Socket.io-client (WebSocket)

### Backend
- FastAPI (Python)
- WebSocket support
- Integration with existing device manager

## Quick Start

```bash
# Navigate to web-ui directory
cd web-ui

# Start both frontend and backend
./start-web-ui.sh
```

This will start:
- 📱 Frontend at http://localhost:3000
- 🔌 API at http://localhost:8000
- 📚 API Docs at http://localhost:8000/docs

## Manual Start

### Backend (API Server)
```bash
# From project root
pip install -r web-ui/requirements-api.txt
python -m uvicorn src.api.api_server:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (React)
```bash
cd web-ui
npm install
npm run dev
```

## Project Structure

```
web-ui/
├── src/
│   ├── components/       # React components
│   │   ├── DeviceCard/   # Device display card
│   │   ├── BlockTimer/   # Timer with progress
│   │   ├── StatusIndicator/
│   │   ├── StatisticsChart/
│   │   └── Header/
│   ├── pages/
│   │   └── Dashboard.tsx # Main dashboard
│   ├── services/
│   │   ├── api.ts        # REST API client
│   │   └── websocket.ts  # WebSocket client
│   ├── theme/
│   │   └── darkTheme.ts  # MUI theme config
│   ├── types/
│   │   └── index.ts      # TypeScript types
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
├── tsconfig.json
└── start-web-ui.sh
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices/list` | List all devices |
| POST | `/api/device/block` | Block a device |
| POST | `/api/device/unblock` | Unblock a device |
| POST | `/api/device/toggle` | Toggle device state |
| POST | `/api/devices/block-all` | Block all devices |
| POST | `/api/devices/unblock-all` | Unblock all devices |
| POST | `/api/timer/set` | Set block timer |
| POST | `/api/timer/cancel` | Cancel timer |
| GET | `/api/timer/status` | Get timer status |
| GET | `/api/stats` | Get statistics |
| GET | `/api/system/status` | Get system status |
| GET | `/api/settings` | Get settings |
| PUT | `/api/settings` | Update settings |

## Development

```bash
# Run in development mode
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## License

MIT License - Same as main project
