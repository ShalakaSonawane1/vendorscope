'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { vendorApi } from '../../../lib/api';
import { VENDOR_TYPE_LABELS } from '../../../types';

export default function AddVendorPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    vendor_type: 'other',
    seed_urls: '',
    description: '',
    is_critical: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
    // Split seed_urls by newline or comma
    const seedUrlsArray = formData.seed_urls
      ? formData.seed_urls.split(/[\n,]+/).map(url => url.trim()).filter(url => url)
      : [];

    await vendorApi.create({
      ...formData,
      seed_urls: seedUrlsArray,
      });
      alert('Vendor added! Crawling will start automatically.');
      router.push('/vendors');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add vendor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Add New Vendor</h1>
        <p className="text-gray-600 mt-1">
          Add a vendor to start analyzing their security posture
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vendor Name *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="e.g., Stripe"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domain *
            </label>
            <input
              type="text"
              required
              value={formData.domain}
              onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="e.g., stripe.com (without https://)"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter just the domain name, not the full URL
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vendor Type *
            </label>
            <select
              value={formData.vendor_type}
              onChange={(e) => setFormData({ ...formData, vendor_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              {Object.entries(VENDOR_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              placeholder="Brief description of what this vendor provides..."
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Seed URLs (Optional)
            </label>
            <textarea
              value={formData.seed_urls}
              onChange={(e) => setFormData({ ...formData, seed_urls: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 placeholder:text-gray-400"
              placeholder="Enter specific URLs to crawl (one per line):
          https://www.adyen.com/legal
          https://www.adyen.com/policies-and-disclaimer/privacy-policy"
            />
            <p className="text-xs text-gray-500 mt-1">
              Optional: Provide specific URLs if the vendor's trust pages aren't at standard locations. One URL per line.
            </p>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_critical"
              checked={formData.is_critical}
              onChange={(e) => setFormData({ ...formData, is_critical: e.target.checked })}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="is_critical" className="ml-2 block text-sm text-gray-700">
              Critical vendor (refresh more frequently)
            </label>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>What happens next:</strong> VendorScope will automatically discover and crawl
              the vendor's trust pages (security, privacy, compliance docs) and start indexing them.
              This usually takes 20-30 seconds.
            </p>
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Adding Vendor...' : 'Add Vendor'}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}