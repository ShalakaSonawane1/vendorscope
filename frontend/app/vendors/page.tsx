'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { vendorApi, Vendor } from '../../lib/api';
import { Trash2, RefreshCw, ExternalLink } from 'lucide-react';
import { RISK_LEVEL_COLORS, VENDOR_TYPE_LABELS } from '../../types';
import { formatDistanceToNow } from 'date-fns';

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [crawling, setCrawling] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      const data = await vendorApi.getAll();
      setVendors(data.vendors);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCrawl = async (id: string) => {
    setCrawling(prev => new Set(prev).add(id));
    try {
      await vendorApi.triggerCrawl(id);
      alert('Crawl started! Check back in a minute.');
    } catch (error) {
      alert('Failed to start crawl');
    } finally {
      setCrawling(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete ${name}? This will remove all associated data.`)) return;
    
    try {
      await vendorApi.delete(id);
      setVendors(prev => prev.filter(v => v.id !== id));
    } catch (error) {
      alert('Failed to delete vendor');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Vendors</h1>
          <p className="text-gray-600 mt-1">Manage and monitor your vendor ecosystem</p>
        </div>
        <Link
          href="/vendors/add"
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition"
        >
          Add Vendor
        </Link>
      </div>

      {vendors.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-600 mb-4">No vendors yet. Add your first vendor to get started!</p>
          <Link
            href="/vendors/add"
            className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 transition"
          >
            Add Your First Vendor
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Vendor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Risk Level
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Documents
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Crawled
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {vendors.map((vendor) => (
                <tr key={vendor.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <Link
                        href={`/vendors/${vendor.id}`}
                        className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
                      >
                        {vendor.name}
                      </Link>
                      <p className="text-sm text-gray-500">{vendor.domain}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">
                      {VENDOR_TYPE_LABELS[vendor.vendor_type as keyof typeof VENDOR_TYPE_LABELS] || vendor.vendor_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full border ${RISK_LEVEL_COLORS[vendor.current_risk_level]}`}>
                      {vendor.current_risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {vendor.total_documents}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {vendor.last_crawled_at
                      ? formatDistanceToNow(new Date(vendor.last_crawled_at), { addSuffix: true })
                      : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleCrawl(vendor.id)}
                      disabled={crawling.has(vendor.id)}
                      className="text-indigo-600 hover:text-indigo-900 disabled:opacity-50"
                      title="Refresh data"
                    >
                      <RefreshCw className={`h-4 w-4 ${crawling.has(vendor.id) ? 'animate-spin' : ''}`} />
                    </button>
                    <Link
                      href={`/vendors/${vendor.id}`}
                      className="text-gray-600 hover:text-gray-900"
                      title="View details"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Link>
                    <button
                      onClick={() => handleDelete(vendor.id, vendor.name)}
                      className="text-red-600 hover:text-red-900"
                      title="Delete vendor"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}