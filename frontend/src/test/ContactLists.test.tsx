import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ContactListsPage } from '../pages/contacts/ContactListsPage';
import { contactListsApi } from '../api/contactLists';

vi.mock('../api/contactLists', () => ({
  contactListsApi: {
    list: vi.fn(),
    create: vi.fn(),
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

describe('ContactListsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders contact lists successfully', async () => {
    (contactListsApi.list as any).mockResolvedValueOnce({
      items: [
        {
          id: 'list-1',
          name: 'Newsletter VIPs',
          description: 'High-value newsletter subscribers',
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
        <MemoryRouter>
          <ContactListsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Newsletter VIPs')).toBeInTheDocument();
      expect(screen.getByText('High-value newsletter subscribers')).toBeInTheDocument();
    });
  });

  it('opens create modal and handles list creation', async () => {
    (contactListsApi.list as any).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
      pages: 0,
    });
    (contactListsApi.create as any).mockResolvedValueOnce({
      id: 'list-2',
      name: 'Beta Users',
      description: 'Product testers',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter>
          <ContactListsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const createBtn = screen.getByRole('button', { name: /Create Contact List/i });
    fireEvent.click(createBtn);

    expect(screen.getByText(/Set up a new audience group/i)).toBeInTheDocument();

    const nameInput = screen.getByLabelText(/List Name/i);
    const descInput = screen.getByLabelText(/Description/i);

    fireEvent.change(nameInput, { target: { value: 'Beta Users' } });
    fireEvent.change(descInput, { target: { value: 'Product testers' } });

    const submitBtn = screen.getByRole('button', { name: /^Create List$/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect((contactListsApi.create as any).mock.calls[0][0]).toEqual({
        name: 'Beta Users',
        description: 'Product testers',
      });
    });
  });
});
