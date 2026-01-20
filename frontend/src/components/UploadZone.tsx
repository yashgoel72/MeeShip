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
    if (isDragReject) return 'border-rose-400 bg-rose-50/50'
    if (isDragActive) return 'border-meesho bg-meesho/5'
    return 'border-slate-200 hover:border-meesho/50'
  }, [disabled, isDragActive, isDragReject])

  return (
    <motion.div 
      whileHover={disabled ? undefined : { scale: 1.01 }} 
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="relative"
    >
      {/* Gradient glow effect */}
      {!disabled && (
        <div className="absolute -inset-1 bg-gradient-to-r from-meesho/20 via-purple-500/20 to-blue-500/20 rounded-[28px] blur-lg opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      )}
      
      <div
        {...getRootProps()}
        className={
          'relative mx-auto w-full max-w-2xl rounded-3xl border-2 border-dashed bg-gradient-to-br from-white to-slate-50 p-8 transition-all duration-300 ' +
          borderClass +
          (disabled ? ' cursor-not-allowed opacity-60' : ' cursor-pointer hover:shadow-lg hover:shadow-meesho/5')
        }
      >
        <input {...getInputProps()} />
        <div className="flex h-48 flex-col items-center justify-center text-center">
          {/* Animated upload icon */}
          <div className={`mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full transition-all duration-300 ${
            isDragActive 
              ? 'bg-meesho/20 scale-110' 
              : 'bg-gradient-to-br from-meesho/10 to-purple-100'
          }`}>
            <motion.svg 
              className={`w-8 h-8 transition-colors ${isDragActive ? 'text-meesho' : 'text-meesho/70'}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              animate={isDragActive ? { y: [0, -4, 0] } : {}}
              transition={{ duration: 0.5, repeat: isDragActive ? Infinity : 0 }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </motion.svg>
          </div>
          
          <div className="text-base font-medium text-slate-700">
            {isDragActive ? 'Drop to generate 30 images!' : 'Drag your product image here'}
          </div>
          <div className="mt-1 text-sm text-slate-500">
            or <span className="text-meesho font-medium">click to browse</span>
          </div>
          <div className="mt-3 text-xs text-slate-400">
            PNG, JPG, WEBP • Max 10MB
          </div>
          
          {acceptedFiles.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {acceptedFiles[0].name}
            </motion.div>
          )}
          
          {/* Tip */}
          {!acceptedFiles.length && (
            <div className="mt-4 inline-flex items-center gap-1.5 text-xs text-slate-400">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Best results with clean product photos
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
