import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FileText, Plus, Search, Trash2, Edit, Eye } from 'lucide-react';
import { templatesApi } from '../../api/templates';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Modal } from '../../components/common/Modal';
import { Pagination } from '../../components/common/Pagination';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { Alert } from '../../components/common/Alert';
import { SafeHtmlPreview } from '../../components/common/SafeHtmlPreview';
import { ApiError, EmailTemplate } from '../../types';

export const TemplatesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<EmailTemplate | null>(null);
  const [previewTarget, setPreviewTarget] = useState<EmailTemplate | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['templates', { page, search }],
    queryFn: () => templatesApi.list({ page, page_size: 9, search: search.trim() || undefined }),
  });

  const deleteMutation = useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setDeleteTarget(null);
      setDeleteError(null);
    },
    onError: (err: ApiError) => {
      setDeleteError(
        err.message || 'Cannot delete template. It is currently referenced by an existing campaign.'
      );
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
          <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">Email Templates</h2>
          <p className="text-xs text-slate-400 mt-1">
            Design reusable HTML and plain text email templates for mass campaigns
          </p>
        </div>
        <Link to="/templates/new">
          <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
            Create Template
          </Button>
        </Link>
      </div>

      {/* Delete Error Alert */}
      {deleteError && <Alert type="error" message={deleteError} title="Delete Rejected" />}

      {/* Search Bar */}
      <div className="flex items-center gap-3">
        <div className="w-full max-w-sm">
          <Input
            placeholder="Search templates by name..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
      </div>

      {/* Templates Grid */}
      <div>
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Skeleton className="h-44 w-full" />
            <Skeleton className="h-44 w-full" />
            <Skeleton className="h-44 w-full" />
          </div>
        ) : data?.items.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
            <EmptyState
              icon={<FileText className="w-6 h-6" />}
              title="No templates found"
              description={
                search
                  ? `No templates matching "${search}".`
                  : "You haven't created any email templates yet. Create one to begin composing campaign emails."
              }
              actionLabel="Create Template"
              onAction={() => (window.location.href = '/templates/new')}
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data?.items.map((tpl) => (
                <div
                  key={tpl.id}
                  className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/70 p-5 hover:border-slate-700 transition-all shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-semibold text-slate-100 truncate text-sm">{tpl.name}</h3>
                      <button
                        onClick={() => setPreviewTarget(tpl)}
                        className="text-slate-400 hover:text-indigo-400 transition-colors p-1"
                        title="Preview HTML"
                        aria-label="Preview HTML"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">
                      <span className="text-slate-500 font-medium">Subject:</span> {tpl.subject}
                    </p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
                      <span>Created {new Date(tpl.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-4 mt-3 border-t border-slate-800/60">
                    <div className="flex items-center gap-1.5">
                      <Link to={`/templates/${tpl.id}/edit`}>
                        <Button variant="outline" size="sm" leftIcon={<Edit className="w-3.5 h-3.5" />}>
                          Edit
                        </Button>
                      </Link>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setDeleteError(null);
                        setDeleteTarget(tpl);
                      }}
                      className="text-red-400 hover:text-red-300 hover:bg-red-950/40"
                      aria-label="Delete template"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>

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

      {/* HTML Sandboxed Preview Modal */}
      <Modal
        isOpen={!!previewTarget}
        onClose={() => setPreviewTarget(null)}
        title={`Preview: ${previewTarget?.name}`}
        description={`Subject: ${previewTarget?.subject}`}
        maxWidth="2xl"
      >
        <div className="space-y-3">
          <SafeHtmlPreview htmlContent={previewTarget?.html_content || ''} />
          {previewTarget?.text_content && (
            <div className="mt-3 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                Plain Text Fallback
              </span>
              <p className="whitespace-pre-wrap">{previewTarget.text_content}</p>
            </div>
          )}
          <div className="flex justify-end pt-3 border-t border-slate-800">
            <Button variant="primary" size="sm" onClick={() => setPreviewTarget(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Template"
        description={`Are you sure you want to delete template "${deleteTarget?.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            This action cannot be undone. If any existing campaign references this template, deletion will be rejected to protect campaign referential integrity.
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
