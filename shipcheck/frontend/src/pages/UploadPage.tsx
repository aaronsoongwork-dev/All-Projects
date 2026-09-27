import { useState, useRef } from 'react'
import type { ComparisonField } from '../types'
import {
  surface,
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  faint,
  green,
  greenBg,
} from '../constants/tokens'
import { SectionLabel, Spinner } from '../components/primitives'
import { compareFilesApi } from '../services/api'

export async function extractPdfText(file: File): Promise<string> {
  const pdfjsLib = await import('pdfjs-dist')
  pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).href
  const arrayBuffer = await file.arrayBuffer()
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
  const pages: string[] = []
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    pages.push(content.items.map((item: any) => item.str).join(' '))
  }
  return pages.join('\n')
}

export const FIELD_PATTERNS: { field: string; patterns: RegExp[] }[] = [
  { field: 'Shipper', patterns: [/shipper[:\s]+([^\n]{3,60})/i, /shipped by[:\s]+([^\n]{3,60})/i] },
  { field: 'Consignee', patterns: [/consignee[:\s]+([^\n]{3,60})/i, /to[:\s]+([^\n]{3,60})/i] },
  { field: 'Notify Party', patterns: [/notify\s*(?:party)?[:\s]+([^\n]{3,60})/i, /also notify[:\s]+([^\n]{3,60})/i] },
  { field: 'Port of Loading', patterns: [/port\s*of\s*load(?:ing)?[:\s]+([^\n]{3,40})/i, /pol[:\s]+([^\n]{3,40})/i, /loading\s*port[:\s]+([^\n]{3,40})/i] },
  { field: 'Port of Discharge', patterns: [/port\s*of\s*discharge[:\s]+([^\n]{3,40})/i, /pod[:\s]+([^\n]{3,40})/i, /discharge\s*port[:\s]+([^\n]{3,40})/i] },
  { field: 'Container Count', patterns: [/(\d+)\s*(?:x\s*)?(?:20|40)?(?:ft|')?\s*containers?/i, /no\.?\s*of\s*containers?[:\s]+(\d+)/i, /(\d+)\s*containers?/i] },
  { field: 'Gross Weight (kg)', patterns: [/gross\s*weight[:\s]+([0-9,.\s]+\s*kg)/i, /total\s*weight[:\s]+([0-9,.\s]+\s*kg)/i, /([0-9,]+)\s*kgs?/i] },
]

interface UploadedDoc { file: File; text: string }

function DropZone({ label, doc, onDrop, onClear }: {
  label: string; doc: UploadedDoc | null;
  onDrop: (f: File) => void; onClear: () => void
}) {
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) onDrop(f) }}
      style={{
        flex: 1, border: `2px dashed ${dragging ? navy : doc ? '#86EFAC' : border}`,
        borderRadius: 6, background: dragging ? '#EEF2FF' : doc ? greenBg : surface,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: '40px 24px', cursor: 'pointer', transition: 'all 0.15s',
        minHeight: 200,
      }}
      onClick={() => !doc && fileInputRef.current?.click()}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.xlsx,.txt"
        style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; if (f) onDrop(f) }}
      />
      {doc ? (
        <>
          <div style={{ fontSize: 28, marginBottom: 10 }}>✓</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: green, marginBottom: 4, textAlign: 'center' }}>{doc.file.name}</div>
          <div style={{ fontSize: 11, color: muted, marginBottom: 16 }}>{(doc.file.size / 1024).toFixed(0)} KB · Ready</div>
          <button
            onClick={e => { e.stopPropagation(); onClear() }}
            style={{ fontSize: 11, color: muted, background: 'none', border: `1px solid ${border}`, borderRadius: 3, padding: '4px 10px', cursor: 'pointer' }}
          >
            Remove
          </button>
        </>
      ) : (
        <>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.3 }}>📄</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: ink, marginBottom: 4 }}>{label}</div>
          <div style={{ fontSize: 12, color: muted, marginBottom: 4 }}>Drop file here or click to browse</div>
          <div style={{ fontSize: 11, color: faint }}>PDF, DOCX, XLSX, or TXT</div>
        </>
      )}
    </div>
  )
}

interface UploadPageProps {
  onCompare: (result: ComparisonField[], siName: string, blName: string) => void
}

export function UploadPage({ onCompare }: UploadPageProps) {
  const [si, setSi] = useState<UploadedDoc | null>(null)
  const [bl, setBl] = useState<UploadedDoc | null>(null)
  const [parsing, setParsing] = useState(false)
  const [comparing, setComparing] = useState(false)
  const [error, setError] = useState('')

  async function handleDrop(type: 'si' | 'bl', file: File) {
    const isPdf = file.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      if (type === 'si') setSi({ file, text: '' })
      else setBl({ file, text: '' })
      return
    }
    setParsing(true)
    setError('')
    try {
      const text = await extractPdfText(file)
      if (type === 'si') setSi({ file, text })
      else setBl({ file, text })
    } catch {
      setError(`Could not parse ${file.name}. Make sure it's a valid, unencrypted PDF.`)
    } finally {
      setParsing(false)
    }
  }

  async function handleCompare() {
    if (!si || !bl) return
    setComparing(true)
    setError('')
    try {
      const res = await compareFilesApi(si.file, bl.file)
      onCompare(res.fields, si.file.name, bl.file.name)
    } catch (err: any) {
      setError(`AI Backend Comparison Failed: ${err.message || String(err)}. Please verify the backend service is running.`)
    } finally {
      setComparing(false)
    }
  }

  return (
    <div style={{ padding: 28 }}>
      <h2 style={{ fontFamily: 'Playfair Display, serif', fontSize: 26, fontWeight: 700, color: ink, margin: '0 0 6px' }}>SI vs Bill of Lading</h2>
      <p style={{ fontSize: 13, color: muted, marginBottom: 28 }}>Upload both documents. ShipCheck sends them to the FastAPI AI service to extract and compare the 7 shipping fields using Claude & Vision models.</p>

      {parsing && (
        <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '14px 20px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          <Spinner size={16} color={navy} />
          <span style={{ fontSize: 13, color: muted }}>Parsing file…</span>
        </div>
      )}
      {comparing && (
        <div style={{ border: `1px solid #BFDBFE`, borderRadius: 4, background: '#EFF6FF', padding: '14px 20px', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
          <Spinner size={16} color="#2563EB" />
          <span style={{ fontSize: 13, color: '#1E40AF', fontWeight: 600 }}>Comparing documents with AI backend (extracting & verifying 7 shipment fields)…</span>
        </div>
      )}
      {error && (
        <div style={{ border: `1px solid #FECACA`, borderRadius: 4, background: '#FEF2F2', padding: '12px 16px', marginBottom: 20, fontSize: 13, color: '#991B1B' }}>⚠ {error}</div>
      )}

      <div className="upload-dropzones" style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <DropZone label="Shipping Instruction (SI)" doc={si} onDrop={f => handleDrop('si', f)} onClear={() => setSi(null)} />
        <DropZone label="Draft Bill of Lading (BL)" doc={bl} onDrop={f => handleDrop('bl', f)} onClear={() => setBl(null)} />
      </div>

      <button
        disabled={!si || !bl || parsing || comparing}
        onClick={handleCompare}
        style={{ fontSize: 13, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', padding: '13px 32px', background: si && bl && !parsing && !comparing ? navy : border, color: white, border: 'none', borderRadius: 4, cursor: si && bl && !parsing && !comparing ? 'pointer' : 'not-allowed', opacity: si && bl && !parsing && !comparing ? 1 : 0.7 }}
      >
        {comparing ? 'Comparing with AI…' : 'Compare Documents →'}
      </button>

      <div style={{ marginTop: 32, border: `1px solid ${borderLight}`, borderRadius: 4, background: surface, padding: '16px 20px' }}>
        <SectionLabel>Fields Compared</SectionLabel>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 8 }}>
          {FIELD_PATTERNS.map(f => (
            <div key={f.field} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: muted }}>
              <span style={{ color: green, fontWeight: 700, fontSize: 11 }}>✓</span> {f.field}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

