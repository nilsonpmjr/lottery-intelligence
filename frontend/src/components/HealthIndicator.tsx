"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";

type Status = "checking" | "connected" | "error";

export default function HealthIndicator() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    fetchHealth()
      .then(() => setStatus("connected"))
      .catch(() => setStatus("error"));
  }, []);

  const color = {
    checking: "bg-yellow-400",
    connected: "bg-green-500",
    error: "bg-red-500",
  }[status];

  const label = {
    checking: "Verificando API...",
    connected: "API Conectada",
    error: "API Indisponivel",
  }[status];

  return (
    <div className="flex items-center gap-2 text-sm text-zinc-400">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} />
      {label}
    </div>
  );
}
