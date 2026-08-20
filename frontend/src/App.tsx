import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { ContactListsPage } from './pages/contacts/ContactListsPage';
import { ContactListDetailPage } from './pages/contacts/ContactListDetailPage';
import { TemplatesPage } from './pages/templates/TemplatesPage';
import { TemplateCreatePage } from './pages/templates/TemplateCreatePage';
import { TemplateEditPage } from './pages/templates/TemplateEditPage';
import { CampaignsPage } from './pages/campaigns/CampaignsPage';
import { CampaignCreatePage } from './pages/campaigns/CampaignCreatePage';
import { CampaignDetailPage } from './pages/campaigns/CampaignDetailPage';
import { CampaignAnalyticsPage } from './pages/campaigns/CampaignAnalyticsPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { SettingsPage } from './pages/settings/SettingsPage';
import { NotFoundPage } from './pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 30, // 30 seconds
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected Routes */}
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              
              {/* Contacts */}
              <Route path="/contacts" element={<ContactListsPage />} />
              <Route path="/contacts/:id" element={<ContactListDetailPage />} />

              {/* Templates */}
              <Route path="/templates" element={<TemplatesPage />} />
              <Route path="/templates/new" element={<TemplateCreatePage />} />
              <Route path="/templates/:id/edit" element={<TemplateEditPage />} />

              {/* Campaigns */}
              <Route path="/campaigns" element={<CampaignsPage />} />
              <Route path="/campaigns/new" element={<CampaignCreatePage />} />
              <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
              <Route path="/campaigns/:id/analytics" element={<CampaignAnalyticsPage />} />

              {/* Analytics */}
              <Route path="/analytics" element={<AnalyticsPage />} />

              {/* Settings */}
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            {/* 404 Fallback */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};
