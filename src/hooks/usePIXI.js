import { useCallback, useEffect, useRef, useState } from "react";
import * as PIXI from "pixi.js";
import { Viewport } from "pixi-viewport";
import { markerTableLabel } from "../data/markerLabel";
import { MAP_MARKER_SIZE, priorityPixiColor } from "../data/markerStyle";

const PIXI_ENABLED = import.meta.env.VITE_ENABLE_PIXI === "true";

function imageCoordinate(value, size) {
  const number = Number(value);
  return number >= 0 && number <= 1 ? number * size : number;
}

export function usePIXI(map, markers, onMarkerClick, onZoomChange) {
  const canvasRef = useRef(null);
  const appRef = useRef(null);
  const viewportRef = useRef(null);
  const spriteRef = useRef(null);
  const markersRef = useRef(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [initialized, setInitialized] = useState(false);
  const [pixiReady, setPixiReady] = useState(false);
  const [rendererFailed, setRendererFailed] = useState(!PIXI_ENABLED);
  const [loadError, setLoadError] = useState(null);
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });

  const setZoom = useCallback((value) => {
    setZoomLevel(value);
    onZoomChange?.(value);
  }, [onZoomChange]);

  const clearWorld = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    if (markersRef.current) { viewport.removeChild(markersRef.current); markersRef.current.destroy({ children: true }); markersRef.current = null; }
    if (spriteRef.current) { viewport.removeChild(spriteRef.current); spriteRef.current.destroy({ texture: false }); spriteRef.current = null; }
  }, []);

  const loadMap = useCallback(async () => {
    const viewport = viewportRef.current;
    if (!viewport || !map?.asset) {
      setPixiReady(false);
      return;
    }
    setLoadError(null);
    setPixiReady(false);
    clearWorld();
    const texture = await PIXI.Assets.load(map.asset);
    const sprite = new PIXI.Sprite(texture);
    sprite.anchor.set(0.5);
    const imageWidth = Number(map.width) || texture.width;
    const imageHeight = Number(map.height) || texture.height;
    viewport.worldWidth = imageWidth;
    viewport.worldHeight = imageHeight;
    sprite.x = imageWidth / 2;
    sprite.y = imageHeight / 2;
    spriteRef.current = sprite;
    viewport.addChild(sprite);
    const fit = Math.min(viewport.screenWidth / imageWidth, viewport.screenHeight / imageHeight) * 0.92;
    viewport.clampZoom({ minScale: fit, maxScale: 10 });
    viewport.setZoom(fit, true);
    viewport.moveCenter(sprite.x, sprite.y);
    setZoom(fit);

    const container = new PIXI.Container();
    markersRef.current = container;
    const left = sprite.x - sprite.width / 2;
    const top = sprite.y - sprite.height / 2;
    markers.forEach((marker) => {
      const point = new PIXI.Container();
      point.x = left + imageCoordinate(marker.x, imageWidth) * (sprite.width / imageWidth);
      point.y = top + imageCoordinate(marker.y, imageHeight) * (sprite.height / imageHeight);
      point.eventMode = "static"; point.cursor = "pointer";
      const box = new PIXI.Graphics();
      const halfMarkerSize = MAP_MARKER_SIZE / 2;
      box.rect(-halfMarkerSize, -halfMarkerSize, MAP_MARKER_SIZE, MAP_MARKER_SIZE).fill(priorityPixiColor(marker.priority)).stroke({ width: 1, color: 0x071016 });
      point.addChild(box);
      const number = new PIXI.Text({ text: markerTableLabel(marker), style: { fontFamily: "Arial", fontSize: 10, fill: 0x001010, fontWeight: "bold" } });
      number.anchor.set(0.5); point.addChild(number);
      if (marker.artists.length > 1) {
        const badgeOffset = halfMarkerSize;
        const badge = new PIXI.Graphics(); badge.circle(badgeOffset, -badgeOffset, 6).fill(0x1c292d).stroke({ width: 1, color: 0xffffff }); point.addChild(badge);
        const count = new PIXI.Text({ text: String(marker.artists.length), style: { fontFamily: "Arial", fontSize: 7, fill: 0xffffff, fontWeight: "bold" } }); count.anchor.set(0.5); count.x = badgeOffset; count.y = -badgeOffset; point.addChild(count);
      }
      point.on("pointerdown", (event) => { event.stopPropagation(); onMarkerClick(marker); });
      container.addChild(point);
    });
    viewport.addChild(container);
    setPixiReady(true);
  }, [clearWorld, map, markers, onMarkerClick, setZoom]);

  useEffect(() => {
    if (!PIXI_ENABLED) {
      return undefined;
    }
    if (appRef.current || !canvasRef.current) return undefined;
    let cancelled = false;
    (async () => {
      const app = new PIXI.Application();
      await app.init({ canvas: canvasRef.current, preference: "webgl", width: windowSize.width, height: windowSize.height, backgroundColor: 0x0a0a0a, resolution: window.devicePixelRatio || 1, antialias: true, autoDensity: true });
      if (cancelled) { app.destroy(true); return; }
      appRef.current = app;
      const viewport = new Viewport({ screenWidth: windowSize.width, screenHeight: windowSize.height, worldWidth: Number(map?.width) || windowSize.width, worldHeight: Number(map?.height) || windowSize.height, ticker: app.ticker, events: app.renderer.events, passiveWheel: false, stopPropagation: true });
      app.stage.addChild(viewport); viewportRef.current = viewport;
      viewport.drag({ pressDrag: false, wheel: false }).pinch({ factor: 1 }).wheel({ smooth: 10, interrupt: true }).decelerate().clamp({ direction: "all", underflow: "center" });
      viewport.clampZoom({ minScale: 0.1, maxScale: 10 });
      viewport.on("zoomed", () => { setZoom(viewport.scale.x); });
      setInitialized(true);
    })().catch((error) => {
      if (!cancelled) {
        setRendererFailed(true);
        setInitialized(false);
        console.warn("PIXI renderer unavailable; using the HTML map fallback.", error);
      }
    });
    return () => { cancelled = true; setInitialized(false); setPixiReady(false); clearWorld(); appRef.current?.destroy(true); appRef.current = null; viewportRef.current = null; };
  }, [clearWorld, map?.height, map?.width, setZoom, windowSize.height, windowSize.width]);

  // The async asset promise is an external system; publish its failure after the promise settles.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (initialized) loadMap().catch((error) => { window.setTimeout(() => setLoadError(error.message || "Could not load this map."), 0); console.error("Map loading failed", error); }); }, [initialized, loadMap]);

  useEffect(() => {
    const resize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener("resize", resize); return () => window.removeEventListener("resize", resize);
  }, []);

  const handleZoomIn = () => { const viewport = viewportRef.current; if (viewport) viewport.setZoom(Math.min(10, viewport.scale.x * 1.2), true); };
  const handleZoomOut = () => { const viewport = viewportRef.current; if (viewport) viewport.setZoom(Math.max(0.1, viewport.scale.x * 0.8), true); };
  const handleResetZoom = () => { if (viewportRef.current && spriteRef.current) { const viewport = viewportRef.current; const sprite = spriteRef.current; const fit = Math.min(viewport.screenWidth / sprite.width, viewport.screenHeight / sprite.height) * 0.92; viewport.setZoom(fit, true); viewport.moveCenter(sprite.x, sprite.y); setZoom(fit); } };
  return { canvasRef, zoomLevel, handleZoomIn, handleZoomOut, handleResetZoom, loadError, pixiReady, rendererFailed };
}
