import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getClient } from './api'
import {
  Upload, Image as ImageIcon, Film, Folder, Download, Loader2, Settings,
  Sparkles
} from 'lucide-react'

const SECTIONS = [
  { key: 'upload', icon: Upload },
  { key: 'imageToAscii', icon: ImageIcon },
  { key: 'videoToAscii', icon: Film },
  { key: 'animation', icon: Sparkles },
  { key: 'projects', icon: Folder },
  { key: 'jobs', icon: Loader2 },
  { key: 'settings', icon: Settings },
]

export default function App() {
  const { t } = useTranslation()
  const [api, setApi] = useState(getClient)
  const [token, setToken] = useState(localStorage.getItem('ams_token') || '')
  const [section, setSection] = useState('upload')
  const [file, setFile] = useState<File | null>(null)
  const [uploaded, setUploaded] = useState<any>(null)
  const [width, setWidth] = useState(120)
  const [mode, setMode] = useState('grayscale')
  const [palette, setPalette] = useState('standard')
  const [background, setBackground] = useState('black')
  const [contrastAdapt, setContrastAdapt] = useState(false)
  const [fps, setFps] = useState(15)
  const [maxDuration, setMaxDuration] = useState(20)
  const [outputFormat, setOutputFormat] = useState('png')
  const [effects, setEffects] = useState<string[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    setApi(getClient())
  }, [token])

  useEffect(() => {
    fetchJobs()
    fetchProjects()
    const interval = setInterval(fetchJobs, 3000)
    return () => clearInterval(interval)
  }, [api])

  const saveToken = (val: string) => {
    setToken(val)
    localStorage.setItem('ams_token', val)
  }

  const fetchJobs = async () => {
    try {
      const { data } = await api.get('/jobs?limit=20')
      setJobs(data.jobs)
    } catch (e: any) {
      if (e.response?.status === 401) setMessage('Neispravan API token.')
    }
  }

  const fetchProjects = async () => {
    try {
      const { data } = await api.get('/projects')
      setProjects(data.projects)
    } catch { /* ignore */ }
  }

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setMessage('')
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await api.post('/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setUploaded(data)
      setMessage('Datoteka učitana: ' + data.filename)
    } catch (e: any) {
      setMessage(e.response?.data?.detail || 'Greška pri učitavanju')
    }
    setLoading(false)
  }

  const buildPayload = (extra: any = {}) => ({
    input_path: uploaded?.path,
    width,
    mode,
    palette,
    background,
    contrast_adapt: contrastAdapt,
    fps,
    max_duration: maxDuration,
    effects: effects.map((name) => ({ name, intensity: 0.5, speed: 1.0, direction: 'horizontal' })),
    ...extra,
  })

  const handleImageConvert = async () => {
    if (!uploaded || uploaded.type !== 'image') {
      setMessage('Prvo učitajte sliku.')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/image/convert', buildPayload({ output_format: outputFormat }))
      setMessage(`Posao pokrenut: #${data.job_id}`)
    } catch (e: any) {
      setMessage(e.response?.data?.detail || 'Greška')
    }
    setLoading(false)
  }

  const handleVideoConvert = async () => {
    if (!uploaded || uploaded.type !== 'video') {
      setMessage('Prvo učitajte video.')
      return
    }
    setLoading(true)
    try {
      const fmt = outputFormat === 'png' ? 'gif' : outputFormat
      const { data } = await api.post('/video/convert', buildPayload({ output_format: fmt }))
      setMessage(`Posao pokrenut: #${data.job_id}`)
    } catch (e: any) {
      setMessage(e.response?.data?.detail || 'Greška')
    }
    setLoading(false)
  }

  const handleAnimationRender = async () => {
    if (!uploaded) {
      setMessage('Prvo učitajte datoteku.')
      return
    }
    setLoading(true)
    try {
      const fmt = section === 'animation' ? (outputFormat === 'png' ? 'gif' : outputFormat) : 'gif'
      const { data } = await api.post('/animation/render', buildPayload({ output_format: fmt }))
      setMessage(`Animacija pokrenuta: #${data.job_id}`)
    } catch (e: any) {
      setMessage(e.response?.data?.detail || 'Greška')
    }
    setLoading(false)
  }

  const handleExport = async () => {
    if (!uploaded) {
      setMessage('Prvo učitajte datoteku.')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/export', buildPayload({ export_type: outputFormat }))
      setMessage(`Export pokrenut: #${data.job_id}`)
    } catch (e: any) {
      setMessage(e.response?.data?.detail || 'Greška')
    }
    setLoading(false)
  }

  const createProject = async () => {
    if (!uploaded) return
    try {
      const { data } = await api.post('/projects', {
        name: uploaded.filename,
        settings: { width, mode, palette, background },
        source_type: uploaded.type,
        source_path: uploaded.path,
      })
      setMessage(`Projekat kreiran: #${data.project_id}`)
      fetchProjects()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || 'Greška')
    }
  }

  const renderPreview = (job: any) => {
    if (!job.output_path) return null
    const url = job.output_path.replace('/var/lib/ascii-motion-studio', '/exports')
    const ext = job.output_path.split('.').pop()
    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) {
      return <img src={url} alt="preview" className="max-w-full border border-slate-700 rounded" />
    }
    if (ext === 'mp4' || ext === 'webm') {
      return <video src={url} controls className="max-w-full border border-slate-700 rounded" />
    }
    if (ext === 'html') {
      return <a href={url} target="_blank" rel="noreferrer" className="text-blue-400 underline">Otvori HTML</a>
    }
    if (ext === 'zip') {
      return <a href={url} download className="text-blue-400 underline">Preuzmi ZIP</a>
    }
    return <a href={url} className="text-blue-400 underline">Preuzmi</a>
  }

  const toggleEffect = (name: string) => {
    setEffects((prev) => prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name])
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 p-4 flex flex-col gap-2">
        <h1 className="text-lg font-bold mb-2 text-white">{t('appName')}</h1>
        {SECTIONS.map((s) => {
          const Icon = s.icon
          return (
            <button
              key={s.key}
              onClick={() => setSection(s.key)}
              className={`flex items-center gap-2 px-3 py-2 rounded text-left ${section === s.key ? 'bg-slate-700 text-white' : 'text-slate-400 hover:bg-slate-800'}`}
            >
              <Icon size={18} />
              {t(s.key)}
            </button>
          )
        })}
        <div className="mt-auto pt-4 border-t border-slate-800">
          <label className="text-xs text-slate-400">API token</label>
          <input
            type="password"
            value={token}
            onChange={(e) => saveToken(e.target.value)}
            placeholder="Unesite API token"
            className="w-full mt-1 p-2 bg-slate-950 border border-slate-700 rounded text-xs"
          />
        </div>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        {message && <div className="mb-4 p-3 bg-slate-800 border border-slate-700 rounded text-sm">{message}</div>}

        {section === 'upload' && (
          <div className="space-y-4 max-w-xl">
            <h2 className="text-xl font-semibold">{t('upload')}</h2>
            <input
              type="file"
              accept="image/*,video/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-slate-700 file:text-white hover:file:bg-slate-600"
            />
            <button
              onClick={handleUpload}
              disabled={loading || !file}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded text-white"
            >
              {loading ? t('processing') : t('upload')}
            </button>
            {uploaded && (
              <div className="p-3 bg-slate-900 border border-slate-700 rounded text-sm">
                <p><strong>Tip:</strong> {uploaded.type}</p>
                <p><strong>Mime:</strong> {uploaded.mime}</p>
                <p><strong>Veličina:</strong> {uploaded.size_bytes} bajtova</p>
                <button onClick={createProject} className="mt-2 px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded text-xs">{t('projects')}: spremi</button>
              </div>
            )}
          </div>
        )}

        {(section === 'imageToAscii' || section === 'videoToAscii' || section === 'animation') && (
          <div className="space-y-4 max-w-2xl">
            <h2 className="text-xl font-semibold">{t(section)}</h2>
            <div className="grid grid-cols-2 gap-4">
              <label className="block">
                {t('width')}
                <input type="number" min={10} max={240} value={width} onChange={(e) => setWidth(Number(e.target.value))} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded" />
              </label>
              <label className="block">
                {t('mode')}
                <select value={mode} onChange={(e) => setMode(e.target.value)} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded">
                  <option value="grayscale">{t('grayscale')}</option>
                  <option value="color">{t('color')}</option>
                  <option value="monochrome">{t('monochrome')}</option>
                </select>
              </label>
              <label className="block">
                {t('palette')}
                <select value={palette} onChange={(e) => setPalette(e.target.value)} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded">
                  {['standard', 'dense', 'minimal', 'blocks', 'binary'].map((p) => <option key={p} value={p}>{t(p)}</option>)}
                </select>
              </label>
              <label className="block">
                {t('background')}
                <select value={background} onChange={(e) => setBackground(e.target.value)} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded">
                  <option value="black">{t('black')}</option>
                  <option value="white">{t('white')}</option>
                  <option value="transparent">{t('transparent')}</option>
                </select>
              </label>
              {section !== 'imageToAscii' && (
                <>
                  <label className="block">
                    {t('fps')}
                    <input type="number" min={1} max={30} value={fps} onChange={(e) => setFps(Number(e.target.value))} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded" />
                  </label>
                  <label className="block">
                    {t('duration')}
                    <input type="number" min={1} max={60} value={maxDuration} onChange={(e) => setMaxDuration(Number(e.target.value))} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded" />
                  </label>
                </>
              )}
              <label className="block">
                {t('outputFormat')}
                <select value={outputFormat} onChange={(e) => setOutputFormat(e.target.value)} className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded">
                  {section === 'imageToAscii' ? (
                    <>
                      <option value="png">PNG</option>
                      <option value="gif">GIF</option>
                      <option value="svg">SVG</option>
                      <option value="html">HTML</option>
                      <option value="txt">TXT</option>
                    </>
                  ) : section === 'animation' ? (
                    <>
                      <option value="gif">GIF</option>
                      <option value="mp4">MP4</option>
                      <option value="webm">WebM</option>
                      <option value="html">HTML</option>
                      <option value="zip">ZIP</option>
                    </>
                  ) : (
                    <>
                      <option value="gif">GIF</option>
                      <option value="mp4">MP4</option>
                      <option value="webm">WebM</option>
                    </>
                  )}
                </select>
              </label>
            </div>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={contrastAdapt} onChange={(e) => setContrastAdapt(e.target.checked)} />
              {t('contrastAdapt')}
            </label>
            {section === 'animation' && (
              <div className="p-3 bg-slate-900 border border-slate-700 rounded">
                <p className="text-sm font-medium mb-2">Efekti</p>
                <div className="flex flex-wrap gap-2">
                  {['pulse', 'flicker', 'scan', 'glitch', 'matrix', 'wave', 'noise', 'fade_in', 'fade_out', 'color_shift'].map((eff) => (
                    <button
                      key={eff}
                      onClick={() => toggleEffect(eff)}
                      className={`px-2 py-1 rounded text-xs border ${effects.includes(eff) ? 'bg-blue-600 border-blue-500' : 'border-slate-600 hover:bg-slate-800'}`}
                    >
                      {eff}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <button
              onClick={section === 'imageToAscii' ? handleImageConvert : section === 'videoToAscii' ? handleVideoConvert : section === 'animation' ? (outputFormat === 'zip' ? handleExport : handleAnimationRender) : handleAnimationRender}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded text-white"
            >
              {loading ? t('processing') : t('convert')}
            </button>
          </div>
        )}

        {section === 'projects' && (
          <div>
            <h2 className="text-xl font-semibold mb-4">{t('projects')}</h2>
            <div className="space-y-2">
              {projects.map((p) => (
                <div key={p.id} className="p-3 bg-slate-900 border border-slate-700 rounded">
                  <p className="font-medium">#{p.id} {p.name}</p>
                  <p className="text-xs text-slate-400">{p.source_type} | {p.updated_at}</p>
                </div>
              ))}
              {projects.length === 0 && <p className="text-slate-400">Nema projekata.</p>}
            </div>
          </div>
        )}

        {section === 'jobs' && (
          <div>
            <h2 className="text-xl font-semibold mb-4">{t('jobs')}</h2>
            <div className="space-y-4">
              {jobs.map((j) => (
                <div key={j.id} className="p-3 bg-slate-900 border border-slate-700 rounded">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium">#{j.id} {j.type}</span>
                    <span className={`text-xs px-2 py-1 rounded ${j.status === 'completed' ? 'bg-green-900 text-green-200' : j.status === 'failed' ? 'bg-red-900 text-red-200' : 'bg-yellow-900 text-yellow-200'}`}>{j.status}</span>
                  </div>
                  <p className="text-xs text-slate-400 mb-2">{j.message} {Math.round(j.progress * 100)}%</p>
                  {j.status === 'completed' && (
                    <div className="mt-2">
                      {renderPreview(j)}
                      <a href={j.output_path.replace('/var/lib/ascii-motion-studio', '/exports')} download className="inline-flex items-center gap-1 mt-2 text-blue-400 hover:text-blue-300 text-sm">
                        <Download size={14} /> {t('download')}
                      </a>
                    </div>
                  )}
                </div>
              ))}
              {jobs.length === 0 && <p className="text-slate-400">Nema poslova.</p>}
            </div>
          </div>
        )}

        {section === 'settings' && (
          <div className="space-y-4 max-w-xl">
            <h2 className="text-xl font-semibold">{t('settings')}</h2>
            <label className="block">
              API token
              <input
                type="password"
                value={token}
                onChange={(e) => saveToken(e.target.value)}
                className="w-full mt-1 p-2 bg-slate-900 border border-slate-700 rounded"
              />
            </label>
            <p className="text-sm text-slate-400">Token se čuva lokalno u pregledniku.</p>
          </div>
        )}
      </main>
    </div>
  )
}
