import { useEffect, useRef } from "react";
import Icon from "./Icon";
import { normalizePriority, priorityLabel } from "../data/markerStyle";

function ArtistProfile({ artist }) {
  const image = artist.avatar_url || artist.banner_url;
  return <article className="artist-profile">
    {artist.banner_url && <img className="artist-banner" src={artist.banner_url} alt="" loading="lazy" onError={(event) => { event.currentTarget.style.display = "none"; }} />}
    <div className="artist-heading">
      {image && <img className="artist-avatar" src={image} alt="" loading="lazy" onError={(event) => { event.currentTarget.style.display = "none"; }} />}
      <div className="artist-heading-copy"><h3>{artist.display_name || artist.username}</h3><a href={artist.profile_url || `https://x.com/${artist.username}`} target="_blank" rel="noreferrer">@{artist.username} <Icon name="external" size={12} /></a></div>
    </div>
    {artist.description && <p className="artist-description">{artist.description}</p>}
  </article>;
}

export default function InfoBoard({ event, day, map, mapPosition, mapCount, markers, doneMarkerIds, selectedMarker, panelOpen, setPanelOpen, setSelectedMarker, onToggleDone, onClearDone }) {
  const previous = useRef(null);
  const contentRef = useRef(null);
  const doneCount = markers.filter((marker) => doneMarkerIds.has(marker.id)).length;
  const totalDone = doneMarkerIds.size;
  const selectedDone = selectedMarker ? doneMarkerIds.has(selectedMarker.id) : false;
  useEffect(() => {
    if (selectedMarker && selectedMarker !== previous.current && !panelOpen) setPanelOpen(true);
    if (selectedMarker && contentRef.current) contentRef.current.scrollTo({ top: 0, behavior: "smooth" });
    previous.current = selectedMarker;
  }, [selectedMarker, panelOpen, setPanelOpen]);

  if (!panelOpen) return <button className="panel-toggle closed" onClick={() => setPanelOpen(true)} aria-label="Open booth list" title="Open booth list"><Icon name="list" size={19} /></button>;
  return <aside className="info-board" aria-label="Map details">
    <div className="panel-header">
      <div>
        <div className="panel-header-meta"><span><Icon name="map" size={13} /> Current map</span><b>{mapPosition} / {mapCount}</b></div>
        <strong>{map.label}</strong>
        <span>{day.label}</span>
        {event?.data_status === "provisional-carry-over" && <em className="data-notice">Preview data · C107 carry-over</em>}
      </div>
      <button onClick={() => setPanelOpen(false)} aria-label="Close booth list" title="Close booth list"><Icon name="x" size={18} /></button>
    </div>
    <div className="panel-content" ref={contentRef}>
      {selectedMarker ? <section className="selected-booth">
        <div className="selected-heading"><div><span className="eyebrow"><Icon name="pin" size={13} /> Selected booth</span><strong>{selectedMarker.label}</strong><span>{selectedMarker.artists.length} artist{selectedMarker.artists.length === 1 ? "" : "s"}</span><span className={`priority-pill priority-${normalizePriority(selectedMarker.priority)}`}>{priorityLabel(selectedMarker.priority)}</span></div><div className="selected-actions"><button className={`done-button ${selectedDone ? "is-done" : ""}`} onClick={() => onToggleDone(selectedMarker.id)} aria-pressed={selectedDone} title={selectedDone ? "Mark booth as not done" : "Mark booth as done"}><Icon name="check" size={15} />{selectedDone ? "Done" : "Mark done"}</button><button onClick={() => setSelectedMarker(null)} aria-label="Close booth details" title="Clear selection"><Icon name="x" size={16} /></button></div></div>
        {selectedMarker.artists.map((artist) => <ArtistProfile key={artist.artist_key} artist={artist} />)}
      </section> : <div className="empty-selection"><span className="empty-selection-icon"><Icon name={markers.length ? "pin" : "map"} size={17} /></span><strong>{markers.length ? "Choose a booth marker" : "No saved exhibitors here yet"}</strong><p>{markers.length ? "Select a marker or location below to see its details." : "Reviewed C108 locations will appear on this map when they are ready."}</p></div>}
      <section className="marker-list"><div className="list-heading"><div><div className="list-title"><Icon name="list" size={15} /><strong>{markers.length ? "Locations on this map" : "Map locations"}</strong><span className="count-badge">{markers.length}</span></div><small>{markers.length ? `${doneCount}/${markers.length} done · select a booth to inspect it` : "Nothing published for this map yet"}</small></div><div className="list-heading-actions"><div className="priority-legend" aria-label="Marker priority colors" title="Marker priority colors"><span><i className="priority-dot priority-0" />0</span><span><i className="priority-dot priority-5" />5</span><span><i className="priority-dot priority-10" />10</span></div>{totalDone > 0 && <button className="clear-done-button" onClick={onClearDone} title="Clear all done markers for this event"><Icon name="x" size={12} />Clear done</button>}</div></div>
        {markers.length === 0 && <p className="muted">The official map is ready. Followed exhibitors will be added after their C108 locations are reviewed.</p>}
        {markers.map((marker, index) => { const isDone = doneMarkerIds.has(marker.id); return <button className={`marker-row ${selectedMarker?.id === marker.id ? "active" : ""} ${isDone ? "done" : ""}`} key={marker.id} onClick={() => setSelectedMarker(marker)} aria-pressed={selectedMarker?.id === marker.id}><span className={`marker-number priority-${normalizePriority(marker.priority)}`} title={priorityLabel(marker.priority)}>{index + 1}</span><span className="marker-row-copy"><strong>{marker.label}</strong><small>{marker.artists.map((artist) => `@${artist.username}`).join(" · ")}</small></span>{isDone && <span className="done-label"><Icon name="check" size={12} />Done</span>}{marker.artists.length > 1 && <span className="count-badge">{marker.artists.length}</span>}<Icon className="row-chevron" name="chevronRight" size={14} /></button>; })}
      </section>
    </div>
  </aside>;
}
