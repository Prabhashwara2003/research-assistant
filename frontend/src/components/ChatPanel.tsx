import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { ArrowUp, LoaderCircle, MessageCircle } from 'lucide-react';
import { getMessages, sendMessage } from '../services/api';
import type { DisplayMessage, SourceReference } from '../types/api';
import ChatMessage from './ChatMessage';
import ImagePreview from './ImagePreview';

export default function ChatPanel({ documentId, onPage }: { documentId: string; onPage: (page: number) => void }) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<SourceReference | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let current = true;
    setMessages([]);
    setError(null);
    setLoadingHistory(true);
    getMessages(documentId).then((history) => {
      if (current) setMessages(history);
    }).catch((reason: Error) => {
      if (current) setError(reason.message);
    }).finally(() => {
      if (current) setLoadingHistory(false);
    });
    return () => { current = false; };
  }, [documentId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, sending]);

  async function submit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || sending || loadingHistory) return;
    setSending(true);
    setError(null);
    setQuestion('');
    const userMessage: DisplayMessage = { id: -Date.now(), document_id: documentId, role: 'user', content: trimmed, created_at: new Date().toISOString() };
    setMessages((current) => [...current, userMessage]);
    try {
      const response = await sendMessage(documentId, trimmed);
      const assistantMessage: DisplayMessage = { id: response.message_id, document_id: documentId, role: 'assistant', content: response.answer, created_at: new Date().toISOString(), sources: response.sources };
      setMessages((current) => [...current, assistantMessage]);
    } catch (reason) {
      setMessages((current) => current.filter((message) => message !== userMessage));
      setQuestion(trimmed);
      setError(reason instanceof Error ? reason.message : 'Could not send your question.');
    } finally {
      setSending(false);
    }
  }

  function onQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return (
    <section aria-label="Research chat" className="flex min-h-[600px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-sm lg:h-[calc(100vh-176px)] lg:min-h-[650px]">
      <div className="border-b border-slate-200 bg-white px-6 py-5"><div className="flex items-center gap-2"><MessageCircle size={19} className="text-sky-700" /><h2 className="font-semibold text-slate-900">Ask about this paper</h2></div><p className="mt-1 text-sm text-slate-500">Answers can include pages and extracted figures.</p></div>
      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-5" aria-live="polite">
        {loadingHistory && <p role="status" className="text-sm text-slate-500">Loading conversation...</p>}
        {!loadingHistory && messages.length === 0 && <div className="flex h-full flex-col items-center justify-center text-center"><div className="mb-4 rounded-2xl bg-white p-4 text-sky-700 shadow-sm"><MessageCircle size={25} /></div><h3 className="font-semibold text-slate-800">Start with a question</h3><p className="mt-2 max-w-xs text-sm leading-6 text-slate-500">Ask about the methodology, results, conclusions, or figures in this paper.</p></div>}
        {messages.map((message) => <ChatMessage key={message.id} message={message} onPage={onPage} onImage={setPreview} />)}
        {sending && <div role="status" className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600"><LoaderCircle size={16} className="animate-spin" /> Claude is analyzing your question...</div>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={submit} className="border-t border-slate-200 bg-white p-4">
        {error && <p role="alert" className="mb-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-white p-2 focus-within:border-slate-400">
          <label htmlFor="question" className="sr-only">Ask a question</label>
          <textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={onQuestionKeyDown} maxLength={2000} rows={2} placeholder="Ask a question about this paper..." className="max-h-36 min-h-12 flex-1 resize-y bg-transparent px-2 py-2 text-sm text-slate-900 outline-none placeholder:text-slate-400" />
          <button type="submit" disabled={!question.trim() || sending || loadingHistory} aria-label="Send question" className="rounded-lg bg-sky-700 p-3 text-white hover:bg-sky-800 disabled:cursor-not-allowed disabled:opacity-40"><ArrowUp size={18} /></button>
        </div>
        <p className="mt-2 text-center text-xs text-slate-400">Enter to send · Shift + Enter for a new line</p>
      </form>
      {preview && <ImagePreview documentId={documentId} source={preview} onClose={() => setPreview(null)} />}
    </section>
  );
}
