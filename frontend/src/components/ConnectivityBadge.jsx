export default function ConnectivityBadge({ status, onRetry }) {
  const labels = {
    connected:    'Backend Connected',
    disconnected: 'Backend Offline',
    checking:     'Checking…',
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span className={`connectivity-badge connectivity-badge--${status}`}>
        <span className="connectivity-dot" />
        {labels[status]}
      </span>
      {status === 'disconnected' && (
        <button
          onClick={onRetry}
          title="Retry connection"
          style={{
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.25)',
            color: '#fff',
            borderRadius: 6,
            padding: '3px 10px',
            fontSize: '0.72rem',
            cursor: 'pointer',
            letterSpacing: '0.04em',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
