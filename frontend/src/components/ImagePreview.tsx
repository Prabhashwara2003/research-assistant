import { useEffect } from 'react';
import { X } from 'lucide-react';
import { documentImageUrl } from '../services/api';
import type { SourceReference } from '../types/api';

export default function ImagePreview({ documentId, source, onClose }: { documentId: string; source: SourceReference; onClose: () => void }) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) { if (event.key === 'Escape') onClose(); }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  if (!source.image_id) return null;
  return (
    <div role="dialog" aria-modal="true" aria-label={`Image from page ${source.page}`} className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4" onMouseDown={onClose}>
      <div className="max-h-[90vh] max-w-4xl overflow-auto rounded-2xl bg-white p-4 shadow-xl" onMouseDown={(event) => event.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between gap-4"><p className="text-sm font-medium text-slate-700">Page {source.page} · Image {source.image_id}</p><button onClick={onClose} aria-label="Close image preview" className="rounded-lg p-2 hover:bg-slate-100"><X size={20} /></button></div>
        <img src={documentImageUrl(documentId, source.image_id)} alt={`Extracted figure ${source.image_id} from page ${source.page}`} className="max-h-[75vh] w-full object-contain" />
      </div>
    </div>
  );
}
