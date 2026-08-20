// User & Auth Types
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

// Contact List & Subscriber Types
export interface ContactList {
  id: string;
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

export type SubscriberStatus = 'active' | 'unsubscribed' | 'bounced';

export interface Subscriber {
  id: string;
  contact_list_id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  status: SubscriberStatus;
  metadata?: Record<string, any>;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SubscriberCreate {
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  status?: SubscriberStatus;
  metadata_json?: Record<string, any>;
}

export interface SubscriberUpdate {
  email?: string;
  first_name?: string | null;
  last_name?: string | null;
  status?: SubscriberStatus;
  metadata_json?: Record<string, any>;
}

// Bulk Import Types (V4)
export type ImportStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface ImportInitiateResponse {
  import_id: string;
  status: string;
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
  imported_rows?: number;
  imported_count?: number;
  duplicate_rows?: number;
  duplicate_count?: number;
  invalid_rows?: number;
  invalid_count?: number;
  error_count?: number;
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

// Template Types
export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  html_content: string;
  text_content: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplateCreate {
  name: string;
  subject: string;
  html_content: string;
  text_content?: string | null;
}

export interface EmailTemplateUpdate {
  name?: string;
  subject?: string;
  html_content?: string;
  text_content?: string | null;
}

// Campaign Types
export type CampaignStatus =
  | 'draft'
  | 'ready'
  | 'scheduled'
  | 'queued'
  | 'sending'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface EmailCampaign {
  id: string;
  owner_id: string;
  name: string;
  subject: string;
  template_id: string;
  contact_list_id: string;
  status: CampaignStatus;
  scheduled_at: string | null;
  timezone: string | null;
  from_name: string | null;
  from_email: string | null;
  reply_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  name: string;
  subject: string;
  template_id: string;
  contact_list_id: string;
  from_name?: string;
  from_email?: string;
  reply_to?: string;
}

export interface CampaignUpdate {
  name?: string;
  subject?: string;
  template_id?: string;
  contact_list_id?: string;
  from_name?: string;
  from_email?: string;
  reply_to?: string;
}

export interface CampaignScheduleRequest {
  scheduled_at: string;
  timezone: string;
}

export interface CampaignSendResponse {
  campaign_id: string;
  status: string;
  message: string;
}

// V5 Campaign Analytics Types
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

// Common Pagination & API Wrappers
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
  status?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
  errors?: Array<{ field?: string; message: string }>;
}
