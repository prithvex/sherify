import { apiClient } from './client';
import { ContactList, ContactListCreate, ContactListUpdate, PaginatedResponse, PaginationParams } from '../types';

export const contactListsApi = {
  list: async (params?: PaginationParams): Promise<PaginatedResponse<ContactList>> => {
    const response = await apiClient.get<PaginatedResponse<ContactList>>('/api/v1/contact-lists', {
      params,
    });
    return response.data;
  },

  getById: async (id: string): Promise<ContactList> => {
    const response = await apiClient.get<ContactList>(`/api/v1/contact-lists/${id}`);
    return response.data;
  },

  create: async (data: ContactListCreate): Promise<ContactList> => {
    const response = await apiClient.post<ContactList>('/api/v1/contact-lists', data);
    return response.data;
  },

  update: async (id: string, data: ContactListUpdate): Promise<ContactList> => {
    const response = await apiClient.patch<ContactList>(`/api/v1/contact-lists/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/contact-lists/${id}`);
  },
};
