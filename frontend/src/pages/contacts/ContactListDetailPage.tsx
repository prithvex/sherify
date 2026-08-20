import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  UserPlus,
  Upload,
  Search,
  Trash2,
  AlertCircle,
  FileSpreadsheet,
  CheckCircle2,
  Clock,
  FileWarning,
} from 'lucide-react';
import { contactListsApi } from '../../api/contactLists';
import { subscribersApi } from '../../api/subscribers';
import { importsApi } from '../../api/imports';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Pagination } from '../../components/common/Pagination';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { Alert } from '../../components/common/Alert';
import { ApiError, ImportJob, Subscriber } from '../../types';

export const ContactListDetailPage: React.FC = () => {
  const { id: listId = '' } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  // Search & Filter
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Subscriber | null>(null);

  // Add Subscriber Form
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [metadataStr, setMetadataStr] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  // CSV Import state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeImportId, setActiveImportId] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [isViewingErrors, setIsViewingErrors] = useState(false);
  const [errorPage, setErrorPage] = useState(1);

  // Contact list query
  const { data: list, isLoading: loadingList } = useQuery({
    queryKey: ['contact-list', listId],
    queryFn: () => contactListsApi.getById(listId),
    enabled: !!listId,
  });

  // Subscribers query
  const { data: subscribersData, isLoading: loadingSubscribers } = useQuery({
    queryKey: ['subscribers', listId, { page, search, status: statusFilter }],
    queryFn: () =>
      subscribersApi.list(listId, {
        page,
        page_size: 10,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
      }),
    enabled: !!listId,
  });

  // Active Import Job Poller
  const { data: activeJob } = useQuery({
    queryKey: ['import-job', activeImportId],
    queryFn: () => importsApi.getJob(activeImportId!),
    enabled: !!activeImportId,
    refetchInterval: (query) => {
      const data = query.state.data as ImportJob | undefined;
      if (data && (data.status === 'completed' || data.status === 'failed')) {
        return false;
      }
      return 1500;
    },
  });

  // Re-fetch subscribers when import finishes
  useEffect(() => {
    if (activeJob?.status === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['subscribers', listId] });
    }
  }, [activeJob?.status, listId, queryClient]);

  // Import Errors query
  const { data: importErrorsData, isLoading: loadingErrors } = useQuery({
    queryKey: ['import-errors', activeImportId, errorPage],
    queryFn: () => importsApi.getJobErrors(activeImportId!, { page: errorPage, page_size: 10 }),
    enabled: !!activeImportId && isViewingErrors,
  });

  // Add Subscriber mutation
  const addMutation = useMutation({
    mutationFn: (data: { email: string; first_name?: string; last_name?: string; metadata?: any }) =>
      subscribersApi.create(listId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscribers', listId] });
      setIsAddModalOpen(false);
      setEmail('');
      setFirstName('');
      setLastName('');
      setMetadataStr('');
      setFormError(null);
    },
    onError: (err: ApiError) => {
      setFormError(err.message || 'Failed to add subscriber.');
    },
  });

  // Delete Subscriber mutation
  const deleteMutation = useMutation({
    mutationFn: (subId: string) => subscribersApi.delete(listId, subId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscribers', listId] });
      setDeleteTarget(null);
    },
  });

  // CSV Import mutation
  const importMutation = useMutation({
    mutationFn: (file: File) => subscribersApi.importCsv(listId, file),
    onSuccess: (data) => {
      setActiveImportId(data.import_id);
      setSelectedFile(null);
      setImportError(null);
    },
    onError: (err: ApiError) => {
      setImportError(err.message || 'CSV upload failed.');
    },
  });

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    let parsedMeta: Record<string, any> = {};
    if (metadataStr.trim()) {
      try {
        parsedMeta = JSON.parse(metadataStr);
      } catch {
        setFormError('Invalid JSON format for metadata.');
        return;
      }
    }

    addMutation.mutate({
      email: email.trim(),
      first_name: firstName.trim() || undefined,
      last_name: lastName.trim() || undefined,
      metadata: Object.keys(parsedMeta).length > 0 ? parsedMeta : undefined,
    });
  };

  const handleUploadCsv = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setImportError('Please select a valid .csv file.');
      return;
    }
    importMutation.mutate(selectedFile);
  };

  return (
    <div className="space-y-6">
      {/* Back Link & Header */}
      <div>
        <Link
          to="/contacts"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Contact Lists
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            {loadingList ? (
              <Skeleton className="h-8 w-48 mb-2" />
            ) : (
              <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
                {list?.name}
              </h2>
            )}
            <p className="text-xs text-slate-400 mt-1">
              {list?.description || 'Audience subscriber list'}
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setImportError(null);
                setIsImportModalOpen(true);
              }}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              Import CSV
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setFormError(null);
                setIsAddModalOpen(true);
              }}
              leftIcon={<UserPlus className="w-4 h-4" />}
            >
              Add Subscriber
            </Button>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="w-full sm:max-w-sm">
          <Input
            placeholder="Search by email, name..."
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
              { value: 'active', label: 'Active' },
              { value: 'unsubscribed', label: 'Unsubscribed' },
              { value: 'bounced', label: 'Bounced' },
            ]}
          />
        </div>
      </div>

      {/* Subscribers Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
        {loadingSubscribers ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : subscribersData?.items.length === 0 ? (
          <EmptyState
            icon={<UserPlus className="w-6 h-6" />}
            title="No subscribers found"
            description={
              search || statusFilter
                ? 'No subscribers matching your filters.'
                : 'This contact list currently has no subscribers. Add individuals or import a CSV file.'
            }
            actionLabel="Add Subscriber"
            onAction={() => setIsAddModalOpen(true)}
          />
        ) : (
          <div className="divide-y divide-slate-800/80 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400">
                  <th className="pb-3 font-semibold">Email</th>
                  <th className="pb-3 font-semibold">Name</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Metadata</th>
                  <th className="pb-3 font-semibold">Added</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {subscribersData?.items.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 pr-4 font-semibold text-slate-200">{sub.email}</td>
                    <td className="py-3.5 pr-4 text-slate-300">
                      {sub.first_name || sub.last_name
                        ? `${sub.first_name || ''} ${sub.last_name || ''}`.trim()
                        : <span className="text-slate-600 italic">None</span>}
                    </td>
                    <td className="py-3.5 pr-4">
                      <Badge variant={sub.status}>{sub.status}</Badge>
                    </td>
                    <td className="py-3.5 pr-4 text-slate-400 font-mono text-[11px]">
                      {Object.keys(sub.metadata_json || {}).length > 0 ? (
                        <span className="truncate max-w-xs block">
                          {JSON.stringify(sub.metadata_json)}
                        </span>
                      ) : (
                        <span className="text-slate-600 italic">{}</span>
                      )}
                    </td>
                    <td className="py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(sub.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTarget(sub)}
                        className="text-red-400 hover:text-red-300 hover:bg-red-950/40"
                        aria-label="Delete subscriber"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {subscribersData && (
              <Pagination
                currentPage={subscribersData.page}
                totalPages={subscribersData.pages}
                totalItems={subscribersData.total}
                pageSize={subscribersData.page_size}
                onPageChange={setPage}
                isLoading={loadingSubscribers}
              />
            )}
          </div>
        )}
      </div>

      {/* Add Subscriber Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => {
          setIsAddModalOpen(false);
          setFormError(null);
        }}
        title="Add New Subscriber"
        description="Insert an individual recipient into this contact list."
      >
        <form onSubmit={handleAddSubmit} className="space-y-4">
          {formError && <Alert type="error" message={formError} />}

          <Input
            label="Email Address"
            type="email"
            placeholder="subscriber@domain.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name"
              placeholder="Jane"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
            <Input
              label="Last Name"
              placeholder="Doe"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Metadata (JSON Optional)
            </label>
            <textarea
              className="w-full rounded-lg border border-slate-700/80 bg-slate-900/90 p-2.5 font-mono text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900"
              rows={3}
              placeholder='{"company": "Acme Corp", "tier": "Enterprise"}'
              value={metadataStr}
              onChange={(e) => setMetadataStr(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={addMutation.isPending}
            >
              Add Subscriber
            </Button>
          </div>
        </form>
      </Modal>

      {/* CSV Bulk Import Modal */}
      <Modal
        isOpen={isImportModalOpen}
        onClose={() => {
          setIsImportModalOpen(false);
          setActiveImportId(null);
          setSelectedFile(null);
          setImportError(null);
          setIsViewingErrors(false);
        }}
        title="Bulk CSV Subscriber Import"
        description="Upload a CSV file containing subscriber emails for streaming background ingestion."
        maxWidth="lg"
      >
        <div className="space-y-5">
          {importError && <Alert type="error" message={importError} />}

          {!activeImportId ? (
            <form onSubmit={handleUploadCsv} className="space-y-4">
              <div className="rounded-xl border-2 border-dashed border-slate-700 bg-slate-900/40 p-6 text-center hover:border-indigo-500 transition-colors">
                <FileSpreadsheet className="mx-auto h-8 w-8 text-indigo-400 mb-2" />
                <label className="block text-xs font-medium text-slate-200 cursor-pointer">
                  <span>Choose a CSV file</span>
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    className="sr-only"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                        setImportError(null);
                      }
                    }}
                  />
                </label>
                <p className="mt-1 text-[11px] text-slate-500">
                  {selectedFile ? selectedFile.name : 'CSV format with email header'}
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsImportModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={importMutation.isPending}
                  disabled={!selectedFile}
                >
                  Start Import
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              {/* Polling Live Progress Card */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {activeJob?.status === 'completed' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : activeJob?.status === 'failed' ? (
                      <AlertCircle className="w-5 h-5 text-rose-400" />
                    ) : (
                      <Clock className="w-5 h-5 text-indigo-400 animate-spin" />
                    )}
                    <div>
                      <h4 className="text-xs font-semibold text-slate-100">
                        Import Status: <Badge variant={activeJob?.status || 'queued'}>{activeJob?.status || 'queued'}</Badge>
                      </h4>
                      <p className="text-[11px] text-slate-400">{activeJob?.original_filename}</p>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-center text-xs">
                  <div className="rounded bg-slate-950 p-2 border border-slate-800">
                    <span className="block font-bold text-emerald-400 text-sm">
                      {activeJob?.imported_rows ?? 0}
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider">Imported</span>
                  </div>
                  <div className="rounded bg-slate-950 p-2 border border-slate-800">
                    <span className="block font-bold text-amber-400 text-sm">
                      {activeJob?.duplicate_rows ?? 0}
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider">Duplicates</span>
                  </div>
                  <div className="rounded bg-slate-950 p-2 border border-slate-800">
                    <span className="block font-bold text-rose-400 text-sm">
                      {activeJob?.invalid_rows ?? 0}
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider">Invalid</span>
                  </div>
                </div>
              </div>

              {/* View Errors Button if errors exist */}
              {activeJob && (activeJob.error_count ?? 0) > 0 && (
                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-rose-300 border-rose-900/60 hover:bg-rose-950/40"
                    leftIcon={<FileWarning className="w-3.5 h-3.5" />}
                    onClick={() => setIsViewingErrors(!isViewingErrors)}
                  >
                    {isViewingErrors ? 'Hide Error Details' : `View ${activeJob.error_count ?? 0} Row Errors`}
                  </Button>

                  {/* Errors Table */}
                  {isViewingErrors && (
                    <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs">
                      {loadingErrors ? (
                        <Skeleton className="h-16 w-full" />
                      ) : (
                        <div>
                          <table className="w-full text-left">
                            <thead>
                              <tr className="text-slate-400 border-b border-slate-800">
                                <th className="pb-2 font-semibold">Row</th>
                                <th className="pb-2 font-semibold">Type</th>
                                <th className="pb-2 font-semibold">Message</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60">
                              {importErrorsData?.items.map((err) => (
                                <tr key={err.id}>
                                  <td className="py-2 pr-2 text-slate-300 font-mono">#{err.row_number}</td>
                                  <td className="py-2 pr-2 text-rose-400 font-semibold">{err.error_type}</td>
                                  <td className="py-2 text-slate-400">{err.message}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>

                          {importErrorsData && (
                            <Pagination
                              currentPage={importErrorsData.page}
                              totalPages={importErrorsData.pages}
                              totalItems={importErrorsData.total}
                              pageSize={importErrorsData.page_size}
                              onPageChange={setErrorPage}
                            />
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              <div className="flex items-center justify-end pt-4 border-t border-slate-800">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setIsImportModalOpen(false);
                    setActiveImportId(null);
                    setSelectedFile(null);
                  }}
                >
                  Done
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>

      {/* Delete Subscriber Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Remove Subscriber"
        description={`Remove "${deleteTarget?.email}" from this list?`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            This subscriber will be removed from this contact list.
          </p>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
              isLoading={deleteMutation.isPending}
            >
              Confirm Remove
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
