import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../styles/globals.css'

const inter = Inter({ subsets: ['latin', 'greek'] })

export const metadata: Metadata = {
  title: 'News Copilot - Κατανόηση Ειδήσεων με AI',
  description: 'Κατανόηση Ελληνικών ειδήσεων με τεχνητή νοημοσύνη',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="el">
      <body className={inter.className}>{children}</body>
    </html>
  )
}