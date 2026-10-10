const STATUS_LABEL = { new: 'New', triaged: 'Needs approval', approved: 'Approved', assigned: 'Assigned', in_progress: 'In progress' }

export default function IssueQueue({ issues, onSelect, flashIds }) {
  return (
    <section className="panel queue">
      <div className="panel-head">
        <h2>Priority queue</h2>
        <span className="muted">{issues.length} open</span>
      </div>
      <ol className="queue-list">
        {issues.map((i, idx) => (
          <li key={i.issue_id} className={flashIds.has(i.issue_id) ? 'queue-item flash' : 'queue-item'}>
            <button onClick={() => onSelect(i.issue_id)}>
              <span className="rank">{idx + 1}</span>
              <span className={`tier tier-${i.priority_tier}`}>{i.priority_tier ?? '…'}</span>
              <span className="queue-body">
                <span className="queue-title">
                  #{i.issue_id} {i.summary}
                </span>
                <span className="queue-sub">
                  {i.address?.replace(', Kansas City, MO', '')} · {i.neighborhood} · {i.report_count} report{i.report_count === 1 ? '' : 's'}
                  {i.possible_duplicate_of && <span className="tag tag-warn">possible dup of #{i.possible_duplicate_of}</span>}
                </span>
                <span className="queue-sub">
                  {i.recommended_department_name}
                  {i.recommended_crew_name && ` → ${i.recommended_crew_name}`}
                </span>
              </span>
              <span className="queue-right">
                <span className="score">{i.priority_score ?? '–'}</span>
                <span className={`status status-${i.status}`}>{STATUS_LABEL[i.status] || i.status}</span>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  )
}
