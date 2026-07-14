import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import QuizCard from "./QuizCard";
import { api } from "../../lib/api";

vi.mock("../../lib/api", () => ({
  api: { post: vi.fn() },
}));

vi.mock("react-hot-toast", () => ({
  default: { error: vi.fn(), success: vi.fn() },
}));

const QUIZ_ID = "11111111-1111-1111-1111-111111111111";

/** A quiz as the server sends it before any attempt: no answer key. */
function unanswered(overrides = {}) {
  return {
    quiz_id: QUIZ_ID,
    question: "What is the time complexity of binary search?",
    options: { A: "O(n)", B: "O(log n)", C: "O(1)", D: "O(n log n)" },
    difficulty: "INTERMEDIATE",
    points: 10,
    correct_option: null,
    hint: null,
    explanation: null,
    selected_option: null,
    is_correct: null,
    points_awarded: null,
    ...overrides,
  };
}

/** A quiz reloaded from history, where an attempt already exists. */
function answered(overrides = {}) {
  return unanswered({
    correct_option: "B",
    hint: "Halve the search space each step.",
    explanation: "Each comparison discards half the remaining elements.",
    selected_option: "B",
    is_correct: true,
    points_awarded: 10,
    ...overrides,
  });
}

beforeEach(() => {
  api.post.mockReset();
});

describe("rendering an unanswered quiz", () => {
  it("shows the question and every option", () => {
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    expect(screen.getByText(/time complexity of binary search/i)).toBeInTheDocument();
    for (const label of ["O(n)", "O(log n)", "O(1)", "O(n log n)"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("shows difficulty and points", () => {
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    expect(screen.getByText("INTERMEDIATE")).toBeInTheDocument();
    expect(screen.getByText(/10 pts/)).toBeInTheDocument();
  });

  it("disables submit until an option is chosen", async () => {
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    const submit = screen.getByRole("button", { name: /submit answer/i });
    expect(submit).toBeDisabled();

    await userEvent.click(screen.getByText("O(log n)"));
    expect(submit).toBeEnabled();
  });

  it("reveals no answer, hint or explanation before submitting", () => {
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    expect(screen.queryByText(/hint:/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/discards half/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/correct!/i)).not.toBeInTheDocument();
  });
});

describe("submitting an answer", () => {
  it("posts the quiz id and the chosen option", async () => {
    api.post.mockResolvedValue({
      correct: true,
      correct_option: "B",
      points_awarded: 10,
      explanation: "Each comparison discards half.",
    });
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    await userEvent.click(screen.getByText("O(log n)"));
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/quiz/submit", {
        quiz_id: QUIZ_ID,
        selected_option: "B",
      })
    );
  });

  it("reports a correct answer and its explanation", async () => {
    api.post.mockResolvedValue({
      correct: true,
      correct_option: "B",
      points_awarded: 10,
      explanation: "Each comparison discards half.",
    });
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    await userEvent.click(screen.getByText("O(log n)"));
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    expect(await screen.findByText(/correct!/i)).toBeInTheDocument();
    expect(screen.getByText(/\+10 pts/)).toBeInTheDocument();
    expect(screen.getByText(/discards half/i)).toBeInTheDocument();
  });

  it("shows the hint only when the answer was wrong", async () => {
    api.post.mockResolvedValue({
      correct: false,
      correct_option: "B",
      points_awarded: 0,
      hint: "Halve the search space each step.",
      explanation: "B is right.",
    });
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    await userEvent.click(screen.getByText("O(n)"));
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    expect(await screen.findByText(/not quite/i)).toBeInTheDocument();
    expect(screen.getByText(/halve the search space/i)).toBeInTheDocument();
  });

  it("hides the submit button once answered", async () => {
    api.post.mockResolvedValue({ correct: true, correct_option: "B", points_awarded: 10 });
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    await userEvent.click(screen.getByText("O(log n)"));
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() =>
      expect(screen.queryByRole("button", { name: /submit answer/i })).not.toBeInTheDocument()
    );
  });

  it("notifies the parent with the result", async () => {
    const result = { correct: true, correct_option: "B", points_awarded: 10 };
    api.post.mockResolvedValue(result);
    const onSubmitted = vi.fn();
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} onSubmitted={onSubmitted} />);

    await userEvent.click(screen.getByText("O(log n)"));
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() => expect(onSubmitted).toHaveBeenCalledWith(result));
  });

  it("stays answerable when the request fails", async () => {
    api.post.mockRejectedValue({ detail: "boom" });
    render(<QuizCard quizId={QUIZ_ID} quizData={unanswered()} />);

    await userEvent.click(screen.getByText("O(log n)"));
    await userEvent.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /submit answer/i })).toBeEnabled()
    );
  });
});

describe("a quiz reopened from history", () => {
  it("renders straight into the completed state", () => {
    render(<QuizCard quizId={QUIZ_ID} quizData={answered()} />);

    expect(screen.getByText(/correct!/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /submit answer/i })).not.toBeInTheDocument();
  });

  it("does not re-submit", async () => {
    render(<QuizCard quizId={QUIZ_ID} quizData={answered()} />);

    await userEvent.click(screen.getByText("O(n)"));

    expect(api.post).not.toHaveBeenCalled();
  });
});

describe("next question", () => {
  it("offers a follow-up once answered", async () => {
    const onNextQuestion = vi.fn();
    render(
      <QuizCard quizId={QUIZ_ID} quizData={answered()} onNextQuestion={onNextQuestion} />
    );

    await userEvent.click(screen.getByRole("button", { name: /next question/i }));

    expect(onNextQuestion).toHaveBeenCalledOnce();
  });

  it("does not offer one before answering", () => {
    render(
      <QuizCard quizId={QUIZ_ID} quizData={unanswered()} onNextQuestion={vi.fn()} />
    );

    expect(screen.queryByRole("button", { name: /next question/i })).not.toBeInTheDocument();
  });
});
