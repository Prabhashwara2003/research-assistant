import { documentFileUrl } from '../services/api';

export default function PdfViewer({ documentId, page }: { documentId: string; page: number | null }) {
  return <iframe key={page ?? 'start'} src={documentFileUrl(documentId, page ?? undefined)} title="Research paper PDF" className="h-[70vh] min-h-[520px] w-full border-0" />;
}
