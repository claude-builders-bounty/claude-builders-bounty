import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CreateInvoiceForm } from "@/components/features/create-invoice-form";

vi.mock("@/server/actions/create-invoice", () => ({
  actionCreateInvoice: vi.fn(),
}));

describe("CreateInvoiceForm", () => {
  it("surfaces server action validation errors", async () => {
    const { actionCreateInvoice } = await import("@/server/actions/create-invoice");
    vi.mocked(actionCreateInvoice).mockResolvedValueOnce({
      ok: false,
      error: "Invalid input",
    });

    render(<CreateInvoiceForm orgSlug="acme" />);
    await userEvent.type(screen.getByRole("spinbutton"), "-1");
    await userEvent.click(screen.getByRole("button", { name: /create/i }));

    expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Invalid input");
  });
});
