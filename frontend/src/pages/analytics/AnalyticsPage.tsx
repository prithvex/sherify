import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { BarChart3, Info } from 'lucide-react';
import { campaignsApi } from '../../api/campaigns';
import { Button } from '../../components/common/Button';
import { Badge } from '../../components/common/Badge';
import { Skeleton } from '../../components/common/Skeleton';
import { EmptyState } from '../../components/common/EmptyState';
import { Pagination } from '../../components/common/Pagination';

export const AnalyticsPage: React.FC = () => {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['campaigns-analytics-list', { page }],
    queryFn: () => campaignsApi.list({ page, page_size: 10 }),
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">Campaign Analytics</h2>
        <p className="text-xs text-slate-400 mt-1">
          Select a campaign to inspect granular delivery funnels, tracking pixels, and bounce metrics
        </p>
      </div>

      {/* Info Alert on Architecture */}
      <div className="rounded-xl border border-indigo-900/60 bg-indigo-950/40 p-4 text-xs text-indigo-300 flex items-start gap-3">
        <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-indigo-200">Per-Campaign Analytics (V5 Architecture)</p>
          <p className="text-indigo-300/90 leading-relaxed">
            The backend calculates engagement and delivery rates dynamically for each campaign using PostgreSQL SQL conditional aggregations. Select any completed or in-flight campaign below to view its statistics dashboard.
          </p>
        </div>
      </div>

      {/* Campaign List */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : data?.items.length === 0 ? (
          <EmptyState
            icon={<BarChart3 className="w-6 h-6" />}
            title="No campaigns available"
            description="You haven't launched any campaigns yet. Create and dispatch a campaign to view live delivery and open analytics."
            actionLabel="Create Campaign"
            onAction={() => (window.location.href = '/campaigns/new')}
          />
        ) : (
          <div className="divide-y divide-slate-800/80 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400">
                  <th className="pb-3 font-semibold">Campaign</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Date Created</th>
                  <th className="pb-3 font-semibold text-right">Analytics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {data?.items.map((camp) => (
                  <tr key={camp.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 pr-4">
                      <p className="font-semibold text-slate-200">{camp.name}</p>
                      <p className="text-slate-500 text-[11px] truncate max-w-xs">{camp.subject}</p>
                    </td>
                    <td className="py-3.5 pr-4">
                      <Badge variant={camp.status}>{camp.status}</Badge>
                    </td>
                    <td className="py-3.5 text-slate-400 whitespace-nowrap">
                      {new Date(camp.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 text-right whitespace-nowrap">
                      <Link to={`/campaigns/${camp.id}/analytics`}>
                        <Button
                          variant="primary"
                          size="sm"
                          leftIcon={<BarChart3 className="w-3.5 h-3.5" />}
                        >
                          View Stats
                        </Button>
                      </Link>
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
    </div>
  );
};
