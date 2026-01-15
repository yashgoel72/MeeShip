export function proxyMinioUrl(url: string): string {
  const encoded = encodeURIComponent(url)
  return `/api/images/proxy/?url=${encoded}`
}
