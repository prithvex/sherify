import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, UserCheck, ChevronDown, ChevronUp } from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { contactListsApi } from '../../api/contactLists';
import { templatesApi } from '../../api/templates';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Select } from '../../components/common/Select';
import { Alert } from '../../components/common/Alert';
import { ApiError } from '../../types';

export const CampaignCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [templateId, setTemplateId] = useState('');
  const [contactListId, setContactListId] = useState('');

  // Optional Sender Identity Overrides
  const [showSenderOptions, setShowSenderOptions] = useState(false);
  const [fromName, setFromName] = useState('');
  const [fromEmail, setFromEmail] = useState('');
  const [replyTo, setReplyTo] = useState('');

  const [error, setError] = useState<string | null>(null);

  // Fetch available contact lists
  const { data: listsData, isLoading: loadingLists } = useQuery({
    queryKey: ['contact-lists', { page: 1, page_size: 100 }],
    queryFn: () => contactListsApi.list({ page: 1, page_size: 100 }),
  });

  // Fetch available templates
  const { data: templatesData, isLoading: loadingTemplates } = useQuery({
    queryKey: ['templates', { page: 1, page_size: 100 }],
    queryFn: () => templatesApi.list({ page: 1, page_size: 100 }),
  });

  const createMutation = useMutation({
    mutationFn: campaignsApi.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      navigate(`/campaigns/${data.id}`);
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to create campaign.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim() || !subject.trim() || !templateId || !contactListId) {
      setError('Please complete all required fields (Name, Subject, Template, and Contact List).');
      return;
    }

    createMutation.mutate({
      name: name.trim(),
      subject: subject.trim(),
      template_id: templateId,
      contact_list_id: contactListId,
      from_name: fromName.trim() || undefined,
      from_email: fromEmail.trim() || undefined,
      reply_to: replyTo.trim() || undefined,
    });
  };

  const listOptions = [
    { value: '', label: '-- Select a Contact List --' },
    ...(listsData?.items.map((l) => ({ value: l.id, label: l.name })) || []),
  ];

  const templateOptions = [
    { value: '', label: '-- Select an Email Template --' },
    ...(templatesData?.items.map((t) => ({ value: t.id, label: t.name })) || []),
  ];

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Back button & Header */}
      <div>
        <Link
          to="/campaigns"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Campaigns
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
              Create New Campaign
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Assemble campaign details, select target audience, choose email template, and set sender identity
            </p>
          </div>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}

      <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-6">
        <Input
          label="Campaign Name"
          placeholder="e.g. Q3 Product Announcement"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          autoFocus
        />

        <Input
          label="Campaign Subject"
          placeholder="e.g. Discover our newest feature updates"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <Select
              label="Target Contact List"
              value={contactListId}
              onChange={(e) => setContactListId(e.target.value)}
              options={listOptions}
              disabled={loadingLists}
              required
            />
            {listsData?.items.length === 0 && !loadingLists && (
              <p className="text-[11px] text-amber-400 mt-1.5">
                No contact lists found.{' '}
                <Link to="/contacts" className="underline font-semibold">
                  Create one first
                </Link>
              </p>
            )}
          </div>

          <div>
            <Select
              label="Email Template"
              value={templateId}
              onChange={(e) => {
                setTemplateId(e.target.value);
                const selectedTpl = templatesData?.items.find((t) => t.id === e.target.value);
                if (selectedTpl && !subject) {
                  setSubject(selectedTpl.subject);
                }
              }}
              options={templateOptions}
              disabled={loadingTemplates}
              required
            />
            {templatesData?.items.length === 0 && !loadingTemplates && (
              <p className="text-[11px] text-amber-400 mt-1.5">
                No templates found.{' '}
                <Link to="/templates/new" className="underline font-semibold">
                  Create one first
                </Link>
              </p>
            )}
          </div>
        </div>

        {/* Expandable Custom Sender Options */}
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-4">
          <button
            type="button"
            onClick={() => setShowSenderOptions(!showSenderOptions)}
            className="w-full flex items-center justify-between text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          >
            <span className="flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-emerald-400" />
              Custom Sender Identity (Optional Override)
            </span>
            {showSenderOptions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showSenderOptions && (
            <div className="pt-3 border-t border-slate-800/80 space-y-4 text-xs">
              <p className="text-[11px] text-slate-400">
                Leave blank to use system default sender (<code className="text-slate-300">campaigns@sherify.internal</code>).
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="From Name"
                  placeholder="e.g. Acme Marketing Team"
                  value={fromName}
                  onChange={(e) => setFromName(e.target.value)}
                />
                <Input
                  type="email"
                  label="From Email Address"
                  placeholder="e.g. news@yourcompany.com"
                  value={fromEmail}
                  onChange={(e) => setFromEmail(e.target.value)}
                />
              </div>
              <Input
                type="email"
                label="Reply-To Email Address"
                placeholder="e.g. support@yourcompany.com"
                value={replyTo}
                onChange={(e) => setReplyTo(e.target.value)}
              />
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-6 border-t border-slate-800">
          <Link to="/campaigns">
            <Button type="button" variant="outline" size="sm">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={createMutation.isPending}
            leftIcon={<Save className="w-4 h-4" />}
          >
            Create Draft Campaign
          </Button>
        </div>
      </form>
    </div>
  );
};
