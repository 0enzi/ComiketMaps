export function fitMapScale(frameWidth, frameHeight, imageWidth, imageHeight) {
  const values = [frameWidth, frameHeight, imageWidth, imageHeight].map(Number);
  if (values.some((value) => !Number.isFinite(value) || value <= 0)) return 0.08;
  return Math.min(values[0] / values[2], values[1] / values[3]);
}

export function clampMapScale(scale, minimumScale, maximumScale = 8) {
  return Math.min(maximumScale, Math.max(minimumScale, Number(scale)));
}
