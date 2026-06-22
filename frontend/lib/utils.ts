import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

export function formatDate(date: string | Date): string {
  try {
    // An ISO date-only string ("YYYY-MM-DD") is parsed by `new Date()` as UTC
    // midnight, which renders as the previous day in negative-offset timezones.
    // Anchor it to UTC on both parse and format so it always shows the input day.
    const isoDateOnly = typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date)
    const dateObj = isoDateOnly ? new Date(`${date}T00:00:00Z`) : new Date(date)
    if (isNaN(dateObj.getTime())) {
      return 'Invalid Date'
    }
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      ...(isoDateOnly ? { timeZone: 'UTC' } : {}),
    }).format(dateObj)
  } catch {
    return 'Invalid Date'
  }
}