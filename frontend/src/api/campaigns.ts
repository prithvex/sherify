import { apiClient } from './client';
import {
  CampaignSendResponse,
  CampaignStats,
  EmailCampaign,
  EmailCampaignCreate,
  EmailCampaignUpdate,
  PaginatedResponse,
  PaginationParams,
} from '../types';

export interface CampaignQueryParams extends PaginationParams {
  status?: string;
}

export const campaignsApi = {
  list: async (params?: CampaignQueryParams): Promise<PaginatedResponse<EmailCampaign>> => {
    const response = await apiClient.get<PaginatedResponse<EmailCampaign>>('/api/v1/campaigns', {
      params,
    });
    return response.data;
  },

  getById: async (id: string): Promise<EmailCampaign> => {
    const response = await apiClient.get<EmailCampaign>(`/api/v1/campaigns/${id}`);
    return response.data;
  },

  create: async (data: EmailCampaignCreate): Promise<EmailCampaign> => {
    const response = await apiClient.post<EmailCampaign>('/api/v1/campaigns', data);
    return response.data;
  },

  update: async (id: string, data: EmailCampaignUpdate): Promise<EmailCampaign> => {
    const response = await apiClient.patch<EmailCampaign>(`/api/v1/campaigns/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/campaigns/${id}`);
  },

  markReady: async (id: string): Promise<EmailCampaign> => {
    const response = await apiClient.post<EmailCampaign>(`/api/v1/campaigns/${id}/ready`);
    return response.data;
  },

  send: async (id: string): Promise<CampaignSendResponse> => {
    const response = await apiClient.post<CampaignSendResponse>(`/api/v1/campaigns/${id}/send`);
    return response.data;
  },

  getStats: async (id: string): Promise<CampaignStats> => {
    const response = await apiClient.get<CampaignStats>(`/api/v1/campaigns/${id}/stats`);
    return response.data;
  },
};
