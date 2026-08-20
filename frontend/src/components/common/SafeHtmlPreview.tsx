import React from 'react';

interface SafeHtmlPreviewProps {
  htmlContent: string;
  className?: string;
  title?: string;
}

export const SafeHtmlPreview: React.FC<SafeHtmlPreviewProps> = ({
  htmlContent,
  className = 'h-96 w-full',
  title = 'Email Template Preview',
}) => {
  // Wrap basic styling inside iframe content if needed
  const styledHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            background: #ffffff;
            margin: 0;
            padding: 16px;
            box-sizing: border-box;
          }
        </style>
      </head>
      <body>
        ${htmlContent || '<p style="color: #94a3b8; font-style: italic;">No HTML content provided.</p>'}
      </body>
    </html>
  `;

  return (
    <div className="relative rounded-lg border border-slate-700 bg-white overflow-hidden shadow-inner">
      <iframe
        title={title}
        srcDoc={styledHtml}
        sandbox=""
        className={`w-full border-0 bg-white ${className}`}
      />
    </div>
  );
};
