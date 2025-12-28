const RotateOverlay = () => (
  <div style={{
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: '#0a0a0a',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    padding: 20,
    textAlign: 'center',
    zIndex: 1000
  }}>
    <div style={{ fontSize: 60, marginBottom: 20 }}>↻</div>
    <h1 style={{ marginBottom: 10, fontSize: '24px' }}>Rotate to Landscape</h1>
    <p style={{ color: '#aaa', marginBottom: 30, fontSize: '16px' }}>
      This map viewer works best in landscape mode
    </p>
  </div>
);

export default RotateOverlay;