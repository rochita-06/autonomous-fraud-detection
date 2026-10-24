"use client";

import { useState } from "react";
import { investigate, type InvestigateResult } from "@/lib/api";

const CATEGORIES = [
  "crypto_exchange",
  "gift_cards",
  "electronics",
  "groceries",
  "dining",
  "utilities",
  "fashion",
  "fuel",
];

const COUNTRIES = ["IN", "US", "GB", "SG", "AE", "NG", "BR", "DE"];

function localNowISO(): string {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export default function InvestigateForm({
  onStart,
  onResult,
  onError,
  busy,
}: {
  onStart: () => void;
  onResult: (r: InvestigateResult) => void;
  onError: (message: string) => void;
  busy: boolean;
}) {
  const [amount, setAmount] = useState("4800");
  const [country, setCountry] = useState("AE");
  const [time, setTime] = useState(localNowISO());
  const [userId, setUserId] = useState("U001");
  const [receiverId, setReceiverId] = useState("U033");
  const [category, setCategory] = useState("crypto_exchange");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    onStart();
    try {
      const result = await investigate({
        user_id: userId.trim() || "U001",
        receiver_id: receiverId.trim(),
        amount: parseFloat(amount) || 0,
        country,
        merchant_category: category,
        timestamp: time ? new Date(time).toISOString() : undefined,
      });
      onResult(result);
    } catch (err) {
      onError(err instanceof Error ? err.message : "investigation failed");
    }
  };

  return (
    <form onSubmit={submit} className="card card-hover h-full p-5">
      <div className="mb-1 text-sm font-semibold">Transaction Input</div>
      <p className="mb-4 text-[11px]" style={{ color: "var(--muted)" }}>
        Submit a transaction for autonomous investigation
      </p>

      <div className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
            Amount (USD)
          </span>
          <input
            className="field tabular"
            type="number"
            min="0"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
            Location
          </span>
          <select className="field" value={country} onChange={(e) => setCountry(e.target.value)}>
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="mb-1 block text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
            Time
          </span>
          <input
            className="field"
            type="datetime-local"
            value={time}
            onChange={(e) => setTime(e.target.value)}
          />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="mb-1 block text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
              Sender
            </span>
            <input className="field" value={userId} onChange={(e) => setUserId(e.target.value)} />
          </label>
          <label className="block">
            <span className="mb-1 block text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
              Receiver
            </span>
            <input className="field" value={receiverId} onChange={(e) => setReceiverId(e.target.value)} />
          </label>
        </div>

        <label className="block">
          <span className="mb-1 block text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
            Merchant Category
          </span>
          <select className="field" value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>

      <button type="submit" disabled={busy} className="btn-primary mt-5 w-full px-4 py-3 text-sm">
        {busy ? "Investigating…" : "Investigate Transaction"}
      </button>
    </form>
  );
}
