import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ForgeMind",
  description:
    "A secure autonomous engineering platform that turns high-level goals into complete, connected, verifiable software systems.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
