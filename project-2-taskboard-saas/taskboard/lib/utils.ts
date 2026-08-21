import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** 合併 Tailwind class（shadcn/ui 的標準寫法） */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
