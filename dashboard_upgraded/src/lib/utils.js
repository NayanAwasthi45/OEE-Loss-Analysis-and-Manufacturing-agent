import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function getOeeClass(value) {
  if (value >= 85) return "kpi-excellent";
  if (value >= 70) return "kpi-good";
  if (value >= 50) return "kpi-attention";
  return "kpi-critical";
}

export function getOeeColor(value) {
  if (value >= 85) return "#10b981";
  if (value >= 70) return "#06b6d4";
  if (value >= 50) return "#f59e0b";
  return "#f43f5e";
}

export function getValidationBadge(status) {
  switch (status) {
    case "Verified":
      return "badge-verified";
    case "Partially Verified":
      return "badge-partial";
    case "Mismatch":
      return "badge-mismatch";
    default:
      return "badge-skipped";
  }
}

export function formatCurrency(value) {
  if (value === null || value === undefined) return "₹0";
  return `₹${Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function formatPercent(value) {
  if (value === null || value === undefined) return "0%";
  return `${Number(value).toFixed(1)}%`;
}
