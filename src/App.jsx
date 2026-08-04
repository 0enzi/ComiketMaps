import React, { useEffect, useMemo, useState } from "react";
import TopBar from "./components/TopBar";
import InfoBoard from "./components/InfoBoard";
import PIXIViewer from "./components/PIXIViewer";
import { loadEvent, loadEventIndex, markersFor } from "./data/eventData";
import { latestEventEntry } from "./data/eventSelection";
import "./index.css";

function App() {
  const [eventIndex, setEventIndex] = useState(null);
  const [event, setEvent] = useState(null);
  const [eventId, setEventId] = useState("");
  const [dayId, setDayId] = useState("");
  const [mapId, setMapId] = useState("");
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadEventIndex()
      .then(async (index) => {
        if (cancelled) return;
        setEventIndex(index);
        const entry = latestEventEntry(index.events);
        if (!entry) throw new Error("No published Comiket events are available.");
        setEventId(entry.event_id);
        const loaded = await loadEvent(entry);
        if (cancelled) return;
        setEvent(loaded);
        setDayId(loaded.days[0]?.id || "");
        setMapId(loaded.maps[0]?.map_id || "");
      })
      .catch((reason) => !cancelled && setError(reason.message || "Could not load events."))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, []);

  const activeDay = event?.days.find((day) => day.id === dayId) || event?.days[0];
  const activeMap = event?.maps.find((map) => map.map_id === mapId) || event?.maps[0];
  const activeMapIndex = Math.max(0, event?.maps.findIndex((map) => map.map_id === activeMap?.map_id) ?? 0);
  const markers = useMemo(() => markersFor(event, activeDay?.id, activeMap?.map_id), [event, activeDay?.id, activeMap?.map_id]);

  const changeEvent = async (nextEventId) => {
    const entry = eventIndex?.events.find((item) => item.event_id === nextEventId);
    if (!entry) return;
    setLoading(true); setError(null); setSelectedMarker(null);
    try {
      const loaded = await loadEvent(entry);
      setEventId(nextEventId); setEvent(loaded); setDayId(loaded.days[0]?.id || ""); setMapId(loaded.maps[0]?.map_id || "");
    } catch (reason) { setError(reason.message || "Could not load this event."); }
    finally { setLoading(false); }
  };

  const changeDay = (nextDayId) => {
    setDayId(nextDayId); setSelectedMarker(null);
    const firstMap = event?.maps[0]?.map_id;
    if (firstMap) setMapId(firstMap);
  };

  if (loading && !event) return <div className="app-state">Loading event archive…</div>;
  if (error && !event) return <div className="app-state error"><h1>Could not load Comiket Maps</h1><p>{error}</p><button onClick={() => window.location.reload()}>Retry</button></div>;
  if (!event || !activeDay || !activeMap) return <div className="app-state">No map data is published yet.</div>;

  return (
    <main className="app-shell">
      <PIXIViewer map={activeMap} markers={markers} selectedMarker={selectedMarker} panelOpen={panelOpen} dayLabel={activeDay.label} onMarkerClick={setSelectedMarker} onZoomChange={setZoomLevel} isLoading={loading} />
      <TopBar
        event={event} eventEntries={eventIndex?.events || []} eventId={eventId} dayId={activeDay.id} mapId={activeMap.map_id} panelOpen={panelOpen}
        zoomLevel={zoomLevel} setEventId={changeEvent} setDayId={changeDay} setMapId={(id) => { setMapId(id); setSelectedMarker(null); }}
      />
      <InfoBoard event={event} day={activeDay} map={activeMap} mapPosition={activeMapIndex + 1} mapCount={event.maps.length} markers={markers} selectedMarker={selectedMarker} panelOpen={panelOpen} setPanelOpen={setPanelOpen} setSelectedMarker={setSelectedMarker} />
      {error && <div className="inline-error">{error}</div>}
    </main>
  );
}

export default App;
