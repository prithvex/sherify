import React from 'react';

export type BadgeVariant =
  | 'draft'
  | 'ready'
  | 'queued'
  | 'sending'
  | 'completed'
  | 'failed'
  | 'bounced'
  | 'active'
  | 'unsubscribed'
  | 'processing'
  | 'default';

interface BadgeProps {
  variant?: BadgeVariant | string;
  children: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  children,
  className = '',
  size = 'sm',
}) => {
  const getStyles = (v: string) => {
    switch (v.toLowerCase()) {
      case 'draft':
        return 'bg-slate-800 text-slate-300 border-slate-700';
      case 'ready':
        return 'bg-blue-950/80 text-blue-300 border-blue-800/60';
      case 'queued':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/60';
      case 'sending':
      case 'processing':
        return 'bg-purple-950/80 text-purple-300 border-purple-800/60 animate-pulse';
      case 'completed':
      case 'active':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/60';
      case 'failed':
      case 'bounced':
        return 'bg-rose-950/80 text-rose-300 border-rose-800/60';
      case 'unsubscribed':
        return 'bg-slate-800 text-slate-400 border-slate-700';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium uppercase tracking-wider ${getStyles(
        variant
      )} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
};
