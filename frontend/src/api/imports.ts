import { apiClient } from './client';
import { ImportErrorItem, ImportJob, PaginatedResponse, PaginationParams } from '../types';

export const importsApi = {
  getJob: async (importJobId: string): Promise<ImportJob> => {
    const response = await apiClient.get<ImportJob>(`/api/v1/imports/${importJobId}`);
    return response.data;
  },

  getJobErrors: async (
    importJobId: string,
    params?: PaginationParams
  ): Promise<PaginatedResponse<ImportErrorItem>> => {
    const response = await apiClient.get<PaginatedResponse<ImportErrorItem>>(
      `/api/v1/imports/${importJobId}/errors`,
      { params }
    );
    return response.data;
  },
};
