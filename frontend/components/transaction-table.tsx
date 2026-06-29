"use client"

import { useState, useMemo } from "react"
import { Search, ChevronUp, ChevronDown, TrendingDown, TrendingUp, Plus, Sparkles } from "lucide-react"
import { formatCurrency, formatDate } from "@/lib/utils"
import type { Transaction } from "@/lib/types"
import { UNCATEGORIZED, suggestCategory } from "@/lib/categories"

interface TransactionTableProps {
  transactions: Transaction[]
  availableCategories: string[]
  onCategorize: (transactionIds: string[], category: string) => void
  onAddCategory: (category: string) => void
}

type SortField = "date" | "description" | "amount" | "category"
type SortOrder = "asc" | "desc"

// Money-movement kinds are excluded from spend analytics; flag them in the list.
const KIND_LABEL: Record<string, string> = {
  transfer: "Transfer",
  card_payment: "Card payment",
  fee: "Fee",
}

// The merchant identity used to group transactions for "apply to all from this
// merchant" and for category suggestions: prefer the normalized merchant, fall
// back to the raw description.
function merchantKey(t: Transaction): string {
  return (t.merchant || t.description).toLowerCase()
}

export function TransactionTable({
  transactions,
  availableCategories,
  onCategorize,
  onAddCategory,
}: TransactionTableProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [categoryFilter, setCategoryFilter] = useState<string>("")
  const [typeFilter, setTypeFilter] = useState<string>("")
  const [accountFilter, setAccountFilter] = useState<string>("")
  const [sortField, setSortField] = useState<SortField>("date")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [currentPage, setCurrentPage] = useState(1)
  const [newCategory, setNewCategory] = useState("")
  const itemsPerPage = 50

  // Get unique categories and types for filters
  const categories = useMemo(() => {
    const cats = [...new Set(transactions.map(t => t.category).filter(Boolean))]
    return cats.sort()
  }, [transactions])

  const types = useMemo(() => {
    return [...new Set(transactions.map(t => t.type))]
  }, [transactions])

  const accounts = useMemo(() => {
    return [...new Set(transactions.map(t => t.account).filter(Boolean))].sort()
  }, [transactions])

  // Map each merchant identity to the ids of every transaction sharing it, so a
  // single tag can be applied across all of them in one click.
  const idsByMerchant = useMemo(() => {
    const map = new Map<string, string[]>()
    for (const t of transactions) {
      const key = merchantKey(t)
      const ids = map.get(key)
      if (ids) ids.push(t.id)
      else map.set(key, [t.id])
    }
    return map
  }, [transactions])

  // Count of transactions still lacking a category — drives the suggestion CTA.
  const uncategorizedCount = useMemo(
    () => transactions.filter(t => !t.category).length,
    [transactions]
  )

  // Filter and sort transactions
  const filteredAndSorted = useMemo(() => {
    const filtered = transactions.filter(transaction => {
      const matchesSearch = !searchTerm ||
        transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (transaction.category?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)

      const matchesCategory = !categoryFilter ||
        (categoryFilter === UNCATEGORIZED ? !transaction.category : transaction.category === categoryFilter)
      const matchesType = !typeFilter || transaction.type === typeFilter
      const matchesAccount = !accountFilter || transaction.account === accountFilter

      return matchesSearch && matchesCategory && matchesType && matchesAccount
    })

    filtered.sort((a, b) => {
      let aVal: string | number | Date = a[sortField] || ""
      let bVal: string | number | Date = b[sortField] || ""

      if (sortField === "date") {
        aVal = new Date(aVal as string).getTime()
        bVal = new Date(bVal as string).getTime()
      } else if (sortField === "amount") {
        aVal = Math.abs(aVal as number)
        bVal = Math.abs(bVal as number)
      } else {
        aVal = (aVal as string)?.toLowerCase() || ""
        bVal = (bVal as string)?.toLowerCase() || ""
      }

      if (aVal < bVal) return sortOrder === "asc" ? -1 : 1
      if (aVal > bVal) return sortOrder === "asc" ? 1 : -1
      return 0
    })

    return filtered
  }, [transactions, searchTerm, categoryFilter, typeFilter, accountFilter, sortField, sortOrder])

  // Pagination
  const totalPages = Math.ceil(filteredAndSorted.length / itemsPerPage)
  const paginatedTransactions = filteredAndSorted.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortOrder("asc")
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null
    return sortOrder === "asc" ?
      <ChevronUp className="h-4 w-4" /> :
      <ChevronDown className="h-4 w-4" />
  }

  const handleAddCategory = () => {
    const trimmed = newCategory.trim()
    if (!trimmed) return
    onAddCategory(trimmed)
    setNewCategory("")
  }

  // Tag every uncategorized transaction whose merchant/description maps to a
  // seed rule, in one pass.
  const handleAutoSuggestAll = () => {
    const byCategory = new Map<string, string[]>()
    for (const t of transactions) {
      if (t.category) continue
      const suggestion = suggestCategory(t.merchant || t.description)
      if (!suggestion) continue
      const ids = byCategory.get(suggestion)
      if (ids) ids.push(t.id)
      else byCategory.set(suggestion, [t.id])
    }
    for (const [category, ids] of byCategory) {
      onCategorize(ids, category)
    }
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
        </div>

        {/* Category Filter */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          aria-label="Filter by category"
          className="border border-input rounded-md bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <option value="">All Categories</option>
          <option value={UNCATEGORIZED}>{UNCATEGORIZED}</option>
          {categories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>

        {/* Type Filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          aria-label="Filter by type"
          className="border border-input rounded-md bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <option value="">All Types</option>
          {types.map(type => (
            <option key={type} value={type}>
              {type === "debit" ? "Expenses" : "Income"}
            </option>
          ))}
        </select>

        {/* Account Filter (only when multiple accounts are present) */}
        {accounts.length > 1 && (
          <select
            value={accountFilter}
            onChange={(e) => setAccountFilter(e.target.value)}
            aria-label="Filter by account"
            className="border border-input rounded-md bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <option value="">All Accounts</option>
            {accounts.map(account => (
              <option key={account} value={account}>{account}</option>
            ))}
          </select>
        )}
      </div>

      {/* Categorization controls */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Add a category…"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault()
                handleAddCategory()
              }
            }}
            aria-label="New category name"
            className="w-44 px-3 py-2 border border-input rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          />
          <button
            type="button"
            onClick={handleAddCategory}
            className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-input rounded-md hover:bg-accent"
          >
            <Plus className="h-4 w-4" />
            Add
          </button>
        </div>

        {uncategorizedCount > 0 && (
          <button
            type="button"
            onClick={handleAutoSuggestAll}
            className="inline-flex items-center gap-1 px-3 py-2 text-sm border border-input rounded-md hover:bg-accent"
          >
            <Sparkles className="h-4 w-4 text-primary" />
            Auto-categorize ({uncategorizedCount} uncategorized)
          </button>
        )}
      </div>

      {/* Results Info */}
      <div className="text-sm text-muted-foreground">
        Showing {paginatedTransactions.length} of {filteredAndSorted.length} transactions
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th
                  className="text-left p-4 font-medium cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={() => handleSort("date")}
                >
                  <div className="flex items-center gap-2">
                    Date
                    {getSortIcon("date")}
                  </div>
                </th>
                <th
                  className="text-left p-4 font-medium cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={() => handleSort("description")}
                >
                  <div className="flex items-center gap-2">
                    Description
                    {getSortIcon("description")}
                  </div>
                </th>
                <th
                  className="text-left p-4 font-medium cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={() => handleSort("category")}
                >
                  <div className="flex items-center gap-2">
                    Category
                    {getSortIcon("category")}
                  </div>
                </th>
                <th className="text-left p-4 font-medium">Account</th>
                <th
                  className="text-right p-4 font-medium cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={() => handleSort("amount")}
                >
                  <div className="flex items-center justify-end gap-2">
                    Amount
                    {getSortIcon("amount")}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {paginatedTransactions.map((transaction, index) => {
                const sharedIds = idsByMerchant.get(merchantKey(transaction)) ?? [transaction.id]
                const suggestion = !transaction.category
                  ? suggestCategory(transaction.merchant || transaction.description)
                  : undefined
                return (
                  <tr
                    key={transaction.id}
                    className={`border-t border-border hover:bg-muted/25 transition-colors ${
                      index % 2 === 0 ? "bg-background" : "bg-muted/10"
                    }`}
                  >
                    <td className="p-4 text-sm">
                      {formatDate(transaction.date)}
                    </td>
                    <td className="p-4 text-sm font-medium">
                      {transaction.description}
                      {transaction.kind && KIND_LABEL[transaction.kind] && (
                        <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
                          {KIND_LABEL[transaction.kind]}
                        </span>
                      )}
                    </td>
                    <td className="p-4 text-sm">
                      <div className="flex flex-col gap-1.5">
                        <select
                          value={transaction.category || ""}
                          onChange={(e) =>
                            onCategorize([transaction.id], e.target.value)
                          }
                          aria-label={`Category for ${transaction.description}`}
                          className="w-40 border border-input rounded-md bg-background px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1"
                        >
                          <option value="">{UNCATEGORIZED}</option>
                          {availableCategories.map(category => (
                            <option key={category} value={category}>{category}</option>
                          ))}
                        </select>

                        {suggestion && (
                          <button
                            type="button"
                            onClick={() => onCategorize([transaction.id], suggestion)}
                            className="inline-flex w-fit items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] text-primary hover:bg-primary/20"
                          >
                            <Sparkles className="h-3 w-3" />
                            Suggest: {suggestion}
                          </button>
                        )}

                        {transaction.category && sharedIds.length > 1 && (
                          <button
                            type="button"
                            onClick={() =>
                              onCategorize(sharedIds, transaction.category as string)
                            }
                            className="w-fit text-[11px] text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                          >
                            Apply to all {sharedIds.length} from this merchant
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">
                      {transaction.account || "—"}
                    </td>
                    <td className="p-4 text-sm text-right">
                      <div className="flex items-center justify-end gap-1">
                        {transaction.type === "debit" ? (
                          <TrendingDown className="h-3 w-3 text-red-500" />
                        ) : (
                          <TrendingUp className="h-3 w-3 text-green-500" />
                        )}
                        <span className={
                          transaction.type === "debit" ? "text-red-600 dark:text-red-400" : "text-green-600 dark:text-green-400"
                        }>
                          {transaction.type === "debit" ? "-" : "+"}
                          {formatCurrency(Math.abs(transaction.amount))}
                        </span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm border border-input rounded hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm border border-input rounded hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
