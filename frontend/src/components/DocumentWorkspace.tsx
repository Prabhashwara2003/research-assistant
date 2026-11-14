import { useState } from 'react';
import { FileText, RotateCcw } from 'lucide-react';
import type { DocumentResponse, ResearchSummary } from '../types/api';
import ChatPanel from './ChatPanel';
import DocumentSummary from './DocumentSummary';
import PdfViewer from './PdfViewer';

export default function DocumentWorkspace({ document, summary, onNewDocument }: { document: DocumentResponse; summary: ResearchSummary; onNewDocument: () => void }) {
  const [tab, setTab] = useState<'summary' | 'pdf'>('summary');
  const [page, setPage] = useState<number | null>(null);

  function showPage(nextPage: number) {
    setPage(nextPage);
    setTab('pdf');
  }

  return (
    <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4"><div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-widest text-sky-300">Research workspace</p><h1 className="mt-1 truncate text-xl font-semibold text-white sm:text-2xl">{document.filename}</h1><p className="mt-1 text-sm text-slate-300">Ready to explore</p></div><button type="button" onClick={onNewDocument} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"><RotateCcw size={16} /> Upload new PDF</button></div>
      <div className="grid gap-5 lg:grid-cols-2">
        <section aria-label="Document" className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:h-[calc(100vh-176px)] lg:min-h-[650px]">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-5 py-4"><div className="flex items-center gap-2 font-semibold text-slate-900"><FileText size={18} className="text-sky-700" /> Document</div><div role="tablist" aria-label="Document view" className="flex rounded-lg bg-slate-100 p-1"><button role="tab" aria-selected={tab === 'summary'} onClick={() => setTab('summary')} className={`rounded-md px-3 py-1.5 text-sm font-medium ${tab === 'summary' ? 'bg-white text-sky-800 shadow-sm' : 'text-slate-600'}`}>Summary</button><button role="tab" aria-selected={tab === 'pdf'} onClick={() => setTab('pdf')} className={`rounded-md px-3 py-1.5 text-sm font-medium ${tab === 'pdf' ? 'bg-white text-sky-800 shadow-sm' : 'text-slate-600'}`}>PDF</button></div></div>
          <div className="h-[calc(100%-69px)] overflow-y-auto">{tab === 'summary' ? <DocumentSummary summary={summary} /> : <PdfViewer documentId={document.id} page={page} />}</div>
        </section>
        <ChatPanel documentId={document.id} onPage={showPage} />
      </div>
    </main>
  );
}
