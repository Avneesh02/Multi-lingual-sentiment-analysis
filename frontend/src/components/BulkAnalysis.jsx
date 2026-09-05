import { useState } from 'react';
import { API_BASE_URL } from '../config.js';
import { EMOTION_META } from './emotionMeta.js';

const EMOTIONS = ['angry', 'happy', 'sad', 'fear', 'neutral'];

export default function BulkAnalysis({ connected }) {
  const [bulkText, setBulkText] = useState('');
  const [running, setRunning]   = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [counts, setCounts]     = useState(null);   // { angry:N, happy:N, ... }
  const [errors, setErrors]     = useState(0);

  const handleAnalyzeAll = async () => {
    const lines = bulkText.split('\n').map(l => l.trim()).filter(Boolean);
    if (!lines.length) return;

    setRunning(true);
    setCounts(null);
    setErrors(0);

    const tally = { angry: 0, happy: 0, sad: 0, fear: 0, neutral: 0 };
    let errCount = 0;

    for (let i = 0; i < lines.length; i++) {
      setProgress({ done: i, total: lines.length });
      try {
        const res = await fetch(`${API_BASE_URL}/emotion/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: lines[i] }),
        });
        if (res.ok) {
          const data = await res.json();
          tally[data.emotion] = (tally[data.emotion] || 0) + 1;
        } else {
          errCount++;
        }
      } catch {
        errCount++;
      }
    }

    setProgress({ done: lines.length, total: lines.length });
    setCounts({ ...tally });
    setErrors(errCount);
    setRunning(false);
  };

  const total = counts ? Object.values(counts).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="card" style={{ marginTop: 'var(--gap-lg)' }}>
      <div className="card__header">
        <span className="card__header-icon">📊</span>
        <span className="card__header-label">Bulk Comment Analysis</span>
      </div>

      <div className="card__body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap-md)' }}>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
          Paste multiple comments — one per line. The system will analyze each and show the overall emotion distribution.
        </p>

        <textarea
          className="input-panel__textarea"
          rows={6}
          placeholder={"Comment 1 (any language)\nComment 2\nComment 3\n…"}
          value={bulkText}
          onChange={e => { setBulkText(e.target.value); setCounts(null); }}
          disabled={running}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--gap-md)', flexWrap: 'wrap' }}>
          <button
            className={`btn-analyze${running ? ' btn-analyze--loading' : ''}`}
            style={{ flex: '0 0 auto' }}
            onClick={handleAnalyzeAll}
            disabled={running || !bulkText.trim() || connected !== 'connected'}
          >
            {running
              ? <><span className="spinner" aria-hidden="true" /> Analyzing {progress.done}/{progress.total}…</>
              : <><span aria-hidden="true">🔍</span> Analyze All Comments</>
            }
          </button>

          {counts && (
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              {total} analyzed{errors > 0 ? ` · ${errors} skipped` : ''}
            </span>
          )}
        </div>

        {/* Progress bar while running */}
        {running && progress.total > 0 && (
          <div className="confidence-track" style={{ marginTop: -4 }}>
            <div
              className="confidence-fill"
              style={{
                width: `${Math.round((progress.done / progress.total) * 100)}%`,
                background: 'var(--navy)',
                transition: 'width 0.2s ease',
              }}
            />
          </div>
        )}

        {/* Results bar chart */}
        {counts && total > 0 && (
          <>
            <div className="section-divider" />
            <div>
              <div className="result-section-label" style={{ marginBottom: 12 }}>
                Emotion Distribution — {total} Comments
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {EMOTIONS.map(em => {
                  const meta  = EMOTION_META[em];
                  const count = counts[em] || 0;
                  const pct   = total > 0 ? Math.round((count / total) * 100) : 0;
                  return (
                    <div key={em} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ width: 72, fontSize: '0.78rem', color: 'var(--text-secondary)', textAlign: 'right', flexShrink: 0 }}>
                        {meta.emoji} {meta.label}
                      </span>
                      <div style={{ flex: 1, background: 'var(--surface-2)', borderRadius: 4, height: 22, overflow: 'hidden' }}>
                        <div style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: meta.color,
                          borderRadius: 4,
                          transition: 'width 0.5s ease',
                          minWidth: count > 0 ? 4 : 0,
                        }} />
                      </div>
                      <span style={{ width: 80, fontSize: '0.78rem', color: 'var(--text-secondary)', flexShrink: 0 }}>
                        {count} ({pct}%)
                      </span>
                    </div>
                  );
                })}
              </div>

              {/* Dominant emotion callout */}
              {(() => {
                const top = EMOTIONS.reduce((a, b) => (counts[a] || 0) >= (counts[b] || 0) ? a : b);
                const topMeta = EMOTION_META[top];
                const topPct  = Math.round(((counts[top] || 0) / total) * 100);
                return (
                  <div style={{
                    marginTop: 14, padding: '10px 14px',
                    background: 'var(--surface-2)', borderRadius: 'var(--radius-md)',
                    borderLeft: `4px solid ${topMeta.color}`,
                    fontSize: '0.82rem', color: 'var(--text-primary)',
                  }}>
                    <strong>Overall Sentiment:</strong> Most comments express{' '}
                    <strong>{topMeta.emoji} {topMeta.label}</strong> ({topPct}% of {total} comments)
                  </div>
                );
              })()}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
