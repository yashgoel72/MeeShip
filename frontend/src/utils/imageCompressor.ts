import imageCompression from 'browser-image-compression'

export async function compressForUpload(file: File): Promise<File> {
  // Target: 1024×1024, ~150–300KB (best effort)
  type ImageCompressionOptions = Parameters<typeof imageCompression>[1]
  const options: ImageCompressionOptions = {
    maxSizeMB: 0.3,
    maxWidthOrHeight: 1024,
    useWebWorker: true,
    initialQuality: 0.85,
    fileType: 'image/jpeg',
  }

  const compressed = await imageCompression(file, options)
  const name = file.name.replace(/\.(png|webp|jpeg|jpg)$/i, '') + '.jpg'
  return new File([compressed], name, { type: 'image/jpeg' })
}
