"use client"

import { useState, useMemo } from "react"
import { Search, ChevronUp, ChevronDown, TrendingDown, TrendingUp } from "lucide-react"
import { formatCurrency, formatDate } from "@/lib/utils"
import type { Transaction } from "@/lib/types"

interface TransactionTableProps {
  transactions: Transaction[]
}

type SortField = "date" | "description" | "amount" | "category"
type SortOrder = "asc" | "desc"

export function TransactionTable({ transactions }: TransactionTableProps) {
  const [searchTerm, setSearchTerm] = useState("")
  const [categoryFilter, setCategoryFilter] = useState<string>("")
  const [typeFilter, setTypeFilter] = useState<string>("")
  const [sortField, setSortField] = useState<SortField>("date")
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc")
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 50

  // Get unique categories and types for filters
  const categories = useMemo(() => {
    const cats = [...new Set(transactions.map(t => t.category).filter(Boolean))]
    return cats.sort()
  }, [transactions])

  const types = useMemo(() => {
    return [...new Set(transactions.map(t => t.type))]
  }, [transactions])

  // Filter and sort transactions
  const filteredAndSorted = useMemo(() => {
    const filtered = transactions.filter(transaction => {
      const matchesSearch = !searchTerm || 
        transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (transaction.category?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
      
      const matchesCategory = !categoryFilter || transaction.category === categoryFilter
      const matchesType = !typeFilter || transaction.type === typeFilter

      return matchesSearch && matchesCategory && matchesType
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
  }, [transactions, searchTerm, categoryFilter, typeFilter, sortField, sortOrder])

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
          className="border border-input rounded-md bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>

        {/* Type Filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-input rounded-md bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <option value="">All Types</option>
          {types.map(type => (
            <option key={type} value={type}>
              {type === "debit" ? "Expenses" : "Income"}
            </option>
          ))}
        </select>
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
              {paginatedTransactions.map((transaction, index) => (
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
                  </td>
                  <td className="p-4 text-sm">
                    <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary text-secondary-foreground text-xs">
                      {transaction.category || "Uncategorized"}
                    </span>
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
              ))}
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