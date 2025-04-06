import "./globals.css";
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "News Search - Powered by Gemini and MiniLM-L12-v2",
  description: "Multilingual news search engine powered by Gemini 1.5 Flash and MiniLM-L12-v2",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}