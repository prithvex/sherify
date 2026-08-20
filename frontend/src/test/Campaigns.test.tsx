import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CampaignsPage } from '../pages/campaigns/CampaignsPage';
import { CampaignAnalyticsPage } from '../pages/campaigns/CampaignAnalyticsPage';
import { campaignsApi } from '../api/campaigns';

vi.mock('../api/campaigns', () => ({
  campaignsApi: {
    list: vi.fn(),
    getById: vi.fn(),
    getStats: vi.fn(),
    delete: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('Campaigns Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders campaigns table and status badge correctly', async () => {
    (campaignsApi.list as any).mockResolvedValueOnce({
      items: [
        {
          id: 'camp-1',
          name: 'Spring Launch',
          subject: 'Big Announcement',
          template_id: 'tpl-1',
          contact_list_id: 'list-1',
          status: 'ready',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      page_size: 10,
      pages: 1,
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter initialEntries={['/campaigns']}>
          <Routes>
            <Route path="/campaigns" element={<CampaignsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Spring Launch')).toBeInTheDocument();
      expect(screen.getByText('ready')).toBeInTheDocument();
    });
  });

  it('renders campaign analytics and calculated rates accurately', async () => {
    (campaignsApi.getById as any).mockResolvedValueOnce({
      id: 'camp-100',
      name: 'Black Friday Campaign',
      subject: '50% Off Everything',
      template_id: 'tpl-1',
      contact_list_id: 'list-1',
      status: 'completed',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    (campaignsApi.getStats as any).mockResolvedValueOnce({
      campaign_id: 'camp-100',
      total_recipients: 1000,
      sent_count: 980,
      failed_count: 20,
      bounced_count: 49,
      opened_count: 392,
      open_rate: 0.4,
      bounce_rate: 0.05,
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter initialEntries={['/campaigns/camp-100/analytics']}>
          <Routes>
            <Route path="/campaigns/:id/analytics" element={<CampaignAnalyticsPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/1,000/i)).toBeInTheDocument();
      expect(screen.getAllByText(/980/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/392/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/49/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/40.0%/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/5.0%/i).length).toBeGreaterThan(0);
    });
  });
});
