import { useEffect, useState } from 'react';
import { BookOpen, LoaderCircle } from 'lucide-react';
import { ApiError, generateSummary, getDocument, getSummary, processDocument, uploadDocument } from './services/api';
import type { DocumentResponse, ResearchSummary } from './types/api';
import DocumentWorkspace from './components/DocumentWorkspace';
import FileUpload from './components/FileUpload';

const savedDocumentKey = 'research-assistant-document-id';
type Phase = 'idle' | 'restoring' | 'uploading' | 'processing' | 'summarizing' | 'ready';

export default function App() {
  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [summary, setSummary] = useState<ResearchSummary | null>(null);
  const [phase, setPhase] = useState<Phase>('restoring');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedId = localStorage.getItem(savedDocumentKey);
    if (!savedId) { setPhase('idle'); return; }
    let current = true;
    async function restore() {
      try {
        const restored = await getDocument(savedId!);
        if (!current) return;
        setDocument(restored);
        if (restored.status === 'failed') {
          setError('Processing failed for this PDF. You can retry processing.');
        } else if (restored.status === 'pending' || restored.status === 'processing') {
          setError('This paper has not finished processing. Check its status before continuing.');
        } else {
          try {
            const savedSummary = await getSummary(restored.id);
            if (current) { setSummary(savedSummary); setPhase('ready'); }
          } catch (reason) {
            if (current) setError(reason instanceof Error ? reason.message : 'Could not load the summary.');
          }
        }
      } catch (reason) {
        if (reason instanceof ApiError && reason.status === 404) {
          localStorage.removeItem(savedDocumentKey);
        } else if (current) {
          setError(reason instanceof Error ? reason.message : 'Could not restore the document.');
        }
      } finally {
        if (current) setPhase((phase) => phase === 'restoring' ? 'idle' : phase);
      }
    }
    void restore();
    return () => { current = false; };
  }, []);

  async function finishSummary(documentId: string) {
    setPhase('summarizing');
    const generated = await generateSummary(documentId);
    const saved = await getSummary(documentId);
    setSummary(saved || generated);
    setPhase('ready');
  }

  async function processUploadedDocument(documentId: string) {
    setError(null);
    setPhase('processing');
    try {
      await processDocument(documentId);
      await finishSummary(documentId);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not process the paper.');
      setPhase('idle');
    }
  }

  async function handleUpload(file: File) {
    setError(null);
    setPhase('uploading');
    try {
      const uploaded = await uploadDocument(file);
      localStorage.setItem(savedDocumentKey, uploaded.id);
      setDocument(uploaded);
      await processUploadedDocument(uploaded.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not upload the PDF.');
      setPhase('idle');
    }
  }

  async function continueDocument() {
    if (!document) return;
    setError(null);
    try {
      const latest = await getDocument(document.id);
      setDocument(latest);
      if (latest.status === 'pending' || latest.status === 'failed') {
        await processUploadedDocument(latest.id);
      } else if (latest.status === 'indexed' || latest.status === 'completed') {
        setPhase('summarizing');
        try {
          const saved = await getSummary(latest.id);
          setSummary(saved);
          setPhase('ready');
        } catch (reason) {
          if (reason instanceof ApiError && reason.status === 404) await finishSummary(latest.id);
          else throw reason;
        }
      } else if (latest.status === 'processing') {
        setError('Processing is still underway. Check again after it finishes.');
      } else {
        setError('The document is not ready. Please check its status again.');
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not check the document.');
      setPhase('idle');
    }
  }

  function startNewDocument() {
    localStorage.removeItem(savedDocumentKey);
    setDocument(null);
    setSummary(null);
    setError(null);
    setPhase('idle');
  }

  const busy = phase === 'uploading' || phase === 'processing' || phase === 'summarizing';
  const status = phase === 'uploading' ? 'Uploading your paper...' : phase === 'processing' ? 'Extracting content and indexing the document...' : phase === 'summarizing' ? 'Generating structured summary...' : null;

  return <div className="min-h-screen bg-slate-900 text-slate-100"><header className="border-b border-slate-200 bg-white"><div className="mx-auto flex h-20 max-w-[1600px] items-center gap-3 px-5 sm:px-6"><div className="rounded-xl bg-sky-700 p-2 text-white"><BookOpen size={20} /></div><span className="font-semibold tracking-tight text-slate-900">Research Assistant</span></div></header>
    {phase === 'restoring' ? <div role="status" className="flex items-center justify-center gap-2 p-16 text-sm"><LoaderCircle size={18} className="animate-spin" /> Restoring your paper...</div>
      : document && summary && phase === 'ready' ? <DocumentWorkspace key={document.id} document={document} summary={summary} onNewDocument={startNewDocument} />
      : document ? <main className="mx-auto max-w-xl px-5 py-20 text-center"><h1 className="text-2xl font-semibold text-white">{document.filename}</h1><p className="mt-3 text-sm text-slate-300">Current status: {document.status}</p>{busy && <p role="status" className="mt-8 inline-flex items-center gap-2 text-sky-200"><LoaderCircle size={18} className="animate-spin" /> {status}</p>}{error && <p role="alert" className="mt-8 rounded-xl bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}{!busy && <div className="mt-8 flex justify-center gap-3"><button onClick={() => void continueDocument()} className="rounded-xl bg-sky-700 px-5 py-3 text-sm font-semibold text-white hover:bg-sky-800">Check and continue</button><button onClick={startNewDocument} className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">Upload new PDF</button></div>}</main>
      : <FileUpload busy={busy} status={status} error={error} onUpload={(file) => void handleUpload(file)} />}</div>;
}
