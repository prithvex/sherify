import React from 'react';
import { AlertCircle, CheckCircle2, Info, XCircle } from 'lucide-react';

interface AlertProps {
  type?: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  message: string;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  message,
  className = '',
}) => {
  const config = {
    success: {
      bg: 'bg-emerald-950/50 border-emerald-800/80 text-emerald-300',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />,
    },
    error: {
      bg: 'bg-rose-950/50 border-rose-800/80 text-rose-300',
      icon: <XCircle className="w-4 h-4 text-rose-400 shrink-0" />,
    },
    warning: {
      bg: 'bg-amber-950/50 border-amber-800/80 text-amber-300',
      icon: <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />,
    },
    info: {
      bg: 'bg-indigo-950/50 border-indigo-800/80 text-indigo-300',
      icon: <Info className="w-4 h-4 text-indigo-400 shrink-0" />,
    },
  };

  const current = config[type];

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border p-3.5 text-xs ${current.bg} ${className}`}
      role="alert"
    >
      {current.icon}
      <div className="space-y-0.5">
        {title && <h4 className="font-semibold text-slate-100">{title}</h4>}
        <p className="leading-relaxed">{message}</p>
      </div>
    </div>
  );
};
