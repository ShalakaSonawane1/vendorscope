'use client';

import { useEffect, useState } from 'react';
import { vendorApi, queryApi, Vendor } from '../../lib/api';
import { ArrowRight } from 'lucide-react';

export default function ComparePage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendors, setSelectedVendors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [comparison, setComparison] = useState<any>(null);

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      const data = await vendorApi.getAll();
      setVendors(data.vendors);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    }
  };

  const handleCompare = async () => {
    if (selectedVendors.length < 2) {
      alert('Please select at least 2 vendors to compare');
      return;
    }

    setLoading(true);
    setComparison(null);

    try {
      const result = await queryApi.compare({
        vendor_ids: selectedVendors,
        comparison_aspects: ['security', 'privacy', 'compliance'],
      });
      setComparison(result);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to compare vendors');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Compare Vendors</h1>
        <p className="text-gray-600 mt-1">
          Side-by-side comparison of vendor security, privacy, and compliance
        </p>
      </div>

      {/* Vendor Selection */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Select Vendors to Compare (2-5)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {vendors.map((vendor) => (
            <label
              key={vendor.id}
              className={`flex items-center space-x-3 p-4 border-2 rounded-lg cursor-pointer transition ${
                selectedVendors.includes(vendor.id)
                  ? 'border-indigo-600 bg-indigo-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedVendors.includes(vendor.id)}
                onChange={(e) => {
                  if (e.target.checked && selectedVendors.length < 5) {
                    setSelectedVendors([...selectedVendors, vendor.id]);
                  } else if (!e.target.checked) {
                    setSelectedVendors(selectedVendors.filter(id => id !== vendor.id));
                  }
                }}
                disabled={!selectedVendors.includes(vendor.id) && selectedVendors.length >= 5}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{vendor.name}</p>
                <p className="text-xs text-gray-500">{vendor.domain}</p>
              </div>
            </label>
          ))}
        </div>

        {vendors.length < 2 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-yellow-800">
              You need at least 2 vendors to compare. Add more vendors first.
            </p>
          </div>
        )}

        <button
          onClick={handleCompare}
          disabled={loading || selectedVendors.length < 2}
          className="w-full bg-indigo-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center space-x-2"
        >
          <span>{loading ? 'Comparing...' : `Compare ${selectedVendors.length} Vendors`}</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Summary</h3>
            <p className="text-gray-700 whitespace-pre-wrap">{comparison.summary}</p>
            {comparison.recommendation && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-900 mb-1">Recommendation</p>
                <p className="text-sm text-blue-800">{comparison.recommendation}</p>
              </div>
            )}
          </div>

          {/* Comparison Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Aspect
                    </th>
                    {comparison.vendors.map((v: any) => (
                      <th key={v.vendor_id} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {v.vendor_name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Security
                    </td>
                    {comparison.vendors.map((v: any) => (
                      <td key={v.vendor_id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {v.security_score}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Privacy
                    </td>
                    {comparison.vendors.map((v: any) => (
                      <td key={v.vendor_id} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                        {v.privacy_score}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      Risk Level
                    </td>
                    {comparison.vendors.map((v: any) => (
                      <td key={v.vendor_id} className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full border ${
                          v.risk_level === 'low' ? 'bg-green-100 text-green-800 border-green-300' :
                          v.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                          v.risk_level === 'high' ? 'bg-red-100 text-red-800 border-red-300' :
                          'bg-gray-100 text-gray-800 border-gray-300'
                        }`}>
                          {v.risk_level}
                        </span>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Detailed Findings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {comparison.vendors.map((vendor: any) => (
              <div key={vendor.vendor_id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{vendor.vendor_name}</h3>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Key Findings</h4>
                    <ul className="space-y-1">
                      {vendor.key_findings.map((finding: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-600">• {finding}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Compliance</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(vendor.compliance_status).map(([key, value]) => (
                        <span
                          key={key}
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            value ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {key}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}