import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import Layout from '../components/shared/Layout';
import RecordTable from '../components/dashboard/RecordTable';
import RecordModal from '../components/dashboard/RecordModal';
import FilterBar from '../components/dashboard/FilterBar';
import StatsBar from '../components/dashboard/StatsBar';

export default function DashboardPage() {
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({ status: 'pending_review' });
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [recs, s] = await Promise.all([
        api.records(filters),
        api.stats(),
      ]);
      // Defensive: ensure we always set an array
      setRecords(Array.isArray(recs) ? recs : []);
      setStats(s);
    } catch (e) {
      console.error('Fetch error:', e);
      setError(e.message || 'Failed to load records. Check the backend is running.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  function handleReviewed() {
    setSelectedRecord(null);
    fetchRecords();
  }

  return (
    <Layout>
      <h1 className="text-xl font-semibold text-gray-900 mb-1">Review Dashboard</h1>
      <p className="text-sm text-gray-500 mb-4">
        Review imported records and approve or reject them before they're locked for audit.
      </p>

      {stats && <StatsBar stats={stats} />}

      <FilterBar filters={filters} onChange={setFilters} />

      {error && (
        <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {error}
        </div>
      )}

      <RecordTable
        records={records}
        loading={loading}
        onSelect={setSelectedRecord}
      />

      {selectedRecord && (
        <RecordModal
          recordId={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          onReviewed={handleReviewed}
        />
      )}
    </Layout>
  );
}