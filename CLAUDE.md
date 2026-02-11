# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AUTO-MAS-Lite is a MAA (Maa's Assistant) specialized lightweight version - a desktop automation management tool for the game Arknights. The project follows a full-stack desktop application architecture.

## Environment Setup

### Python Backend
```bash
pip install -r requirements.txt
python main.py  # Runs on port 36163, requires administrator
```

### Frontend (Vue 3 + Vite) - Web-only Mode
```bash
cd frontend
yarn install
yarn dev                    # Vite dev server (localhost:5173) - Web mode
yarn dev:fullstack         # Frontend + Backend (both ports)
yarn build                  # Production build (outputs to frontend/dist)
```

## Web-only Migration Status

### Completed ✅
- Added FastAPI static file serving in `main.py` for SPA support
- Created `frontend/src/utils/logger.ts` with web-compatible logger
- Added Electron detection via `'installPython' in window.electronAPI` check
- Lazy-loaded Monaco Editor (~3-5MB savings on initial load)
- Removed Electron dev dependencies from `package.json`
- Updated `frontend/src/main.ts` with web polyfills and detection
- Updated `frontend/src/views/Initialization/index.vue` to skip install steps in web mode
- Updated `frontend/src/views/Initialization/components/BackendStartStep.vue` to skip backend start in web mode
- **[Feb 11] TitleBar.vue** - Hidden window control buttons in Web mode, show appropriate messages
- **[Feb 11] config.ts** - Switched to localStorage for configuration persistence
- **[Feb 11] useFileSelection.ts** - Created Web UI file selection composable using HTML5 input

### Key Detection Pattern
```typescript
// In main.ts - detect real Electron API
const hasRealElectronAPI = typeof window !== 'undefined' &&
  window.electronAPI !== undefined &&
  'installPython' in (window as any).electronAPI
const isElectron = hasRealElectronAPI
```

### Files Modified for Web Compatibility
- `frontend/src/main.ts` - Main entry with web polyfills
- `frontend/src/utils/logger.ts` - Shared logger utility
- `frontend/src/utils/config.ts` - localStorage-based configuration (Web mode)
- `frontend/src/components/TitleBar.vue` - Hidden window controls in Web mode
- `frontend/src/composables/useFileSelection.ts` - Web file selection with HTML5 input
- `frontend/src/views/Initialization/index.vue` - Skip install steps in web mode
- `frontend/src/views/Initialization/components/BackendStartStep.vue` - Skip backend start in web mode
- `app/api/core.py` - Added CORS support for WebSocket

### In Progress 🔄
- File selection integration in components (GeneralScriptEdit, MAAScriptEdit, etc.)
- Backend file upload API endpoint

### Planned for Cleanup 🗑️
- Remove Electron IPC calls from remaining components
- Remove Electron file dialog calls
- Remove Electron window control methods
- General Electron API cleanup

## Architecture

```
AUTO-MAS-Lite/
├── main.py                  # Backend entry point (FastAPI on port 36163)
├── app/
│   ├── api/                # 12 API routers
│   │   ├── core.py         # Core operations
│   │   ├── info.py         # System info
│   │   ├── scripts.py      # Script management
│   │   ├── plan.py         # Plan configuration
│   │   ├── emulator.py     # Emulator management
│   │   ├── queue.py        # Queue management
│   │   ├── dispatch.py     # Task dispatch
│   │   ├── history.py      # History records
│   │   ├── setting.py      # Settings
│   │   ├── update.py       # Updates
│   │   ├── ocr.py          # OCR functionality
│   │   └── ws_debug.py     # WebSocket debug
│   ├── core/
│   │   ├── config.py       # Configuration management (Pydantic models)
│   │   ├── task_manager.py # MAA script execution
│   │   ├── timer.py        # MainTimer for scheduled tasks
│   │   └── emulator_manager.py
│   ├── task/
│   │   ├── MAA/            # MAA automation tasks
│   │   └── general/        # General automation tasks
│   ├── services/          # External services (notification, update, matomo)
│   └── utils/              # Utilities (ADB, emulator, OCR, websocket)
└── frontend/
    └── src/
        ├── main.ts         # Vue app entry
        ├── App.vue
        ├── router/         # Vue Router
        ├── api/            # Auto-generated from OpenAPI specs
        └── components/
```

## Key Patterns

- **Backend**: async/await throughout, Pydantic v2 models, loguru for logging
- **Frontend**: Vue 3 Composition API, Pinia for state, Ant Design Vue 4.x, Monaco Editor
- **Communication**: REST API + WebSocket for real-time updates; IPC for Electron main process
- **Configuration**: JSON files in `data/` directory, synced via WebSocket broadcasts

## Important Notes

- **Windows-only**: Uses pywin32, ctypes.windll.shell32, requires admin privileges
- **Admin requirement**: Backend auto-restarts with admin if not running as admin (main.py:202-205)
- **Ports**: 5173 (Vite dev), 36163 (FastAPI), MCP at /mcp
- **API clients**: Auto-generated in `frontend/src/api/` from OpenAPI specs
- **Frontend API BASE**: Set dynamically via `window.electronAPI.getApiEndpoint()` or defaults to `http://localhost:36163`

## Web Mode Behavior

When running in browser (not Electron):
- Initialization steps (Python/Pip/Git install) are skipped automatically
- Backend start step shows "Web mode: backend needs manual start"
- File dialogs and window controls show warnings or are disabled
- All logging falls back to `console.log/warn/error/debug`

## Running Web Mode

```bash
# Option 1: Frontend only (requires backend running separately)
cd frontend && yarn dev

# Option 2: Full stack (both frontend and backend)
cd frontend && yarn dev:fullstack

# Then open http://localhost:5173
# Or for production build:
cd frontend && yarn build
# Then access via http://localhost:36163 (backend serves static files)
```
