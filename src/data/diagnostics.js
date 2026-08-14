const STORAGE_KEY = "comiket-map-diagnostics-v1";
const MAX_ENTRIES = 80;
const subscribers = new Set();

function readEntries() {
  if (typeof window === "undefined") return [];
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(stored) ? stored.slice(-MAX_ENTRIES) : [];
  } catch {
    return [];
  }
}

let entries = readEntries();

function serializableDetails(details) {
  try {
    return JSON.parse(JSON.stringify(details));
  } catch {
    return { value: String(details) };
  }
}

function saveEntries() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // Diagnostics must never become another failure mode.
  }
  subscribers.forEach((subscriber) => {
    try {
      subscriber();
    } catch {
      // A diagnostics subscriber must not affect the app being observed.
    }
  });
}

function environmentSnapshot() {
  if (typeof window === "undefined") return {};
  const visualViewport = window.visualViewport;
  return {
    url: window.location.href,
    userAgent: navigator.userAgent,
    devicePixelRatio: window.devicePixelRatio,
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    screenWidth: window.screen?.width,
    screenHeight: window.screen?.height,
    assets: [
      ...[...document.scripts].map((script) => script.src).filter(Boolean),
      ...[...document.querySelectorAll('link[rel="stylesheet"]')].map((link) => link.href).filter(Boolean),
    ],
    visualViewport: visualViewport ? {
      width: visualViewport.width,
      height: visualViewport.height,
      scale: visualViewport.scale,
      offsetLeft: visualViewport.offsetLeft,
      offsetTop: visualViewport.offsetTop,
    } : null,
  };
}

export function recordDiagnostic(type, details = {}) {
  if (typeof window === "undefined") return;
  entries = [...entries.slice(-(MAX_ENTRIES - 1)), {
    time: new Date().toISOString(),
    type,
    details: serializableDetails(details),
  }];
  saveEntries();
}

export function diagnosticReport() {
  return {
    capturedAt: new Date().toISOString(),
    environment: environmentSnapshot(),
    entries: [...entries],
  };
}

export function clearDiagnostics() {
  entries = [];
  saveEntries();
}

export function subscribeDiagnostics(subscriber) {
  subscribers.add(subscriber);
  return () => subscribers.delete(subscriber);
}

function errorDescription(value) {
  if (value instanceof Error) return { name: value.name, message: value.message, stack: value.stack };
  return { message: typeof value === "string" ? value : String(value) };
}

export function installGlobalDiagnostics() {
  if (typeof window === "undefined" || window.__comiketDiagnosticsInstalled) return;
  window.__comiketDiagnosticsInstalled = true;
  recordDiagnostic("session-start", environmentSnapshot());

  window.addEventListener("error", (event) => {
    recordDiagnostic("window-error", {
      message: event.message,
      filename: event.filename,
      line: event.lineno,
      column: event.colno,
      error: errorDescription(event.error),
    });
  });
  window.addEventListener("unhandledrejection", (event) => {
    recordDiagnostic("unhandled-rejection", errorDescription(event.reason));
  });
  window.addEventListener("pagehide", (event) => recordDiagnostic("page-hide", { persisted: event.persisted }));
  window.addEventListener("pageshow", (event) => recordDiagnostic("page-show", { persisted: event.persisted }));
  document.addEventListener("visibilitychange", () => recordDiagnostic("visibility", { state: document.visibilityState }));
}
