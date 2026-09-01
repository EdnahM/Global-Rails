function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ActivityPage({ activities }) {
  return (
    <section className="content">
      <p className="page-intro">
        Real executions from this session — every tool call from the AI
        Agent chat or the Swap/Transfer/x402 pages lands here as it happens.
      </p>

      <div className="card">
        <div className="card-heading">
          <div>
            <span className="card-label">SESSION HISTORY</span>
            <h3>Latest executions</h3>
          </div>
        </div>

        {activities.length === 0 ? (
          <p className="empty-state">
            Nothing yet — try a quick-reply in the AI Agent tab, or run a
            swap/transfer/x402 payment from their pages.
          </p>
        ) : (
          activities.map((item) => (
            <div className="activity" key={item.id}>
              <div className="activity-icon">{item.icon}</div>

              <div>
                <strong>{item.title}</strong>
                <span>
                  {item.detail} · {formatTime(item.timestamp)}
                </span>
              </div>

              <b>{item.amount}</b>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

export default ActivityPage;
