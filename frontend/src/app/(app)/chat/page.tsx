"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, MessageSquarePlus, Send, Sparkles, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/page-header";
import { cn, formatDateTime } from "@/lib/utils";
import { useApiQuery } from "@/lib/use-api";
import { api, ApiError } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

const SUGGESTIONS = [
  "What's my revenue trend this month?",
  "Which products have the highest refund rate?",
  "Who are my at-risk customers?",
  "Summarize my abandoned carts.",
];

export default function ChatPage() {
  const sessionsQuery = useApiQuery(() => api.chat.sessions());
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const messagesQuery = useApiQuery(
    () => (activeSessionId ? api.chat.messages(activeSessionId) : Promise.resolve<ChatMessage[]>([])),
    [activeSessionId],
  );

  useEffect(() => {
    setLocalMessages(messagesQuery.data ?? []);
  }, [messagesQuery.data]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [localMessages, sending]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setSendError(null);
    setInput("");
    const optimisticUser: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    setLocalMessages((prev) => [...prev, optimisticUser]);
    setSending(true);
    try {
      const res = await api.chat.send({ session_id: activeSessionId ?? undefined, message: trimmed });
      setActiveSessionId(res.session_id);
      setLocalMessages((prev) => [
        ...prev,
        { id: `local-reply-${Date.now()}`, role: "assistant", content: res.reply, created_at: new Date().toISOString() },
      ]);
      sessionsQuery.refetch();
    } catch (err) {
      setSendError(err instanceof ApiError ? err.message : "Could not send message. Please try again.");
    } finally {
      setSending(false);
    }
  }

  const sessions = sessionsQuery.data ?? [];

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col md:h-[calc(100vh-3.5rem)]">
      <PageHeader title="AI Chat" description="Ask about your store's performance -- the agent can query your live data." />

      <div className="flex min-h-0 flex-1 gap-4">
        <aside className="hidden w-56 shrink-0 flex-col gap-1 overflow-y-auto lg:flex">
          <Button
            variant="outline"
            size="sm"
            className="mb-2 justify-start"
            onClick={() => {
              setActiveSessionId(null);
              setLocalMessages([]);
            }}
          >
            <MessageSquarePlus className="h-4 w-4" />
            New conversation
          </Button>
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={cn(
                "truncate rounded-md px-3 py-2 text-left text-sm text-muted-foreground hover:bg-accent",
                activeSessionId === s.id && "bg-accent text-accent-foreground font-medium",
              )}
            >
              {s.title}
            </button>
          ))}
        </aside>

        <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border bg-card">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6">
            {localMessages.length === 0 && (
              <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-primary">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium">Ask MerchantGPT anything about your store</p>
                  <p className="mt-1 text-sm text-muted-foreground">It can query revenue, refunds, segments, churn, and carts.</p>
                </div>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => sendMessage(s)}
                      className="rounded-lg border border-border px-3 py-2 text-left text-sm text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex flex-col gap-4">
              {localMessages.map((m) => (
                <div key={m.id} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
                  <div
                    className={cn(
                      "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-line",
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground",
                    )}
                  >
                    {m.content}
                    <div
                      className={cn(
                        "mt-1 text-[10px] opacity-60",
                        m.role === "user" ? "text-primary-foreground" : "text-muted-foreground",
                      )}
                    >
                      {formatDateTime(m.created_at)}
                    </div>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-2.5 text-sm text-muted-foreground">
                    <Wrench className="h-3.5 w-3.5 animate-pulse" />
                    Thinking…
                  </div>
                </div>
              )}
            </div>
          </div>

          {sendError && <p className="mx-4 mb-2 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{sendError}</p>}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            className="flex items-center gap-2 border-t border-border p-3"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about revenue, leaks, churn, campaigns…"
              className="h-10 flex-1 rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={sending}
            />
            <Button type="submit" size="icon" disabled={sending || !input.trim()}>
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
