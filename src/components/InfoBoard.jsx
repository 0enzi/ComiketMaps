import { useEffect, useRef } from "react";

function ArtistProfile({ artist }) {
  const image = artist.avatar_url || artist.banner_url;
  return <article className="artist-profile">
    {artist.banner_url && <img className="artist-banner" src={artist.banner_url} alt="" onError={(event) => { event.currentTarget.style.display = "none"; }} />}
    <div className="artist-heading">
      {image && <img className="artist-avatar" src={image} alt="" onError={(event) => { event.currentTarget.style.display = "none"; }} />}
      <div><h3>{artist.display_name || artist.username}</h3><a href={artist.profile_url || `https://x.com/${artist.username}`} target="_blank" rel="noreferrer">@{artist.username}</a></div>
    </div>
    {artist.description && <p className="artist-description">{artist.description}</p>}
  </article>;
}

export default function InfoBoard({ event, day, map, mapPosition, mapCount, markers, selectedMarker, panelOpen, setPanelOpen, setSelectedMarker }) {
  const previous = useRef(null);
  const contentRef = useRef(null);
  useEffect(() => {
    if (selectedMarker && selectedMarker !== previous.current && !panelOpen) setPanelOpen(true);
    if (selectedMarker && contentRef.current) contentRef.current.scrollTo({ top: 0, behavior: "smooth" });
    previous.current = selectedMarker;
  }, [selectedMarker, panelOpen, setPanelOpen]);

  if (!panelOpen) return <button className="panel-toggle closed" onClick={() => setPanelOpen(true)} aria-label="Open booth list">☰</button>;
  return <aside className="info-board">
    <div className="panel-header">
      <div>
        <div className="panel-header-meta"><span>Current map</span><b>{mapPosition} / {mapCount}</b></div>
        <strong>{map.label}</strong>
        <span>{day.label}</span>
        {event?.data_status === "provisional-carry-over" && <em className="data-notice">Preview data · C107 carry-over</em>}
      </div>
      <button onClick={() => setPanelOpen(false)} aria-label="Close booth list">×</button>
    </div>
    <div className="panel-content" ref={contentRef}>
      {selectedMarker ? <section className="selected-booth">
        <div className="selected-heading"><div><strong>{selectedMarker.label}</strong><span>{selectedMarker.artists.length} artist{selectedMarker.artists.length === 1 ? "" : "s"}</span></div><button onClick={() => setSelectedMarker(null)} aria-label="Close booth details">×</button></div>
        {selectedMarker.artists.map((artist) => <ArtistProfile key={artist.artist_key} artist={artist} />)}
      </section> : <div className="empty-selection"><span className="empty-selection-icon">✦</span><strong>{markers.length ? "Choose a booth marker" : "No saved exhibitors here yet"}</strong><p>{markers.length ? "Select a marker or location below to see its details." : "Reviewed C108 locations will appear on this map when they are ready."}</p></div>}
      <section className="marker-list"><div className="list-heading"><div><strong>{markers.length ? "Locations on this map" : "Map locations"}</strong><small>{markers.length ? "Select a booth to inspect it" : "Nothing published for this map yet"}</small></div><span>{markers.length}</span></div>
        {markers.length === 0 && <p className="muted">The official map is ready. Followed exhibitors will be added after their C108 locations are reviewed.</p>}
        {markers.map((marker, index) => <button className={`marker-row ${selectedMarker?.id === marker.id ? "active" : ""}`} key={marker.id} onClick={() => setSelectedMarker(marker)}><span className="marker-number">{index + 1}</span><span className="marker-row-copy"><strong>{marker.label}</strong><small>{marker.artists.map((artist) => `@${artist.username}`).join(" · ")}</small></span>{marker.artists.length > 1 && <span className="count-badge">{marker.artists.length}</span>}</button>)}
      </section>
    </div>
  </aside>;
}
