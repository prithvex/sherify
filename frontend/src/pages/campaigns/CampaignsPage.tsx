import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Send, Plus, Search, Trash2, ArrowRight, BarChart3 } from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Pagination } from '../../components/common/Pagination';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { Alert } from '../../components/common/Alert';
import { ApiError, EmailCampaign } from '../../types';

export const CampaignsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<EmailCampaign | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['campaigns', { page, search, status: statusFilter }],
    queryFn: () =>
      campaignsApi.list({
        page,
        page_size: 10,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
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
            Create, validate, dispatch, and track your mass email broadcasts
          </p>
        </div>
        <Link to="/campaigns/new">
          <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
            Create Campaign
          </Button>
        </Link>
      </div>

      {deleteError && <Alert type="error" message={deleteError} title="Delete Failed" />}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="w-full sm:max-w-sm">
          <Input
            placeholder="Search campaigns..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            options={[
              { value: '', label: 'All Statuses' },
              { value: 'draft', label: 'Draft' },
              { value: 'ready', label: 'Ready' },
              { value: 'queued', label: 'Queued' },
              { value: 'sending', label: 'Sending' },
              { value: 'completed', label: 'Completed' },
              { value: 'failed', label: 'Failed' },
            ]}
          />
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
              search || statusFilter
                ? 'No campaigns matching your filter criteria.'
                : "You haven't created any campaigns yet. Start by defining a new campaign."
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
                  <th className="pb-3 font-semibold">Subject</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Created</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data?.items.map((camp) => (
                  <tr key={camp.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 pr-4 font-semibold text-slate-200">
                      <Link to={`/campaigns/${camp.id}`} className="hover:text-indigo-400">
                        {camp.name}
                      </Link>
                    </td>
                    <td className="py-3.5 pr-4 text-slate-400 max-w-xs truncate">{camp.subject}</td>
                    <td className="py-3.5 pr-4">
                      <Badge variant={camp.status}>{camp.status}</Badge>
                    </td>
                    <td className="py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(camp.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <Link to={`/campaigns/${camp.id}`}>
                          <Button variant="outline" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                            Manage
                          </Button>
                        </Link>
                        {(camp.status === 'completed' || camp.status === 'sending' || camp.status === 'queued') && (
                          <Link to={`/campaigns/${camp.id}/analytics`}>
                            <Button variant="secondary" size="sm" leftIcon={<BarChart3 className="w-3.5 h-3.5" />}>
                              Stats
                            </Button>
                          </Link>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDeleteError(null);
                            setDeleteTarget(camp);
                          }}
                          className="text-red-400 hover:text-red-300 hover:bg-red-950/40"
                          aria-label="Delete campaign"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
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

      {/* Delete Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Campaign"
        description={`Are you sure you want to delete "${deleteTarget?.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            This will permanently remove the campaign and any associated execution records.
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
