import Icon from "./Icon";

const TopBar = ({ event, eventEntries, eventId, dayId, mapId, zoomLevel, panelOpen, offlineReady, onOfflineHelp, setEventId, setDayId, setMapId }) => {
  const mapIndex = Math.max(0, event.maps.findIndex((map) => map.map_id === mapId));
  const map = event.maps[mapIndex];
  const day = event.days.find((item) => item.id === dayId) || event.days[0];
  const moveMap = (offset) => {
    const next = event.maps[(mapIndex + offset + event.maps.length) % event.maps.length];
    if (next) setMapId(next.map_id);
  };
  return (
    <header className={`top-bar ${panelOpen ? "with-panel" : ""}`}>
      <div className="top-brand">
        <div className="brand-kicker"><Icon name="map" size={13} /> <span>Comiket maps</span><i>·</i><span>event archive</span></div>
        <strong>{event.name}</strong>
        <span>{event.data_status === "provisional-carry-over" ? "Preview · C107 booth assignments" : event.attribution?.split(".")[0]}</span>
      </div>
      <div className="top-controls">
        {eventEntries.length > 1 && <label className="select-control"><Icon name="layers" size={14} /><span>Event</span><select value={eventId} onChange={(e) => setEventId(e.target.value)} aria-label="Event">{eventEntries.map((item) => <option key={item.event_id} value={item.event_id}>{item.event_id}</option>)}</select></label>}
        <label className="select-control"><Icon name="calendar" size={14} /><span>Day</span><select value={day.id} onChange={(e) => setDayId(e.target.value)} aria-label="Day">{event.days.map((item) => <option key={item.id} value={item.id}>Day {item.number}</option>)}</select></label>
        <button className={`offline-button ${offlineReady ? "ready" : ""}`} onClick={onOfflineHelp} aria-label="Use Comiket Maps offline" title="Use Comiket Maps offline"><Icon name="download" size={16} /><span>{offlineReady ? "Saved" : "Offline"}</span></button>
        <button className="nav-button" aria-label="Previous map" title="Previous map" onClick={() => moveMap(-1)}><Icon name="chevronLeft" size={18} /></button>
        <span className="map-status"><span className="map-status-kicker"><Icon name="map" size={12} /> Map {mapIndex + 1} / {event.maps.length}</span><strong>{map?.label}</strong><small>{day.label}</small></span>
        <button className="nav-button" aria-label="Next map" title="Next map" onClick={() => moveMap(1)}><Icon name="chevronRight" size={18} /></button>
      </div>
      <div className="zoom-readout" aria-label="Current zoom"><Icon name="zoom" size={14} /><strong>{Number(zoomLevel || 1).toFixed(1)}×</strong></div>
    </header>
  );
};

export default TopBar;
