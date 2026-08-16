import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import TerminalLog, { LogLine } from "./TerminalLog";

describe("TerminalLog Component", () => {
  it("renders empty placeholder when no logs provided", () => {
    render(<TerminalLog logs={[]} />);
    expect(screen.getByText(/Ready to execute job optimization pipeline/i)).toBeInTheDocument();
  });

  it("renders chronological stream logs with stages and messages", () => {
    const mockLogs: LogLine[] = [
      { id: "1", timestamp: "12:00:01", stage: "Research", message: "Searching for recent company signals..." },
      { id: "2", timestamp: "12:00:02", stage: "Research", message: "2 signals found and verified" },
      { id: "3", timestamp: "12:00:03", stage: "Ollama", message: "Swapping Resume Section {{PROJECTS}} & {{SKILLS}}..." },
      { id: "4", timestamp: "12:00:04", stage: "Completed", message: "Pack successfully written to /output/amazon/" },
    ];

    render(<TerminalLog logs={mockLogs} isRunning={true} />);

    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByText("Searching for recent company signals...")).toBeInTheDocument();
    expect(screen.getByText("2 signals found and verified")).toBeInTheDocument();
    expect(screen.getByText("Swapping Resume Section {{PROJECTS}} & {{SKILLS}}...")).toBeInTheDocument();
    expect(screen.getByText("Pack successfully written to /output/amazon/")).toBeInTheDocument();
  });
});
