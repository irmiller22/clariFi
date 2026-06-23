import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeToggle } from '@/components/theme-toggle'

describe('ThemeToggle', () => {
  it('renders a toggle button and swaps the icon on click', async () => {
    const user = userEvent.setup()
    const { container } = render(<ThemeToggle />)

    const button = screen.getByRole('button', { name: /toggle theme/i })
    expect(button).toBeInTheDocument()
    // Light theme by default (matchMedia mock reports not-dark) -> moon icon.
    expect(container.querySelector('.lucide-moon')).toBeInTheDocument()

    await user.click(button)
    // Toggled to dark -> sun icon.
    expect(container.querySelector('.lucide-sun')).toBeInTheDocument()
  })
})
