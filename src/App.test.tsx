import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("Maxume App Entrypoint", () => {
  it("renders Maxume title and navigation items", () => {
    render(<App />);
    expect(screen.getByText("MAXUME")).toBeInTheDocument();
    expect(screen.getByText(/Maxume Job Application Assistant/i)).toBeInTheDocument();
    expect(screen.getByText(/Home Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Projects Sync/i)).toBeInTheDocument();
    expect(screen.getByText(/Apply & Optimize/i)).toBeInTheDocument();
    expect(screen.getByText(/History Logs/i)).toBeInTheDocument();
  });
});
