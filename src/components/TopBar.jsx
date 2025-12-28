import { markerData } from '../data/markerData';
import MarkerNumberBox from './MarkerNumberBox';

const TopBar = ({ 
  activeDay, 
  activeImage, 
  zoomLevel, 
  setActiveDay, 
  setActiveImage,
  setSelectedMarker 
}) => {
  const markerCount = markerData[activeDay]?.[activeImage]?.length || 0;

  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: 60,
      background: activeDay === 'Day 1' 
        ? 'linear-gradient(to bottom, rgba(26, 35, 126, 0.9) 0%, rgba(26, 35, 126, 0) 100%)'
        : 'linear-gradient(to bottom, rgba(0, 77, 64, 0.9) 0%, rgba(0, 77, 64, 0) 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      zIndex: 100,
      transition: 'background 0.3s ease'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'rgba(0, 0, 0, 1)',
        padding: '8px 15px',
        borderRadius: 30,
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <select 
          value={activeDay}
          onChange={(e) => {
            console.log(`Day changed to: ${e.target.value}`);
            setActiveDay(e.target.value);
            setSelectedMarker(null);
          }}
          style={{
            background:  'rgba(0, 0, 0, 1)',
            color: 'white',
            border: 'none',
            padding: '8px 12px',
            borderRadius: 6,
            fontSize: 14,
            cursor: 'pointer',
            minWidth: 100,
            fontWeight: 'bold'
          }}
        >
          <option value="Day 1">Day 1</option>
          <option value="Day 2">Day 2</option>
        </select>
      </div>
      
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'rgba(0,0,0,0.6)',
        padding: '8px 15px',
        borderRadius: 30,
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)'
      }}>
        <button 
          onClick={() => {
            console.log('Previous image');
            setActiveImage(prev => (prev - 1 + 4) % 4);
            setSelectedMarker(null);
          }}
          style={{
            width: 36,
            height: 36,
            background: 'rgba(255,255,255,0.1)',
            color: 'white',
            border: 'none',
            borderRadius: '50%',
            fontSize: 18,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.transform = 'scale(1.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          ←
        </button>
        
        <div style={{ 
          color: 'white', 
          fontSize: 16, 
          fontWeight: 500, 
          minWidth: 100, 
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '2px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>Map {activeImage + 1} / 4</span>
          </div>
          <div style={{
            fontSize: 12,
            color: activeDay === 'Day 1' ? '#90caf9' : '#ffcc80',
            marginTop: 2
          }}>
            Found {markerCount} booths.
          </div>
        </div>
        
        <button 
          onClick={() => {
            console.log('Next image');
            setActiveImage(prev => (prev + 1) % 4);
            setSelectedMarker(null);
          }}
          style={{
            width: 36,
            height: 36,
            background: 'rgba(255,255,255,0.1)',
            color: 'white',
            border: 'none',
            borderRadius: '50%',
            fontSize: 18,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.2)';
            e.currentTarget.style.transform = 'scale(1.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          →
        </button>
      </div>
      
      <div style={{
        background: 'rgba(0,0,0,0.6)',
        color: 'white',
        padding: '8px 15px',
        borderRadius: 30,
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        fontSize: 14,
        display: 'flex',
        alignItems: 'center',
        gap: 10
      }}>
        <MarkerNumberBox 
          number={activeDay === 'Day 1' ? '❶' : '❷'} 
          day={activeDay} 
          size={28}
          fontSize={14}
          style={{ border: '2px solid rgba(255,255,255,0.3)' }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <div style={{ color: '#ccc', fontSize: '11px' }}>Zoom</div>
          <div style={{ fontWeight: 'bold' }}>{zoomLevel.toFixed(1)}x</div>
        </div>
      </div>
    </div>
  );
};

export default TopBar;