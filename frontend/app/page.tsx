"use client"

import { useState } from "react"
import { UploadIcon, BarChart3, CreditCard, DollarSign } from "lucide-react"
import { UploadZone } from "@/components/upload-zone"
import { TransactionTable } from "@/components/transaction-table"
import { AnalyticsDashboard } from "@/components/analytics-dashboard"
import { ThemeToggle } from "@/components/theme-toggle"
import type { Transaction, AnalyticsSummary } from "@/lib/types"

export default function Home() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [activeTab, setActiveTab] = useState<"upload" | "transactions" | "analytics">("upload")

  const handleUploadSuccess = (data: { transactions: Transaction[], summary: AnalyticsSummary }) => {
    setTransactions(data.transactions)
    setSummary(data.summary)
    setActiveTab("transactions")
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between px-4 lg:px-8">
          <div className="flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            <h1 className="text-xl font-semibold">clariFi</h1>
          </div>
          <div className="flex items-center gap-4">
            <nav className="hidden md:flex items-center gap-6">
              <button
                onClick={() => setActiveTab("upload")}
                className={`text-sm font-medium transition-colors hover:text-foreground/80 ${
                  activeTab === "upload" ? "text-foreground" : "text-foreground/60"
                }`}
              >
                Upload
              </button>
              <button
                onClick={() => setActiveTab("transactions")}
                className={`text-sm font-medium transition-colors hover:text-foreground/80 ${
                  activeTab === "transactions" ? "text-foreground" : "text-foreground/60"
                }`}
                disabled={transactions.length === 0}
              >
                Transactions
              </button>
              <button
                onClick={() => setActiveTab("analytics")}
                className={`text-sm font-medium transition-colors hover:text-foreground/80 ${
                  activeTab === "analytics" ? "text-foreground" : "text-foreground/60"
                }`}
                disabled={!summary}
              >
                Analytics
              </button>
            </nav>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container px-4 py-8 lg:px-8">
        {activeTab === "upload" && (
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold tracking-tight mb-4">
                Analyze Your Spending
              </h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                Upload your credit card CSV files to get detailed insights into your spending patterns, 
                categorize transactions, and track your financial health.
              </p>
            </div>
            <UploadZone onUploadSuccess={handleUploadSuccess} />
            
            {/* Features Section */}
            <div className="grid md:grid-cols-3 gap-6 mt-16">
              <div className="text-center p-6 rounded-lg border border-border/40 bg-card">
                <UploadIcon className="h-8 w-8 mx-auto mb-4 text-primary" />
                <h3 className="font-semibold mb-2">Easy CSV Upload</h3>
                <p className="text-sm text-muted-foreground">
                  Drag and drop your bank CSV files for instant analysis
                </p>
              </div>
              <div className="text-center p-6 rounded-lg border border-border/40 bg-card">
                <BarChart3 className="h-8 w-8 mx-auto mb-4 text-primary" />
                <h3 className="font-semibold mb-2">Smart Analytics</h3>
                <p className="text-sm text-muted-foreground">
                  Get insights into spending patterns and category breakdowns
                </p>
              </div>
              <div className="text-center p-6 rounded-lg border border-border/40 bg-card">
                <DollarSign className="h-8 w-8 mx-auto mb-4 text-primary" />
                <h3 className="font-semibold mb-2">Financial Health</h3>
                <p className="text-sm text-muted-foreground">
                  Track your income, expenses, and net financial position
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === "transactions" && transactions.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Transactions</h2>
              <p className="text-muted-foreground">
                {transactions.length} transaction{transactions.length !== 1 ? "s" : ""} loaded
              </p>
            </div>
            <TransactionTable transactions={transactions} />
          </div>
        )}

        {activeTab === "analytics" && summary && (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold">Analytics Dashboard</h2>
              <p className="text-muted-foreground">
                Financial insights from your uploaded transactions
              </p>
            </div>
            <AnalyticsDashboard transactions={transactions} summary={summary} />
          </div>
        )}
      </main>
    </div>
  )
}