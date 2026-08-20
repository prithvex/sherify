import { apiClient } from './client';
import {
  EmailCampaign,
  CampaignCreate,
  CampaignUpdate,
  CampaignScheduleRequest,
  CampaignSendResponse,
  CampaignStats,
  PaginatedResponse,
  PaginationParams,
} from '../types';

export const campaignsApi = {
  list: async (params: PaginationParams = {}): Promise<PaginatedResponse<EmailCampaign>> => {
    const response = await apiClient.get<PaginatedResponse<EmailCampaign>>('/api/v1/campaigns', {
      params,
    });
    return response.data;
  },

  getById: async (id: string): Promise<EmailCampaign> => {
    const response = await apiClient.get<EmailCampaign>(`/api/v1/campaigns/${id}`);
    return response.data;
  },

  create: async (data: CampaignCreate): Promise<EmailCampaign> => {
    const response = await apiClient.post<EmailCampaign>('/api/v1/campaigns', data);
    return response.data;
  },

  update: async (id: string, data: CampaignUpdate): Promise<EmailCampaign> => {
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

  schedule: async (id: string, data: CampaignScheduleRequest): Promise<EmailCampaign> => {
    const response = await apiClient.post<EmailCampaign>(`/api/v1/campaigns/${id}/schedule`, data);
    return response.data;
  },

  cancel: async (id: string): Promise<EmailCampaign> => {
    const response = await apiClient.post<EmailCampaign>(`/api/v1/campaigns/${id}/cancel`);
    return response.data;
  },

  getStats: async (id: string): Promise<CampaignStats> => {
    const response = await apiClient.get<CampaignStats>(`/api/v1/campaigns/${id}/stats`);
    return response.data;
  },
};
