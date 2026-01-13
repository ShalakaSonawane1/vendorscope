'use client';

import { useEffect, useState } from 'react';
import { vendorApi, queryApi, Vendor, QueryResponse } from '../../lib/api';
import { Send, ExternalLink } from 'lucide-react';

export default function QueryPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [selectedVendors, setSelectedVendors] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedVendors.length === 0 || !query.trim()) return;

    setLoading(true);
    setResponse(null);

    try {
      const result = await queryApi.ask({
        query: query.trim(),
        vendor_ids: selectedVendors,
        include_sources: true,
      });
      setResponse(result);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to process query');
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    "Is this vendor SOC 2 compliant?",
    "What security certifications do they have?",
    "Have there been any security incidents?",
    "Does this vendor share data with third parties?",
    "What is their data retention policy?",
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Query Vendors</h1>
        <p className="text-gray-600 mt-1">
          Ask questions about vendor security, compliance, and risk
        </p>
      </div>

      {/* Query Form */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Vendor(s) *
            </label>
            <div className="space-y-2">
              {vendors.map((vendor) => (
                <label key={vendor.id} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedVendors.includes(vendor.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedVendors([...selectedVendors, vendor.id]);
                      } else {
                        setSelectedVendors(selectedVendors.filter(id => id !== vendor.id));
                      }
                    }}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <span className="text-sm text-gray-700">{vendor.name} ({vendor.domain})</span>
                </label>
              ))}
            </div>
            {vendors.length === 0 && (
              <p className="text-sm text-gray-500 mt-2">
                No vendors available. Add a vendor first.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Question *
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="e.g., Is Stripe SOC 2 compliant and what security certifications do they have?"
            />
          </div>

          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Example Questions:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuery(example)}
                  className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || selectedVendors.length === 0 || !query.trim()}
            className="w-full bg-indigo-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center space-x-2"
          >
            <Send className="h-4 w-4" />
            <span>{loading ? 'Processing...' : 'Ask Question'}</span>
          </button>
        </form>
      </div>

      {/* Response */}
      {response && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Answer</h3>
            <div className="prose prose-sm max-w-none">
              <p className="text-gray-700 whitespace-pre-wrap">{response.answer}</p>
            </div>
          </div>

          {response.risk_assessment && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Risk Assessment</h4>
              <p className="text-sm text-gray-700">{response.risk_assessment}</p>
            </div>
          )}

          <div className="border-t pt-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500">Confidence: </span>
              <span className={`text-xs font-medium ${
                response.confidence_level === 'high' ? 'text-green-600' :
                response.confidence_level === 'medium' ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {response.confidence_level.toUpperCase()}
              </span>
            </div>
            <div className="text-xs text-gray-500">
              Processed in {response.processing_time_ms}ms
            </div>
          </div>

          {response.citations && response.citations.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Sources</h4>
              <div className="space-y-2">
                {response.citations.map((citation, idx) => (
                  <div key={idx} className="bg-gray-50 rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-xs font-medium text-gray-900">{citation.title || 'Document'}</p>
                        <p className="text-xs text-gray-600 mt-1">{citation.excerpt}</p>
                      </div>
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-indigo-600 hover:text-indigo-700"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}