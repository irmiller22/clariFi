"use client"

import { useEffect, useState } from "react"
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { formatCurrency } from "@/lib/utils"
import { api, ApiError } from "@/lib/api"
import type { Cashflow } from "@/lib/types"

const TREND_TOOLTIP = {
  backgroundColor: "hsl(var(--background))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "6px",
}

const SERIES_LABELS: Record<string, string> = {
  income: "Income",
  spend: "Spend",
  net: "Net",
}

export function CashflowPanel() {
  const [cashflow, setCashflow] = useState<Cashflow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await api.getCashflow()
        if (cancelled) return
        setCashflow(data)
      } catch (err) {
        if (cancelled) return
        const message = err instanceof ApiError ? err.message : "Failed to load cashflow"
        setError(message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground" role="status">
        Loading cashflow…
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-300" role="alert">
        {error}
      </div>
    )
  }

  if (cashflow.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-6 text-center text-muted-foreground">
        No cashflow to analyze yet.
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Cashflow</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={cashflow} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis dataKey="month" fontSize={12} />
            <YAxis tickFormatter={(value) => formatCurrency(value)} fontSize={12} />
            <Tooltip
              formatter={(value: number, name: string) => [
                formatCurrency(value),
                SERIES_LABELS[name] ?? name,
              ]}
              contentStyle={TREND_TOOLTIP}
            />
            <Legend formatter={(value: string) => SERIES_LABELS[value] ?? value} />
            <Bar dataKey="income" fill="#00C49F" radius={[4, 4, 0, 0]} name="income" />
            <Bar dataKey="spend" fill="#FF8042" radius={[4, 4, 0, 0]} name="spend" />
            <Line
              type="monotone"
              dataKey="net"
              stroke="#0088FE"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="net"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
