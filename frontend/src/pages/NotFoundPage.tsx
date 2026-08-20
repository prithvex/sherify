import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-950 px-4 text-center text-slate-100">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-4">
        <Sparkles className="h-6 w-6" />
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl font-mono">404</h1>
      <h2 className="mt-2 text-lg font-semibold text-slate-300">Page Not Found</h2>
      <p className="mt-1 text-xs text-slate-500 max-w-sm">
        The requested dashboard route does not exist or has been moved.
      </p>
      <div className="mt-6">
        <Link to="/dashboard">
          <Button variant="primary" size="sm" leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}>
            Return to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};
