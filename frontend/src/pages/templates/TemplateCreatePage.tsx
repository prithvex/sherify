import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Eye, Code } from 'lucide-react';
import { templatesApi } from '../../api/templates';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Alert } from '../../components/common/Alert';
import { SafeHtmlPreview } from '../../components/common/SafeHtmlPreview';
import { ApiError } from '../../types';

export const TemplateCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [htmlContent, setHtmlContent] = useState(
    `<div style="max-width: 600px; margin: 0 auto; font-family: sans-serif; padding: 20px;">\n  <h1 style="color: #4f46e5;">Welcome to Sherify!</h1>\n  <p>Thank you for subscribing to our updates.</p>\n  <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;" />\n  <p style="font-size: 12px; color: #64748b;">You received this email because you are on our audience list.</p>\n</div>`
  );
  const [textContent, setTextContent] = useState(
    'Welcome to Sherify!\nThank you for subscribing to our updates.'
  );
  const [activeTab, setActiveTab] = useState<'editor' | 'preview'>('editor');
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: templatesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      navigate('/templates');
    },
    onError: (err: ApiError) => {
      setError(err.message || 'Failed to create template.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim() || !subject.trim()) {
      setError('Template name and subject line are required.');
      return;
    }

    createMutation.mutate({
      name: name.trim(),
      subject: subject.trim(),
      html_content: htmlContent || null,
      text_content: textContent || null,
    });
  };

  return (
    <div className="space-y-6">
      {/* Back button & Header */}
      <div>
        <Link
          to="/templates"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Templates
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
              Create Email Template
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Author HTML and plain text content for your campaign broadcasts
            </p>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleSubmit}
            isLoading={createMutation.isPending}
            leftIcon={<Save className="w-4 h-4" />}
          >
            Save Template
          </Button>
        </div>
      </div>

      {error && <Alert type="error" message={error} />}

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Form & Editors */}
        <div className="space-y-5 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur">
          <Input
            label="Template Name"
            placeholder="e.g. Welcome Series - Day 1"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            autoFocus
          />

          <Input
            label="Default Subject Line"
            placeholder="e.g. Welcome to our community!"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
          />

          {/* HTML Editor */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                HTML Content
              </label>
              <div className="flex items-center gap-1 bg-slate-950 rounded-lg p-1 border border-slate-800 lg:hidden">
                <button
                  type="button"
                  onClick={() => setActiveTab('editor')}
                  className={`px-2 py-0.5 text-xs rounded font-medium ${
                    activeTab === 'editor' ? 'bg-indigo-600 text-white' : 'text-slate-400'
                  }`}
                >
                  <Code className="w-3 h-3 inline mr-1" /> Code
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('preview')}
                  className={`px-2 py-0.5 text-xs rounded font-medium ${
                    activeTab === 'preview' ? 'bg-indigo-600 text-white' : 'text-slate-400'
                  }`}
                >
                  <Eye className="w-3 h-3 inline mr-1" /> Preview
                </button>
              </div>
            </div>
            <textarea
              className="w-full rounded-lg border border-slate-700/80 bg-slate-950 p-3 font-mono text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900"
              rows={12}
              value={htmlContent}
              onChange={(e) => setHtmlContent(e.target.value)}
            />
          </div>

          {/* Text Content */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
              Plain Text Version (Fallback)
            </label>
            <textarea
              className="w-full rounded-lg border border-slate-700/80 bg-slate-950 p-3 font-mono text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900"
              rows={4}
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
            />
          </div>
        </div>

        {/* Right Column: Live Sandboxed Preview */}
        <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <Eye className="w-4 h-4 text-indigo-400" />
              <span>Live Sandboxed Preview</span>
            </div>
            <span className="text-[11px] text-slate-500">Subject: {subject || 'None'}</span>
          </div>

          <div className="flex-1 min-h-[400px] mt-2">
            <SafeHtmlPreview htmlContent={htmlContent} className="h-full min-h-[420px]" />
          </div>
        </div>
      </form>
    </div>
  );
};
