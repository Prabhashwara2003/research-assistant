import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { DocumentResponse, ResearchSummary } from '../types/api';
import FileUpload from '../components/FileUpload';
import DocumentSummary from '../components/DocumentSummary';
import ChatMessage from '../components/ChatMessage';
import DocumentWorkspace from '../components/DocumentWorkspace';
import ChatPanel from '../components/ChatPanel';
import App from '../App';

vi.mock('../services/api', async (importOriginal) => {
  const original = await importOriginal<typeof import('../services/api')>();
  return { ...original, getMessages: vi.fn(), sendMessage: vi.fn(), getDocument: vi.fn(), getSummary: vi.fn() };
});

import { getDocument, getMessages, getSummary, sendMessage } from '../services/api';

const summary: ResearchSummary = {
  title: 'A Paper About Research', authors: ['Ada', 'Grace'], abstract: 'An abstract',
  methodology: 'A careful method', key_result: ['First result', 'Second result'], conclusion: 'A conclusion',
};
const document: DocumentResponse = { id: 'paper-1', filename: 'paper.pdf', status: 'completed', summary_json: '{}', created_at: '2026-01-01T00:00:00Z' };

beforeEach(() => {
  vi.mocked(getMessages).mockResolvedValue([]);
  vi.mocked(getDocument).mockResolvedValue(document);
  vi.mocked(getSummary).mockResolvedValue(summary);
  vi.mocked(sendMessage).mockReset();
});

describe('upload', () => {
  it('rejects non-PDF files and does not submit them', async () => {
    const onUpload = vi.fn();
    render(<FileUpload busy={false} status={null} error={null} onUpload={onUpload} />);
    await userEvent.upload(screen.getByLabelText('Research paper PDF'), new File(['notes'], 'notes.txt', { type: 'text/plain' }), { applyAccept: false });
    expect(screen.getByRole('alert')).toHaveTextContent('Choose a PDF file');
    expect(screen.getByRole('button', { name: /upload and analyze/i })).toBeDisabled();
    expect(onUpload).not.toHaveBeenCalled();
  });

  it('disables repeat submission and announces progress', async () => {
    render(<FileUpload busy={true} status="Extracting content..." error={null} onUpload={vi.fn()} />);
    expect(screen.getByRole('button', { name: /working on your paper/i })).toBeDisabled();
    expect(screen.getByRole('status')).toHaveTextContent('Extracting content');
  });
});

it('renders every summary section with list results', () => {
  render(<DocumentSummary summary={summary} />);
  for (const section of ['Authors', 'Abstract', 'Problem statement', 'Methodology', 'Key results', 'Conclusion']) {
    expect(screen.getByRole('heading', { name: section })).toBeInTheDocument();
  }
  expect(screen.getByText('First result')).toBeInTheDocument();
});

it('renders source page and image controls only when supplied', async () => {
  const onPage = vi.fn();
  const onImage = vi.fn();
  render(<ChatMessage message={{ id: 1, document_id: 'paper-1', role: 'assistant', content: 'The answer', created_at: '', sources: [{ page: 4, image_id: 'figure-1' }] }} onPage={onPage} onImage={onImage} />);
  await userEvent.click(screen.getByRole('button', { name: 'Page 4' }));
  await userEvent.click(screen.getByRole('button', { name: 'Image' }));
  expect(onPage).toHaveBeenCalledWith(4);
  expect(onImage).toHaveBeenCalledWith({ page: 4, image_id: 'figure-1' });
});

it('renders a user message without invented citations', () => {
  render(<ChatMessage message={{ id: 2, document_id: 'paper-1', role: 'user', content: 'What is the result?', created_at: '' }} onPage={vi.fn()} onImage={vi.fn()} />);
  expect(screen.getByText('What is the result?')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Page/ })).not.toBeInTheDocument();
});

it('renders assistant Markdown as headings, emphasis, and lists', () => {
  render(<ChatMessage message={{ id: 3, document_id: 'paper-1', role: 'assistant', content: '## **The Reality Gap**\n\n**Evidence 5** reveals a tension:\n\n- First point\n- Second point', created_at: '' }} onPage={vi.fn()} onImage={vi.fn()} />);
  expect(screen.getByRole('heading', { level: 2, name: 'The Reality Gap' })).toBeInTheDocument();
  expect(screen.getByText('Evidence 5', { selector: 'strong' })).toBeInTheDocument();
  expect(screen.getByText('First point').closest('li')).toBeInTheDocument();
  expect(screen.getByText('Second point').closest('li')).toBeInTheDocument();
});

it('switches between summary and PDF without losing chat', async () => {
  render(<DocumentWorkspace document={document} summary={summary} onNewDocument={vi.fn()} />);
  expect(screen.getByText('A careful method')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('tab', { name: 'PDF' }));
  expect(screen.getByTitle('Research paper PDF')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('tab', { name: 'Summary' }));
  expect(screen.getByText('A careful method')).toBeInTheDocument();
  expect(screen.getByRole('region', { name: 'Research chat' })).toBeInTheDocument();
});

describe('chat', () => {
  it('prevents empty questions', async () => {
    render(<ChatPanel documentId="paper-1" onPage={vi.fn()} />);
    await waitFor(() => expect(screen.getByRole('button', { name: 'Send question' })).toBeDisabled());
    fireEvent.change(screen.getByLabelText('Ask a question'), { target: { value: '   ' } });
    expect(screen.getByRole('button', { name: 'Send question' })).toBeDisabled();
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('shows a loading state while an answer is pending', async () => {
    vi.mocked(sendMessage).mockImplementation(() => new Promise(() => {}));
    render(<ChatPanel documentId="paper-1" onPage={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText('Loading conversation...')).not.toBeInTheDocument());
    await userEvent.type(screen.getByLabelText('Ask a question'), 'What happened?');
    await userEvent.click(screen.getByRole('button', { name: 'Send question' }));
    expect(screen.getByText('Claude is analyzing your question...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send question' })).toBeDisabled();
  });

  it('shows an API error and restores the unsent question', async () => {
    vi.mocked(sendMessage).mockRejectedValue(new Error('AI response generation failed'));
    render(<ChatPanel documentId="paper-1" onPage={vi.fn()} />);
    await waitFor(() => expect(screen.queryByText('Loading conversation...')).not.toBeInTheDocument());
    await userEvent.type(screen.getByLabelText('Ask a question'), 'Why?');
    await userEvent.click(screen.getByRole('button', { name: 'Send question' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('AI response generation failed');
    expect(screen.getByLabelText('Ask a question')).toHaveValue('Why?');
  });
});

it('restores the saved document and summary on refresh', async () => {
  localStorage.setItem('research-assistant-document-id', 'paper-1');
  render(<App />);
  expect(await screen.findByText('A careful method')).toBeInTheDocument();
  expect(getDocument).toHaveBeenCalledWith('paper-1');
  expect(getSummary).toHaveBeenCalledWith('paper-1');
});
