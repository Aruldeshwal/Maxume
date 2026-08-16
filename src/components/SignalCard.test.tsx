import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import SignalCard from "./SignalCard";

describe("SignalCard Component", () => {
  it("renders informational notice when no signals are found", () => {
    render(<SignalCard status="NO_SIGNALS_FOUND" companyName="Acme Corp" />);
    
    expect(screen.getByTestId("signal-none-found")).toBeInTheDocument();
    expect(screen.getByText(/Informational Notice/i)).toBeInTheDocument();
    expect(screen.getByText(/No recent public signal found for/i)).toBeInTheDocument();
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
  });

  it("renders verified signal cards with source tiers when signals are found", () => {
    const mockSignals = [
      {
        signal_type: "product_launch",
        headline: "Acme unveils warehouse-picking arm v3",
        source_url: "https://acme.com/blog/arm-v3",
        source_tier: 1,
        published_at: "2026-08-01",
        guard_check_passed: true,
      },
      {
        signal_type: "funding",
        headline: "Acme raises $45M Series B for global expansion",
        source_url: "https://techcrunch.com/2026/acme-series-b",
        source_tier: 2,
        published_at: "2026-07-20",
        guard_check_passed: true,
      }
    ];

    render(<SignalCard status="FOUND" signals={mockSignals} companyName="Acme Corp" />);

    expect(screen.getByTestId("signal-found-container")).toBeInTheDocument();
    expect(screen.getByText(/Grounded Company Signals \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText("Acme unveils warehouse-picking arm v3")).toBeInTheDocument();
    expect(screen.getByText("Acme raises $45M Series B for global expansion")).toBeInTheDocument();
    expect(screen.getByText(/Tier 1: Official Domain/i)).toBeInTheDocument();
    expect(screen.getByText(/Tier 2: Tech Press/i)).toBeInTheDocument();
  });
});
