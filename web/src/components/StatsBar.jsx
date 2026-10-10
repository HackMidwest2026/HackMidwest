export default function StatsBar({ stats, stream, children }) {
  const b = stats?.last_batch
  return (
    <section className="statsbar">
      <div className="stat">
        <span className="stat-num">{stats?.open_issues ?? '–'}</span>
        <span className="stat-label">open issues</span>
      </div>
      <div className="stat">
        <span className="stat-num">{stats?.total_reports ?? '–'}</span>
        <span className="stat-label">reports</span>
      </div>
      <div className="stat">
        <span className="stat-num tier-P1-text">{stats?.open_by_tier?.P1 ?? 0}</span>
        <span className="stat-label">P1 urgent</span>
      </div>
      {b && (
        <div className="stat stat-batch" title={b.ground_truth ? `Ground truth: ${b.ground_truth.true_issues} real issues` : ''}>
          <span className="stat-num">
            {b.reports} → {b.issues}
          </span>
          <span className="stat-label">
            last batch · {b.duplicate_reduction_pct}% duplicate reduction
            {b.ground_truth &&
              ` · category ${Math.round(b.ground_truth.category_accuracy * 100)}% · dedup P/R ${Math.round(b.ground_truth.dedup_precision * 100)}/${Math.round(b.ground_truth.dedup_recall * 100)}%`}
            {` · ${(b.duration_ms / 1000).toFixed(1)} s`}
          </span>
        </div>
      )}
      <div className="stat-actions">
        <span className={`stream stream-${stream}`}>{stream === 'live' ? '● live' : `○ ${stream}`}</span>
        {children}
      </div>
    </section>
  )
}
