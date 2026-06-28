"use client"

import { useEffect, useState } from "react"
import { CreditCard } from "lucide-react"
import { formatCurrency, formatDate } from "@/lib/utils"
import { api, ApiError } from "@/lib/api"
import type { RecurringCharge } from "@/lib/types"

const WEEKS_PER_MONTH = 52 / 12

// Normalize a charge's typical amount to a monthly-equivalent cost so we can
// compare and total across cadences. Weekly charges are scaled by 52/12;
// everything else is treated as already roughly monthly.
function monthlyEquivalent(charge: RecurringCharge): number {
  if (charge.cadence.toLowerCase() === "weekly") {
    return charge.typicalAmount * WEEKS_PER_MONTH
  }
  return charge.typicalAmount
}

export function SubscriptionsPanel() {
  const [charges, setCharges] = useState<RecurringCharge[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await api.getRecurring()
        if (cancelled) return
        setCharges(data)
      } catch (err) {
        if (cancelled) return
        const message = err instanceof ApiError ? err.message : "Failed to load subscriptions"
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
        Loading subscriptions…
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

  if (charges.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-6 text-center text-muted-foreground">
        No recurring subscriptions detected yet.
      </div>
    )
  }

  const sorted = [...charges].sort((a, b) => monthlyEquivalent(b) - monthlyEquivalent(a))
  const monthlyTotal = sorted.reduce((sum, charge) => sum + monthlyEquivalent(charge), 0)

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
          <CreditCard className="h-6 w-6 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Subscriptions</h3>
          <p className="text-sm text-muted-foreground">
            ≈ {formatCurrency(monthlyTotal)}/mo across {sorted.length}{" "}
            {sorted.length === 1 ? "subscription" : "subscriptions"}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 font-medium">Merchant</th>
              <th className="text-left py-2 font-medium">Cadence</th>
              <th className="text-right py-2 font-medium">Typical Amount</th>
              <th className="text-right py-2 font-medium">Next Expected</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((charge) => (
              <tr key={charge.merchant} className="border-b border-border/50">
                <td className="py-3">{charge.merchant}</td>
                <td className="py-3 capitalize text-muted-foreground">{charge.cadence}</td>
                <td className="text-right py-3 font-medium">
                  {formatCurrency(charge.typicalAmount)}
                </td>
                <td className="text-right py-3 text-muted-foreground">
                  {formatDate(charge.nextExpectedDate)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
