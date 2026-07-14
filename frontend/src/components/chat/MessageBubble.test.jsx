import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import MessageBubble from "./MessageBubble";

vi.mock("../../lib/api", () => ({
  api: { post: vi.fn() },
}));

vi.mock("react-hot-toast", () => ({
  default: { error: vi.fn(), success: vi.fn() },
}));

function message(overrides = {}) {
  return {
    id: "m1",
    role: "assistant",
    message_type: "GENERAL",
    content: "Binary search halves the range each step.",
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

const REASONS = [
  { label: "Example-first", detail: "Started with a concrete example." },
  { label: "Extra care", detail: "Went slower on Recursion." },
];

describe("role styling", () => {
  it("renders a user message as plain text", () => {
    render(<MessageBubble message={message({ role: "user", content: "what is O(1)?" })} />);

    expect(screen.getByText("what is O(1)?")).toBeInTheDocument();
  });

  it("renders assistant content as markdown", () => {
    render(<MessageBubble message={message({ content: "**bold idea**" })} />);

    const strong = screen.getByText("bold idea");
    expect(strong.tagName).toBe("STRONG");
  });
});

describe("quiz messages", () => {
  it("renders a QuizCard instead of the text body", () => {
    render(
      <MessageBubble
        message={message({
          message_type: "QUIZ",
          content: "Quiz generated",
          quiz_data: {
            quiz_id: "q1",
            question: "Which is O(log n)?",
            options: { A: "linear scan", B: "binary search" },
            points: 10,
          },
        })}
      />
    );

    expect(screen.getByText("Which is O(log n)?")).toBeInTheDocument();
    // The placeholder body text must never leak into the UI.
    expect(screen.queryByText("Quiz generated")).not.toBeInTheDocument();
  });
});

describe("why this response", () => {
  it("summarises how many signals shaped the reply", () => {
    render(<MessageBubble message={message({ personalization_reasons: REASONS })} />);

    expect(screen.getByRole("button", { name: /why this response/i })).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("keeps the detail collapsed until asked", () => {
    render(<MessageBubble message={message({ personalization_reasons: REASONS })} />);

    expect(screen.queryByText(/started with a concrete example/i)).not.toBeInTheDocument();
  });

  it("reveals every reason when expanded", async () => {
    render(<MessageBubble message={message({ personalization_reasons: REASONS })} />);

    await userEvent.click(screen.getByRole("button", { name: /why this response/i }));

    expect(screen.getByText("Example-first")).toBeInTheDocument();
    expect(screen.getByText(/started with a concrete example/i)).toBeInTheDocument();
    expect(screen.getByText("Extra care")).toBeInTheDocument();
    expect(screen.getByText(/went slower on recursion/i)).toBeInTheDocument();
  });

  it("collapses again on a second click", async () => {
    render(<MessageBubble message={message({ personalization_reasons: REASONS })} />);
    const toggle = screen.getByRole("button", { name: /why this response/i });

    await userEvent.click(toggle);
    await userEvent.click(toggle);

    expect(screen.queryByText(/started with a concrete example/i)).not.toBeInTheDocument();
  });

  it("is absent when the reply carried no signals", () => {
    render(<MessageBubble message={message({ personalization_reasons: [] })} />);

    expect(screen.queryByRole("button", { name: /why this response/i })).not.toBeInTheDocument();
  });

  it("is absent on user messages even if reasons are attached", () => {
    render(
      <MessageBubble
        message={message({ role: "user", content: "hi", personalization_reasons: REASONS })}
      />
    );

    expect(screen.queryByRole("button", { name: /why this response/i })).not.toBeInTheDocument();
  });
});
