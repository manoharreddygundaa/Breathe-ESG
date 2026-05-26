import { useState, useEffect } from 'react';
import { api } from '../../services/api';

export default function RecordModal({ recordId, onClose, onReviewed }) {
  const [record, setRecord] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [note, setNote] = useState('');
  const [edits, setEdits] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('details'); // 'details' | 'raw' | 'audit'

  useEffect(() => {
    Promise.all([api.record(recordId), api.auditLog(recordId)])
      .then(([r, logs]) => {
        setRecord(r);
        setAuditLog(logs);
      })
      .catch(console.error);
  }, [recordId]);

  async function handleAction(action) {
    setSubmitting(true);
    setError('');
    try {
      await api.reviewRecord(recordId, action, note, edits);
      onReviewed();
    } catch (err) {
      setError(err.data?.error || 'Action failed.');
    } finally {
      setSubmitting(false);
    }
  }

  if (!record) {
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 text-sm text-gray-500">Loading…</div>
      </div>
    );
  }

  const isLocked = record.status === 'approved';
  const isFailed = record.status === 'failed';

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl shadow-xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div>
            <h2 className="font-semibold text-gray-900">
              {record.activity_type}
              {record.flag !== 'ok' && (
                <span className={`ml-2 text-xs font-medium px-2 py-0.5 rounded-full ${
                  record.flag === 'suspicious' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'
                }`}>
                  {record.flag}
                </span>
              )}
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Row {record.source_row_index} · {record.data_source_name}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-5">
          {['details', 'raw', 'audit'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-2 px-3 text-sm capitalize transition-colors border-b-2 -mb-px ${
                tab === t ? 'border-green-500 text-green-700 font-medium' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t === 'audit' ? 'Audit log' : t}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {tab === 'details' && (
            <div className="space-y-3">
              {record.flag_reason && (
                <div className={`text-sm rounded px-3 py-2 ${
                  record.flag === 'suspicious' ? 'bg-orange-50 border border-orange-200 text-orange-800' : 'bg-red-50 border border-red-200 text-red-800'
                }`}>
                  <strong>Flag reason:</strong> {record.flag_reason}
                </div>
              )}

              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <dt className="text-gray-500">Scope</dt>
                <dd className="font-medium">{record.scope}</dd>
                <dt className="text-gray-500">Activity</dt>
                <dd>{record.activity_type}</dd>
                <dt className="text-gray-500">Date</dt>
                <dd>
                  {isLocked ? record.activity_date : (
                    <input
                      type="date"
                      defaultValue={record.activity_date}
                      onChange={(e) => setEdits({ ...edits, activity_date: e.target.value })}
                      className="border border-gray-300 rounded px-2 py-0.5 text-sm"
                    />
                  )}
                </dd>
                <dt className="text-gray-500">Quantity</dt>
                <dd>
                  {isLocked ? `${record.quantity} ${record.unit}` : (
                    <div className="flex gap-2">
                      <input
                        type="number"
                        defaultValue={record.quantity}
                        step="any"
                        onChange={(e) => setEdits({ ...edits, quantity: e.target.value })}
                        className="border border-gray-300 rounded px-2 py-0.5 text-sm w-28"
                      />
                      <input
                        type="text"
                        defaultValue={record.unit}
                        onChange={(e) => setEdits({ ...edits, unit: e.target.value })}
                        className="border border-gray-300 rounded px-2 py-0.5 text-sm w-16"
                      />
                    </div>
                  )}
                </dd>
                <dt className="text-gray-500">Location</dt>
                <dd className="font-mono text-xs">{record.location || '—'}</dd>
                <dt className="text-gray-500">Description</dt>
                <dd>{record.description || '—'}</dd>
                <dt className="text-gray-500">Status</dt>
                <dd className="font-medium capitalize">{record.status.replace('_', ' ')}</dd>
                {record.reviewed_by_name && (
                  <>
                    <dt className="text-gray-500">Reviewed by</dt>
                    <dd>{record.reviewed_by_name} on {new Date(record.reviewed_at).toLocaleString()}</dd>
                  </>
                )}
                {record.analyst_note && (
                  <>
                    <dt className="text-gray-500">Analyst note</dt>
                    <dd className="italic text-gray-600">"{record.analyst_note}"</dd>
                  </>
                )}
              </dl>
            </div>
          )}

          {tab === 'raw' && (
            <pre className="text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto text-gray-700 whitespace-pre-wrap">
              {JSON.stringify(record.raw_data, null, 2)}
            </pre>
          )}

          {tab === 'audit' && (
            <div className="space-y-2">
              {auditLog.length === 0 ? (
                <p className="text-sm text-gray-400">No audit events yet.</p>
              ) : (
                auditLog.map((log) => (
                  <div key={log.id} className="text-sm border-l-2 border-gray-200 pl-3 py-1">
                    <span className="font-medium text-gray-700 capitalize">{log.action}</span>
                    <span className="text-gray-400 mx-2">·</span>
                    <span className="text-gray-500">{log.actor_name}</span>
                    <span className="text-gray-300 mx-2">·</span>
                    <span className="text-gray-400 text-xs">{new Date(log.timestamp).toLocaleString()}</span>
                    {log.detail && <p className="text-gray-500 text-xs mt-0.5">{log.detail}</p>}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer — review actions */}
        {!isLocked && !isFailed && (
          <div className="border-t border-gray-200 px-5 py-4 space-y-3">
            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</p>
            )}
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Optional note (required for rejections)"
              rows={2}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-green-500 resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={() => handleAction('approve')}
                disabled={submitting}
                className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded px-4 py-2 transition-colors"
              >
                Approve
              </button>
              <button
                onClick={() => handleAction('reject')}
                disabled={submitting}
                className="bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium rounded px-4 py-2 transition-colors"
              >
                Reject
              </button>
            </div>
          </div>
        )}

        {isLocked && (
          <div className="border-t border-gray-200 px-5 py-3">
            <p className="text-xs text-gray-400">This record is approved and locked for audit.</p>
          </div>
        )}

        {isFailed && (
          <div className="border-t border-gray-200 px-5 py-3">
            <p className="text-xs text-red-500">Failed records cannot be approved. Correct the source data and re-upload.</p>
          </div>
        )}
      </div>
    </div>
  );
}
