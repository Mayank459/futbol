import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const viewport: Viewport = {
  themeColor: "#07090e",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "Stake.ac Quant Terminal | Football AI Value-Betting & Arbitrage Intelligence",
  description: "Autonomous Football Quantitative Betting Terminal with Dixon-Coles xG, Kalman Form Momentum, Correlated Copula SGP Engine, and Pinnacle Latency Arbitrage Radar.",
  keywords: ["football quant", "value betting", "arbitrage", "kalman filter", "dixon-coles", "copula parlay", "stake.ac", "pinnacle"],
  authors: [{ name: "Stake Quant Engineering" }],
  openGraph: {
    title: "Stake.ac Quant Terminal | Football AI Value-Betting Intelligence",
    description: "High-Frequency Sports Quant & Latency Arbitrage Terminal. Powered by Dixon-Coles, Kalman filter form tracking, and SGP Copula models.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-cyber-darkest text-slate-100 min-h-screen selection:bg-cyan-500 selection:text-black`}
      >
        {children}
      </body>
    </html>
  );
}
