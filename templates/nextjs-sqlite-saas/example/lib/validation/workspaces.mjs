export function validateCreateWorkspace(input) {
  const errors = {};
  const name = String(input.name ?? "").trim();
  const slug = String(input.slug ?? "").trim().toLowerCase();

  if (name.length < 2) errors.name = "Workspace name must be at least 2 characters.";
  if (!/^[a-z0-9-]{3,40}$/.test(slug)) {
    errors.slug = "Slug must be 3-40 lowercase letters, numbers, or hyphens.";
  }

  if (Object.keys(errors).length > 0) {
    return { ok: false, errors };
  }

  return { ok: true, data: { name, slug } };
}
