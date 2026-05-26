import { useState, useRef } from 'react';
import { api } from '../services/api';
import Layout from '../components/shared/Layout';

const SOURCE_TYPES = [
  {
    value: 'sap_fuel',
    label: 'SAP Fuel & Procurement',
    scope: 'Scope 1',
    description: 'Flat file export from SAP MM/PM. Expects columns: Material, Menge, Einheit, Plant, Posting_Date',
    example: 'Material,Menge,Einheit,Plant,Posting_Date\nDiesel,500,L,HYD01,12.03.2026\nHSD,1200,L,BOM02,15.03.2026',
  },
  {
    value: 'utility',
    label: 'Utility Electricity',
    scope: 'Scope 2',
    description: 'Portal CSV export from electricity provider. Expects columns: Meter_ID, Consumption_kWh, Billing_Start, Billing_End',
    example: 'Meter_ID,Consumption_kWh,Billing_Start,Billing_End\nMTR001,1200,2026-03-01,2026-03-31\nMTR002,850.5,2026-03-01,2026-03-31',
  },
  {
    value: 'travel',
    label: 'Corporate Travel',
    scope: 'Scope 3',
    description: 'Export from Concur/Navan or similar. Expects columns: Employee, Departure, Arrival, Travel_Type, Travel_Date, Distance_km',
    example: 'Employee,Departure,Arrival,Travel_Type,Travel_Date,Distance_km\nRahul,HYD,DEL,Flight,2026-03-10,1250\nSarah,BLR,BOM,Flight,2026-03-11,980',
  },
];

export default function UploadPage() {
  const [selectedType, setSelectedType] = useState('');
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [showExample, setShowExample] = useState(false);
  const fileInputRef = useRef();

  const selectedSource = SOURCE_TYPES.find((s) => s.value === selectedType);

  async function handleUpload() {
    if (!file || !selectedType) return;
    setError('');
    setResult(null);
    setUploading(true);
    try {
      const res = await api.uploadCsv(file, selectedType);
      setResult(res);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setError(err.data?.error || 'Upload failed. Check your CSV format and try again.');
    } finally {
      setUploading(false);
    }
  }

  return (
    <Layout>
      <div className="max-w-2xl">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Upload Data</h1>
        <p className="text-sm text-gray-500 mb-6">
          Import emissions activity data from one of three source types.
          Records will enter the review queue — nothing is auto-approved.
        </p>

        {/* Source type selector */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Data source type</label>
          <div className="space-y-2">
            {SOURCE_TYPES.map((s) => (
              <label
                key={s.value}
                className={`flex items-start gap-3 border rounded-lg p-3 cursor-pointer transition-colors ${
                  selectedType === s.value
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="radio"
                  name="source_type"
                  value={s.value}
                  checked={selectedType === s.value}
                  onChange={() => { setSelectedType(s.value); setShowExample(false); }}
                  className="mt-0.5"
                />
                <div>
                  <div className="text-sm font-medium text-gray-800">
                    {s.label}
                    <span className="ml-2 text-xs font-normal text-gray-400">{s.scope}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{s.description}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {selectedSource && (
          <div className="mb-4">
            <button
              onClick={() => setShowExample(!showExample)}
              className="text-xs text-green-600 hover:text-green-700 underline"
            >
              {showExample ? 'Hide' : 'Show'} example CSV format
            </button>
            {showExample && (
              <pre className="mt-2 text-xs bg-gray-50 border border-gray-200 rounded p-3 overflow-x-auto text-gray-700">
                {selectedSource.example}
              </pre>
            )}
          </div>
        )}

        {/* File input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">CSV file</label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0] || null)}
            className="block w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-gray-300 file:text-sm file:bg-white file:text-gray-700 hover:file:bg-gray-50"
          />
          {file && (
            <p className="text-xs text-gray-400 mt-1">{file.name} — {(file.size / 1024).toFixed(1)} KB</p>
          )}
        </div>

        {error && (
          <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
            {error}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || !selectedType || uploading}
          className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded px-5 py-2 transition-colors"
        >
          {uploading ? 'Uploading…' : 'Upload and parse'}
        </button>

        {/* Result summary */}
        {result && (
          <div className="mt-6 border border-green-200 bg-green-50 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-green-800 mb-2">Upload complete</h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
              <dt className="text-gray-600">Total rows</dt>
              <dd className="font-medium">{result.total_rows}</dd>
              <dt className="text-gray-600">Pending review</dt>
              <dd className="font-medium text-amber-700">{result.pending_review}</dd>
              <dt className="text-gray-600">Suspicious (flagged)</dt>
              <dd className="font-medium text-orange-700">{result.suspicious}</dd>
              <dt className="text-gray-600">Failed (parse errors)</dt>
              <dd className="font-medium text-red-700">{result.failed}</dd>
            </dl>
            <p className="text-xs text-gray-500 mt-3">
              Go to the review dashboard to approve or reject records.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
}
