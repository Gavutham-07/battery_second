/**
 * Telemetry Stream Simulation Service for ReVolt Screening
 * Generates realistic 90-second screening datasets for different data sources & profiles.
 */

export function generateTelemetryPoint(second, profile = 'healthy', dataSource = 'virtual_circuit') {
  const t = Math.min(Math.max(0, second), 90);
  const progressRatio = t / 90;

  // Base jitter for realism
  const vJitter = (Math.random() - 0.5) * 0.015;
  const iJitter = (Math.random() - 0.5) * 0.15;
  const tJitter = (Math.random() - 0.5) * 0.2;

  let voltage = 3.35;
  let current = 10.0;
  let temperature = 25.0;

  if (dataSource === 'lab_dataset') {
    // High-precision Sandia / MIT laboratory cell discharge profile
    voltage = 3.42 - (progressRatio * 0.18) + vJitter * 0.4;
    current = 10.0 + iJitter * 0.2;
    temperature = 24.5 + (progressRatio * 3.2) + tJitter * 0.3;
  } else if (dataSource === 'replay_recorded') {
    // Replay of a standardized 90s fleet test log
    voltage = 3.32 - (progressRatio * 0.22) + vJitter;
    current = 9.8 + (Math.sin(t / 8) * 0.6) + iJitter;
    temperature = 26.0 + (progressRatio * 6.5) + tJitter;
  } else {
    // Virtual Circuit with selectable profiles
    switch (profile) {
      case 'thermally_unsafe':
        // Rapid voltage sag, unstable current draw, runaway temperature > 45°C
        voltage = 3.25 - (progressRatio * 0.55) + vJitter * 2;
        current = 10.0 + (progressRatio > 0.4 ? (Math.random() * 6 + 4) : 0) + iJitter;
        temperature = 30.0 + (progressRatio * 25.5) + tJitter; // Climbs to ~55°C
        break;

      case 'moderately_aged':
        // Normal degradation, higher thermal rise, noticeable voltage sag
        voltage = 3.32 - (progressRatio * 0.28) + vJitter;
        current = 10.0 + iJitter;
        temperature = 26.5 + (progressRatio * 12.0) + tJitter; // Reaches ~38.5°C
        break;

      case 'healthy':
      default:
        // Nominal LFP discharge plateau, minimal thermal rise
        voltage = 3.38 - (progressRatio * 0.12) + vJitter;
        current = 10.0 + iJitter;
        temperature = 25.0 + (progressRatio * 4.5) + tJitter; // Reaches ~29.5°C
        break;
    }
  }

  return {
    time: t,
    voltage: Number(Math.max(2.5, voltage).toFixed(3)),
    current: Number(Math.max(0, current).toFixed(2)),
    temperature: Number(temperature.toFixed(1))
  };
}

/**
 * Pre-generates the complete 90-second series for instant playback or streaming
 */
export function generateFullScreeningDataset(profile = 'healthy', dataSource = 'virtual_circuit') {
  const points = [];
  for (let s = 0; s <= 90; s++) {
    points.push(generateTelemetryPoint(s, profile, dataSource));
  }
  return points;
}

