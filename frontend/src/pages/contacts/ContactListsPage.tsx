import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Users, Plus, Search, Trash2, ArrowRight, FolderOpen } from 'lucide-react';
import { contactListsApi } from '../../api/contactLists';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Modal } from '../../components/common/Modal';
import { Pagination } from '../../components/common/Pagination';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { Alert } from '../../components/common/Alert';
import { ApiError, ContactList } from '../../types';

export const ContactListsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ContactList | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['contact-lists', { page, search }],
    queryFn: () => contactListsApi.list({ page, page_size: 10, search: search.trim() || undefined }),
  });

  const createMutation = useMutation({
    mutationFn: contactListsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contact-lists'] });
      setIsCreateModalOpen(false);
      setName('');
      setDescription('');
      setFormError(null);
    },
    onError: (err: ApiError) => {
      setFormError(err.message || 'Failed to create contact list');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: contactListsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contact-lists'] });
      setDeleteTarget(null);
      setDeleteError(null);
    },
    onError: (err: ApiError) => {
      setDeleteError(err.message || 'Cannot delete contact list. It may be referenced by an active campaign.');
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError('Contact list name is required.');
      return;
    }
    createMutation.mutate({ name: name.trim(), description: description.trim() || null });
  };

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
          <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">Contact Lists</h2>
          <p className="text-xs text-slate-400 mt-1">
            Organize your audiences, manage subscribers, and run bulk CSV imports
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => setIsCreateModalOpen(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Create Contact List
        </Button>
      </div>

      {/* Global Delete Error if any */}
      {deleteError && (
        <Alert type="error" message={deleteError} title="Delete Failed" />
      )}

      {/* Search & Filter Bar */}
      <div className="flex items-center gap-3">
        <div className="w-full max-w-sm">
          <Input
            placeholder="Search contact lists..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            leftIcon={<Search className="w-4 h-4" />}
          />
        </div>
      </div>

      {/* Contact Lists Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : data?.items.length === 0 ? (
          <EmptyState
            icon={<Users className="w-6 h-6" />}
            title="No contact lists found"
            description={search ? `No contact lists matching "${search}".` : "You haven't created any contact lists yet."}
            actionLabel="Create Contact List"
            onAction={() => setIsCreateModalOpen(true)}
          />
        ) : (
          <div className="divide-y divide-slate-800/80 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400">
                  <th className="pb-3 font-semibold">List Name</th>
                  <th className="pb-3 font-semibold">Description</th>
                  <th className="pb-3 font-semibold">Created At</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data?.items.map((list) => (
                  <tr key={list.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 pr-4">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          <FolderOpen className="w-3.5 h-3.5" />
                        </div>
                        <Link
                          to={`/contacts/${list.id}`}
                          className="font-semibold text-slate-200 hover:text-indigo-400 transition-colors"
                        >
                          {list.name}
                        </Link>
                      </div>
                    </td>
                    <td className="py-3.5 pr-4 text-slate-400 max-w-xs truncate">
                      {list.description || <span className="text-slate-600 italic">No description</span>}
                    </td>
                    <td className="py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(list.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <Link to={`/contacts/${list.id}`}>
                          <Button variant="outline" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                            Manage
                          </Button>
                        </Link>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDeleteError(null);
                            setDeleteTarget(list);
                          }}
                          className="text-red-400 hover:text-red-300 hover:bg-red-950/40"
                          aria-label="Delete contact list"
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

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setFormError(null);
        }}
        title="Create Contact List"
        description="Set up a new audience group for subscriber management and campaign targeting."
      >
        <form onSubmit={handleCreate} className="space-y-4">
          {formError && <Alert type="error" message={formError} />}

          <Input
            label="List Name"
            placeholder="e.g. Early Adopters, Newsletter"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoFocus
          />

          <Input
            label="Description (Optional)"
            placeholder="Brief notes about this audience segment"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createMutation.isPending}
            >
              Create List
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Contact List"
        description={`Are you sure you want to delete "${deleteTarget?.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-400">
            This will permanently remove the contact list and all associated subscribers.
            This action cannot be undone. If a campaign is currently referencing this list, deletion will be rejected.
          </p>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteTarget(null)}
            >
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
