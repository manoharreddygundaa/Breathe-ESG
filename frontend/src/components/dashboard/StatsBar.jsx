export default function StatsBar({ stats }) {
  const items = [
    { label: 'Pending review', value: stats.pending, color: 'text-amber-700' },
    { label: 'Suspicious', value: stats.suspicious, color: 'text-orange-600' },
    { label: 'Failed', value: stats.failed, color: 'text-red-600' },
    { label: 'Approved', value: stats.approved, color: 'text-green-700' },
    { label: 'Rejected', value: stats.rejected, color: 'text-gray-500' },
  ];

  return (
    <div className="flex flex-wrap gap-4 mb-4">
      {items.map((item) => (
        <div key={item.label} className="bg-white border border-gray-200 rounded-lg px-4 py-2 min-w-[100px]">
          <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
          <p className="text-xs text-gray-500">{item.label}</p>
        </div>
      ))}
    </div>
  );
}
