import { usePIXI } from '../hooks/usePIXI';
import { markerData } from '../data/markerData';

const PIXIViewer = ({ 
  activeImage, 
  activeDay, 
  panelOpen, 
  onMarkerClick,
  isLoading, 
  onRetryLoad // coming back to this for error handling
}) => {
  const { 
    canvasRef,
    zoomLevel,
    handleZoomIn,
    handleZoomOut,
    handleResetZoom,
    isMobile,
  } = usePIXI(activeImage, activeDay, markerData, onMarkerClick);

  return (
    <>
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: panelOpen ? 'calc(100vw - 320px)' : '100vw',
          height: '100vh',
          zIndex: 1,
          transition: 'width 0.3s ease',
          overflow: 'hidden'
        }}
      >
        <canvas
          ref={canvasRef}
          style={{
            display: 'block',
            width: '100%',
            height: '100%'
          }}
        />
        
        {/* LOADING OVERLAY */}
        {isLoading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0,0,0,0.7)',
            zIndex: 50
          }}>
            <div style={{
              background: activeDay === 'Day 1' 
                ? 'rgba(26, 35, 126, 0.9)' 
                : 'rgba(0, 77, 64, 0.9)',
              padding: '30px 40px',
              borderRadius: 15,
              textAlign: 'center',
              border: activeDay === 'Day 1' 
                ? '2px solid rgba(33, 150, 243, 0.5)' 
                : '2px solid rgba(255, 152, 0, 0.5)'
            }}>
              <div style={{ 
                color: 'white', 
                fontSize: 18, 
                marginBottom: 10,
                fontWeight: 'bold'
              }}>
                Loading {activeDay}, Map {activeImage + 1}...
              </div>
              <div style={{ 
                color: activeDay === 'Day 1' ? '#90caf9' : '#ffcc80', 
                fontSize: 14, 
                marginTop: 10 
              }}>
                Please wait while the map loads
              </div>
              <div style={{
                marginTop: 20,
                width: '100%',
                height: 4,
                background: 'rgba(255,255,255,0.1)',
                borderRadius: 2,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '100%',
                  height: '100%',
                  background: activeDay === 'Day 1' ? '#2196f3' : '#ff9800',
                  animation: 'loading 1.5s ease-in-out infinite'
                }}></div>
              </div>
            </div>
          </div>
        )}
        
        {/* Add CSS animation */}
        <style>{`
          @keyframes loading {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
        `}</style>
      </div>
    </>
  );
};

export default PIXIViewer;