import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { 
  Upload as UploadIcon, 
  Film, 
  X, 
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { videosApi } from '../api/client'
import toast from 'react-hot-toast'

interface UploadedFile {
  file: File
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  videoId?: number
  error?: string
}

export default function Upload() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const navigate = useNavigate()
  
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      // Validate file type
      if (!file.type.startsWith('video/')) {
        toast.error(`${file.name} is not a video file`)
        continue
      }
      
      // Validate file size (500MB max)
      if (file.size > 500 * 1024 * 1024) {
        toast.error(`${file.name} is too large (max 500MB)`)
        continue
      }
      
      // Add to state
      const uploadFile: UploadedFile = {
        file,
        progress: 0,
        status: 'uploading'
      }
      
      setFiles(prev => [...prev, uploadFile])
      
      try {
        // Upload file
        const video = await videosApi.upload(file, (progress) => {
          setFiles(prev => prev.map(f => 
            f.file === file ? { ...f, progress } : f
          ))
        })
        
        // Update status
        setFiles(prev => prev.map(f => 
          f.file === file 
            ? { ...f, status: 'completed', videoId: video.id, progress: 100 } 
            : f
        ))
        
        toast.success(`${file.name} uploaded successfully!`)
        
      } catch (error: any) {
        setFiles(prev => prev.map(f => 
          f.file === file 
            ? { ...f, status: 'error', error: error.message } 
            : f
        ))
        toast.error(`Failed to upload ${file.name}`)
      }
    }
  }, [])
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.webm', '.mkv']
    },
    maxFiles: 5
  })
  
  const removeFile = (file: File) => {
    setFiles(prev => prev.filter(f => f.file !== file))
  }
  
  const processVideo = async (uploadedFile: UploadedFile) => {
    if (!uploadedFile.videoId) return
    
    setFiles(prev => prev.map(f => 
      f.file === uploadedFile.file 
        ? { ...f, status: 'processing' } 
        : f
    ))
    
    try {
      await videosApi.process(uploadedFile.videoId, {
        max_clips: 5,
        min_clip_duration: 15,
        max_clip_duration: 60
      })
      
      toast.success('Video processing started!')
      navigate(`/videos/${uploadedFile.videoId}`)
      
    } catch (error) {
      toast.error('Failed to start processing')
      setFiles(prev => prev.map(f => 
        f.file === uploadedFile.file 
          ? { ...f, status: 'completed' } 
          : f
      ))
    }
  }
  
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }
  
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Upload Video</h1>
        <p className="text-slate-400 mt-1">
          Upload your video and we'll automatically find the best clips
        </p>
      </div>
      
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200
          ${isDragActive 
            ? 'border-primary-500 bg-primary-500/10' 
            : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center">
          <div className={`
            w-16 h-16 rounded-2xl flex items-center justify-center mb-4
            ${isDragActive ? 'bg-primary-500/20' : 'bg-slate-700'}
          `}>
            <UploadIcon className={`w-8 h-8 ${isDragActive ? 'text-primary-400' : 'text-slate-400'}`} />
          </div>
          <p className="text-lg font-medium text-white mb-2">
            {isDragActive ? 'Drop your video here' : 'Drag & drop your video'}
          </p>
          <p className="text-sm text-slate-400 mb-4">
            or click to browse
          </p>
          <p className="text-xs text-slate-500">
            MP4, MOV, AVI, WebM • Max 500MB
          </p>
        </div>
      </div>
      
      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">Uploaded Files</h2>
          
          {files.map((uploadedFile, index) => (
            <div key={index} className="glass rounded-xl p-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-slate-700 rounded-lg flex items-center justify-center">
                  <Film className="w-6 h-6 text-slate-400" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium text-white truncate">
                      {uploadedFile.file.name}
                    </p>
                    <span className="text-xs text-slate-400 ml-2">
                      {formatFileSize(uploadedFile.file.size)}
                    </span>
                  </div>
                  
                  {/* Progress bar */}
                  {uploadedFile.status === 'uploading' && (
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div 
                        className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadedFile.progress}%` }}
                      />
                    </div>
                  )}
                  
                  {/* Status */}
                  <div className="flex items-center gap-2 mt-1">
                    {uploadedFile.status === 'uploading' && (
                      <>
                        <Loader2 className="w-4 h-4 text-primary-400 animate-spin" />
                        <span className="text-xs text-primary-400">
                          Uploading... {uploadedFile.progress}%
                        </span>
                      </>
                    )}
                    {uploadedFile.status === 'processing' && (
                      <>
                        <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" />
                        <span className="text-xs text-yellow-400">Processing...</span>
                      </>
                    )}
                    {uploadedFile.status === 'completed' && (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span className="text-xs text-green-400">Ready to process</span>
                      </>
                    )}
                    {uploadedFile.status === 'error' && (
                      <>
                        <AlertCircle className="w-4 h-4 text-red-400" />
                        <span className="text-xs text-red-400">
                          {uploadedFile.error || 'Upload failed'}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-2">
                  {uploadedFile.status === 'completed' && (
                    <button
                      onClick={() => processVideo(uploadedFile)}
                      className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      Process
                    </button>
                  )}
                  <button
                    onClick={() => removeFile(uploadedFile.file)}
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Info */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">How it works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-primary-400">1</span>
            </div>
            <div>
              <p className="text-sm font-medium text-white">Upload</p>
              <p className="text-xs text-slate-400">Upload your video file</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-primary-400">2</span>
            </div>
            <div>
              <p className="text-sm font-medium text-white">Analyze</p>
              <p className="text-xs text-slate-400">AI finds the best moments</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-bold text-primary-400">3</span>
            </div>
            <div>
              <p className="text-sm font-medium text-white">Share</p>
              <p className="text-xs text-slate-400">Post to social media</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
