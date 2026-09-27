import React from 'react'
import {
  surface,
  white,
  border,
  borderLight,
  navy,
  ink,
  muted,
  faint,
} from '../../constants/tokens'
import { SectionLabel, Spinner } from './index'

// ─── Base Skeleton Primitive ──────────────────────────────────────────────────

export interface SkeletonProps {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  style?: React.CSSProperties
  className?: string
}

export function Skeleton({
  width = '100%',
  height = 14,
  borderRadius = 4,
  style = {},
  className = '',
}: SkeletonProps) {
  return (
    <div
      className={`skeleton-shimmer ${className}`}
      style={{
        width,
        height,
        borderRadius,
        display: 'inline-block',
        verticalAlign: 'middle',
        ...style,
      }}
    />
  )
}

// ─── Inbox Skeleton ───────────────────────────────────────────────────────────

export function InboxSkeleton() {
  return (
    <div style={{ padding: 28 }}>
      <SectionLabel>Email Inbox</SectionLabel>

      {/* Cloud Service Connection / Waking Banner */}
      <div
        style={{
          background: surface,
          border: `1px solid ${border}`,
          borderRadius: 4,
          padding: '12px 18px',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <Spinner size={14} color={navy} />
        <span style={{ fontSize: 12, fontWeight: 600, color: navy }}>
          Connecting to backend service & retrieving emails… (Initial instance spin-up may take a few moments)
        </span>
      </div>

      {/* Search & Filter Controls Skeleton */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 24, alignItems: 'center' }}>
        <div style={{ flex: 1, maxWidth: 360 }}>
          <Skeleton height={35} borderRadius={4} />
        </div>
        <Skeleton width={88} height={35} borderRadius={4} />
        <Skeleton width={148} height={35} borderRadius={4} />
        <div style={{ marginLeft: 'auto' }}>
          <Skeleton width={70} height={14} borderRadius={3} />
        </div>
      </div>

      {/* Grouped Category Skeletons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
        {/* Category 1: Document Comparison */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ color: muted, fontSize: 13 }}>—</span>
            <Skeleton width={170} height={12} borderRadius={3} />
            <Skeleton width={30} height={12} borderRadius={3} />
          </div>
          <InboxTableSkeleton rowsCount={4} />
        </div>

        {/* Category 2: New SI Request */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ color: muted, fontSize: 13 }}>—</span>
            <Skeleton width={130} height={12} borderRadius={3} />
            <Skeleton width={30} height={12} borderRadius={3} />
          </div>
          <InboxTableSkeleton rowsCount={2} />
        </div>

        {/* Category 3: General Inquiries */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ color: muted, fontSize: 13 }}>—</span>
            <Skeleton width={100} height={12} borderRadius={3} />
            <Skeleton width={30} height={12} borderRadius={3} />
          </div>
          <InboxTableSkeleton rowsCount={2} />
        </div>
      </div>
    </div>
  )
}

function InboxTableSkeleton({ rowsCount = 3 }: { rowsCount?: number }) {
  return (
    <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${borderLight}`, background: surface }}>
            {['', 'Sender', 'Subject', 'Classification', 'BL Status', 'Date'].map(h => (
              <th
                key={h}
                style={{
                  padding: '11px 16px',
                  textAlign: 'left',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  color: muted,
                }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rowsCount }).map((_, i) => (
            <tr
              key={i}
              style={{
                borderBottom: i < rowsCount - 1 ? `1px solid ${borderLight}` : 'none',
                background: white,
              }}
            >
              {/* Dot placeholder */}
              <td style={{ padding: '14px 16px', width: 16 }}>
                <Skeleton width={7} height={7} borderRadius="50%" />
              </td>

              {/* Sender Name & Email */}
              <td style={{ padding: '14px 16px', width: 180 }}>
                <Skeleton width={i % 2 === 0 ? 110 : 130} height={13} borderRadius={3} style={{ display: 'block', marginBottom: 5 }} />
                <Skeleton width={i % 2 === 0 ? 130 : 95} height={10} borderRadius={3} />
              </td>

              {/* Subject & Snippet */}
              <td style={{ padding: '14px 16px' }}>
                <Skeleton width={i % 2 === 0 ? '78%' : '65%'} height={14} borderRadius={3} style={{ display: 'block', marginBottom: 6 }} />
                <Skeleton width={i % 2 === 0 ? '55%' : '42%'} height={11} borderRadius={3} />
              </td>

              {/* Classification Pill */}
              <td style={{ padding: '14px 16px', width: 160 }}>
                <Skeleton width={125} height={22} borderRadius={3} />
              </td>

              {/* BL Status Pill */}
              <td style={{ padding: '14px 16px', width: 110 }}>
                <Skeleton width={72} height={22} borderRadius={3} />
              </td>

              {/* Date */}
              <td style={{ padding: '14px 16px', width: 85 }}>
                <Skeleton width={50} height={12} borderRadius={3} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Dashboard Skeleton ───────────────────────────────────────────────────────

export function DashboardSkeleton({
  greeting = 'Good day',
  firstName = 'User',
}: {
  greeting?: string
  firstName?: string
}) {
  return (
    <div style={{ padding: 28, flex: 1 }}>
      {/* Greeting Header */}
      <div style={{ marginBottom: 20 }}>
        <h1
          style={{
            fontFamily: 'Playfair Display, serif',
            fontSize: 36,
            fontWeight: 700,
            color: ink,
            lineHeight: 1.1,
            margin: '0 0 14px',
          }}
        >
          {greeting}, <em style={{ fontStyle: 'italic', color: navy }}>{firstName}.</em>
        </h1>

        {/* Status Strip Skeleton (4 cells matching the exact Dashboard strip) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'stretch',
            gap: 0,
            border: `1px solid ${border}`,
            borderRadius: 4,
            overflow: 'hidden',
            marginBottom: 18,
            background: white,
          }}
        >
          {['Emails', 'Doc Checks', 'Mismatches', 'Needs Review'].map((label, i) => (
            <div
              key={label}
              style={{
                flex: 1,
                padding: '12px 18px',
                borderLeft: i > 0 ? `1px solid ${border}` : 'none',
              }}
            >
              <div
                style={{
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  color: faint,
                  marginBottom: 6,
                }}
              >
                {label}
              </div>
              <Skeleton width={38} height={26} borderRadius={3} style={{ display: 'block', marginBottom: 5 }} />
              <Skeleton width={56} height={10} borderRadius={3} />
            </div>
          ))}
        </div>

        {/* Cold Start / Waking Notice Banner */}
        <div
          style={{
            background: surface,
            border: `1px solid ${border}`,
            borderRadius: 4,
            padding: '12px 18px',
            marginBottom: 18,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <Spinner size={14} color={navy} />
          <span style={{ fontSize: 12, fontWeight: 600, color: navy }}>
            Connecting to backend service & fetching recent shipping records…
          </span>
        </div>
      </div>

      {/* Main Grid: Recent Activity + Side Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
        {/* Left Column: Recent Activity Skeleton */}
        <div>
          <SectionLabel>Recent Activity</SectionLabel>
          <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  padding: '13px 20px',
                  borderBottom: i < 5 ? `1px solid ${borderLight}` : 'none',
                }}
              >
                {/* Avatar */}
                <Skeleton width={28} height={28} borderRadius={4} style={{ flexShrink: 0, marginTop: 1 }} />

                {/* Content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <Skeleton width={i % 2 === 0 ? '65%' : '75%'} height={14} borderRadius={3} />
                    <Skeleton width={40} height={10} borderRadius={3} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Skeleton width={90} height={11} borderRadius={3} />
                    <Skeleton width={68} height={18} borderRadius={3} />
                    <Skeleton width={52} height={18} borderRadius={3} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Actions & Status Skeleton */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Quick Actions Skeleton */}
          <div>
            <SectionLabel>Quick Actions</SectionLabel>
            <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
              <Skeleton height={38} borderRadius={4} />
              <Skeleton height={38} borderRadius={4} />
            </div>
          </div>

          {/* System Overview Skeleton */}
          <div>
            <SectionLabel>System Status</SectionLabel>
            <div style={{ border: `1px solid ${border}`, borderRadius: 4, background: white, padding: '16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Skeleton width={80} height={12} borderRadius={3} />
                <Skeleton width={60} height={12} borderRadius={3} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Skeleton width={90} height={12} borderRadius={3} />
                <Skeleton width={50} height={12} borderRadius={3} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Skeleton width={75} height={12} borderRadius={3} />
                <Skeleton width={65} height={12} borderRadius={3} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Review Skeleton ──────────────────────────────────────────────────────────

export function ReviewSkeleton() {
  return (
    <div style={{ padding: 28 }}>
      <SectionLabel>Human Review Queue</SectionLabel>

      <div
        style={{
          background: surface,
          border: `1px solid ${border}`,
          borderRadius: 4,
          padding: '12px 18px',
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <Spinner size={14} color={navy} />
        <span style={{ fontSize: 12, fontWeight: 600, color: navy }}>
          Checking review queue and fetching pending discrepancy records…
        </span>
      </div>

      <div style={{ border: `1px solid ${border}`, borderRadius: 4, overflow: 'hidden', background: white }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: surface, borderBottom: `1px solid ${borderLight}` }}>
              {['Email / Document', 'Sender', 'Received', ''].map(h => (
                <th
                  key={h}
                  style={{
                    padding: '10px 20px',
                    textAlign: 'left',
                    fontSize: 9,
                    fontWeight: 700,
                    letterSpacing: '0.14em',
                    textTransform: 'uppercase',
                    color: muted,
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 4 }).map((_, i) => (
              <tr key={i} style={{ borderBottom: i < 3 ? `1px solid ${borderLight}` : 'none' }}>
                <td style={{ padding: '13px 20px', maxWidth: 320 }}>
                  <Skeleton width="80%" height={14} borderRadius={3} style={{ display: 'block', marginBottom: 5 }} />
                  <Skeleton width="55%" height={11} borderRadius={3} />
                </td>
                <td style={{ padding: '13px 20px' }}>
                  <Skeleton width={110} height={12} borderRadius={3} />
                </td>
                <td style={{ padding: '13px 20px' }}>
                  <Skeleton width={60} height={11} borderRadius={3} />
                </td>
                <td style={{ padding: '13px 20px', textAlign: 'right' }}>
                  <Skeleton width={68} height={24} borderRadius={3} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
