import { usePIXI } from "../hooks/usePIXI";
import { useCallback, useEffect, useRef, useState } from "react";
import { clampMapScale, clampMapView, fitMapScale, MAP_MAX_SCALE, MAP_MOBILE_MAX_SCALE, visibleMapRect } from "../data/mapViewport";
import { markerTableLabel } from "../data/markerLabel";
import { normalizePriority, priorityLabel } from "../data/markerStyle";
import { recordDiagnostic } from "../data/diagnostics";

function imageCoordinate(value, size) {
  const number = Number(value);
  return number >= 0 && number <= 1 ? number * size : number;
}

function MapFallback({ map, markers, doneMarkerIds, selectedMarker, onMarkerClick, onZoomChange }) {
  const frameRef = useRef(null);
  const mapCanvasRef = useRef(null);
  const imageRef = useRef(null);
  const canvasErrorRef = useRef("");
  const dragRef = useRef(null);
  const pointersRef = useRef(new Map());
  const pinchRef = useRef(null);
  const [frame, setFrame] = useState({ width: 0, height: 0 });
  const [view, setView] = useState({ scale: 1, x: 0, y: 0 });
  const [imageState, setImageState] = useState({ asset: "", status: "loading" });
  const imageWidth = Number(map?.width) || 1720;
  const imageHeight = Number(map?.height) || 1215;
  const touchDevice = typeof navigator !== "undefined" && navigator.maxTouchPoints > 0;
  const maximumScale = touchDevice ? MAP_MOBILE_MAX_SCALE : MAP_MAX_SCALE;
  const imageReady = imageState.asset === map.asset && imageState.status === "ready";
  const imageError = imageState.asset === map.asset && imageState.status === "error";
  const markerScale = Math.min(1, Math.max(0.55, Math.sqrt(view.scale)));

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

  useEffect(() => {
    let cancelled = false;
    const asset = map.asset;
    const image = new Image();
    image.decoding = "async";
    image.onload = () => {
      if (cancelled) return;
      imageRef.current = image;
      setImageState({ asset, status: "ready" });
    };
    image.onerror = () => {
      if (cancelled) return;
      imageRef.current = null;
      setImageState({ asset, status: "error" });
    };
    image.src = asset;
    return () => {
      cancelled = true;
      image.onload = null;
      image.onerror = null;
      if (imageRef.current === image) imageRef.current = null;
    };
  }, [map.asset]);

  useEffect(() => {
    const canvas = mapCanvasRef.current;
    if (!canvas || !frame.width || !frame.height) return undefined;

    const animationFrame = window.requestAnimationFrame(() => {
      const pixelRatio = Math.min(2, Math.max(1, Number(window.devicePixelRatio) || 1));
      const canvasWidth = Math.max(1, Math.round(frame.width * pixelRatio));
      const canvasHeight = Math.max(1, Math.round(frame.height * pixelRatio));
      if (canvas.width !== canvasWidth) canvas.width = canvasWidth;
      if (canvas.height !== canvasHeight) canvas.height = canvasHeight;

      const context = canvas.getContext("2d", { alpha: true, desynchronized: true });
      if (!context) return;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      context.clearRect(0, 0, frame.width, frame.height);

      const image = imageRef.current;
      const visible = imageReady ? visibleMapRect(view, frame.width, frame.height, imageWidth, imageHeight) : null;
      if (!image || !visible) return;

      const sourceScaleX = image.naturalWidth / imageWidth;
      const sourceScaleY = image.naturalHeight / imageHeight;
      context.imageSmoothingEnabled = true;
      context.imageSmoothingQuality = "high";
      try {
        context.drawImage(
          image,
          visible.sourceX * sourceScaleX,
          visible.sourceY * sourceScaleY,
          visible.sourceWidth * sourceScaleX,
          visible.sourceHeight * sourceScaleY,
          visible.destinationX,
          visible.destinationY,
          visible.destinationWidth,
          visible.destinationHeight,
        );
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        if (canvasErrorRef.current !== message) {
          canvasErrorRef.current = message;
          recordDiagnostic("canvas-draw-error", { message, visible, canvasWidth, canvasHeight });
        }
      }
    });

    return () => window.cancelAnimationFrame(animationFrame);
  }, [frame.height, frame.width, imageHeight, imageReady, imageWidth, view]);

  const startDrag = (event) => {
    if (event.button !== 0) return;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    pointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointersRef.current.size === 2) {
      const [first, second] = [...pointersRef.current.values()];
      const distance = Math.max(1, Math.hypot(second.x - first.x, second.y - first.y));
      pinchRef.current = { distance, view, latestScale: view.scale, lastScaleBucket: Math.floor(view.scale * 2) };
      recordDiagnostic("pinch-start", {
        distance,
        scale: view.scale,
        frameWidth: frame.width,
        frameHeight: frame.height,
        canvasWidth: mapCanvasRef.current?.width,
        canvasHeight: mapCanvasRef.current?.height,
        imageWidth,
        imageHeight,
      });
      dragRef.current = null;
      return;
    }
    dragRef.current = { x: event.clientX, y: event.clientY, viewX: view.x, viewY: view.y };
  };
  const moveDrag = (event) => {
    if (pointersRef.current.has(event.pointerId)) {
      pointersRef.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    }
    const start = pinchRef.current;
    const frameElement = frameRef.current;
    if (pointersRef.current.size >= 2 && start && frameElement) {
      const [first, second] = [...pointersRef.current.values()];
      const distance = Math.max(1, Math.hypot(second.x - first.x, second.y - first.y));
      const midpoint = { x: (first.x + second.x) / 2, y: (first.y + second.y) / 2 };
      const rect = frameElement.getBoundingClientRect();
      const cursorX = midpoint.x - rect.left;
      const cursorY = midpoint.y - rect.top;
      const minimumScale = fitMapScale(frameElement.clientWidth, frameElement.clientHeight, imageWidth, imageHeight);
      const nextScale = clampMapScale(start.view.scale * distance / start.distance, minimumScale, maximumScale);
      const nextView = clampMapView({
        scale: nextScale,
        x: cursorX - (cursorX - start.view.x) * (nextScale / start.view.scale),
        y: cursorY - (cursorY - start.view.y) * (nextScale / start.view.scale),
      }, frameElement.clientWidth, frameElement.clientHeight, imageWidth, imageHeight);
      start.latestScale = nextScale;
      const scaleBucket = Math.floor(nextScale * 2);
      if (scaleBucket !== start.lastScaleBucket) {
        start.lastScaleBucket = scaleBucket;
        recordDiagnostic("pinch-scale", { scale: nextScale, x: nextView.x, y: nextView.y, distance, pointerCount: pointersRef.current.size });
      }
      setView(nextView);
      return;
    }
    if (!dragRef.current) return;
    const drag = dragRef.current;
    setView((current) => clampMapView({ ...current, x: drag.viewX + event.clientX - drag.x, y: drag.viewY + event.clientY - drag.y }, frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight));
  };
  const stopDrag = (event) => {
    const endingPinch = pinchRef.current;
    pointersRef.current.delete(event.pointerId);
    if (pointersRef.current.size < 2) {
      pinchRef.current = null;
      if (endingPinch) recordDiagnostic("pinch-end", { event: event.type, scale: endingPinch.latestScale, remainingPointers: pointersRef.current.size });
    }
    dragRef.current = null;
  };
  const zoomAt = useCallback((event) => {
    event.preventDefault();
    const rect = frameRef.current?.getBoundingClientRect();
    if (!rect) return;
    const factor = event.deltaY < 0 ? 1.15 : 0.87;
    setView((current) => {
      const minimumScale = fitMapScale(frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight);
      const nextScale = clampMapScale(current.scale * factor, minimumScale, maximumScale);
      const cursorX = event.clientX - rect.left;
      const cursorY = event.clientY - rect.top;
      return clampMapView({
        scale: nextScale,
        x: cursorX - (cursorX - current.x) * (nextScale / current.scale),
        y: cursorY - (cursorY - current.y) * (nextScale / current.scale),
      }, frameRef.current.clientWidth, frameRef.current.clientHeight, imageWidth, imageHeight);
    });
  }, [imageHeight, imageWidth, maximumScale]);

  useEffect(() => {
    const frameElement = frameRef.current;
    if (!frameElement) return undefined;
    frameElement.addEventListener("wheel", zoomAt, { passive: false });
    return () => frameElement.removeEventListener("wheel", zoomAt);
  }, [zoomAt]);

  return <div className="map-fallback" ref={frameRef} onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={stopDrag} onPointerCancel={stopDrag}>
    <canvas ref={mapCanvasRef} className="map-fallback-canvas" role="img" aria-label={`${map.label} map`} />
    <div className="map-fallback-markers" aria-hidden="false">
      {markers.map((marker) => <button
        type="button"
        className={`map-fallback-marker priority-${normalizePriority(marker.priority)} ${marker.id === selectedMarker?.id ? "selected" : ""} ${doneMarkerIds.has(marker.id) ? "done" : ""}`}
        key={marker.id}
        style={{
          left: view.x + imageCoordinate(marker.x, imageWidth) * view.scale,
          top: view.y + imageCoordinate(marker.y, imageHeight) * view.scale,
          "--marker-scale": markerScale,
        }}
        onPointerDown={(event) => event.stopPropagation()}
        onClick={() => onMarkerClick(marker)}
        aria-label={`${marker.label}, table ${markerTableLabel(marker)}, ${priorityLabel(marker.priority)}${doneMarkerIds.has(marker.id) ? ", done" : ""}`}
        aria-pressed={marker.id === selectedMarker?.id}
      >
        <span>{markerTableLabel(marker)}</span>
        {doneMarkerIds.has(marker.id) && <i aria-hidden="true">✓</i>}
        {marker.artists.length > 1 && <b>{marker.artists.length}</b>}
      </button>)}
    </div>
    {imageError && <div className="map-fallback-error">Map image could not be loaded.</div>}
    <div className="map-fallback-hint">{touchDevice ? "Drag to pan · pinch to zoom" : "Drag to pan · scroll to zoom"}</div>
    {(!frame.width || (!imageReady && !imageError)) && <div className="map-loading">Loading {map.label}…</div>}
  </div>;
}

export default function PIXIViewer({ map, markers, doneMarkerIds, selectedMarker, panelOpen, dayLabel, onMarkerClick, onZoomChange, isLoading }) {
  const { canvasRef, loadError, pixiReady, rendererFailed } = usePIXI(map, markers, doneMarkerIds, onMarkerClick, onZoomChange);
  const showFallback = rendererFailed || !pixiReady || Boolean(loadError);
  return <div className={`viewer-shell ${panelOpen ? "panel-open" : "panel-closed"}`}>
    {showFallback && <MapFallback map={map} markers={markers} doneMarkerIds={doneMarkerIds} selectedMarker={selectedMarker} onMarkerClick={onMarkerClick} onZoomChange={onZoomChange} />}
    <canvas ref={canvasRef} className={showFallback ? "pixi-canvas is-hidden" : "pixi-canvas"} />
    {isLoading && !showFallback && <div className="map-loading">Loading {dayLabel}…</div>}
    {loadError && <div className="map-error-toast"><span>Interactive renderer unavailable; map remains usable.</span></div>}
  </div>;
}
