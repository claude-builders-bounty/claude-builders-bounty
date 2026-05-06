# CLAUDE.md - SaaS Template Protocol

## Project Overview
This is a standard template for Next.js + SQLite SaaS projects. It includes project structure, build commands, and development guidelines for Claude Code agents.

## Build Commands
- `npm run dev`: Start local development server
- - `npm run build`: Build for production
  - - `npm run lint`: Run linting checks
    - - `npm run test`: Run test suite
      - - `npm run db:setup`: Initialize SQLite database schema
        - - `npm run db:migrate`: Run database migrations
         
          - ## Project Structure
          - - `/app`: Next.js App Router source
            - - `/components`: UI and shared components
              - - `/lib`: Server-side logic and database access
                - - `/db`: Database schema definitions
                  - - `/public`: Static assets
                    - - `/scripts`: Utility scripts for automation
                     
                      - ## Code Style & Conventions
                      - - Use TypeScript for all new code.
                        - - Follow the existing project structure for components.
                          - - Use `lib/db.ts` for all database interactions.
                            - - Ensure all environment variables are documented in `.env.example`.
                             
                              - ## Agent Guidelines
                              - - Always check `db/schema.sql` before making database changes.
                                - - Use `npm run build` to verify changes before submission.
                                  - 
