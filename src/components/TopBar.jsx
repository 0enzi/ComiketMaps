const TopBar = ({ event, eventEntries, eventId, dayId, mapId, zoomLevel, panelOpen, setEventId, setDayId, setMapId }) => {
  const mapIndex = Math.max(0, event.maps.findIndex((map) => map.map_id === mapId));
  const map = event.maps[mapIndex];
  const day = event.days.find((item) => item.id === dayId) || event.days[0];
  const moveMap = (offset) => {
    const next = event.maps[(mapIndex + offset + event.maps.length) % event.maps.length];
    if (next) setMapId(next.map_id);
  };
  return (
    <header className={`top-bar ${panelOpen ? "with-panel" : ""}`}>
      <div className="top-brand"><strong>{event.name}</strong><span>{event.data_status === "provisional-carry-over" ? "Preview · C107 booth assignments" : event.attribution?.split(".")[0]}</span></div>
      <div className="top-controls">
        {eventEntries.length > 1 && <label><span>Event</span><select value={eventId} onChange={(e) => setEventId(e.target.value)} aria-label="Event">{eventEntries.map((item) => <option key={item.event_id} value={item.event_id}>{item.event_id}</option>)}</select></label>}
        <label><span>Day</span><select value={day.id} onChange={(e) => setDayId(e.target.value)} aria-label="Day">{event.days.map((item) => <option key={item.id} value={item.id}>Day {item.number}</option>)}</select></label>
        <button aria-label="Previous map" title="Previous map" onClick={() => moveMap(-1)}>←</button>
        <span className="map-status"><strong>{map?.label}</strong><small>Map {mapIndex + 1} of {event.maps.length}</small></span>
        <button aria-label="Next map" title="Next map" onClick={() => moveMap(1)}>→</button>
      </div>
      <div className="zoom-readout" aria-label="Current zoom">{Number(zoomLevel || 1).toFixed(1)}×</div>
    </header>
  );
};

export default TopBar;
