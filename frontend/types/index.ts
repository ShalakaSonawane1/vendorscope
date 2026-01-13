export type RiskLevel = 'low' | 'medium' | 'high' | 'unknown';

export type VendorType = 
  | 'payments'
  | 'cloud'
  | 'analytics'
  | 'security'
  | 'customer_support'
  | 'marketing'
  | 'data_storage'
  | 'api_service'
  | 'other';

export const VENDOR_TYPE_LABELS: Record<VendorType, string> = {
  payments: 'Payments',
  cloud: 'Cloud',
  analytics: 'Analytics',
  security: 'Security',
  customer_support: 'Customer Support',
  marketing: 'Marketing',
  data_storage: 'Data Storage',
  api_service: 'API Service',
  other: 'Other',
};

export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  low: 'bg-green-100 text-green-800 border-green-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  high: 'bg-red-100 text-red-800 border-red-300',
  unknown: 'bg-gray-100 text-gray-800 border-gray-300',
};