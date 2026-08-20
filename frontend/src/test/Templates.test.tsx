import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemplatesPage } from '../pages/templates/TemplatesPage';
import { TemplateCreatePage } from '../pages/templates/TemplateCreatePage';
import { templatesApi } from '../api/templates';

vi.mock('../api/templates', () => ({
  templatesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    getById: vi.fn(),
    update: vi.fn(),
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

describe('Templates Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders templates list', async () => {
    (templatesApi.list as any).mockResolvedValueOnce({
      items: [
        {
          id: 'tpl-1',
          name: 'Welcome Template',
          subject: 'Welcome to our platform',
          html_content: '<h1>Welcome</h1>',
          text_content: 'Welcome',
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
          <TemplatesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Welcome Template')).toBeInTheDocument();
      expect(screen.getByText(/Welcome to our platform/i)).toBeInTheDocument();
    });
  });

  it('submits new template with valid fields', async () => {
    (templatesApi.create as any).mockResolvedValueOnce({
      id: 'tpl-2',
      name: 'Product Update',
      subject: 'New features available',
      html_content: '<p>New features</p>',
      text_content: 'New features',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter>
          <TemplateCreatePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const nameInput = screen.getByLabelText(/Template Name/i);
    const subjectInput = screen.getByLabelText(/Default Subject Line/i);
    const saveBtn = screen.getByRole('button', { name: /Save Template/i });

    fireEvent.change(nameInput, { target: { value: 'Product Update' } });
    fireEvent.change(subjectInput, { target: { value: 'New features available' } });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect((templatesApi.create as any).mock.calls[0][0]).toEqual(
        expect.objectContaining({
          name: 'Product Update',
          subject: 'New features available',
        })
      );
    });
  });
});
