'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { vendorApi, Vendor } from '../lib/api';
import { Shield, TrendingUp, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { RISK_LEVEL_COLORS } from '../types';

export default function HomePage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    lowRisk: 0,
    mediumRisk: 0,
    highRisk: 0,
    recentlyCrawled: 0,
  });

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      const data = await vendorApi.getAll();
      setVendors(data.vendors);
      
      // Calculate stats
      const lowRisk = data.vendors.filter(v => v.current_risk_level === 'low').length;
      const mediumRisk = data.vendors.filter(v => v.current_risk_level === 'medium').length;
      const highRisk = data.vendors.filter(v => v.current_risk_level === 'high').length;
      const recentlyCrawled = data.vendors.filter(v => {
        if (!v.last_crawled_at) return false;
        const daysSince = (Date.now() - new Date(v.last_crawled_at).getTime()) / (1000 * 60 * 60 * 24);
        return daysSince < 7;
      }).length;

      setStats({
        total: data.total,
        lowRisk,
        mediumRisk,
        highRisk,
        recentlyCrawled,
      });
    } catch (error) {
      console.error('Failed to load vendors:', error);
    } finally {
      setLoading(false);
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
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold text-gray-900">
          AI-Powered Vendor Risk Analysis
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Automatically discover, analyze, and monitor vendor security postures with intelligent due diligence
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Vendors"
          value={stats.total}
          icon={<Shield className="h-6 w-6 text-indigo-600" />}
          color="indigo"
        />
        <StatCard
          title="Low Risk"
          value={stats.lowRisk}
          icon={<CheckCircle className="h-6 w-6 text-green-600" />}
          color="green"
        />
        <StatCard
          title="Medium Risk"
          value={stats.mediumRisk}
          icon={<AlertCircle className="h-6 w-6 text-yellow-600" />}
          color="yellow"
        />
        <StatCard
          title="Recently Crawled"
          value={stats.recentlyCrawled}
          icon={<Clock className="h-6 w-6 text-blue-600" />}
          color="blue"
        />
      </div>

      {/* Recent Vendors */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Recent Vendors</h2>
          <Link
            href="/vendors"
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            View All →
          </Link>
        </div>
        <div className="divide-y divide-gray-200">
          {vendors.slice(0, 5).map((vendor) => (
            <Link
              key={vendor.id}
              href={`/vendors/${vendor.id}`}
              className="block px-6 py-4 hover:bg-gray-50 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-gray-900">{vendor.name}</h3>
                  <p className="text-sm text-gray-500">{vendor.domain}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full border ${RISK_LEVEL_COLORS[vendor.current_risk_level]}`}>
                    {vendor.current_risk_level}
                  </span>
                  <span className="text-sm text-gray-500">
                    {vendor.total_documents} docs
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ActionCard
          title="Add New Vendor"
          description="Start analyzing a new vendor's security posture"
          href="/vendors/add"
          color="indigo"
        />
        <ActionCard
          title="Query Vendors"
          description="Ask questions about vendor compliance and security"
          href="/query"
          color="blue"
        />
        <ActionCard
          title="Compare Vendors"
          description="Side-by-side risk analysis of multiple vendors"
          href="/compare"
          color="purple"
        />
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }: any) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg bg-${color}-50`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function ActionCard({ title, description, href, color }: any) {
  return (
    <Link
      href={href}
      className="block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition group"
    >
      <h3 className={`text-lg font-semibold text-gray-900 group-hover:text-${color}-600 transition`}>
        {title}
      </h3>
      <p className="text-sm text-gray-600 mt-2">{description}</p>
      <div className="mt-4 text-sm font-medium text-indigo-600 group-hover:text-indigo-700">
        Get Started →
      </div>
    </Link>
  );
}