# Getting Started with AgenticRealm

## Quick Setup

### Backend (Python/FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

The backend will start at `http://localhost:8000`

### Frontend (JavaScript/Phaser)

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:5173`

---

## Accessing the Application

1. Open your browser to `http://localhost:5173`
2. Open DevTools (`F12`) → Console tab
3. Verify connection by checking: `socket.connected` (should be `true`)

---

## Testing

### Browser Console Commands

```javascript
// Check connection
socket.connected

// Request game state
requestState()

// Send an action
sendAction('move', { direction: 'forward' })

// Listen for state updates
socket.on('state_update', (state) => console.log('State:', state))
```

### Backend API

Visit `http://localhost:8000/docs` to see the API documentation.

### Integration Test

```bash
cd backend
source venv/bin/activate
python3 test_integration.py
```

---

## Troubleshooting

**Backend import errors?**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Frontend won't load?**
- Check that `npm run dev` is running
- Try accessing `http://127.0.0.1:5173` instead of localhost
- Vite server listens on all interfaces by default (0.0.0.0)

**Connection issues?**
- Verify both servers are running on correct ports
- Check browser console for WebSocket errors
- Backend must be running before accessing frontend

---

## What's Working

✅ Backend orchestration engine  
✅ Frontend Phaser.io integration  
✅ WebSocket communication  
✅ Game state management  
✅ Agent registration system  

## Next Steps

- Implement LLM agent logic
- Create game scenes and assets
- Add collision detection
- Build agent creation UI
