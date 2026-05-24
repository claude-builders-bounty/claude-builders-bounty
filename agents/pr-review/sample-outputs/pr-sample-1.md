## 🤖 PR Review

### Summary
This PR refactors the user authentication module from class-based components to React hooks, consolidating session management logic into a custom `useAuth` hook. It also migrates the token refresh logic from `setTimeout` intervals to a more reliable `requestAnimationFrame`-based approach with proper cleanup. The changes affect 12 files across the auth subsystem.

### ⚠️ Risks
- The `useAuth` hook does not handle the race condition where a token refresh is in progress while the user logs out — this could leave stale requests in flight.
- Removing the `AuthProvider` wrapper from `App.tsx` without a codemod may break existing consumers that rely on context injection.
- The new `refreshToken` function uses `async/await` inside a `useEffect` without an AbortController, which could cause state updates on unmounted components.

### 💡 Suggestions
- Add an `AbortController` signal to the `refreshToken` fetch call and abort it in the `useEffect` cleanup function to prevent memory leaks.
- Consider adding a `useAuthTransition` hook to handle loading states during token refresh, giving UI feedback to users.
- Add integration tests for the concurrent logout-during-refresh scenario described above.
- Document the migration path for components currently using `withAuth()` HOC pattern.

### Confidence: **Medium**

The diff is well-structured and the refactoring direction is sound, but the absence of tests for the new hook and the race condition risks reduce confidence in the correctness of the implementation.
