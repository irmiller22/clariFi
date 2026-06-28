"use client"

import { useEffect, useState } from "react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts"
import { DollarSign, TrendingDown, TrendingUp, CreditCard, Minus } from "lucide-react"
import { formatCurrency } from "@/lib/utils"
import { api, ApiError } from "@/lib/api"
import { SubscriptionsPanel } from "@/components/subscriptions-panel"
import { CashflowPanel } from "@/components/cashflow-panel"
import type {
  AnalyticsSummary,
  CategorySpending,
  TimelineData,
  SpendingTrends,
  TrendDirection,
} from "@/lib/types"

interface AnalyticsDashboardProps {
  summary: AnalyticsSummary
}

const COLORS = [
  "#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8",
  "#82CA9D", "#FFC658", "#FF7C7C", "#8DD1E1", "#D084D0",
]

const TREND_TOOLTIP = {
  backgroundColor: "hsl(var(--background))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "6px",
}

function DirectionIcon({ direction }: { direction: TrendDirection }) {
  if (direction === "up") return <TrendingUp className="h-4 w-4 text-red-500" aria-label="up" />
  if (direction === "down") return <TrendingDown className="h-4 w-4 text-green-500" aria-label="down" />
  return <Minus className="h-4 w-4 text-muted-foreground" aria-label="flat" />
}

export function AnalyticsDashboard({ summary }: AnalyticsDashboardProps) {
  const [categories, setCategories] = useState<CategorySpending[]>([])
  const [timeline, setTimeline] = useState<TimelineData[]>([])
  const [trends, setTrends] = useState<SpendingTrends | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [categoryData, timelineData, trendsData] = await Promise.all([
          api.getCategoryAnalytics(),
          api.getTimelineAnalytics(),
          api.getTrends(),
        ])
        if (cancelled) return
        setCategories(categoryData)
        setTimeline(timelineData)
        setTrends(trendsData)
      } catch (err) {
        if (cancelled) return
        const message = err instanceof ApiError ? err.message : "Failed to load analytics"
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
        Loading analytics…
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

  const topCategories = categories.slice(0, 8)
  const hasSpend = categories.length > 0

  return (
    <div className="space-y-8">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-6 bg-card border border-border rounded-lg">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-lg">
              <TrendingDown className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Spent</p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {formatCurrency(Math.abs(summary.totalSpent))}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
              <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Income</p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {formatCurrency(summary.totalIncome)}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <DollarSign className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Net Amount</p>
              <p className={`text-2xl font-bold ${
                summary.netAmount >= 0
                  ? "text-green-600 dark:text-green-400"
                  : "text-red-600 dark:text-red-400"
              }`}>
                {formatCurrency(summary.netAmount)}
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-lg">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
              <CreditCard className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Transactions</p>
              <p className="text-2xl font-bold">{summary.transactionCount}</p>
              <p className="text-xs text-muted-foreground">
                Avg: {formatCurrency(summary.avgTransactionAmount)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {!hasSpend && (
        <div className="rounded-lg border border-border bg-card p-6 text-center text-muted-foreground">
          No spending to analyze yet.
        </div>
      )}

      {hasSpend && (
        <>
          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Spending by Category</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topCategories} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} interval={0} fontSize={12} />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} fontSize={12} />
                    <Tooltip
                      formatter={(value: number) => [formatCurrency(value), "Amount"]}
                      contentStyle={TREND_TOOLTIP}
                    />
                    <Bar dataKey="amount" fill="#0088FE" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Category Distribution</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categories.slice(0, 6).map((item) => ({
                        name: item.category,
                        value: item.amount,
                      }))}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      fontSize={12}
                    >
                      {categories.slice(0, 6).map((entry, index) => (
                        <Cell key={`cell-${entry.category}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => [formatCurrency(value), "Amount"]}
                      contentStyle={TREND_TOOLTIP}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Timeline Chart */}
          {timeline.length > 1 && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Spending Timeline</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeline} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                    <XAxis dataKey="date" fontSize={12} />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} fontSize={12} />
                    <Tooltip
                      formatter={(value: number, name: string) => [
                        formatCurrency(value),
                        name === "amount" ? "Spend" : "Cumulative",
                      ]}
                      contentStyle={TREND_TOOLTIP}
                    />
                    <Line type="monotone" dataKey="amount" stroke="#0088FE" strokeWidth={2} dot={{ r: 4 }} name="Spend" />
                    <Line type="monotone" dataKey="cumulative" stroke="#00C49F" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4 }} name="Cumulative" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Month-over-month trends */}
          {trends && trends.overall.length > 1 && (
            <div className="bg-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Month-over-Month Trend</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 font-medium">Month</th>
                      <th className="text-right py-2 font-medium">Spend</th>
                      <th className="text-right py-2 font-medium">Change</th>
                      <th className="text-right py-2 font-medium" />
                    </tr>
                  </thead>
                  <tbody>
                    {trends.overall.map((point) => (
                      <tr key={point.month} className="border-b border-border/50">
                        <td className="py-3">{point.month}</td>
                        <td className="text-right py-3 font-medium">{formatCurrency(point.amount)}</td>
                        <td className="text-right py-3 text-muted-foreground">
                          {point.pctChange === null ? "—" : `${point.pctChange.toFixed(1)}%`}
                        </td>
                        <td className="py-3">
                          <div className="flex justify-end">
                            <DirectionIcon direction={point.direction} />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cashflow: income vs spend vs net */}
          <CashflowPanel />

          {/* Recurring subscriptions */}
          <SubscriptionsPanel />

          {/* Category Details Table */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Category Breakdown</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2 font-medium">Category</th>
                    <th className="text-right py-2 font-medium">Amount</th>
                    <th className="text-right py-2 font-medium">Transactions</th>
                    <th className="text-right py-2 font-medium">Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  {categories.map((category, index) => (
                    <tr key={category.category} className="border-b border-border/50">
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                          {category.category}
                        </div>
                      </td>
                      <td className="text-right py-3 font-medium">{formatCurrency(category.amount)}</td>
                      <td className="text-right py-3 text-muted-foreground">{category.count}</td>
                      <td className="text-right py-3 text-muted-foreground">{category.percentage.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
