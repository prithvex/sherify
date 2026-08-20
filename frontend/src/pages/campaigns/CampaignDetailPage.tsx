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
} from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { contactListsApi } from '../../api/contactLists';
import { templatesApi } from '../../api/templates';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Skeleton } from '../../components/common/Skeleton';
import { Alert } from '../../components/common/Alert';
import { ApiError, EmailCampaign } from '../../types';

export const CampaignDetailPage: React.FC = () => {
  const { id: campaignId = '' } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [isSendModalOpen, setIsSendModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sendSuccessMessage, setSendSuccessMessage] = useState<string | null>(null);

  // Campaign Query with auto-polling if in-flight
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
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to transition campaign to READY status.');
    },
  });

  // Send Campaign mutation (202 Accepted)
  const sendMutation = useMutation({
    mutationFn: () => campaignsApi.send(campaignId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['campaign', campaignId] });
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setIsSendModalOpen(false);
      setError(null);
      setSendSuccessMessage(data.message || 'Campaign queued successfully. Worker is processing dispatches.');
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to enqueue campaign for sending.');
    },
  });

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

          <div className="flex items-center gap-3">
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

            {/* READY -> SEND Action */}
            {campaign.status === 'ready' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsSendModalOpen(true)}
                leftIcon={<Send className="w-4 h-4" />}
                className="bg-emerald-600 hover:bg-emerald-500 border-emerald-500/30"
              >
                Send Campaign
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
      {sendSuccessMessage && <Alert type="success" message={sendSuccessMessage} />}

      {/* Execution Tracker Card for in-flight or finished campaigns */}
      {(campaign.status === 'queued' || campaign.status === 'sending' || campaign.status === 'completed' || campaign.status === 'failed') && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {campaign.status === 'completed' ? (
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              ) : campaign.status === 'failed' ? (
                <AlertCircle className="w-6 h-6 text-rose-400" />
              ) : (
                <Flame className="w-6 h-6 text-indigo-400 animate-pulse" />
              )}
              <div>
                <h3 className="text-sm font-semibold text-white capitalize">
                  Campaign Execution: {campaign.status}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {campaign.status === 'queued' && 'Task received and queued in Redis for Celery worker dispatch.'}
                  {campaign.status === 'sending' && 'Celery worker is actively dispatching emails in batches.'}
                  {campaign.status === 'completed' && 'All recipient snapshots processed. Real delivery & engagement stats available.'}
                  {campaign.status === 'failed' && 'Execution encountered permanent errors during delivery.'}
                </p>
              </div>
            </div>

            <Link to={`/campaigns/${campaign.id}/analytics`}>
              <Button variant="outline" size="sm" leftIcon={<BarChart3 className="w-3.5 h-3.5" />}>
                Live Stats
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Campaign Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
      </div>

      {/* Immutability Note */}
      {campaign.status !== 'draft' && (
        <div className="rounded-lg border border-slate-800/80 bg-slate-900/40 p-4 flex items-center gap-3 text-xs text-slate-400">
          <Lock className="w-4 h-4 text-slate-500 shrink-0" />
          <span>
            This campaign is locked in <strong>{campaign.status.toUpperCase()}</strong> status. Its template and audience associations cannot be modified.
          </span>
        </div>
      )}

      {/* Send Confirmation Modal */}
      <Modal
        isOpen={isSendModalOpen}
        onClose={() => setIsSendModalOpen(false)}
        title="Confirm Campaign Dispatch"
        description={`You are about to send "${campaign.name}" to the subscribers in "${contactList?.name}".`}
      >
        <div className="space-y-4">
          <div className="rounded-lg bg-amber-950/40 border border-amber-800/60 p-3.5 text-xs text-amber-300 space-y-1">
            <p className="font-semibold flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-amber-400" /> Asynchronous Batch Execution
            </p>
            <p>
              Submitting this form will snapshot all active subscribers in the contact list, transition the campaign to QUEUED, and dispatch the background Celery task.
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
    </div>
  );
};
