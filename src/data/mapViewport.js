export const MAP_MAX_SCALE = 4;
export const MAP_MOBILE_MAX_SCALE = 4;

export function fitMapScale(frameWidth, frameHeight, imageWidth, imageHeight) {
  const values = [frameWidth, frameHeight, imageWidth, imageHeight].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return 0.08;
  return Math.min(values[0] / values[2], values[1] / values[3]);
}

export function clampMapScale(scale, minimumScale, maximumScale = MAP_MAX_SCALE) {
  return Math.min(maximumScale, Math.max(minimumScale, Number(scale)));
}

export function clampMapView(view, frameWidth, frameHeight, imageWidth, imageHeight) {
  const values = [frameWidth, frameHeight, imageWidth, imageHeight, view?.scale].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return view;

  const [width, height, sourceWidth, sourceHeight, scale] = values;
  const clampPosition = (position, frameSize, scaledSize) => {
    const value = Number(position);
    if (scaledSize <= frameSize) return (frameSize - scaledSize) / 2;
    const safeValue = Number.isFinite(value) ? value : (frameSize - scaledSize) / 2;
    return Math.min(0, Math.max(frameSize - scaledSize, safeValue));
  };

  return {
    ...view,
    scale,
    x: clampPosition(view.x, width, sourceWidth * scale),
    y: clampPosition(view.y, height, sourceHeight * scale),
  };
}

export function visibleMapRect(view, frameWidth, frameHeight, imageWidth, imageHeight) {
  const values = [view?.scale, view?.x, view?.y, frameWidth, frameHeight, imageWidth, imageHeight].map(Number);
  if (values.some((value) => !Number.isFinite(value)) || values[0] <= 0 || values.slice(3).some((value) => value <= 0)) return null;

  const [scale, x, y, width, height, sourceWidth, sourceHeight] = values;
  const destinationX = Math.max(0, x);
  const destinationY = Math.max(0, y);
  const destinationRight = Math.min(width, x + sourceWidth * scale);
  const destinationBottom = Math.min(height, y + sourceHeight * scale);
  const destinationWidth = destinationRight - destinationX;
  const destinationHeight = destinationBottom - destinationY;
  if (destinationWidth <= 0 || destinationHeight <= 0) return null;

  return {
    sourceX: (destinationX - x) / scale,
    sourceY: (destinationY - y) / scale,
    sourceWidth: destinationWidth / scale,
    sourceHeight: destinationHeight / scale,
    destinationX,
    destinationY,
    destinationWidth,
    destinationHeight,
  };
}
