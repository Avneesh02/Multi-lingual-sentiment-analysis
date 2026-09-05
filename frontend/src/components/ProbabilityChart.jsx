// Fixed display order for the 5 classes
const EMOTION_ORDER = ['angry', 'happy', 'sad', 'fear', 'neutral'];

export default function ProbabilityChart({ probabilities, predicted }) {
  if (!probabilities) return null;

  return (
    <div className="prob-chart" role="list" aria-label="Emotion probability breakdown">
      {EMOTION_ORDER.map((emotion) => {
        const prob = probabilities[emotion] ?? 0;
        const pct = Math.round(prob * 100);
        const isWinner = emotion === predicted;

        return (
          <div
            key={emotion}
            className="prob-row"
            role="listitem"
            style={isWinner ? { fontWeight: 700 } : undefined}
          >
            <span className="prob-label" style={isWinner ? { color: 'var(--text-primary)' } : undefined}>
              {isWinner ? '▶ ' : ''}{emotion}
            </span>
            <div className="prob-track">
              <div
                className={`prob-fill prob-fill--${emotion}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="prob-pct" style={isWinner ? { color: 'var(--text-primary)', fontWeight: 700 } : undefined}>
              {pct}%
            </span>
          </div>
        );
      })}
    </div>
  );
}
