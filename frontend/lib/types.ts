export interface Transaction {
  id: string
  date: string
  description: string
  merchant?: string
  amount: number
  category?: string
  type: 'debit' | 'credit'
  kind?: 'spending' | 'income' | 'transfer' | 'card_payment' | 'fee'
  account?: string
}

export interface AnalyticsSummary {
  totalSpent: number
  totalIncome: number
  netAmount: number
  transactionCount: number
  avgTransactionAmount: number
}

export interface CategorySpending {
  category: string
  amount: number
  count: number
  percentage: number
}

export interface TimelineData {
  date: string
  amount: number
  cumulative: number
}

export interface UploadResponse {
  success: boolean
  message: string
  transactions?: Transaction[]
  summary?: AnalyticsSummary
}

export type TrendDirection = 'up' | 'down' | 'flat'

export interface MonthlyTrend {
  month: string
  amount: number
  delta: number
  pctChange: number | null
  direction: TrendDirection
}

export interface CategoryTrend {
  category: string
  points: MonthlyTrend[]
}

export interface SpendingTrends {
  overall: MonthlyTrend[]
  byCategory: CategoryTrend[]
}

export interface MerchantSpending {
  merchant: string
  amount: number
  count: number
}

export interface RecurringCharge {
  merchant: string
  cadence: string
  typicalAmount: number
  occurrences: number
  lastDate: string
  nextExpectedDate: string
}

export interface Anomaly {
  date: string
  description: string
  category: string
  amount: number
  categoryMedian: number
}

export interface RollingAverage {
  month: string
  spend: number
  movingAverage: number
}

export interface Cashflow {
  month: string
  income: number
  spend: number
  net: number
}