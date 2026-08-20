// Common Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
  search?: string;
}

// User & Auth
export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

// Contact List
export interface ContactList {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactListCreate {
  name: string;
  description?: string | null;
}

export interface ContactListUpdate {
  name?: string;
  description?: string | null;
}

// Subscriber
export type SubscriberStatus = 'active' | 'unsubscribed' | 'bounced';

export interface Subscriber {
  id: string;
  contact_list_id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  status: SubscriberStatus;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SubscriberCreate {
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  metadata?: Record<string, any>;
}

export interface SubscriberUpdate {
  email?: string;
  first_name?: string | null;
  last_name?: string | null;
  status?: SubscriberStatus;
  metadata?: Record<string, any>;
}

// Bulk CSV Import
export type ImportStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface ImportInitiateResponse {
  import_id: string;
  status: ImportStatus;
  message: string;
}

export interface ImportJob {
  id: string;
  owner_id: string;
  contact_list_id: string;
  status: ImportStatus;
  original_filename: string;
  file_path: string;
  total_rows: number;
  processed_rows: number;
  imported_rows: number;
  skipped_rows: number;
  duplicate_rows: number;
  invalid_rows: number;
  error_count: number;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImportErrorItem {
  id: string;
  import_job_id: string;
  row_number: number;
  error_type: string;
  message: string;
  created_at: string;
}

// Email Template
export interface EmailTemplate {
  id: string;
  owner_id: string;
  name: string;
  subject: string;
  html_content: string | null;
  text_content: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplateCreate {
  name: string;
  subject: string;
  html_content?: string | null;
  text_content?: string | null;
}

export interface EmailTemplateUpdate {
  name?: string;
  subject?: string | null;
  html_content?: string | null;
  text_content?: string | null;
}

// Email Campaign
export type CampaignStatus = 'draft' | 'ready' | 'queued' | 'sending' | 'completed' | 'failed';

export interface EmailCampaign {
  id: string;
  owner_id: string;
  name: string;
  subject: string;
  template_id: string;
  contact_list_id: string;
  status: CampaignStatus;
  created_at: string;
  updated_at: string;
}

export interface EmailCampaignCreate {
  name: string;
  subject: string;
  template_id: string;
  contact_list_id: string;
}

export interface EmailCampaignUpdate {
  name?: string;
  subject?: string;
  template_id?: string;
  contact_list_id?: string;
}

export interface CampaignSendResponse {
  campaign_id: string;
  status: string;
  message: string;
}

export interface CampaignStats {
  campaign_id: string;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  bounced_count: number;
  opened_count: number;
  open_rate: number;
  bounce_rate: number;
}

// Health & Metadata
export interface HealthResponse {
  status: string;
  database: string;
  version: string;
  app_name: string;
}

// Normalized API Error
export interface ApiError {
  status: number;
  message: string;
  details?: any;
}
