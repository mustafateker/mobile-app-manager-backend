import { scryptSync, timingSafeEqual } from 'node:crypto';

const SESSION_COOKIE = 'mam_session';

const digest = (value: string) => scryptSync(value, 'mobil-app-manager-v1', 64);

export const passwordMatches = (actual: string, expected: string) =>
  timingSafeEqual(digest(actual), digest(expected));

type CookieReply = {
  setCookie(name: string, value: string, options: Record<string, unknown>): unknown;
  clearCookie(name: string, options: Record<string, unknown>): unknown;
};
type CookieRequest = {
  cookies: Record<string, string | undefined>;
  unsignCookie(value: string): { valid: boolean; value: string | null };
};

export const setSession = (reply: CookieReply, secure: boolean) => {
  reply.setCookie(SESSION_COOKIE, 'admin', {
    path: '/', httpOnly: true, sameSite: 'strict', secure, signed: true, maxAge: 60 * 60 * 12,
  });
};

export const clearSession = (reply: CookieReply, secure: boolean) => {
  reply.clearCookie(SESSION_COOKIE, { path: '/', httpOnly: true, sameSite: 'strict', secure });
};

export const isAuthenticated = (request: CookieRequest) => {
  const raw = request.cookies[SESSION_COOKIE];
  return Boolean(raw && request.unsignCookie(raw).valid && request.unsignCookie(raw).value === 'admin');
};
