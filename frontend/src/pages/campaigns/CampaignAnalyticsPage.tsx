import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Send,
  MailCheck,
  MailX,
  Eye,
  TrendingUp,
  RotateCcw,
  Calendar,
  UserCheck,
} from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Skeleton } from '../../components/common/Skeleton';
import { Alert } from '../../components/common/Alert';

export const CampaignAnalyticsPage: React.FC = () => {
  const { id: campaignId = '' } = useParams<{ id: string }>();

  const { data: campaign } = useQuery({
    queryKey: ['campaign', campaignId],
    queryFn: () => campaignsApi.getById(campaignId),
    enabled: !!campaignId,
  });

  const {
    data: stats,
    isLoading,
    isRefetching,
    refetch,
    error,
  } = useQuery({
    queryKey: ['campaign-stats', campaignId],
    queryFn: () => campaignsApi.getStats(campaignId),
    enabled: !!campaignId,
    refetchInterval: () => {
      if (campaign && (campaign.status === 'queued' || campaign.status === 'sending')) {
        return 2000;
      }
      return false;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Alert type="error" message="Unable to load campaign statistics." />
        <Link to={`/campaigns/${campaignId}`}>
          <Button variant="outline" size="sm">Back to Campaign</Button>
        </Link>
      </div>
    );
  }

  const openRatePct = stats ? (stats.open_rate * 100).toFixed(1) : '0.0';
  const bounceRatePct = stats ? (stats.bounce_rate * 100).toFixed(1) : '0.0';

  const total = stats?.total_recipients || 0;
  const sent = stats?.sent_count || 0;
  const failed = stats?.failed_count || 0;
  const bounced = stats?.bounced_count || 0;
  const opened = stats?.opened_count || 0;

  const deliveryRate = total > 0 ? (((sent - bounced) / total) * 100).toFixed(1) : '0.0';

  return (
    <div className="space-y-8">
      {/* Back button & Header */}
      <div>
        <Link
          to={`/campaigns/${campaignId}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Campaign Details
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
                Analytics: {campaign?.name || 'Campaign'}
              </h2>
              {campaign && <Badge variant={campaign.status}>{campaign.status}</Badge>}
            </div>
            <p className="text-xs text-slate-400">
              Durable delivery & engagement metrics computed via PostgreSQL SQL aggregation
            </p>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            isLoading={isRefetching}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
          >
            Refresh Stats
          </Button>
        </div>
      </div>

      {/* Campaign Metadata Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold block mb-1">
            Subject Line
          </span>
          <p className="text-slate-200 font-semibold truncate">{campaign?.subject}</p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex items-start gap-3">
          <UserCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5 truncate">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold block">
              Sender Identity
            </span>
            <p className="text-slate-200 font-medium truncate">
              {campaign?.from_name ? `${campaign.from_name} <${campaign.from_email}>` : 'System Default Sender'}
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex items-start gap-3">
          <Calendar className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold block">
              Dispatch Schedule
            </span>
            <p className="text-slate-200 font-medium">
              {campaign?.scheduled_at ? (
                <span>
                  {new Date(campaign.scheduled_at).toLocaleString()} ({campaign.timezone || 'UTC'})
                </span>
              ) : (
                'Immediate Dispatch'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Recipients */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Total Recipients
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Send className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{total.toLocaleString()}</span>
            <p className="mt-1 text-[11px] text-slate-500">Immutable recipient snapshot</p>
          </div>
        </div>

        {/* Successfully Sent */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Delivered / Sent
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <MailCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-400">{sent.toLocaleString()}</span>
            <p className="mt-1 text-[11px] text-slate-500">{deliveryRate}% delivery rate</p>
          </div>
        </div>

        {/* Unique Opens */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Unique Opens
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Eye className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-purple-400">{opened.toLocaleString()}</span>
              <span className="text-sm font-semibold text-purple-300 font-mono">
                ({openRatePct}%)
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">First-open pixel events</p>
          </div>
        </div>

        {/* Bounces */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Bounced Emails
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <MailX className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-rose-400">{bounced.toLocaleString()}</span>
              <span className="text-sm font-semibold text-rose-300 font-mono">
                ({bounceRatePct}%)
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">Provider webhook bounces</p>
          </div>
        </div>
      </div>

      {/* Visual Rate Breakdown Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Delivery Funnel Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Delivery Status Breakdown</span>
            </div>
            <span className="text-xs text-slate-400 font-mono">{sent} / {total} Dispatched</span>
          </div>

          <div className="space-y-4">
            {/* Sent bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Successfully Sent</span>
                <span className="text-emerald-400 font-bold">{sent} ({total > 0 ? ((sent / total) * 100).toFixed(1) : 0}%)</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${total > 0 ? (sent / total) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Bounced bar */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Bounced (Provider Webhook)</span>
                <span className="text-rose-400 font-bold">{bounced} ({bounceRatePct}%)</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full transition-all duration-500"
                  style={{ width: `${sent > 0 ? (bounced / sent) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Permanent Failures */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Delivery Failures</span>
                <span className="text-amber-400 font-bold">{failed} ({total > 0 ? ((failed / total) * 100).toFixed(1) : 0}%)</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full transition-all duration-500"
                  style={{ width: `${total > 0 ? (failed / total) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Engagement Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <Eye className="w-4 h-4 text-purple-400" />
              <span>Audience Engagement (Open Rate)</span>
            </div>
            <span className="text-xs text-purple-400 font-mono">{opened} Opened</span>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-center p-6 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-center space-y-1">
                <span className="text-4xl font-extrabold text-purple-400 font-mono">{openRatePct}%</span>
                <p className="text-xs text-slate-400">Unique Email Open Rate</p>
                <p className="text-[11px] text-slate-500">
                  {opened} of {sent} delivered recipients opened the email
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Open Rate Progression</span>
                <span className="text-purple-400 font-bold">{openRatePct}%</span>
              </div>
              <div className="h-2.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(parseFloat(openRatePct), 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
