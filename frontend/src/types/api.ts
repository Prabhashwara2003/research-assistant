export interface DocumentResponse {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'indexed' | 'completed' | 'failed';
  summary_json: string | null;
  created_at: string;
}

export interface ProcessResponse {
  document_id: string;
  status: 'indexed';
  chunk_count: number;
}

// ResearchSummary has no dedicated problem_statement field in the backend.
export interface ResearchSummary {
  title: string;
  authors: string[];
  abstract: string;
  methodology: string;
  key_result: string[];
  conclusion: string;
}

export interface SourceReference {
  page: number;
  image_id: string | null;
}

export interface ChatResponse {
  message_id: number;
  answer: string;
  sources: SourceReference[];
}

export interface MessageResponse {
  id: number;
  document_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface DisplayMessage extends MessageResponse {
  sources?: SourceReference[];
}
