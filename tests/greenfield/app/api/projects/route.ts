import { NextResponse } from "next/server";
import { listProjects } from "@/lib/services/project";
import { projectQuery } from "@/lib/validation/project";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const parsed = projectQuery.safeParse(
    Object.fromEntries(new URL(request.url).searchParams),
  );
  if (!parsed.success) {
    return NextResponse.json({ error: "invalid_request" }, { status: 400 });
  }
  return NextResponse.json({ projects: listProjects(parsed.data.ownerId) });
}
