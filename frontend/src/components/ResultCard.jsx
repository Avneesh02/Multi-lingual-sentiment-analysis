import { EMOTION_META, NATIVE_NAMES } from './emotionMeta.js';
import ProbabilityChart from './ProbabilityChart.jsx';

function openGoogleTranslate(text, langCode) {
  const sl = langCode === 'unknown' ? 'auto' : langCode;
  const url = `https://translate.google.com/?sl=${sl}&tl=en&text=${encodeURIComponent(text)}&op=translate`;
  window.open(url, '_blank', 'noopener,noreferrer');
}

export default function ResultCard({ result, loading, originalText }) {
  if (loading) {
    return (
      <div className="card">
        <div className="card__header">
          <span className="card__header-icon">📊</span>
          <span className="card__header-label">Analysis Result</span>
        </div>
        <div className="card__body result-empty">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '32px 0' }}>
            <span className="spinner" style={{ width: 36, height: 36, borderWidth: 3, borderColor: 'rgba(15,32,68,.12)', borderTopColor: 'var(--navy)', display: 'inline-block', borderRadius: '50%', animation: 'spin 0.7s linear infinite' }} />
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Running inference…</p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="card">
        <div className="card__header">
          <span className="card__header-icon">📊</span>
          <span className="card__header-label">Analysis Result</span>
        </div>
        <div className="card__body result-empty" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: '2.2rem', marginBottom: 12, opacity: 0.25 }}>📋</div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            Submit a comment to see<br />the emotion prediction here.
          </p>
        </div>
      </div>
    );
  }

  const meta = EMOTION_META[result.emotion] ?? { emoji: '❓', color: '#666', label: result.emotion };
  const langNative = NATIVE_NAMES[result.language?.code];
  const confidencePct = Math.round(result.confidence * 100);
  const langCode = result.language?.code ?? 'auto';

  const gaugeColor =
    result.confidence >= 0.75 ? 'var(--success)' :
    result.confidence >= 0.50 ? 'var(--saffron)' :
    'var(--error)';

  return (
    <div className="card">
      <div className="card__header">
        <span className="card__header-icon">📊</span>
        <span className="card__header-label">Analysis Result</span>
      </div>

      <div className="card__body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap-md)' }}>

        {/* Emotion + Language row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div className="result-section-label">Detected Emotion</div>
            <span className={`emotion-pill emotion-pill--${result.emotion}`}>
              <span className="emotion-icon" aria-hidden="true">{meta.emoji}</span>
              {meta.label}
            </span>
          </div>
          <div>
            <div className="result-section-label">Language</div>
            <span className="language-badge">
              {result.language?.name ?? 'Unknown'}
              {langNative && langNative !== result.language?.name && (
                <span className="language-native">· {langNative}</span>
              )}
            </span>
          </div>
        </div>

        {/* Confidence gauge */}
        <div className="confidence-section">
          <div className="confidence-header">
            <span className="confidence-label">Confidence</span>
            <span className="confidence-value">{confidencePct}%</span>
          </div>
          <div className="confidence-track" role="progressbar" aria-valuenow={confidencePct} aria-valuemin={0} aria-valuemax={100}>
            <div className="confidence-fill" style={{ width: `${confidencePct}%`, background: gaugeColor }} />
          </div>
        </div>

        <div className="section-divider" />

        {/* Probability breakdown */}
        <div>
          <div className="result-section-label" style={{ marginBottom: 10 }}>Probability Breakdown</div>
          <ProbabilityChart probabilities={result.probabilities} predicted={result.emotion} />
        </div>
      </div>
    </div>
  );
}
