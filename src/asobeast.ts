export class AsoBeastClient {
  constructor(private readonly baseUrl: string, private readonly token: string) {}

  configured() { return this.token.startsWith('asob_'); }

  async request<T>(path: string, init?: RequestInit): Promise<T> {
    if (!this.configured()) throw new Error('ASOBEAST_NOT_CONFIGURED');
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      signal: AbortSignal.timeout(15_000),
      headers: { 'content-type': 'application/json', authorization: `Bearer ${this.token}`, ...init?.headers },
    });
    const body = await response.text();
    if (!response.ok) throw new Error(`ASOBEAST_${response.status}:${body.slice(0, 400)}`);
    return (body ? JSON.parse(body) : null) as T;
  }

  status() { return this.request<Record<string, unknown>>('/ai/status'); }
  apps() { return this.request<Array<Record<string, unknown>>>('/apps'); }
  summary(id: string) { return this.request<Record<string, unknown>>(`/apps/${encodeURIComponent(id)}/summary`); }
  audit(id: string) { return this.request<Record<string, unknown>>(`/apps/${encodeURIComponent(id)}/audit`); }
  keywords(id: string) { return this.request<Array<Record<string, unknown>>>(`/apps/${encodeURIComponent(id)}/keywords`); }
  import(url: string) { return this.request<Record<string, unknown>>('/apps', { method: 'POST', body: JSON.stringify({ url }) }); }
  runDaily(id: string) { return this.request<Record<string, unknown>>(`/apps/${encodeURIComponent(id)}/run-daily`, { method: 'POST', body: '{}' }); }
}
