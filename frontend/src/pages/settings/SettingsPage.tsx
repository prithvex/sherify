import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { User as UserIcon, Server, HardDrive } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { healthApi } from '../../api/health';
import { Badge } from '../../components/common/Badge';
import { Skeleton } from '../../components/common/Skeleton';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  const { data: health, isLoading: loadingHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.check,
    refetchInterval: 10000,
  });

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Top Header */}
      <div className="border-b border-slate-800 pb-5">
        <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">Settings & Profile</h2>
        <p className="text-xs text-slate-400 mt-1">
          Account details, authentication status, and backend connectivity diagnostics
        </p>
      </div>

      {/* User Profile Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-5">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <UserIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Authenticated Profile</h3>
            <p className="text-xs text-slate-400">Your registered account credentials</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
              Account Email
            </span>
            <p className="font-semibold text-slate-200">{user?.email}</p>
          </div>

          <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
              Account Status
            </span>
            <div>
              <Badge variant={user?.is_active ? 'active' : 'failed'}>
                {user?.is_active ? 'Active User' : 'Inactive'}
              </Badge>
            </div>
          </div>

          <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
              User ID (UUID)
            </span>
            <p className="font-mono text-[11px] text-slate-400 truncate">{user?.id}</p>
          </div>

          <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
            <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
              Member Since
            </span>
            <p className="text-slate-300">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Backend Infrastructure Diagnostics Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-5">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">System Connectivity & Health</h3>
            <p className="text-xs text-slate-400">Live API and PostgreSQL database diagnostics</p>
          </div>
        </div>

        {loadingHealth ? (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
              <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                API Service
              </span>
              <div className="flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="font-semibold text-emerald-400 capitalize">{health?.status || 'Online'}</span>
              </div>
            </div>

            <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
              <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                Database (PostgreSQL)
              </span>
              <div className="flex items-center gap-2">
                <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-semibold text-slate-200 capitalize">{health?.database || 'Connected'}</span>
              </div>
            </div>

            <div className="rounded-lg bg-slate-950 p-3.5 border border-slate-800/80 space-y-1">
              <span className="text-slate-500 uppercase tracking-wider text-[10px] font-bold">
                App Version
              </span>
              <p className="font-mono font-semibold text-indigo-400">{health?.version || '0.1.0'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
