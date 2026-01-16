/**
 * Return the URL directly since backend now returns presigned S3 URLs
 * that can be accessed directly from the browser.
 * 
 * Presigned URLs are temporary (15 min default) and don't require proxy.
 * If URL expires, the backend will generate a fresh one on next request.
 */
export function proxyMinioUrl(url: string): string {
  // Backend now returns presigned URLs from Backblaze B2
  // These URLs can be used directly without proxying
  return url
}
