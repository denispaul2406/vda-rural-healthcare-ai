import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'VDA — Virtual Digital Assistant for Rural NCD Care',
  description: 'AI-guided NCD care navigation voice-first assistant in rural India',
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
