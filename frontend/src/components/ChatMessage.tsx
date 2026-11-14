import { Image as ImageIcon } from 'lucide-react';
import Markdown from 'react-markdown';
import type { DisplayMessage, SourceReference } from '../types/api';

export default function ChatMessage({ message, onPage, onImage }: { message: DisplayMessage; onPage: (page: number) => void; onImage: (source: SourceReference) => void }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[85%] ${isUser ? 'bg-sky-700 text-white' : 'border border-slate-200 bg-white text-slate-800'}`}>
        {isUser
          ? <p className="whitespace-pre-wrap">{message.content}</p>
          : <div className="message-markdown"><Markdown skipHtml>{message.content}</Markdown></div>}
        {!!message.sources?.length && <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-200 pt-3">
          {message.sources.map((source, index) => <span key={`${source.page}-${source.image_id}-${index}`} className="inline-flex items-center gap-1">
            <button type="button" onClick={() => onPage(source.page)} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-sky-800 hover:bg-slate-200">Page {source.page}</button>
            {source.image_id && <button type="button" onClick={() => onImage(source)} className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-sky-800 hover:bg-slate-200"><ImageIcon size={13} /> Image</button>}
          </span>)}
        </div>}
      </div>
    </div>
  );
}
