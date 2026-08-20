import { apiClient } from './client';
import { EmailTemplate, EmailTemplateCreate, EmailTemplateUpdate, PaginatedResponse, PaginationParams } from '../types';

export const templatesApi = {
  list: async (params?: PaginationParams): Promise<PaginatedResponse<EmailTemplate>> => {
    const response = await apiClient.get<PaginatedResponse<EmailTemplate>>('/api/v1/templates', {
      params,
    });
    return response.data;
  },

  getById: async (id: string): Promise<EmailTemplate> => {
    const response = await apiClient.get<EmailTemplate>(`/api/v1/templates/${id}`);
    return response.data;
  },

  create: async (data: EmailTemplateCreate): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>('/api/v1/templates', data);
    return response.data;
  },

  update: async (id: string, data: EmailTemplateUpdate): Promise<EmailTemplate> => {
    const response = await apiClient.patch<EmailTemplate>(`/api/v1/templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/templates/${id}`);
  },
};
