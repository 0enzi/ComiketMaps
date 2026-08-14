import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import CrashBoundary from './components/CrashBoundary.jsx'
import { installGlobalDiagnostics } from './data/diagnostics.js'

installGlobalDiagnostics()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <CrashBoundary>
      <App />
    </CrashBoundary>
  </React.StrictMode>,
)
