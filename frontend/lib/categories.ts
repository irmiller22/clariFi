// Client-side categorization (LAT-100). In-session only: the suggestion
// dictionary and category list live in memory; a persistent rules store
// (LAT-101) and AI suggestions for unknowns (LAT-102) come later.

// The built-in categories a user can tag a transaction with. Custom categories
// the user adds at runtime are merged on top of these in the UI.
export const DEFAULT_CATEGORIES = [
  'Groceries',
  'Dining',
  'Shopping',
  'Transportation',
  'Travel',
  'Entertainment',
  'Health',
  'Utilities',
  'Housing',
  'Subscriptions',
  'Income',
  'Transfers',
  'Fees',
  'Other',
] as const

// The label used for a transaction that has not been categorized yet.
export const UNCATEGORIZED = 'Uncategorized'

// Seed merchant→category rules. Keys are matched as case-insensitive substrings
// against a transaction's merchant (preferred) or description. Ordered most- to
// least-specific within each category isn't required — `suggestCategory` returns
// the first rule that matches, so keep genuinely ambiguous prefixes out.
const MERCHANT_RULES: ReadonlyArray<readonly [pattern: string, category: string]> = [
  // Groceries
  ['whole foods', 'Groceries'],
  ['trader joe', 'Groceries'],
  ['safeway', 'Groceries'],
  ['kroger', 'Groceries'],
  ['costco', 'Groceries'],
  ['wegmans', 'Groceries'],
  ['aldi', 'Groceries'],
  ['publix', 'Groceries'],
  // Dining
  ['starbucks', 'Dining'],
  ['mcdonald', 'Dining'],
  ['chipotle', 'Dining'],
  ['doordash', 'Dining'],
  ['uber eats', 'Dining'],
  ['grubhub', 'Dining'],
  ['restaurant', 'Dining'],
  ['coffee', 'Dining'],
  ['pizza', 'Dining'],
  // Transportation
  ['uber', 'Transportation'],
  ['lyft', 'Transportation'],
  ['shell', 'Transportation'],
  ['chevron', 'Transportation'],
  ['exxon', 'Transportation'],
  ['parking', 'Transportation'],
  ['transit', 'Transportation'],
  // Travel
  ['airlines', 'Travel'],
  ['airline', 'Travel'],
  ['hotel', 'Travel'],
  ['airbnb', 'Travel'],
  ['marriott', 'Travel'],
  ['delta air', 'Travel'],
  ['united air', 'Travel'],
  // Shopping
  ['amazon', 'Shopping'],
  ['target', 'Shopping'],
  ['walmart', 'Shopping'],
  ['best buy', 'Shopping'],
  ['ebay', 'Shopping'],
  // Entertainment
  ['spotify', 'Subscriptions'],
  ['netflix', 'Subscriptions'],
  ['hulu', 'Subscriptions'],
  ['disney+', 'Subscriptions'],
  ['hbo', 'Subscriptions'],
  ['youtube premium', 'Subscriptions'],
  ['apple.com/bill', 'Subscriptions'],
  ['prime video', 'Subscriptions'],
  ['cinema', 'Entertainment'],
  ['amc ', 'Entertainment'],
  // Health
  ['pharmacy', 'Health'],
  ['cvs', 'Health'],
  ['walgreens', 'Health'],
  ['fitness', 'Health'],
  ['gym', 'Health'],
  // Utilities
  ['comcast', 'Utilities'],
  ['xfinity', 'Utilities'],
  ['verizon', 'Utilities'],
  ['at&t', 'Utilities'],
  ['t-mobile', 'Utilities'],
  ['pg&e', 'Utilities'],
  ['electric', 'Utilities'],
  ['water', 'Utilities'],
]

/**
 * Suggest a category for a transaction from its merchant/description using the
 * seed rule set. Returns `undefined` when no rule matches (the caller leaves it
 * Uncategorized; AI suggestions for these arrive in LAT-102).
 */
export function suggestCategory(
  merchantOrDescription: string | undefined | null
): string | undefined {
  if (!merchantOrDescription) return undefined
  const haystack = merchantOrDescription.toLowerCase()
  for (const [pattern, category] of MERCHANT_RULES) {
    if (haystack.includes(pattern)) return category
  }
  return undefined
}
