import type { ChatResponse, DocumentResponse, MessageResponse, ProcessResponse, ResearchSummary } from '../types/api';

const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

const defaultErrors: Record<number, string> = {
  400: 'Please check your file or request and try again.',
  404: 'The document or resource was not found.',
  409: 'This document is not ready for that action.',
  413: 'The PDF exceeds the upload size limit.',
  422: 'The request could not be processed. Please check your input.',
  500: 'The server encountered an error. Please try again later.',
  502: 'The AI could not generate a response. Please try again.',
  503: 'Document search is temporarily unavailable. Please try again.',
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, options);
  } catch {
    throw new ApiError(0, 'Could not reach the backend. Check that FastAPI is running.');
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = (await response.json()).detail;
    } catch {
      // A proxy or server error might not return JSON.
    }
    const message = typeof detail === 'string' && response.status < 500
      ? detail
      : defaultErrors[response.status] || 'The request failed. Please try again.';
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}

function documentPath(documentId: string): string {
  return `/api/documents/${encodeURIComponent(documentId)}`;
}

export function documentFileUrl(documentId: string, page?: number): string {
  const url = `${baseUrl}${documentPath(documentId)}/file`;
  return page ? `${url}#page=${page}` : url;
}

export function documentImageUrl(documentId: string, imageId: string): string {
  return `${baseUrl}${documentPath(documentId)}/images/${encodeURIComponent(imageId)}`;
}

export function uploadDocument(file: File): Promise<DocumentResponse> {
  const body = new FormData();
  body.append('file', file);
  return request('/api/documents', { method: 'POST', body });
}

export function getDocument(documentId: string): Promise<DocumentResponse> {
  return request(documentPath(documentId));
}

export function processDocument(documentId: string): Promise<ProcessResponse> {
  return request(`${documentPath(documentId)}/process`, { method: 'POST' });
}

export function getSummary(documentId: string): Promise<ResearchSummary> {
  return request(`${documentPath(documentId)}/summary`);
}

export function generateSummary(documentId: string): Promise<ResearchSummary> {
  return request(`${documentPath(documentId)}/summary`, { method: 'POST' });
}

export function getMessages(documentId: string): Promise<MessageResponse[]> {
  return request(`${documentPath(documentId)}/messages`);
}

export function sendMessage(documentId: string, question: string): Promise<ChatResponse> {
  return request(`${documentPath(documentId)}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
}
