# CLAUDE.md Template: React + TypeScript + Vite

> Optimized for AI-assisted development with Claude Code

## Project Overview

This is a [React + TypeScript + Vite](https://vitejs.dev/) project.

## Tech Stack

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Testing**: Vitest + React Testing Library
- **Linting**: ESLint + Prettier

## Project Structure

```
src/
├── components/     # Reusable UI components
│   ├── ui/         # Base UI components (Button, Input, etc.)
│   └── features/   # Feature-specific components
├── hooks/          # Custom React hooks
├── lib/            # Utility functions
├── pages/          # Page components (if using routing)
├── services/       # API calls and external services
├── types/          # TypeScript type definitions
└── App.tsx         # Root component
```

## AI Assistant Guidelines

### Code Style

- Use functional components with hooks
- Prefer named exports: `export function Component() {}`
- Use TypeScript strict mode
- Follow ESLint + Prettier rules

### Component Pattern

```typescript
// components/ui/Button.tsx
import { type ButtonHTMLAttributes, forwardRef } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', className = '', children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`btn btn-${variant} ${className}`}
        {...props}
      >
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
```

### Hook Pattern

```typescript
// hooks/useLocalStorage.ts
import { useState, useEffect } from 'react'

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.error(error)
      return initialValue
    }
  })

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(storedValue))
    } catch (error) {
      console.error(error)
    }
  }, [key, storedValue])

  return [storedValue, setStoredValue] as const
}
```

### Testing Pattern

```typescript
// components/ui/Button.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('calls onClick when clicked', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click me</Button>)
    
    await userEvent.click(screen.getByRole('button'))
    
    expect(onClick).toHaveBeenCalledOnce()
  })
})
```

## Common Tasks

### Add a new component

1. Create `src/components/ui/NewComponent.tsx`
2. Add TypeScript interface
3. Export from `src/components/ui/index.ts`
4. Create test file `NewComponent.test.tsx`
5. Run `npm test` to verify

### Add a new hook

1. Create `src/hooks/useNewHook.ts`
2. Add TypeScript return type
3. Export from `src/hooks/index.ts`
4. Create test file `useNewHook.test.ts`

### Add a new API service

1. Create `src/services/newService.ts`
2. Define types in `src/types/newService.ts`
3. Use fetch or axios for API calls
4. Add error handling

## Performance Guidelines

- Use `React.memo()` for expensive components
- Use `useMemo()` and `useCallback()` judiciously
- Lazy load pages: `const Page = lazy(() => import('./Page'))`
- Optimize images: use WebP, lazy load, responsive sizes

## Accessibility

- Use semantic HTML elements
- Add ARIA labels when needed
- Ensure keyboard navigation works
- Test with screen readers

## Deployment

- Build: `npm run build`
- Preview: `npm run preview`
- Deploy to: Vercel, Netlify, or GitHub Pages

---

**Built with Claude Code** 🤖
