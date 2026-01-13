import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Vendor {
  id: string;
  name: string;
  domain: string;
  vendor_type: string;
  description?: string;
  is_active: boolean;
  is_critical: boolean;
  current_risk_level: 'low' | 'medium' | 'high' | 'unknown';
  risk_summary?: string;
  compliance_status: Record<string, boolean>;
  last_crawled_at?: string;
  next_crawl_scheduled_at?: string;
  created_at: string;
  updated_at: string;
  total_documents: number;
  discovered_urls_count: number;
}

export interface VendorCreate {
  name: string;
  domain: string;
  vendor_type: string;
  description?: string;
  seed_urls?: string[];
  is_critical?: boolean;
}

export interface QueryRequest {
  query: string;
  vendor_ids: string[];
  include_sources: boolean;
}

export interface Citation {
  document_id: string;
  url: string;
  title?: string;
  excerpt: string;
  relevance_score: number;
}

export interface QueryResponse {
  query: string;
  answer: string;
  risk_assessment?: string;
  confidence_level: string;
  citations: Citation[];
  metadata: Record<string, any>;
  processing_time_ms: number;
  created_at: string;
}

export interface ComparisonRequest {
  vendor_ids: string[];
  comparison_aspects: string[];
}

// API Functions
export const vendorApi = {
  // Get all vendors
  getAll: async () => {
    const response = await api.get<{ vendors: Vendor[]; total: number }>('/api/vendors/');
    return response.data;
  },

  // Get single vendor
  getById: async (id: string) => {
    const response = await api.get<Vendor>(`/api/vendors/${id}`);
    return response.data;
  },

  // Create vendor
  create: async (data: VendorCreate) => {
    const response = await api.post<Vendor>('/api/vendors/', data);
    return response.data;
  },

  // Delete vendor
  delete: async (id: string) => {
    await api.delete(`/api/vendors/${id}`);
  },

  // Trigger crawl
  triggerCrawl: async (id: string) => {
    const response = await api.post(`/api/vendors/${id}/crawl`);
    return response.data;
  },
};

export const queryApi = {
  // Ask a question
  ask: async (data: QueryRequest) => {
    const response = await api.post<QueryResponse>('/api/queries/ask', data);
    return response.data;
  },

  // Compare vendors
  compare: async (data: ComparisonRequest) => {
    const response = await api.post('/api/queries/compare', data);
    return response.data;
  },
};

export const healthApi = {
  check: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },
};