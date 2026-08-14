import { usePIXI } from "../hooks/usePIXI";
import { useCallback, useEffect, useRef, useState } from "react";
import { clampMapScale, clampMapView, fitMapScale } from "../data/mapViewport";
import { markerTableLabel } from "../data/markerLabel";
import { normalizePriority, priorityLabel } from "../data/markerStyle";

function imageCoordinate(value, size) {
  const number = Number(value);
  return number >= 0 && number <= 1 ? number * size : number;
}

function MapFallback({ map, markers, selectedMarker, onMarkerClick, onZoomChange }) {
  const frameRef = useRef(null);
  const dragRef = useRef(null);
  const pointersRef = useRef(new Map());
  const pinchRef = useRef(null);
  const [frame, setFrame] = useState({ width: 0, height: 0 });
  const [view, setView] = useState({ scale: 1, x: 0, y: 0 });
  const [imageError, setImageError] = useState(false);
  const imageWidth = Number(map?.width) || 1720;
  const imageHeight = Number(map?.height) || 1215;

  const fitImage = useCallback(() => {
    if (!frameRef.current) return;
    const width = frameRef.current.clientWidth;
    const height = frameRef.current.clientHeight;
    if (!width || !height) return;
    const scale = fitMapScale(width, height, imageWidth, imageHeight);
    setFrame({ width, height });
    setView(clampMapView({ scale, x: (width - imageWidth * scale) / 2, y: (height - imageHeight * scale) / 2 }, width, height, imageWidth, imageHeight));
  }, [imageHeight, imageWidth]);

  useEffect(() => {
    fitImage();
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(fitImage) : null;
    if (observer && frameRef.current) observer.observe(frameRef.current);
    return () => observer?.disconnect();
  }, [fitImage]);

  useEffect(() => { onZoomChange?.(view.scale); }, [onZoomChange, view.scale]);

  const startDrag = (event) => {
    if (event.button !== 0) return;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    pointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointersRef.current.size === 2) {
      const [first, second] = [...pointersRef.current.values()];
      const distance = Math.hypot(second.x - first.x, second.y - first.y);
      pinchRef.current = { distance, view };
      dragRef.current = null;
      return;
    }
    dragRef.current = { x: event.clientX, y: event.clientY, viewX: view.x, viewY: view.y };
  };
  const moveDrag = (event) => {
    if (pointersRef.current.has(event.pointerId)) {
      pointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    }
    if (pointersRef.current.size >= 2 && pinchRef.current && frameRef.current) {
      const [first, second] = [...pointersRef.current.values()];
      const distance = Math.max(1, Math.hypot(second.x - first.x, second.y - first.y));
      const midpoint = { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 };
      const rect = frameRef.current.getBoundingClientRect();
      const cursorX = midpoint.x - rect.left;
      const cursorY = midpoint.y - rect.top;
      setView(() => {
        const start = pinchRef.current;
        const minimumScale = fitMapScale(frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight);
        const nextScale = clampMapScale(start.view.scale * distance / start.distance, minimumScale);
        return clampMapView({
          scale: nextScale,
          x: cursorX - (cursorX - start.view.x) * (nextScale / start.view.scale),
          y: cursorY - (cursorY - start.view.y) * (nextScale / start.view.scale),
        }, frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight);
      });
      return;
    }
    if (!dragRef.current) return;
    const drag = dragRef.current;
    setView((current) => clampMapView({ ...current, x: drag.viewX + event.clientX - drag.x, y: drag.viewY + event.clientY - drag.y }, frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight));
  };
  const stopDrag = (event) => {
    pointersRef.current.delete(event.pointerId);
    if (pointersRef.current.size < 2) pinchRef.current = null;
    dragRef.current = null;
  };
  const zoomAt = (event) => {
    event.preventDefault();
    const rect = frameRef.current?.getBoundingClientRect();
    if (!rect) return;
    const factor = event.deltaY < 0 ? 1.15 : 0.87;
    setView((current) => {
      const minimumScale = fitMapScale(frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight);
      const nextScale = clampMapScale(current.scale * factor, minimumScale);
      const cursorX = event.clientX - rect.left;
      const cursorY = event.clientY - rect.top;
      return clampMapView({
        scale: nextScale,
        x: cursorX - (cursorX - current.x) * (nextScale / current.scale),
        y: cursorY - (cursorY - current.y) * (nextScale / current.scale),
      }, frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight);
    });
  };

  return <div className="map-fallback" ref={frameRef} onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={stopDrag} onPointerCancel={stopDrag} onWheel={zoomAt}>
    <div className="map-fallback-stage" style={{ width: imageWidth, height: imageHeight, transform: `translate3d(${view.x}px, ${view.y}px, 0) scale(${view.scale})` }}>
      {!imageError ? <img src={map.asset} alt={`${map.label} map`} draggable="false" onError={() => setImageError(true)} /> : <div className="map-fallback-error">Map image could not be loaded.</div>}
      {markers.map((marker) => <button
        type="button"
        className={`map-fallback-marker priority-${normalizePriority(marker.priority)} ${marker.id === selectedMarker?.id ? "selected" : ""}`}
        key={marker.id}
        style={{
          left: imageCoordinate(marker.x, imageWidth),
          top: imageCoordinate(marker.y, imageHeight),
        }}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={() => onMarkerClick(marker)}
        aria-label={`${marker.label}, table ${markerTableLabel(marker)}, ${priorityLabel(marker.priority)}`}
        aria-pressed={marker.id === selectedMarker?.id}
      >
        <span>{markerTableLabel(marker)}</span>
        {marker.artists.length > 1 && <b>{marker.artists.length}</b>}
      </button>)}
    </div>
    <div className="map-fallback-hint">Drag to pan · scroll to zoom</div>
    {!frame.width && <div className="map-loading">Loading {map.label}…</div>}
  </div>;
}

export default function PIXIViewer({ map, markers, selectedMarker, panelOpen, dayLabel, onMarkerClick, onZoomChange, isLoading }) {
  const { canvasRef, loadError, pixiReady, rendererFailed } = usePIXI(map, markers, onMarkerClick, onZoomChange);
  const showFallback = rendererFailed || !pixiReady || Boolean(loadError);
  return <div className={`viewer-shell ${panelOpen ? "panel-open" : "panel-closed"}`}>
    {showFallback && <MapFallback map={map} markers={markers} selectedMarker={selectedMarker} onMarkerClick={onMarkerClick} onZoomChange={onZoomChange} />}
    <canvas ref={canvasRef} className={showFallback ? "pixi-canvas is-hidden" : "pixi-canvas"} />
    {isLoading && !showFallback && <div className="map-loading">Loading {dayLabel}…</div>}
    {loadError && <div className="map-error-toast"><span>Interactive renderer unavailable; map remains usable.</span></div>}
  </div>;
}
