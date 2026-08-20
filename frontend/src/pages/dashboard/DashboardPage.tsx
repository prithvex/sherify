import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Users,
  Send,
  FileText,
  TrendingUp,
  Plus,
  ArrowRight,
  BarChart3,
} from 'lucide-react';
import { contactListsApi } from '../../api/contactLists';
import { campaignsApi } from '../../api/campaigns';
import { templatesApi } from '../../api/templates';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';

export const DashboardPage: React.FC = () => {
  const { data: contactListsData, isLoading: loadingLists } = useQuery({
    queryKey: ['contact-lists', { page: 1, page_size: 10 }],
    queryFn: () => contactListsApi.list({ page: 1, page_size: 10 }),
  });

  const { data: campaignsData, isLoading: loadingCampaigns } = useQuery({
    queryKey: ['campaigns', { page: 1, page_size: 5 }],
    queryFn: () => campaignsApi.list({ page: 1, page_size: 5 }),
  });

  const { data: templatesData, isLoading: loadingTemplates } = useQuery({
    queryKey: ['templates', { page: 1, page_size: 10 }],
    queryFn: () => templatesApi.list({ page: 1, page_size: 10 }),
  });

  const totalLists = contactListsData?.total ?? 0;
  const totalCampaigns = campaignsData?.total ?? 0;
  const totalTemplates = templatesData?.total ?? 0;

  const recentCampaigns = campaignsData?.items ?? [];

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
            System Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time campaign delivery metrics and resource status
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/campaigns/new">
            <Button variant="primary" size="sm" leftIcon={<Plus className="w-3.5 h-3.5" />}>
              Create Campaign
            </Button>
          </Link>
          <Link to="/contacts">
            <Button variant="outline" size="sm" leftIcon={<Users className="w-3.5 h-3.5" />}>
              Manage Lists
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Campaigns */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Total Campaigns
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Send className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loadingCampaigns ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <span className="text-2xl font-bold text-white">{totalCampaigns}</span>
            )}
            <p className="mt-1 text-[11px] text-slate-500">Recorded campaign entities</p>
          </div>
        </div>

        {/* Total Contact Lists */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Contact Lists
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loadingLists ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <span className="text-2xl font-bold text-white">{totalLists}</span>
            )}
            <p className="mt-1 text-[11px] text-slate-500">Audience segments defined</p>
          </div>
        </div>

        {/* Email Templates */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Email Templates
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {loadingTemplates ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <span className="text-2xl font-bold text-white">{totalTemplates}</span>
            )}
            <p className="mt-1 text-[11px] text-slate-500">Reusable HTML & text designs</p>
          </div>
        </div>

        {/* Delivery Engine Health */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Execution Engine
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-semibold text-emerald-400">Celery + Redis Active</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">Ready for batch dispatches</p>
          </div>
        </div>
      </div>

      {/* Quick Launch & Recent Campaigns */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Recent Campaigns Table */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-white">Recent Campaigns</h3>
              <p className="text-xs text-slate-400 mt-0.5">Latest dispatches and their status</p>
            </div>
            <Link
              to="/campaigns"
              className="text-xs font-medium text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="mt-4">
            {loadingCampaigns ? (
              <div className="space-y-3">
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </div>
            ) : recentCampaigns.length === 0 ? (
              <EmptyState
                icon={<Send className="w-6 h-6" />}
                title="No campaigns yet"
                description="Create your first campaign to begin dispatching bulk emails to your audiences."
                actionLabel="Create Campaign"
                onAction={() => (window.location.href = '/campaigns/new')}
              />
            ) : (
              <div className="divide-y divide-slate-800/80 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-400">
                      <th className="pb-3 font-semibold">Name & Subject</th>
                      <th className="pb-3 font-semibold">Status</th>
                      <th className="pb-3 font-semibold">Created</th>
                      <th className="pb-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {recentCampaigns.map((campaign) => (
                      <tr key={campaign.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3.5 pr-4">
                          <p className="font-semibold text-slate-200">{campaign.name}</p>
                          <p className="text-slate-500 text-[11px] truncate max-w-xs">{campaign.subject}</p>
                        </td>
                        <td className="py-3.5 pr-4">
                          <Badge variant={campaign.status}>{campaign.status}</Badge>
                        </td>
                        <td className="py-3.5 text-slate-400 whitespace-nowrap">
                          {new Date(campaign.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3.5 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <Link to={`/campaigns/${campaign.id}`}>
                              <Button variant="outline" size="sm">
                                Details
                              </Button>
                            </Link>
                            {campaign.status === 'completed' && (
                              <Link to={`/campaigns/${campaign.id}/analytics`}>
                                <Button variant="secondary" size="sm" leftIcon={<BarChart3 className="w-3.5 h-3.5" />}>
                                  Stats
                                </Button>
                              </Link>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Quick Help / Steps Guide */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-4">
          <h3 className="text-sm font-semibold text-white">Campaign Workflow</h3>
          <p className="text-xs text-slate-400">
            Follow the standard 4-step sequence to dispatch asynchronous campaigns:
          </p>

          <div className="space-y-3 text-xs">
            <div className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/90 p-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400 font-bold shrink-0">
                1
              </div>
              <div>
                <p className="font-semibold text-slate-200">Create Contact List</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Upload CSV or add subscribers individually.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/90 p-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400 font-bold shrink-0">
                2
              </div>
              <div>
                <p className="font-semibold text-slate-200">Design Email Template</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Compose HTML and text formats with live preview.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/90 p-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400 font-bold shrink-0">
                3
              </div>
              <div>
                <p className="font-semibold text-slate-200">Transition to READY</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Validates ownership and locks template snapshot.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/90 p-3">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-indigo-400 font-bold shrink-0">
                4
              </div>
              <div>
                <p className="font-semibold text-slate-200">Send & Track Analytics</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Queues Celery task (202) and tracks real opens & bounces.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
