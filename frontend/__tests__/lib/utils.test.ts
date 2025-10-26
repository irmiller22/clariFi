import { cn, formatCurrency, formatDate } from '@/lib/utils'

describe('Utility Functions', () => {
  describe('cn (className utility)', () => {
    it('merges class names correctly', () => {
      expect(cn('bg-red-500', 'text-white')).toBe('bg-red-500 text-white')
    })

    it('handles conditional classes', () => {
      expect(cn('base-class', true && 'conditional-class')).toBe('base-class conditional-class')
      expect(cn('base-class', false && 'conditional-class')).toBe('base-class')
    })

    it('handles Tailwind CSS conflicts', () => {
      expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500')
      expect(cn('p-4', 'px-2')).toBe('p-4 px-2')
    })

    it('handles arrays and objects', () => {
      expect(cn(['class1', 'class2'], { 'class3': true, 'class4': false }))
        .toBe('class1 class2 class3')
    })

    it('handles undefined and null values', () => {
      expect(cn('class1', undefined, null, 'class2')).toBe('class1 class2')
    })
  })

  describe('formatCurrency', () => {
    it('formats positive amounts correctly', () => {
      expect(formatCurrency(100)).toBe('$100.00')
      expect(formatCurrency(1234.56)).toBe('$1,234.56')
      expect(formatCurrency(0)).toBe('$0.00')
    })

    it('formats negative amounts correctly', () => {
      expect(formatCurrency(-100)).toBe('-$100.00')
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56')
    })

    it('handles decimal precision', () => {
      expect(formatCurrency(100.1)).toBe('$100.10')
      expect(formatCurrency(100.123)).toBe('$100.12')
      expect(formatCurrency(100.999)).toBe('$101.00')
    })

    it('handles large amounts', () => {
      expect(formatCurrency(1000000)).toBe('$1,000,000.00')
      expect(formatCurrency(1234567.89)).toBe('$1,234,567.89')
    })

    it('handles very small amounts', () => {
      expect(formatCurrency(0.01)).toBe('$0.01')
      expect(formatCurrency(0.001)).toBe('$0.00')
    })
  })

  describe('formatDate', () => {
    it('formats Date objects correctly', () => {
      const date = new Date('2024-01-15T10:30:00Z')
      const formatted = formatDate(date)
      expect(formatted).toMatch(/Jan 1[45], 2024/) // Accounting for timezone differences
    })

    it('formats ISO date strings correctly', () => {
      const formatted = formatDate('2024-01-15')
      expect(formatted).toMatch(/Jan 1[45], 2024/) // Accounting for timezone differences
    })

    it('formats MM/DD/YYYY strings correctly', () => {
      const formatted = formatDate('01/15/2024')
      expect(formatted).toMatch(/Jan 1[45], 2024/)
    })

    it('handles different date formats', () => {
      expect(formatDate('2024-12-25')).toMatch(/Dec 2[45], 2024/)
      expect(formatDate('12/25/2024')).toMatch(/Dec 2[45], 2024/)
    })

    it('handles edge cases', () => {
      // New Year's Day (more flexible to handle timezone differences)
      const newYear = formatDate('2024-01-01T12:00:00Z')
      expect(newYear).toMatch(/Jan \d{1,2}, 2024/)
      
      // Leap year
      const leapYear = formatDate('2024-02-29T12:00:00Z')
      expect(leapYear).toMatch(/Feb \d{1,2}, 2024/)
      
      // End of year
      const endYear = formatDate('2024-12-31T12:00:00Z')
      expect(endYear).toMatch(/Dec \d{1,2}, 2024/)
    })

    it('maintains consistent format structure', () => {
      const formatted = formatDate('2024-06-15')
      
      // Should match pattern: "Mon DD, YYYY"
      expect(formatted).toMatch(/^[A-Z][a-z]{2} \d{1,2}, \d{4}$/)
    })
  })

  describe('Edge cases and error handling', () => {
    it('handles formatCurrency with NaN', () => {
      expect(formatCurrency(NaN)).toBe('$NaN')
    })

    it('handles formatCurrency with Infinity', () => {
      expect(formatCurrency(Infinity)).toBe('$∞')
    })

    it('handles formatDate with invalid dates', () => {
      expect(() => formatDate('invalid-date')).not.toThrow()
      expect(formatDate('invalid-date')).toBe('Invalid Date')
    })

    it('handles formatDate with empty string', () => {
      expect(() => formatDate('')).not.toThrow()
      expect(formatDate('')).toBe('Invalid Date')
    })
  })
})