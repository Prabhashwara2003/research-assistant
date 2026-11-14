import type { ResearchSummary } from '../types/api';

export default function DocumentSummary({ summary }: { summary: ResearchSummary }) {
  return (
    <article className="space-y-7 p-6 text-slate-800 sm:p-8">
      <section><p className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-700">Paper summary</p><h2 className="text-2xl font-semibold leading-tight text-slate-900">{summary.title || 'Untitled paper'}</h2></section>
      <section><h3 className="section-heading">Authors</h3><p>{summary.authors.length ? summary.authors.join(', ') : 'Not provided'}</p></section>
      <section><h3 className="section-heading">Abstract</h3><p className="whitespace-pre-wrap">{summary.abstract || 'Not provided'}</p></section>
      <section><h3 className="section-heading">Problem statement</h3><p>Not provided separately in this summary. See the abstract for the paper’s research problem.</p></section>
      <section><h3 className="section-heading">Methodology</h3><p className="whitespace-pre-wrap">{summary.methodology || 'Not provided'}</p></section>
      <section><h3 className="section-heading">Key results</h3>{summary.key_result.length ? <ul className="list-disc space-y-2 pl-5">{summary.key_result.map((result, index) => <li key={index}>{result}</li>)}</ul> : <p>Not provided</p>}</section>
      <section><h3 className="section-heading">Conclusion</h3><p className="whitespace-pre-wrap">{summary.conclusion || 'Not provided'}</p></section>
    </article>
  );
}
