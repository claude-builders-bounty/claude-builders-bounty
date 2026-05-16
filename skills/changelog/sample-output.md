# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-16

### ⚠️ Breaking Changes

- remove deprecated API endpoints (`878c283`)

### 🔒 Security

- patch XSS vulnerability (`475e5dd`)

### ✨ Added

- Add new feature for dark mode (`79c9160`)
- add user authentication system (`a46586e`)

### 🔄 Changed

- Update configuration settings (`5b63d96`)
- format code with prettier (`f1175dc`)
- optimize image loading (`77fcfc2`)
- improve database connection pooling (`d3c3a05`)

### 🐛 Fixed

- Fix bug in login page (`75fbc84`)
- resolve memory leak in cache handler (`7b95705`)

### 🗑️ Removed

- delete legacy authentication flow (`b9cfd6f`)

### 📚 Documentation

- update API documentation (`9c7621b`)

### 📦 Other

- update webpack configuration (`901e189`)
- add GitHub Actions workflow (`249445f`)
- update dependencies (`4617d49`)
- add unit tests for auth module (`a3f7c84`)
