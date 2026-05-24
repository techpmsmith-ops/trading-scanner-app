"use client";

import { Bot, Send } from "lucide-react";
import { useState } from "react";
import { api, FocusExplainResponse, FocusExplanationContext } from "@/lib/api";

export function FocusExplainPanel({ context }: { context: FocusExplanationContext }) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const analysis = context.latest_analysis;

  async function ask(prompt?: string) {
    setLoading(true);
    setAnswer("");
    const asked = prompt || question;
    try {
      const response = await api<FocusExplainResponse>(`/phase2/focus/${context.symbol}/explain`, {
        method: "POST",
        body: JSON.stringify({ question: asked })
      });
      setAnswer(response.explanation);
      setQuestion(asked);
    } catch (exc) {
      setAnswer(exc instanceof Error ? exc.message : "Explanation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-md border border-border bg-panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">AI Explanation Assistant</h2>
          <p className="mt-1 text-sm text-muted">Grounded only in stored scanner, Focus Group, prediction, and sentiment context.</p>
        </div>
        <button onClick={() => setOpen((value) => !value)} className="inline-flex items-center gap-2 rounded-md border border-border bg-panelSoft px-3 py-2 text-sm">
          <Bot size={16} /> {open ? "Close" : "Ask AI"}
        </button>
      </div>
      {open ? (
        <div className="mt-4 space-y-4">
          <div className="rounded-md border border-border bg-panelSoft p-3 text-sm text-muted">
            <div className="font-semibold text-ink">{context.symbol} context loaded</div>
            <p className="mt-1">
              Bias {analysis?.bias || "-"} | Confidence {analysis ? `${Math.round(analysis.confidence * 100)}%` : "-"} | Risk {analysis?.risk_level || "-"} | Sentiment {analysis?.news_sentiment_label || "-"}
            </p>
            <p className="mt-2 text-xs text-caution">{context.disclaimer}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {["Why is this stock neutral?", "Why is risk high?", "What would make this bullish?", "Is this a trade setup or just a watchlist item?"].map((item) => (
              <button key={item} onClick={() => ask(item)} disabled={loading} className="rounded-md border border-border bg-panelSoft px-3 py-2 text-xs text-muted hover:text-ink disabled:opacity-60">
                {item}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <input value={question} onChange={(event) => setQuestion(event.target.value)} className="min-w-0 flex-1 px-3 py-2 text-sm" placeholder="Ask about this analysis..." />
            <button onClick={() => ask()} disabled={loading || !question.trim()} className="inline-flex items-center gap-2 bg-positive px-3 py-2 text-sm font-semibold text-[#07130d] disabled:opacity-60">
              <Send size={16} /> Ask
            </button>
          </div>
          {answer ? <div className="rounded-md border border-border bg-panelSoft p-3 text-sm leading-6 text-muted">{answer}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
