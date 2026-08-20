import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CampaignDetailPage } from '../pages/campaigns/CampaignDetailPage';
import { campaignsApi } from '../api/campaigns';

vi.mock('../api/campaigns', () => ({
  campaignsApi: {
    list: vi.fn(),
    getById: vi.fn(),
    schedule: vi.fn(),
    cancel: vi.fn(),
    send: vi.fn(),
    markReady: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../api/contactLists', () => ({
  contactListsApi: {
    getById: vi.fn().mockResolvedValue({ id: 'list-1', name: 'VIP List', description: 'VIPs' }),
  },
}));

vi.mock('../api/templates', () => ({
  templatesApi: {
    getById: vi.fn().mockResolvedValue({ id: 'tpl-1', name: 'Promo Template', subject: 'Special Offer' }),
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

describe('Campaign Scheduling & Cancellation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders schedule action on READY campaign and opens schedule modal', async () => {
    (campaignsApi.getById as any).mockResolvedValueOnce({
      id: 'camp-ready-1',
      name: 'Spring Launch',
      subject: 'Big News',
      template_id: 'tpl-1',
      contact_list_id: 'list-1',
      status: 'ready',
      scheduled_at: null,
      timezone: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    (campaignsApi.schedule as any).mockResolvedValueOnce({
      id: 'camp-ready-1',
      name: 'Spring Launch',
      subject: 'Big News',
      template_id: 'tpl-1',
      contact_list_id: 'list-1',
      status: 'scheduled',
      scheduled_at: new Date(Date.now() + 86400000).toISOString(),
      timezone: 'UTC',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter initialEntries={['/campaigns/camp-ready-1']}>
          <Routes>
            <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Schedule for Later')).toBeInTheDocument();
      expect(screen.getByText('Send Immediately')).toBeInTheDocument();
    });

    // Open Schedule Modal
    fireEvent.click(screen.getByText('Schedule for Later'));

    expect(screen.getByText(/Configure date, time, and timezone/i)).toBeInTheDocument();

    const dateInput = screen.getByLabelText(/Schedule Date/i);
    const timeInput = screen.getByLabelText(/Schedule Time/i);

    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
    fireEvent.change(dateInput, { target: { value: tomorrow } });
    fireEvent.change(timeInput, { target: { value: '14:30' } });

    const submitBtn = screen.getByRole('button', { name: /Confirm Schedule/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(campaignsApi.schedule).toHaveBeenCalledWith(
        'camp-ready-1',
        expect.objectContaining({
          timezone: expect.any(String),
        })
      );
    });
  });

  it('renders cancel action on SCHEDULED campaign and handles cancellation', async () => {
    (campaignsApi.getById as any).mockResolvedValueOnce({
      id: 'camp-scheduled-1',
      name: 'Future Promo',
      subject: 'Upcoming Deals',
      template_id: 'tpl-1',
      contact_list_id: 'list-1',
      status: 'scheduled',
      scheduled_at: new Date(Date.now() + 86400000).toISOString(),
      timezone: 'Asia/Kolkata',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    (campaignsApi.cancel as any).mockResolvedValueOnce({
      id: 'camp-scheduled-1',
      name: 'Future Promo',
      subject: 'Upcoming Deals',
      template_id: 'tpl-1',
      contact_list_id: 'list-1',
      status: 'cancelled',
      scheduled_at: new Date(Date.now() + 86400000).toISOString(),
      timezone: 'Asia/Kolkata',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter initialEntries={['/campaigns/camp-scheduled-1']}>
          <Routes>
            <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Cancel Scheduled Campaign/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Cancel Scheduled Campaign/i));

    expect(screen.getByText(/Cancelling this campaign will halt future scheduler triggers/i)).toBeInTheDocument();

    const confirmBtn = screen.getByRole('button', { name: /Confirm Cancellation/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(campaignsApi.cancel).toHaveBeenCalledWith('camp-scheduled-1');
    });
  });
});
