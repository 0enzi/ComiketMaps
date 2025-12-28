import React, { useEffect, useRef } from "react";
import { infoBoardData } from "../data/infoBoardData";
import { markerData } from "../data/markerData";

const InfoBoard = ({
  activeDay,
  activeImage,
  selectedMarker,
  panelOpen,
  setPanelOpen,
  setSelectedMarker,
  zoomLevel,
  isTouchDevice,
}) => {
  const currentInfo =
    infoBoardData[activeDay]?.[activeImage] || infoBoardData["Day 1"][0];
  const markerCount = markerData[activeDay]?.[activeImage]?.length || 0;
  const currentDayMarkers = markerData[activeDay]?.[activeImage] || [];

  // FIX: Add this missing ref declaration
  const prevSelectedMarkerRef = useRef(null);

  // Auto-open panel when a marker is selected
  useEffect(() => {
    if (
      selectedMarker &&
      selectedMarker !== prevSelectedMarkerRef.current &&
      !panelOpen
    ) {
      console.log("Auto-opening panel for NEW marker selection");
      setPanelOpen(true);
    }

    // Update ref with current selection
    prevSelectedMarkerRef.current = selectedMarker;
  }, [selectedMarker, panelOpen, setPanelOpen]);

  if (!panelOpen) {
    return (
      <button
        onClick={() => setPanelOpen(true)}
        style={{
          position: "fixed",
          right: "20px",
          top: "50%",
          transform: "translateY(-50%)",
          width: "40px",
          height: "80px",
          background: activeDay === "Day 1" ? "#1a237e" : "#004d40",
          color: "white",
          border: "1px solid #333",
          borderRight: "none",
          borderRadius: "8px 0 0 8px",
          fontSize: "20px",
          cursor: "pointer",
          zIndex: 99,
        }}
      >
        →
      </button>
    );
  }

  // Helper to get marker number (1-based index)
  const getMarkerNumber = (marker) => {
    const index = currentDayMarkers.findIndex((m) => m.id === marker.id);
    return index >= 0 ? (index + 1).toString() : "?";
  };

  return (
    <div
      style={{
        position: "fixed",
        right: "0",
        top: "0",
        bottom: "0",
        width: "320px",
        background:
          activeDay === "Day 1" ? "rgba(0, 0, 0, 1)" : "rgba(0, 16, 13, 1)",
        borderLeft: "1px solid rgba(255, 255, 255, 0.1)",
        zIndex: 100,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        backdropFilter: "blur(10px)",
        transition: "background 0.3s ease",
      }}
    >
      <div
        style={{
          padding: "20px",
          background:
            activeDay === "Day 1" ? "rgba(0, 0, 0, 1)" : "rgba(0, 0, 0, 0.99)",
          borderBottom:
            activeDay === "Day 1"
              ? "1px solid rgba(0, 0, 0, 1)"
              : "1px solid rgba(0, 0, 0, 1)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h3
          style={{
            color: "white",
            margin: 0,
            fontSize: "18px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span>Comic Market</span>
          <br></br>
        </h3>

        <button
          onClick={() => setPanelOpen(false)}
          style={{
            width: "32px",
            height: "32px",
            background: "rgba(255, 255, 255, 0.1)",
            color: "white",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            borderRadius: "50%",
            fontSize: "20px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          ×
        </button>
      </div>

      <div style={{ padding: "20px", overflowY: "auto", flex: 1 }}>
        {selectedMarker ? (
          <div
            style={{
              background: "#000000",
              borderRadius: "12px",
              overflow: "hidden",
              border: "1px solid #333",
              marginBottom: "20px",
            }}
          >
            {/* Banner */}
            {selectedMarker.banner && (
              <div
                style={{
                  height: "120px",
                  backgroundImage: `url(${selectedMarker.banner})`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  position: "relative",
                }}
              >
                {/* Profile picture */}
                {selectedMarker.pfp && (
                  <div
                    style={{
                      position: "absolute",
                      bottom: "-40px",
                      left: "16px",
                      width: "80px",
                      height: "80px",
                      borderRadius: "50%",
                      border: "4px solid #000",
                      overflow: "hidden",
                      background: "#000",
                    }}
                  >
                    <img
                      src={selectedMarker.pfp}
                      alt=""
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "cover",
                      }}
                    />
                  </div>
                )}
              </div>
            )}

            <div
              style={{
                padding: "16px",
                paddingTop: selectedMarker.banner ? "50px" : "16px",
              }}
            >
              {/* Header with username and close */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  marginBottom: "16px",
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: "20px",
                      fontWeight: "bold",
                      color: "white",
                      lineHeight: "1.3",
                    }}
                  >
                    {selectedMarker.title}
                  </div>
                  {selectedMarker.handle && (
                    <div
                      style={{
                        fontSize: "14px",
                        color: "#888",
                        marginTop: "4px",
                      }}
                    >
                      {selectedMarker.handle}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setSelectedMarker(null)}
                  style={{
                    width: "32px",
                    height: "32px",
                    background: "rgba(255, 255, 255, 0.1)",
                    color: "white",
                    border: "1px solid #333",
                    borderRadius: "50%",
                    fontSize: "20px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  ×
                </button>
              </div>

              {/* Description */}
              {selectedMarker.description && (
                <div
                  style={{
                    fontSize: "14px",
                    lineHeight: "1.5",
                    color: "#ccc",
                    whiteSpace: "pre-wrap",
                    wordWrap: "break-word",
                    padding: "12px",
                    background: "rgba(255, 255, 255, 0.05)",
                    borderRadius: "8px",
                    border: "1px solid #333",
                  }}
                >
                  {selectedMarker.description.split("\n").map((line, i) => (
                    <div key={i} style={{ marginBottom: "8px" }}>
                      {line}
                    </div>
                  ))}
                </div>
              )}

              {/* Booth info if exists */}
              {selectedMarker.booth && (
                <div
                  style={{
                    fontSize: "14px",
                    color: "white",
                    padding: "10px",
                    background: "rgba(29, 155, 240, 0.1)",
                    borderRadius: "8px",
                    marginTop: "16px",
                    border: "1px solid rgba(29, 155, 240, 0.3)",
                    fontWeight: "500",
                  }}
                >
                  {selectedMarker.booth}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              borderRadius: "10px",
              padding: "20px",
              border: "1px solid rgba(255, 255,255, 0.1)",
              marginBottom: "20px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                color: activeDay === "Day 1" ? "#90caf9" : "#ffcc80",
                fontSize: "14px",
                marginBottom: "15px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <span>No Booth Selected</span>
            </div>
            <p
              style={{
                color: "#888",
                fontSize: "12px",
                lineHeight: "1.4",
                marginBottom: "15px",
              }}
            >
              Click on any numbered box on the map to see its details here.
            </p>
            <div
              style={{
                padding: "12px",
                background: "rgba(255, 255, 255, 0.02)",
                borderRadius: "6px",
                fontSize: "12px",
                color: activeDay === "Day 1" ? "#90caf9" : "#ffcc80",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              <span>
                {markerCount} booth{markerCount !== 1 ? "s" : ""} available on{" "}
                {activeDay}, Map {activeImage + 1}
              </span>
            </div>
          </div>
        )}

        <div
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            borderRadius: "10px",
            padding: "20px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            marginBottom: "20px",
          }}
        >
          <div
            style={{
              color: activeDay === "Day 1" ? "#2196f3" : "#ff9800",
              fontSize: "14px",
              fontWeight: "600",
              marginBottom: "15px",
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          ></div>
          <h4 style={{ color: "white", fontSize: "20px", margin: "10px 0" }}>
            Map {activeImage + 1} - {currentInfo.title}
          </h4>
          <div
            style={{ color: "#aaa", fontSize: "14px", marginBottom: "20px" }}
          >
            {currentInfo.description}
          </div>

          <div
            style={{
              marginTop: "20px",
              paddingTop: "20px",
              borderTop: "1px solid rgba(255,255,255,0.1)",
            }}
          >
            <div
              style={{
                color: "#ccc",
                fontSize: "12px",
                marginBottom: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>Available Markers ({markerCount})</span>
            </div>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                marginTop: "8px",
              }}
            >
              {currentDayMarkers.map((marker, index) => (
                <div
                  key={marker.id}
                  style={{
                    background:
                      activeDay === "Day 1"
                        ? "rgba(33, 150, 243, 0.1)"
                        : "rgba(255, 152, 0, 0.1)",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px solid rgba(255,255,255,0.1)",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    transition: "all 0.2s ease",
                  }}
                  onClick={() => setSelectedMarker(marker)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background =
                      activeDay === "Day 1"
                        ? "rgba(33, 150, 243, 0.2)"
                        : "rgba(255, 152, 0, 0.2)";
                    e.currentTarget.style.transform = "translateX(4px)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background =
                      activeDay === "Day 1"
                        ? "rgba(33, 150, 243, 0.1)"
                        : "rgba(255, 152, 0, 0.1)";
                    e.currentTarget.style.transform = "translateX(0)";
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        color: "white",
                        fontWeight: "bold",
                        fontSize: "14px",
                      }}
                    >
                      {marker.title}
                    </div>
                    <div
                      style={{
                        color: "#aaa",
                        fontSize: "12px",
                        marginTop: "2px",
                      }}
                    >
                      {marker.description}
                    </div>
                    <div
                      style={{
                        color: activeDay === "Day 1" ? "#90caf9" : "#ffcc80",
                        fontSize: "11px",
                        marginTop: "4px",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <span
                        style={{
                          background: "rgba(255,255,255,0.1)",
                          padding: "2px 6px",
                          borderRadius: "3px",
                          textTransform: "uppercase",
                          fontWeight: "500",
                        }}
                      >
                        {marker.type}
                      </span>
                      <span>#{index + 1}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfoBoard;
