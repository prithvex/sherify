import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Send,
  Plus,
  Search,
  Trash2,
  ArrowRight,
  BarChart3,
  Calendar,
} from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Pagination } from '../../components/common/Pagination';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { Alert } from '../../components/common/Alert';
import { ApiError, CampaignStatus, EmailCampaign } from '../../types';

const STATUS_TABS: { label: string; value: CampaignStatus | '' }[] = [
  { label: 'All', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Ready', value: 'ready' },
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Queued', value: 'queued' },
  { label: 'Sending', value: 'sending' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'Failed', value: 'failed' },
];

export const CampaignsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<CampaignStatus | ''>('');
  const [deleteTarget, setDeleteTarget] = useState<EmailCampaign | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['campaigns', { page, search, status: selectedStatus }],
    queryFn: () =>
      campaignsApi.list({
        page,
        page_size: 10,
        search: search.trim() || undefined,
        status: selectedStatus || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: campaignsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setDeleteTarget(null);
      setDeleteError(null);
    },
    onError: (err: ApiError) => {
      setDeleteError(err.message || 'Failed to delete campaign.');
    },
  });

  const handleDelete = () => {
    if (deleteTarget) {
      deleteMutation.mutate(deleteTarget.id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">Campaigns</h2>
          <p className="text-xs text-slate-400 mt-1">
            Design, schedule, and dispatch bulk email campaigns to targeted contact lists
          </p>
        </div>
        <Link to="/campaigns/new">
          <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
            Create Campaign
          </Button>
        </Link>
      </div>

      {deleteError && <Alert type="error" message={deleteError} title="Action Failed" />}

      {/* Search & Status Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="w-full max-w-sm">
          <Input
            placeholder="Search campaigns by name or subject..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>

        {/* Status Filter Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => {
                setSelectedStatus(tab.value);
                setPage(1);
              }}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors whitespace-nowrap ${
                selectedStatus === tab.value
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Campaigns Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : data?.items.length === 0 ? (
          <EmptyState
            icon={<Send className="w-6 h-6" />}
            title="No campaigns found"
            description={
              search || selectedStatus
                ? 'No campaigns match your current filters.'
                : "You haven't created any campaigns yet. Build your first campaign to begin dispatching bulk emails."
            }
            actionLabel="Create Campaign"
            onAction={() => (window.location.href = '/campaigns/new')}
          />
        ) : (
          <div className="divide-y divide-slate-800/80 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400">
                  <th className="pb-3 font-semibold">Campaign Name</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Schedule / Timing</th>
                  <th className="pb-3 font-semibold">Date Created</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data?.items.map((camp) => (
                  <tr key={camp.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 pr-4">
                      <div className="space-y-0.5">
                        <Link
                          to={`/campaigns/${camp.id}`}
                          className="font-semibold text-slate-200 hover:text-indigo-400 transition-colors"
                        >
                          {camp.name}
                        </Link>
                        <p className="text-slate-500 text-[11px] truncate max-w-xs">{camp.subject}</p>
                      </div>
                    </td>
                    <td className="py-3.5 pr-4">
                      <Badge variant={camp.status}>{camp.status}</Badge>
                    </td>
                    <td className="py-3.5 pr-4 text-slate-400 whitespace-nowrap">
                      {camp.status === 'scheduled' && camp.scheduled_at ? (
                        <div className="flex items-center gap-1.5 text-cyan-400">
                          <Calendar className="w-3.5 h-3.5" />
                          <span className="text-[11px]">{new Date(camp.scheduled_at).toLocaleDateString()}</span>
                        </div>
                      ) : (
                        <span className="text-slate-600 italic">Immediate</span>
                      )}
                    </td>
                    <td className="py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(camp.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <Link to={`/campaigns/${camp.id}`}>
                          <Button variant="outline" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                            Details
                          </Button>
                        </Link>
                        {(camp.status === 'completed' || camp.status === 'sending' || camp.status === 'queued') && (
                          <Link to={`/campaigns/${camp.id}/analytics`}>
                            <Button variant="secondary" size="sm" leftIcon={<BarChart3 className="w-3.5 h-3.5" />}>
                              Stats
                            </Button>
                          </Link>
                        )}
                        {camp.status === 'draft' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setDeleteError(null);
                              setDeleteTarget(camp);
                            }}
                            className="text-red-400 hover:text-red-300 hover:bg-red-950/40"
                            aria-label="Delete draft campaign"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data && (
              <Pagination
                currentPage={data.page}
                totalPages={data.pages}
                totalItems={data.total}
                pageSize={data.page_size}
                onPageChange={setPage}
                isLoading={isLoading}
              />
            )}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal for Drafts */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Campaign"
        description={`Are you sure you want to delete "${deleteTarget?.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            This will permanently remove this draft campaign. This action cannot be undone.
          </p>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleDelete}
              isLoading={deleteMutation.isPending}
            >
              Confirm Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
