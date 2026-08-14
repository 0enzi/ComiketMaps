export function fitMapScale(frameWidth, frameHeight, imageWidth, imageHeight) {
  const values = [frameWidth, frameHeight, imageWidth, imageHeight].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return 0.08;
  return Math.min(values[0] / values[2], values[1] / values[3]);
}

export function clampMapScale(scale, minimumScale, maximumScale = 8) {
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
