export const fetcher = (url: string) => fetch(url).then((res) => res.json());

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";
