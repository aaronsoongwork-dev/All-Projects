import { useState, useEffect } from 'react'
import {
  white,
  border,
  navy,
  ink,
  muted,
  faint,
  green,
  greenBg,
} from '../constants/tokens'
import { SectionLabel, Spinner } from '../components/primitives'

interface ProcessingPageProps {
  onDone: () => void
}

export function ProcessingPage({ onDone }: ProcessingPageProps) {
  const [step, setStep] = useState(0)
  useEffect(() => {
    const t1 = setTimeout(() => setStep(1), 800)
    const t2 = setTimeout(() => setStep(2), 1700)
    const t3 = setTimeout(() => { setStep(3); setTimeout(onDone, 600) }, 2600)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [onDone])

  const steps = [
    { label: 'Email classified', done: true },
    { label: 'Shipping Instruction identified', done: true },
    { label: 'Bill of Lading identified', done: true },
    { label: 'Extracting shipment fields', done: step >= 1 },
    { label: 'Comparing SI and BL', done: step >= 2 },
    { label: 'Preparing report', done: step >= 3 },
  ]
  const cur = steps.findIndex(s => !s.done)

  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '40px 48px', width: '100%', maxWidth: 400 }}>
        <SectionLabel>Processing Documents</SectionLabel>
        <div style={{ fontFamily: 'Playfair Display, serif', fontSize: 22, fontWeight: 700, color: ink, marginBottom: 6 }}>Extracting fields</div>
        <p style={{ fontSize: 12, color: muted, marginBottom: 28 }}>Comparing 7 shipment fields across SI and BL</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {steps.map((s, i) => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {s.done
                ? <span style={{ width: 18, height: 18, borderRadius: '50%', background: greenBg, border: `1px solid #86EFAC`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, color: green, flexShrink: 0 }}>✓</span>
                : i === cur
                  ? <Spinner size={18} color={navy} />
                  : <span style={{ width: 18, height: 18, borderRadius: '50%', border: `1px solid ${border}`, flexShrink: 0, display: 'block' }} />
              }
              <span style={{ fontSize: 13, color: s.done ? ink : i === cur ? navy : faint, fontWeight: i === cur ? 600 : 400 }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

