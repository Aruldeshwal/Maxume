import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import QuotaRing from "./QuotaRing";

describe("QuotaRing Component", () => {
  it("renders label, quota ratio, and correct percentage", () => {
    render(<QuotaRing label="Gemini 2.5 Flash" current={750} total={1000} unit="req/day" />);

    expect(screen.getByText("Gemini 2.5 Flash")).toBeInTheDocument();
    expect(screen.getByText("750 / 1,000 req/day")).toBeInTheDocument();
    expect(screen.getByTestId("quota-percentage")).toHaveTextContent("75%");
  });

  it("handles zero usage cleanly", () => {
    render(<QuotaRing label="Google CSE" current={0} total={100} unit="queries/day" />);

    expect(screen.getByText("Google CSE")).toBeInTheDocument();
    expect(screen.getByTestId("quota-percentage")).toHaveTextContent("0%");
  });
});
