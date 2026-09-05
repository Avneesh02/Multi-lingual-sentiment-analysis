import { EMOTION_META, NATIVE_NAMES } from './emotionMeta.js';

function formatTime(date) {
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function truncate(str, n = 80) {
  return str.length > n ? str.slice(0, n) + '…' : str;
}

export default function SessionHistory({ history }) {
  return (
    <div className="card">
      <div className="card__header">
        <span className="card__header-icon">🗂️</span>
        <span className="card__header-label">
          Session History
          {history.length > 0 && (
            <span style={{ marginLeft: 8, background: 'var(--navy)', color: '#fff', borderRadius: 10, padding: '1px 7px', fontSize: '0.68rem', fontWeight: 700 }}>
              {history.length}
            </span>
          )}
        </span>
      </div>

      <div className="card__body">
        {history.length === 0 ? (
          <p className="history-empty">No comments analyzed yet in this session.</p>
        ) : (
          <div className="history-list" role="log" aria-label="Session analysis history" aria-live="polite">
            {history.map((item) => {
              const meta = EMOTION_META[item.emotion] ?? { emoji: '❓', color: '#666' };
              const native = NATIVE_NAMES[item.language?.code];

              return (
                <div key={item.id} className="history-item">
                  <span
                    className={`history-emotion-dot history-emotion-dot--${item.emotion}`}
                    title={item.emotion}
                  />
                  <div>
                    <div className="history-text">{truncate(item.text)}</div>
                    <div className="history-meta">
                      {meta.emoji} {item.emotion} &nbsp;·&nbsp;
                      {item.language?.name ?? 'Unknown'}
                      {native && native !== item.language?.name ? ` (${native})` : ''}
                    </div>
                  </div>
                  <div className="history-right">
                    <div className="history-confidence">{Math.round(item.confidence * 100)}%</div>
                    <div className="history-time">{formatTime(item.timestamp)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
