import { useMemo } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion } from 'framer-motion'

type Props = {
  disabled?: boolean
  onFileAccepted: (file: File) => void
}

const accept = {
  'image/*': ['.png', '.jpg', '.jpeg', '.webp'],
}

export default function UploadZone({ disabled, onFileAccepted }: Props) {
  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject,
    acceptedFiles,
  } = useDropzone({
    accept,
    maxFiles: 1,
    multiple: false,
    disabled,
    onDropAccepted: (files) => {
      const file = files[0]
      if (file) onFileAccepted(file)
    },
  })

  const borderClass = useMemo(() => {
    if (disabled) return 'border-slate-200'
    if (isDragReject) return 'border-rose-400'
    if (isDragActive) return 'border-blue-400'
    return 'border-slate-200 hover:border-blue-400'
  }, [disabled, isDragActive, isDragReject])

  return (
    <motion.div whileHover={disabled ? undefined : { scale: 1.005 }} transition={{ duration: 0.3, ease: 'easeInOut' }}>
      <div
        {...getRootProps()}
        className={
          'mx-auto w-full max-w-2xl rounded-3xl border-2 border-dashed bg-gradient-to-br from-slate-50 to-blue-50/60 p-6 transition-colors ' +
          borderClass +
          (disabled ? ' cursor-not-allowed opacity-60' : ' cursor-pointer')
        }
      >
        <input {...getInputProps()} />
        <div className="flex h-64 flex-col items-center justify-center text-center">
          <div className="text-sm font-medium text-slate-700">
            {isDragActive ? 'Drop to generate' : 'Drag image here or click'}
          </div>
          <div className="mt-2 text-xs text-slate-500">PNG/JPG/WEBP • 1 file</div>
          {acceptedFiles.length > 0 && (
            <div className="mt-4 text-xs text-slate-600">Selected: {acceptedFiles[0].name}</div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
