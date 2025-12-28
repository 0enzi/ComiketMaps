import React, { useState, useEffect, useRef } from "react";
import RotateOverlay from "./components/RotateOverlay";
import TopBar from "./components/TopBar";
import InfoBoard from "./components/InfoBoard";
import PIXIViewer from "./components/PIXIViewer";
import "./index.css";

function App() {
  const [activeImage, setActiveImage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [panelOpen, setPanelOpen] = useState(true);
  const [activeDay, setActiveDay] = useState("Day 1");
  const [selectedMarker, setSelectedMarker] = useState(null);
  const [showRotateOverlay, setShowRotateOverlay] = useState(false);
  const [error, setError] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);

  const isTouchDevice =
    "ontouchstart" in window || navigator.maxTouchPoints > 0;
  const prevSelectedMarkerRef = useRef(null);

  useEffect(() => {
    console.log("App mounted");

    const checkOrientation = () => {
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
      const isPortrait = window.innerHeight > window.innerWidth;
      setShowRotateOverlay(isMobile && isPortrait);
    };

    checkOrientation();
    window.addEventListener("resize", checkOrientation);

    return () => {
      console.log("App unmounting");
      window.removeEventListener("resize", checkOrientation);
    };
  }, []);

  useEffect(() => {
    if (
      selectedMarker &&
      selectedMarker !== prevSelectedMarkerRef.current &&
      !panelOpen
    ) {
      console.log("Auto-opening panel for new marker selection");
      setPanelOpen(true);
    }

    prevSelectedMarkerRef.current = selectedMarker;
  }, [selectedMarker, panelOpen]);

  const handleMarkerClick = (marker) => {
    console.log(`Marker clicked: ${marker.title} (${marker.id})`);
    setSelectedMarker(marker);
  };

  const handleRetryLoad = () => {
    console.log("Retrying load...");
    setError(null);
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 1000);
  };

  const handleZoomChange = (newZoom) => {
    setZoomLevel(newZoom);
  };

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        backgroundColor: "#0a0a0a",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <PIXIViewer
        activeImage={activeImage}
        activeDay={activeDay}
        panelOpen={panelOpen}
        onMarkerClick={handleMarkerClick}
        isLoading={isLoading}
      />

      {!showRotateOverlay && (
        <TopBar
          activeDay={activeDay}
          activeImage={activeImage}
          zoomLevel={zoomLevel}
          setActiveDay={setActiveDay}
          setActiveImage={setActiveImage}
          setSelectedMarker={setSelectedMarker}
        />
      )}

      {showRotateOverlay && <RotateOverlay />}

      {!showRotateOverlay && (
        <InfoBoard
          activeDay={activeDay}
          activeImage={activeImage}
          selectedMarker={selectedMarker}
          panelOpen={panelOpen}
          setPanelOpen={setPanelOpen}
          setSelectedMarker={setSelectedMarker}
          zoomLevel={zoomLevel}
          isTouchDevice={isTouchDevice}
        />
      )}
    </div>
  );
}

export default App;
