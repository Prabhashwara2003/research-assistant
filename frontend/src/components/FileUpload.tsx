import { useState, type FormEvent } from 'react';
import { FileUp, LoaderCircle } from 'lucide-react';

interface Props {
  busy: boolean;
  status: string | null;
  error: string | null;
  onUpload: (file: File) => void;
}

export default function FileUpload({ busy, status, error, onUpload }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  function selectFile(selectedFile?: File) {
    if (!selectedFile) return;
    if (!selectedFile.name.toLowerCase().endsWith('.pdf') || (selectedFile.type && selectedFile.type !== 'application/pdf')) {
      setFile(null);
      setValidationError('Choose a PDF file.');
      return;
    }
    setValidationError(null);
    setFile(selectedFile);
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file && !busy) onUpload(file);
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-80px)] max-w-2xl flex-col items-center justify-center px-5 py-14 text-center">
      <div className="mb-6 rounded-2xl bg-sky-50 p-4 text-sky-700"><FileUp size={28} /></div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">Your research workspace</p>
      <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">Understand papers faster.</h1>
      <p className="mt-5 max-w-lg text-base leading-7 text-slate-300">Upload a research PDF to get a structured summary, explore the original paper, and ask questions with page references.</p>
      <form onSubmit={submit} className="mt-10 w-full rounded-3xl border border-slate-200 bg-white p-7 shadow-sm sm:p-10">
        <label htmlFor="pdf-file" className="block text-left text-sm font-semibold text-slate-800">Research paper PDF</label>
        <input id="pdf-file" type="file" accept=".pdf,application/pdf" disabled={busy}
          onChange={(event) => selectFile(event.target.files?.[0])}
          className="mt-3 block w-full cursor-pointer rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:font-medium file:text-white hover:file:bg-slate-700" />
        <p className="mt-3 text-left text-sm text-slate-500">{file ? `Selected: ${file.name}` : 'PDF files only. One paper at a time.'}</p>
        <button type="submit" disabled={!file || busy} className="mt-7 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-sky-700 px-5 py-3 font-semibold text-white hover:bg-sky-800 disabled:cursor-not-allowed disabled:opacity-50">
          {busy ? <LoaderCircle size={18} className="animate-spin" /> : <FileUp size={18} />}
          {busy ? 'Working on your paper' : 'Upload and analyze'}
        </button>
        {status && <p role="status" className="mt-4 text-sm text-sky-800">{status}</p>}
        {(validationError || error) && <p role="alert" className="mt-4 rounded-lg bg-rose-50 p-3 text-left text-sm text-rose-700">{validationError || error}</p>}
      </form>
    </div>
  );
}
