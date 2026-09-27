# Greenfield test notes

Cách test: `mkdir /tmp/greenfield && cp templates/nextjs-sqlite-saas/CLAUDE.md /tmp/greenfield/`,
đọc file như Claude mới onboard và check:

1. `npm run dev/build/test/db:migrate` — đủ 4 lệnh, không thiếu bước nào.
2. Mọi path trong §3 (`app/api`, `lib/db.ts`, `migrations/`) đều tạo được đúng như mô tả.
3. `lib/env.ts` copy-paste chạy ngay (chỉ `npm i zod`).
4. Migration example chạy được trên sqlite3 trống.
5. Không câu hỏi nào cần hỏi lại: stack, structure, naming, DB, CI đều có default.

`python3 validate_template.py` tự động hóa các check 1-4 (12 asserts).
Smoke prompts để hỏi Claude sau khi paste (đều trả lời được từ file):
- "Tôi thêm cột mới vào users thì làm gì?" → §5 rule 1 + example.
- "Form thanh toán viết ở đâu?" → §6 Server Action.
- "Thêm STRIPE_WEBHOOK_SECRET thì sửa gì?" → §7 env contract.
