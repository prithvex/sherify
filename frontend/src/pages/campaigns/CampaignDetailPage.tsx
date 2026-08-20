import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Send,
  CheckCircle,
  AlertCircle,
  FileText,
  Users,
  BarChart3,
  CheckCircle2,
  Lock,
  Flame,
  Calendar,
  Clock,
  XCircle,
  Globe,
  UserCheck,
} from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { contactListsApi } from '../../api/contactLists';
import { templatesApi } from '../../api/templates';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Skeleton } from '../../components/common/Skeleton';
import { Alert } from '../../components/common/Alert';
import { ApiError, EmailCampaign } from '../../types';

const COMMON_TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
  { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST +5:30)' },
  { value: 'America/New_York', label: 'America/New_York (EST/EDT -5/-4)' },
  { value: 'America/Chicago', label: 'America/Chicago (CST/CDT -6/-5)' },
  { value: 'America/Denver', label: 'America/Denver (MST/MDT -7/-6)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST/PDT -8/-7)' },
  { value: 'Europe/London', label: 'Europe/London (GMT/BST +0/+1)' },
  { value: 'Europe/Paris', label: 'Europe/Paris (CET/CEST +1/+2)' },
  { value: 'Europe/Berlin', label: 'Europe/Berlin (CET/CEST +1/+2)' },
  { value: 'Asia/Dubai', label: 'Asia/Dubai (GST +4)' },
  { value: 'Asia/Singapore', label: 'Asia/Singapore (SGT +8)' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST +9)' },
  { value: 'Australia/Sydney', label: 'Australia/Sydney (AEST/AEDT +10/+11)' },
];

export const CampaignDetailPage: React.FC = () => {
  const { id: campaignId = '' } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [isSendModalOpen, setIsSendModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);

  // Scheduling Form State
  const defaultBrowserTz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [scheduleTimezone, setScheduleTimezone] = useState(defaultBrowserTz);

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Campaign Query with auto-polling if in-flight or scheduled
  const { data: campaign, isLoading } = useQuery({
    queryKey: ['campaign', campaignId],
    queryFn: () => campaignsApi.getById(campaignId),
    enabled: !!campaignId,
    refetchInterval: (query) => {
      const data = query.state.data as EmailCampaign | undefined;
      if (data && (data.status === 'queued' || data.status === 'sending')) {
        return 1500;
      }
      return false;
    },
  });

  // Associated Contact List
  const { data: contactList } = useQuery({
    queryKey: ['contact-list', campaign?.contact_list_id],
    queryFn: () => contactListsApi.getById(campaign!.contact_list_id),
    enabled: !!campaign?.contact_list_id,
  });

  // Associated Template
  const { data: template } = useQuery({
    queryKey: ['template', campaign?.template_id],
    queryFn: () => templatesApi.getById(campaign!.template_id),
    enabled: !!campaign?.template_id,
  });

  // Transition to READY mutation
  const readyMutation = useMutation({
    mutationFn: () => campaignsApi.markReady(campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign', campaignId] });
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setError(null);
      setSuccessMessage('Campaign marked READY and validated for dispatch.');
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to transition campaign to READY status.');
    },
  });

  // Send Immediately mutation (202 Accepted)
  const sendMutation = useMutation({
    mutationFn: () => campaignsApi.send(campaignId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['campaign', campaignId] });
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setIsSendModalOpen(false);
      setError(null);
      setSuccessMessage(data.message || 'Campaign queued successfully. Worker is processing dispatches.');
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to enqueue campaign for sending.');
    },
  });

  // Schedule Campaign mutation
  const scheduleMutation = useMutation({
    mutationFn: (data: { scheduled_at: string; timezone: string }) =>
      campaignsApi.schedule(campaignId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['campaign', campaignId] });
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setIsScheduleModalOpen(false);
      setError(null);
      const scheduledLocal = data.scheduled_at ? new Date(data.scheduled_at).toLocaleString() : 'target date';
      setSuccessMessage(`Campaign scheduled successfully for ${scheduledLocal} (${data.timezone}).`);
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to schedule campaign.');
    },
  });

  // Cancel Campaign mutation
  const cancelMutation = useMutation({
    mutationFn: () => campaignsApi.cancel(campaignId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign', campaignId] });
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setIsCancelModalOpen(false);
      setError(null);
      setSuccessMessage('Campaign has been successfully cancelled.');
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to cancel campaign.');
    },
  });

  const handleScheduleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!scheduleDate || !scheduleTime) {
      setError('Please select both a scheduled date and time.');
      return;
    }

    try {
      // Build date-time string in local timezone format
      const combinedLocal = `${scheduleDate}T${scheduleTime}:00`;
      const localDate = new Date(combinedLocal);

      if (isNaN(localDate.getTime())) {
        setError('Invalid date or time value provided.');
        return;
      }

      if (localDate.getTime() <= Date.now()) {
        setError('Scheduled datetime must be in the future.');
        return;
      }

      scheduleMutation.mutate({
        scheduled_at: localDate.toISOString(),
        timezone: scheduleTimezone,
      });
    } catch {
      setError('Failed to construct valid scheduled datetime.');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="space-y-4">
        <Alert type="error" message="Campaign not found." />
        <Link to="/campaigns">
          <Button variant="outline" size="sm">Back to Campaigns</Button>
        </Link>
      </div>
    );
  }

  // Today string for min date (YYYY-MM-DD)
  const todayStr = new Date().toISOString().split('T')[0];

  return (
    <div className="space-y-6">
      {/* Back button & Header */}
      <div>
        <Link
          to="/campaigns"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Campaigns
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
                {campaign.name}
              </h2>
              <Badge variant={campaign.status}>{campaign.status}</Badge>
            </div>
            <p className="text-xs text-slate-400">Subject: {campaign.subject}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* DRAFT -> READY Action */}
            {campaign.status === 'draft' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => readyMutation.mutate()}
                isLoading={readyMutation.isPending}
                leftIcon={<CheckCircle className="w-4 h-4" />}
              >
                Mark as READY
              </Button>
            )}

            {/* READY -> Schedule or Send Actions */}
            {campaign.status === 'ready' && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsScheduleModalOpen(true)}
                  leftIcon={<Calendar className="w-4 h-4 text-cyan-400" />}
                >
                  Schedule for Later
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsSendModalOpen(true)}
                  leftIcon={<Send className="w-4 h-4" />}
                  className="bg-emerald-600 hover:bg-emerald-500 border-emerald-500/30"
                >
                  Send Immediately
                </Button>
              </>
            )}

            {/* SCHEDULED -> Cancel Action */}
            {campaign.status === 'scheduled' && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => setIsCancelModalOpen(true)}
                leftIcon={<XCircle className="w-4 h-4" />}
              >
                Cancel Scheduled Campaign
              </Button>
            )}

            {/* QUEUED -> Cancel Action */}
            {campaign.status === 'queued' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCancelModalOpen(true)}
                className="text-rose-400 hover:text-rose-300"
                leftIcon={<XCircle className="w-4 h-4" />}
              >
                Cancel Queue
              </Button>
            )}

            {/* Stats shortcut */}
            {(campaign.status === 'completed' || campaign.status === 'sending' || campaign.status === 'queued') && (
              <Link to={`/campaigns/${campaign.id}/analytics`}>
                <Button variant="secondary" size="sm" leftIcon={<BarChart3 className="w-4 h-4" />}>
                  View Analytics
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}
      {successMessage && <Alert type="success" message={successMessage} />}

      {/* Scheduled State Tracker Card */}
      {campaign.status === 'scheduled' && campaign.scheduled_at && (
        <div className="rounded-xl border border-cyan-900/60 bg-cyan-950/40 p-5 shadow-lg space-y-3 backdrop-blur">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Campaign Scheduled for Delivery</h3>
                <p className="text-xs text-cyan-300/90 mt-0.5">
                  Target Time:{' '}
                  <strong className="text-white">
                    {new Date(campaign.scheduled_at).toLocaleString()}
                  </strong>{' '}
                  ({campaign.timezone || 'UTC'})
                </p>
              </div>
            </div>
            <Badge variant="scheduled">SCHEDULED</Badge>
          </div>
          <p className="text-[11px] text-slate-400 border-t border-cyan-900/40 pt-2.5">
            Celery Beat periodic scheduler automatically detects due scheduled campaigns and atomically queues execution.
          </p>
        </div>
      )}

      {/* Execution Tracker Card for in-flight or finished campaigns */}
      {(campaign.status === 'queued' || campaign.status === 'sending' || campaign.status === 'completed' || campaign.status === 'failed' || campaign.status === 'cancelled') && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {campaign.status === 'completed' ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              ) : campaign.status === 'failed' ? (
                <AlertCircle className="w-6 h-6 text-rose-400" />
              ) : campaign.status === 'cancelled' ? (
                <XCircle className="w-6 h-6 text-slate-400" />
              ) : (
                <Flame className="w-6 h-6 text-indigo-400 animate-pulse" />
              )}
              <div>
                <h3 className="text-sm font-semibold text-white capitalize">
                  Campaign Status: {campaign.status}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {campaign.status === 'queued' && 'Task received and queued in Redis for Celery worker dispatch.'}
                  {campaign.status === 'sending' && 'Celery worker is actively dispatching emails with rate limiting.'}
                  {campaign.status === 'completed' && 'All recipient snapshots processed. Real delivery & engagement stats available.'}
                  {campaign.status === 'failed' && 'Execution encountered permanent errors during delivery.'}
                  {campaign.status === 'cancelled' && 'Campaign execution was cancelled. No further dispatches will occur.'}
                </p>
              </div>
            </div>

            {campaign.status !== 'cancelled' && (
              <Link to={`/campaigns/${campaign.id}/analytics`}>
                <Button variant="outline" size="sm" leftIcon={<BarChart3 className="w-3.5 h-3.5" />}>
                  Live Stats
                </Button>
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Campaign Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Contact List Details */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <div className="flex items-center gap-2.5 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-3">
            <Users className="w-4 h-4 text-indigo-400" />
            <span>Target Audience</span>
          </div>
          <div>
            <h4 className="font-semibold text-slate-200 text-sm">
              {contactList?.name || 'Loading List...'}
            </h4>
            <p className="text-xs text-slate-400 mt-1">
              {contactList?.description || 'No description provided.'}
            </p>
          </div>
          {contactList && (
            <div className="pt-2">
              <Link to={`/contacts/${contactList.id}`}>
                <Button variant="ghost" size="sm" className="text-indigo-400 hover:text-indigo-300 -ml-2">
                  View Contact List →
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Template Details */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <div className="flex items-center gap-2.5 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-3">
            <FileText className="w-4 h-4 text-purple-400" />
            <span>Email Template</span>
          </div>
          <div>
            <h4 className="font-semibold text-slate-200 text-sm">
              {template?.name || 'Loading Template...'}
            </h4>
            <p className="text-xs text-slate-400 mt-1">
              Subject: <span className="text-slate-300 font-medium">{template?.subject}</span>
            </p>
          </div>
          {template && (
            <div className="pt-2">
              <Link to={`/templates/${template.id}/edit`}>
                <Button variant="ghost" size="sm" className="text-purple-400 hover:text-purple-300 -ml-2">
                  View Template Details →
                </Button>
              </Link>
            </div>
          )}
        </div>

        {/* Sender Identity Details */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <div className="flex items-center gap-2.5 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-3">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            <span>Sender Identity</span>
          </div>
          <div className="space-y-1.5 text-xs">
            <div>
              <span className="text-slate-500 font-semibold block text-[10px] uppercase">From Name</span>
              <p className="text-slate-200">{campaign.from_name || <span className="text-slate-500 italic">Default system sender</span>}</p>
            </div>
            <div>
              <span className="text-slate-500 font-semibold block text-[10px] uppercase">From Email</span>
              <p className="text-slate-200">{campaign.from_email || <span className="text-slate-500 italic">Default system address</span>}</p>
            </div>
            {campaign.reply_to && (
              <div>
                <span className="text-slate-500 font-semibold block text-[10px] uppercase">Reply-To</span>
                <p className="text-slate-300 font-mono text-[11px]">{campaign.reply_to}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Immutability Note */}
      {campaign.status !== 'draft' && campaign.status !== 'ready' && (
        <div className="rounded-lg border border-slate-800/80 bg-slate-900/40 p-4 flex items-center gap-3 text-xs text-slate-400">
          <Lock className="w-4 h-4 text-slate-500 shrink-0" />
          <span>
            This campaign is locked in <strong>{campaign.status.toUpperCase()}</strong> status. Its template, audience, and schedule associations are immutable.
          </span>
        </div>
      )}

      {/* Send Confirmation Modal */}
      <Modal
        isOpen={isSendModalOpen}
        onClose={() => setIsSendModalOpen(false)}
        title="Confirm Immediate Dispatch"
        description={`You are about to send "${campaign.name}" to subscribers in "${contactList?.name}".`}
      >
        <div className="space-y-4">
          <div className="rounded-lg bg-amber-950/40 border border-amber-800/60 p-3.5 text-xs text-amber-300 space-y-1">
            <p className="font-semibold flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-amber-400" /> Asynchronous Batch Execution
            </p>
            <p>
              Submitting this request snapshots all active subscribers in the contact list, transitions the campaign to QUEUED, and dispatches the background Celery task.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsSendModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => sendMutation.mutate()}
              isLoading={sendMutation.isPending}
              leftIcon={<Send className="w-4 h-4" />}
              className="bg-emerald-600 hover:bg-emerald-500 border-emerald-500/30"
            >
              Confirm & Queue Campaign
            </Button>
          </div>
        </div>
      </Modal>

      {/* Schedule Campaign Modal */}
      <Modal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        title="Schedule Campaign Dispatch"
        description={`Configure date, time, and timezone for "${campaign.name}".`}
      >
        <form onSubmit={handleScheduleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              type="date"
              label="Schedule Date"
              min={todayStr}
              value={scheduleDate}
              onChange={(e) => setScheduleDate(e.target.value)}
              required
            />
            <Input
              type="time"
              label="Schedule Time"
              value={scheduleTime}
              onChange={(e) => setScheduleTime(e.target.value)}
              required
            />
          </div>

          <Select
            label="Timezone"
            value={scheduleTimezone}
            onChange={(e) => setScheduleTimezone(e.target.value)}
            options={COMMON_TIMEZONES}
            required
          />

          <div className="rounded-lg bg-cyan-950/40 border border-cyan-800/60 p-3.5 text-xs text-cyan-300 flex items-start gap-2.5">
            <Globe className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold">Timezone-Aware UTC Scheduling</p>
              <p className="text-[11px] text-cyan-300/90 leading-relaxed">
                The campaign schedule will be converted to UTC and executed by Celery Beat at your selected target time.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsScheduleModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={scheduleMutation.isPending}
              leftIcon={<Calendar className="w-4 h-4" />}
            >
              Confirm Schedule
            </Button>
          </div>
        </form>
      </Modal>

      {/* Cancel Confirmation Modal */}
      <Modal
        isOpen={isCancelModalOpen}
        onClose={() => setIsCancelModalOpen(false)}
        title="Cancel Campaign"
        description={`Are you sure you want to cancel "${campaign.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            Cancelling this campaign will halt future scheduler triggers or abort pending Celery worker batches. Any emails already sent to the provider cannot be unsent.
          </p>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsCancelModalOpen(false)}>
              Back
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => cancelMutation.mutate()}
              isLoading={cancelMutation.isPending}
            >
              Confirm Cancellation
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
