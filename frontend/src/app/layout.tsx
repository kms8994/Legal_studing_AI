import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "StackSync AI 판례 분석",
  description: "공식 법률 데이터와 AI 구조화를 활용한 판례 분석 워크스페이스",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
