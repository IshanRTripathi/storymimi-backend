# Migration Roadmap: Supabase Client Refactor

## Overview
This document tracks the migration from a monolithic `supabase_client.py` file to a modular, maintainable structure.

---

## 📁 New File Structure

- `supabase_client/base.py`: Base client logic
- `supabase_client/users.py`: UserRepository
- `supabase_client/stories.py`: StoryRepository
- `supabase_client/scenes.py`: SceneRepository
- `supabase_client/storage.py`: StorageService
- `supabase_client/health.py`: SupabaseHealthService

---

## ✅ Migration Checklist

- [ ] Create `supabase_client/` directory
- [ ] Move core init logic to `base.py`
- [ ] Move user methods to `users.py`
- [ ] Move story methods to `stories.py`
- [ ] Move scene methods to `scenes.py`
- [ ] Move storage methods to `storage.py`
- [ ] Move health check to `health.py`
- [ ] Refactor service classes to inherit from `SupabaseBaseClient`
- [ ] Update imports in consuming code
- [ ] Run full integration tests
- [ ] Delete old monolithic `supabase_client.py`

---

## 📌 Tips

- Use `SupabaseBaseClient` for shared access to `self.client` and `self.storage`
- Ensure `__init__.py` files exist to treat folders as packages