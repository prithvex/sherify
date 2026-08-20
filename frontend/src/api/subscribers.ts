import { apiClient } from './client';
import {
  ImportInitiateResponse,
  PaginatedResponse,
  PaginationParams,
  Subscriber,
  SubscriberCreate,
  SubscriberUpdate,
} from '../types';

export interface SubscriberQueryParams extends PaginationParams {
  status?: string;
}

export const subscribersApi = {
  list: async (
    contactListId: string,
    params?: SubscriberQueryParams
  ): Promise<PaginatedResponse<Subscriber>> => {
    const response = await apiClient.get<PaginatedResponse<Subscriber>>(
      `/api/v1/contact-lists/${contactListId}/subscribers`,
      { params }
    );
    return response.data;
  },

  getById: async (contactListId: string, subscriberId: string): Promise<Subscriber> => {
    const response = await apiClient.get<Subscriber>(
      `/api/v1/contact-lists/${contactListId}/subscribers/${subscriberId}`
    );
    return response.data;
  },

  create: async (contactListId: string, data: SubscriberCreate): Promise<Subscriber> => {
    const response = await apiClient.post<Subscriber>(
      `/api/v1/contact-lists/${contactListId}/subscribers`,
      data
    );
    return response.data;
  },

  update: async (
    contactListId: string,
    subscriberId: string,
    data: SubscriberUpdate
  ): Promise<Subscriber> => {
    const response = await apiClient.patch<Subscriber>(
      `/api/v1/contact-lists/${contactListId}/subscribers/${subscriberId}`,
      data
    );
    return response.data;
  },

  delete: async (contactListId: string, subscriberId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/contact-lists/${contactListId}/subscribers/${subscriberId}`);
  },

  importCsv: async (contactListId: string, file: File): Promise<ImportInitiateResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<ImportInitiateResponse>(
      `/api/v1/contact-lists/${contactListId}/subscribers/import`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
