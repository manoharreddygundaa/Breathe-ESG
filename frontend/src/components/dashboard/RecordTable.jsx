const SCOPE_LABEL = {
  scope1: { label: 'S1', color: 'bg-blue-100 text-blue-700' },
  scope2: { label: 'S2', color: 'bg-purple-100 text-purple-700' },
  scope3: { label: 'S3', color: 'bg-indigo-100 text-indigo-700' },
};

const STATUS_STYLE = {
  pending_review: 'text-amber-700 bg-amber-50',
  approved: 'text-green-700 bg-green-50',
  rejected: 'text-gray-500 bg-gray-100',
  failed: 'text-red-700 bg-red-50',
};

const FLAG_STYLE = {
  suspicious: 'text-orange-600',
  failed: 'text-red-600',
  ok: 'text-gray-300',
};

export default function RecordTable({ records, loading, onSelect }) {
  if (loading) {
    return <p className="text-sm text-gray-400 py-8 text-center">Loading records…</p>;
  }

  if (!records.length) {
    return <p className="text-sm text-gray-400 py-8 text-center">No records match the current filters.</p>;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Scope</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Activity</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Quantity</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Date</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Location</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Status</th>
            <th className="text-left px-4 py-2 font-medium text-gray-600">Flag</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {records.map((r) => {
            const scope = SCOPE_LABEL[r.scope] || { label: '?', color: 'bg-gray-100 text-gray-500' };
            return (
              <tr
                key={r.id}
                onClick={() => onSelect(r.id)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-2.5">
                  <span className={`text-xs font-mono font-semibold px-1.5 py-0.5 rounded ${scope.color}`}>
                    {scope.label}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-gray-800">{r.activity_type}</td>
                <td className="px-4 py-2.5 text-gray-700 font-mono">
                  {Number(r.quantity).toLocaleString()} {r.unit}
                </td>
                <td className="px-4 py-2.5 text-gray-600">{r.activity_date}</td>
                <td className="px-4 py-2.5 text-gray-500 max-w-[120px] truncate">{r.location || '—'}</td>
                <td className="px-4 py-2.5">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLE[r.status]}`}>
                    {r.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-4 py-2.5">
                  <span className={`text-xs font-medium ${FLAG_STYLE[r.flag] || 'text-gray-400'}`}>
                    {r.flag === 'ok' ? '—' : r.flag}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
