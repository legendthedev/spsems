/**
 * Resolves an institution's logo URL to an absolute, renderable source.
 * Handles Base64 Data URIs, absolute HTTP/HTTPS links, and backend /uploads paths.
 */
export function resolveLogoUrl(url) {
  if (!url) return null;
  const clean = String(url).trim();
  if (!clean) return null;

  // Base64 Data URI or absolute web URL
  if (clean.startsWith('data:') || clean.startsWith('http://') || clean.startsWith('https://')) {
    return clean;
  }

  // Backend uploads path (/uploads/... or /api/uploads/...)
  if (clean.startsWith('/uploads') || clean.startsWith('/api/uploads')) {
    const rawApi = (process.env.REACT_APP_API_URL || '').trim().replace(/\/api\/?$/, '');
    if (rawApi) {
      return `${rawApi}${clean.startsWith('/') ? clean : `/${clean}`}`;
    }
    // In local development environment
    if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
      return `http://localhost:8000${clean.startsWith('/') ? clean : `/${clean}`}`;
    }
  }

  // Root-relative asset path like /unilag.svg or /kwasu.png
  return clean;
}
