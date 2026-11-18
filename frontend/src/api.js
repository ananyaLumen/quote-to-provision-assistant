const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export { API_URL };
const TIMEOUT_MS = 120_000; // the pipeline makes several LLM calls: typically 8-25 s

export class ApiError extends Error {
  constructor(message, kind) {
    super(message);
    this.kind = kind;
  }
}

function describe(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(d => d.msg || JSON.stringify(d)).join('; ');
  return '';
}

export async function generateQuote(requirementText) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response;
  try {
    response = await fetch(`${API_URL}/quote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirement_text: requirementText }),
      signal: controller.signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new ApiError('The request took longer than two minutes and was cancelled. Please try again.', 'timeout');
    }
    throw new ApiError(
      `Can't reach the API at ${API_URL}. Check that the backend is running (uvicorn backend.main:app --port 8000) and that you are on the corporate network or VPN.`,
      'network',
    );
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    let detail = '';
    try { detail = describe((await response.json()).detail); } catch { /* body was not JSON */ }
    throw new ApiError(`The backend returned ${response.status}${detail ? `: ${detail}` : ''}.`, 'server');
  }
  return response.json();
}
