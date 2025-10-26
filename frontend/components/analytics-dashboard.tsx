"use client"

import { useMemo } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts"
import { DollarSign, TrendingDown, TrendingUp, CreditCard } from "lucide-react"
import { formatCurrency } from "@/lib/utils"
import type { Transaction, AnalyticsSummary, CategorySpending, TimelineData } from "@/lib/types"

interface AnalyticsDashboardProps {
  transactions: Transaction[]
  summary: AnalyticsSummary
}

const COLORS = [
  "#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8",
  "#82CA9D", "#FFC658", "#FF7C7C", "#8DD1E1", "#D084D0"
]

export function AnalyticsDashboard({ transactions, summary }: AnalyticsDashboardProps) {
  // Calculate category spending
  const categoryData = useMemo((): CategorySpending[] => {
    const categoryMap = new Map<string, { amount: number, count: number }>()
    
    transactions
      .filter(t => t.type === "debit")
      .forEach(transaction => {
        const category = transaction.category || "Uncategorized"
        const existing = categoryMap.get(category) || { amount: 0, count: 0 }
        categoryMap.set(category, {
          amount: existing.amount + Math.abs(transaction.amount),
          count: existing.count + 1
        })
      })

    const totalSpent = Math.abs(summary.totalSpent)
    
    return Array.from(categoryMap.entries())
      .map(([category, data]) => ({
        category,
        amount: data.amount,
        count: data.count,
        percentage: totalSpent > 0 ? (data.amount / totalSpent) * 100 : 0
      }))
      .sort((a, b) => b.amount - a.amount)
  }, [transactions, summary])

  // Calculate timeline data (monthly aggregation)
  const timelineData = useMemo((): TimelineData[] => {
    const monthlyMap = new Map<string, number>()
    
    transactions.forEach(transaction => {
      const date = new Date(transaction.date)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const existing = monthlyMap.get(monthKey) || 0
      monthlyMap.set(monthKey, existing + transaction.amount)
    })

    const sortedEntries = Array.from(monthlyMap.entries()).sort()
    let cumulative = 0
    
    return sortedEntries.map(([date, amount]) => {
      cumulative += amount
      return {
        date: new Date(date + '-01').toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        amount,
        cumulative
      }
    })
  }, [transactions])

  // Top spending categories for bar chart
  const topCategories = categoryData.slice(0, 8)

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

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Category Spending Bar Chart */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Spending by Category</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topCategories} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="category" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  interval={0}
                  fontSize={12}
                />
                <YAxis 
                  tickFormatter={(value) => formatCurrency(value)}
                  fontSize={12}
                />
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), "Amount"]}
                  labelStyle={{ color: "hsl(var(--foreground))" }}
                  contentStyle={{ 
                    backgroundColor: "hsl(var(--background))", 
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px"
                  }}
                />
                <Bar dataKey="amount" fill="#0088FE" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Distribution Pie Chart */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Category Distribution</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData.slice(0, 6).map(item => ({
                    name: item.category,
                    value: item.amount,
                    percentage: item.percentage
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
                  {categoryData.slice(0, 6).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => [formatCurrency(value), "Amount"]}
                  contentStyle={{ 
                    backgroundColor: "hsl(var(--background))", 
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px"
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Timeline Chart */}
      {timelineData.length > 1 && (
        <div className="bg-card border border-border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Spending Timeline</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelineData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis dataKey="date" fontSize={12} />
                <YAxis tickFormatter={(value) => formatCurrency(value)} fontSize={12} />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    formatCurrency(value), 
                    name === "amount" ? "Monthly Net" : "Cumulative"
                  ]}
                  labelStyle={{ color: "hsl(var(--foreground))" }}
                  contentStyle={{ 
                    backgroundColor: "hsl(var(--background))", 
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "6px"
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="amount" 
                  stroke="#0088FE" 
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="Monthly Net"
                />
                <Line 
                  type="monotone" 
                  dataKey="cumulative" 
                  stroke="#00C49F" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ r: 4 }}
                  name="Cumulative"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

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
              {categoryData.map((category, index) => (
                <tr key={category.category} className="border-b border-border/50">
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      {category.category}
                    </div>
                  </td>
                  <td className="text-right py-3 font-medium">
                    {formatCurrency(category.amount)}
                  </td>
                  <td className="text-right py-3 text-muted-foreground">
                    {category.count}
                  </td>
                  <td className="text-right py-3 text-muted-foreground">
                    {category.percentage.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}